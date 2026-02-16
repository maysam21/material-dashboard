import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("Material Planning – Executive Analytical Dashboard")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    excel = pd.ExcelFile(file)
    selected_sheet = st.selectbox("Business Unit", excel.sheet_names)

    # Correct header row
    df = pd.read_excel(excel, sheet_name=selected_sheet, header=1)
    df.columns = df.columns.str.strip()

    # Keep only valid data rows (where PART NAME exists)
    df = df[df["PART NAME"].notna()]

    # Convert numeric columns safely
    numeric_cols = ["TOTAL STOCK", "Shortage"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ---------------- KPI ----------------
    total_stock = df["TOTAL STOCK"].sum()
    total_shortage = df["Shortage"].sum()

    total_required = total_stock + total_shortage
    completion_percent = ((total_required - total_shortage) / total_required * 100) if total_required else 0
    stock_coverage = (total_stock / total_shortage * 100) if total_shortage else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Required", f"{total_required:,.0f}")
    col2.metric("Total Stock Available", f"{total_stock:,.0f}")
    col3.metric("Total Shortage", f"{total_shortage:,.0f}")
    col4.metric("Stock Coverage %", f"{stock_coverage:.1f}%")

    st.markdown("---")

    # ---------------- SHORTAGE BY SUPPLIER ----------------
    if "Supplier" in df.columns:
        supplier_data = df.groupby("Supplier")["Shortage"].sum().sort_values(ascending=False)

        fig_supplier = px.bar(
            supplier_data.head(10),
            orientation="h",
            template="plotly_dark",
            title="Top 10 Supplier Shortages"
        )

        st.plotly_chart(fig_supplier, use_container_width=True)

    st.markdown("---")

    # ---------------- MODEL DEMAND BREAKDOWN ----------------
    model_columns = [
        col for col in df.columns
        if any(x in col for x in ["Arista", "Asteria", "BLDC"])
    ]

    model_totals = []
    for model in model_columns:
        total = pd.to_numeric(df[model], errors="coerce").sum()
        model_totals.append({"Model": model, "Total Demand": total})

    model_df = pd.DataFrame(model_totals)

    if not model_df.empty:
        fig_models = px.bar(
            model_df,
            x="Model",
            y="Total Demand",
            template="plotly_dark",
            title="Model-wise Demand Distribution"
        )
        st.plotly_chart(fig_models, use_container_width=True)

    st.markdown("---")

    # ---------------- CRITICAL SHORTAGE ITEMS ----------------
    critical = df.sort_values("Shortage", ascending=False).head(10)

    fig_critical = px.bar(
        critical,
        x="Shortage",
        y="PART NAME",
        orientation="h",
        template="plotly_dark",
        title="Top 10 Critical Shortage Parts"
    )

    st.plotly_chart(fig_critical, use_container_width=True)

    # ---------------- ETA RISK VIEW ----------------
    if "ETA" in df.columns:
        eta_risk = df[df["Shortage"] > 0][["PART NAME", "ETA", "Shortage"]]

        st.markdown("### Risk Items Awaiting ETA")
        st.dataframe(eta_risk.head(10), use_container_width=True)
