import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import math

st.set_page_config(layout="wide")

st.title("SKU Wise – Production Clarity Dashboard")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    excel = pd.ExcelFile(file)
    sheet = st.selectbox("Business Unit", excel.sheet_names)

    # Read sheet
    df = pd.read_excel(excel, sheet_name=sheet, header=1)
    df.columns = df.columns.str.strip()

    df = df[df["PART NAME"].notna()]

    # Detect SKU columns
    sku_columns = [
        col for col in df.columns
        if any(x in col for x in [
            "Arista", "Asteria", "Eris", "Elara", "Cube", "ORION"
        ])
    ]

    selected_sku = st.selectbox("Select SKU", sku_columns)

    # ---------------- JFM PRODUCTION PLAN ----------------
    production_qty = pd.to_numeric(df.iloc[0][selected_sku], errors="coerce")

    # Convert numeric safely
    df["TOTAL STOCK"] = pd.to_numeric(df["TOTAL STOCK"], errors="coerce").fillna(0)
    df["QTY PER M/C"] = pd.to_numeric(df["QTY PER M/C"], errors="coerce").fillna(0)

    # ---- Vertical Logic ----
    required_series = df[selected_sku]
    sku_df = df[required_series.notna()].copy()

    sku_df["Required"] = pd.to_numeric(sku_df[selected_sku], errors="coerce")
    sku_df = sku_df[sku_df["Required"].notna()]

    # Shortage
    sku_df["Shortage"] = sku_df["Required"] - sku_df["TOTAL STOCK"]
    sku_df["Shortage"] = sku_df["Shortage"].apply(lambda x: x if x > 0 else 0)

    # ---------------- KPI ----------------
    total_required = sku_df["Required"].sum()
    total_stock = sku_df["TOTAL STOCK"].sum()
    total_shortage = sku_df["Shortage"].sum()

    gap_percent = (total_shortage / total_required * 100) if total_required else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("JFM Production Plan", int(production_qty) if not pd.isna(production_qty) else 0)
    col2.metric("Total Required", f"{total_required:,.0f}")
    col3.metric("Total Stock", f"{total_stock:,.0f}")
    col4.metric("Total Shortage", f"{total_shortage:,.0f}")
    col5.metric("Gap %", f"{gap_percent:.1f}%")

    st.markdown("---")

    # ---------------- NEW FG LOGIC (YOUR REQUEST) ----------------
    # ---------------- TRUE FG LOGIC ----------------

# If any required part has zero stock → production = 0
if (sku_df["TOTAL STOCK"] == 0).any():
    fg_buildable = 0
    production_status = "🔴 BLOCKED – At least one required part has zero stock."
else:
    sku_df["Possible_FG_From_Part"] = np.floor(
        sku_df["TOTAL STOCK"] / sku_df["Required"]
    )
    fg_buildable = int(sku_df["Possible_FG_From_Part"].min())
    production_status = "🟢 Production Feasible"

st.markdown("### Production Feasibility")

st.metric("FG Buildable", fg_buildable)
st.write(production_status)

# Identify bottleneck part only if production possible
if fg_buildable > 0:
    bottleneck_part = sku_df.loc[
        sku_df["Possible_FG_From_Part"].idxmin()
    ]["PART NAME"]

    st.write(f"**Bottleneck Part:** {bottleneck_part}")


    # ---------------- TOP BOTTLENECK PARTS ----------------
    bottleneck = sku_df.sort_values("Shortage", ascending=False).head(10)

    fig = px.bar(
        bottleneck,
        x="Shortage",
        y="PART NAME",
        orientation="h",
        template="plotly_dark",
        title=f"Bottleneck Parts – {selected_sku}"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.markdown("### Parts Required for This SKU")
    st.dataframe(
        sku_df[[
            "PART NAME",
            "QTY PER M/C",
            "Required",
            "TOTAL STOCK",
            "Shortage",
            "Supplier",
            "ETA"
        ]],
        use_container_width=True
    )
