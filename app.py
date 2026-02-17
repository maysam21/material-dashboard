import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide")

st.title("SKU Wise – Production Clarity Dashboard")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    excel = pd.ExcelFile(file)
    sheet = st.selectbox("Business Unit", excel.sheet_names)

    # Read sheet with correct header
    df = pd.read_excel(excel, sheet_name=sheet, header=1)
    df.columns = df.columns.str.strip()

    # Keep only rows where PART NAME exists
    df = df[df["PART NAME"].notna()]

    # Detect SKU columns dynamically
    sku_columns = [
        col for col in df.columns
        if any(x in col for x in [
            "Arista", "Asteria", "Eris", "Elara", "Cube", "ORION"
        ])
    ]

    selected_sku = st.selectbox("Select SKU", sku_columns)

    # Convert stock safely
    df["TOTAL STOCK"] = pd.to_numeric(df["TOTAL STOCK"], errors="coerce").fillna(0)

    # ---- VERTICAL LOGIC ----
    # Required only if cell is NOT blank

    required_series = df[selected_sku]

    # Keep only rows where SKU cell is NOT blank
    sku_df = df[required_series.notna()].copy()

    # Convert required qty safely
    sku_df["Required"] = pd.to_numeric(sku_df[selected_sku], errors="coerce")

    # Drop rows where conversion failed
    sku_df = sku_df[sku_df["Required"].notna()]

    # Shortage calculation
    sku_df["Shortage"] = sku_df["Required"] - sku_df["TOTAL STOCK"]
    sku_df["Shortage"] = sku_df["Shortage"].apply(lambda x: x if x > 0 else 0)

    # ---------------- KPI ----------------
    total_required = sku_df["Required"].sum()
    total_stock = sku_df["TOTAL STOCK"].sum()
    total_shortage = sku_df["Shortage"].sum()

    gap_percent = (total_shortage / total_required * 100) if total_required else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Required", f"{total_required:,.0f}")
    col2.metric("Total Stock", f"{total_stock:,.0f}")
    col3.metric("Total Shortage", f"{total_shortage:,.0f}")
    col4.metric("Gap %", f"{gap_percent:.1f}%")

    st.markdown("---")

    # ---------------- PRODUCTION FEASIBILITY ----------------
    sku_df["Build Capacity"] = np.where(
        sku_df["Required"] > 0,
        sku_df["TOTAL STOCK"] / sku_df["Required"],
        np.inf
    )

    max_build_units = int(sku_df["Build Capacity"].min()) if not sku_df.empty else 0

    st.markdown(f"### Production Feasibility")
    st.write(f"Based on current stock, you can build approximately **{max_build_units} units** of {selected_sku}.")

    st.markdown("---")

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
        sku_df[["PART NAME", "Required", "TOTAL STOCK", "Shortage", "Supplier", "ETA"]],
        use_container_width=True
    )

