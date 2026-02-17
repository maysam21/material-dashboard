import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")

st.title("Material Planning – SKU Intelligence Dashboard")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    excel = pd.ExcelFile(file)
    sheet = st.selectbox("Business Unit", excel.sheet_names)

    df = pd.read_excel(excel, sheet_name=sheet, header=1)
    df.columns = df.columns.str.strip()

    df = df[df["PART NAME"].notna()]

    # Convert numeric safely
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    sku_list = df["PART NUMBER"].dropna().unique()
    selected_sku = st.selectbox("Select SKU (Part Number)", sku_list)

    sku_df = df[df["PART NUMBER"] == selected_sku].iloc[0]

    # ---------------- CORE METRICS ----------------
    total_stock = pd.to_numeric(sku_df["TOTAL STOCK"], errors="coerce")
    shortage = pd.to_numeric(sku_df["Shortage"], errors="coerce")
    required = total_stock + shortage

    gap_percent = (shortage / required * 100) if required else 0

    # Risk classification
    if gap_percent > 40:
        risk = "🔴 CRITICAL"
        color = "red"
    elif gap_percent > 20:
        risk = "🟡 WATCH"
        color = "orange"
    else:
        risk = "🟢 HEALTHY"
        color = "green"

    # ---------------- KPI ROW ----------------
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Required", f"{required:,.0f}")
    col2.metric("Stock", f"{total_stock:,.0f}")
    col3.metric("Shortage", f"{shortage:,.0f}")
    col4.metric("Gap %", f"{gap_percent:.1f}%")
    col5.markdown(f"<h3 style='color:{color}'>{risk}</h3>", unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- MODEL BREAKDOWN ----------------
    model_cols = [
        col for col in df.columns
        if any(x in col for x in ["Arista", "Asteria", "BLDC"])
    ]

    model_data = []
    for model in model_cols:
        val = pd.to_numeric(sku_df[model], errors="coerce")
        if not pd.isna(val):
            model_data.append({"Model": model, "Demand": val})

    model_df = pd.DataFrame(model_data)

    colA, colB = st.columns(2)

    if not model_df.empty:
        fig_model = px.bar(
            model_df,
            x="Model",
            y="Demand",
            template="plotly_dark",
            title="Model-wise Demand"
        )
        colA.plotly_chart(fig_model, use_container_width=True)

    # ---------------- STOCK vs SHORTAGE ----------------
    fig_donut = go.Figure(data=[go.Pie(
        labels=["Stock", "Shortage"],
        values=[total_stock, shortage],
        hole=0.65
    )])

    fig_donut.update_layout(
        template="plotly_dark",
        title="Supply Position"
    )

    colB.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("---")

    # ---------------- PROCUREMENT DETAILS ----------------
    st.markdown("### Procurement & Supply Details")

    details_cols = [
        "Supplier", "PO Number", "ETA", "Received Qty"
    ]

    detail_data = {}
    for col in details_cols:
        if col in df.columns:
            detail_data[col] = sku_df[col]

    st.table(pd.DataFrame(detail_data.items(), columns=["Field", "Value"]))

    st.markdown("---")

    st.markdown("### Executive Insight")

    st.write(f"• This SKU has a {gap_percent:.1f}% supply gap.")
    st.write(f"• Supplier: {sku_df.get('Supplier', 'N/A')}")
    st.write(f"• Current stock covers {((total_stock / required)*100 if required else 0):.1f}% of demand.")
