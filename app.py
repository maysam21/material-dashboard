import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import math

st.set_page_config(layout="wide")

# ---------------- HEADER ----------------
#col_logo, col_title = st.columns([1, 4])
#with col_logo:
    #st.image("logo.png", width=120)
#with col_title:
    st.markdown(
        "<h2 style='padding-top:20px;'>Production Intelligence Command Center</h2>",
        unsafe_allow_html=True
    )

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    excel = pd.ExcelFile(file)
    sheet = st.selectbox("Business Unit", excel.sheet_names)

    df = pd.read_excel(excel, sheet_name=sheet, header=1)
    df.columns = df.columns.str.strip()
    df = df[df["PART NAME"].notna()]

    df["TOTAL STOCK"] = pd.to_numeric(df["TOTAL STOCK"], errors="coerce").fillna(0)
    df["QTY PER M/C"] = pd.to_numeric(df["QTY PER M/C"], errors="coerce").fillna(0)

    sku_columns = [
        col for col in df.columns
        if any(x in col for x in [
            "Arista", "Asteria", "Eris", "Elara", "Cube", "ORION"
        ])
    ]

    # ---------------- MULTI SKU FEASIBILITY ----------------
    multi_sku_results = []

    for sku in sku_columns:
        temp_df = df[df[sku].notna()].copy()
        temp_df["Required"] = pd.to_numeric(temp_df[sku], errors="coerce")
        temp_df = temp_df[temp_df["Required"].notna()]

        if temp_df.empty or (temp_df["TOTAL STOCK"] == 0).any():
            fg = 0
        else:
            temp_df["Possible"] = np.floor(
                temp_df["TOTAL STOCK"] / temp_df["Required"]
            )
            fg = int(temp_df["Possible"].min())

        multi_sku_results.append({"SKU": sku, "FG Buildable": fg})

    multi_df = pd.DataFrame(multi_sku_results)

    st.markdown("### Multi-SKU Feasibility Overview")

    fig_multi = px.bar(
        multi_df,
        x="SKU",
        y="FG Buildable",
        template="plotly_dark"
    )
    st.plotly_chart(fig_multi, use_container_width=True)

    # ---------------- SKU SELECTION ----------------
    colA, colB = st.columns(2)
    selected_sku = colA.selectbox("Select Primary SKU", sku_columns)
    compare_sku = colB.selectbox("Compare With SKU", sku_columns)

    def calculate_sku(sku_name):
        sku_df = df[df[sku_name].notna()].copy()
        sku_df["Required"] = pd.to_numeric(sku_df[sku_name], errors="coerce")
        sku_df = sku_df[sku_df["Required"].notna()]

        if sku_df.empty or (sku_df["TOTAL STOCK"] == 0).any():
            fg = 0
        else:
            sku_df["Possible"] = np.floor(
                sku_df["TOTAL STOCK"] / sku_df["Required"]
            )
            fg = int(sku_df["Possible"].min())

        return fg, sku_df

    fg_primary, sku_df = calculate_sku(selected_sku)
    fg_compare, _ = calculate_sku(compare_sku)

    # ---------------- WHAT-IF PLANNER ----------------
    st.markdown("### What-If Production Planner")

    target_qty = st.number_input(
        "Enter Target FG Quantity",
        min_value=0,
        step=10
    )

    if target_qty > 0:
        sku_df["Required_for_Target"] = sku_df["Required"] * target_qty
        sku_df["Additional_Needed"] = (
            sku_df["Required_for_Target"] - sku_df["TOTAL STOCK"]
        ).apply(lambda x: x if x > 0 else 0)

        total_additional = sku_df["Additional_Needed"].sum()

        st.write(f"Additional parts required to achieve target: {int(total_additional)} units")

    # ---------------- FORECAST AFTER ETA ----------------
    st.markdown("### Forecast After Incoming ETA Stock")

    if "Incoming Qty" in df.columns:
        df["Incoming Qty"] = pd.to_numeric(df["Incoming Qty"], errors="coerce").fillna(0)

        forecast_stock = sku_df["TOTAL STOCK"] + sku_df["Incoming Qty"]

        sku_df["Forecast_FG"] = np.floor(
            forecast_stock / sku_df["Required"]
        )

        forecast_fg = int(sku_df["Forecast_FG"].min())

        st.write(f"Projected FG Buildable After Incoming Stock: {forecast_fg}")

    # ---------------- FINANCIAL IMPACT ----------------
    st.markdown("### Financial Impact Analysis")

    if "Rate" in df.columns:
        df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce").fillna(0)

        sku_df["Shortage"] = sku_df["Required"] - sku_df["TOTAL STOCK"]
        sku_df["Shortage"] = sku_df["Shortage"].apply(lambda x: x if x > 0 else 0)

        sku_df["Financial Impact"] = sku_df["Shortage"] * sku_df["Rate"]

        total_impact = sku_df["Financial Impact"].sum()

        st.metric("Total Financial Exposure (₹)", f"{int(total_impact):,}")

    # ---------------- RISK HEATMAP ----------------
    st.markdown("### Risk Heatmap Matrix")

    sku_df["Demand Level"] = pd.qcut(
        sku_df["Required"],
        3,
        labels=["Low", "Medium", "High"]
    )

    sku_df["Stock Risk"] = pd.qcut(
        sku_df["TOTAL STOCK"],
        3,
        labels=["Low", "Medium", "High"]
    )

    heat_data = sku_df.groupby(
        ["Demand Level", "Stock Risk"]
    ).size().reset_index(name="Count")

    fig_heat = px.density_heatmap(
        heat_data,
        x="Demand Level",
        y="Stock Risk",
        z="Count",
        template="plotly_dark"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # ---------------- SKU COMPARISON ----------------
    st.markdown("### SKU Comparison")

    compare_df = pd.DataFrame({
        "SKU": [selected_sku, compare_sku],
        "FG Buildable": [fg_primary, fg_compare]
    })

    fig_compare = px.bar(
        compare_df,
        x="SKU",
        y="FG Buildable",
        template="plotly_dark"
    )
    st.plotly_chart(fig_compare, use_container_width=True)




