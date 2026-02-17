import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide")

st.title("Material Planning – Advanced Analytics Dashboard")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    excel = pd.ExcelFile(file)
    sheet = st.selectbox("Business Unit", excel.sheet_names)

    df = pd.read_excel(excel, sheet_name=sheet, header=1)
    df.columns = df.columns.str.strip()

    df = df[df["PART NAME"].notna()]

    # Convert numeric safely
    for col in ["TOTAL STOCK", "Shortage"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Estimate Required
    df["Required"] = df["TOTAL STOCK"] + df["Shortage"]

    # Avoid division by zero
    df["Gap %"] = np.where(
        df["Required"] > 0,
        (df["Shortage"] / df["Required"]) * 100,
        0
    )

    # ---------------- KPI SECTION ----------------
    total_required = df["Required"].sum()
    total_stock = df["TOTAL STOCK"].sum()
    total_shortage = df["Shortage"].sum()

    coverage_ratio = (total_stock / total_required * 100) if total_required else 0
    shortage_ratio = (total_shortage / total_required * 100) if total_required else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Required", f"{total_required:,.0f}")
    col2.metric("Stock Coverage %", f"{coverage_ratio:.1f}%")
    col3.metric("Shortage %", f"{shortage_ratio:.1f}%")
    col4.metric("Critical Items", int((df["Gap %"] > 40).sum()))

    st.markdown("---")

    # ---------------- SUPPLIER RISK ----------------
    if "Supplier" in df.columns:

        supplier_risk = (
            df.groupby("Supplier")
            .agg({
                "Shortage": "sum",
                "Required": "sum"
            })
            .reset_index()
        )

        supplier_risk["Risk %"] = (
            supplier_risk["Shortage"] /
            supplier_risk["Required"] * 100
        )

        fig_supplier = px.bar(
            supplier_risk.sort_values("Risk %", ascending=False),
            x="Risk %",
            y="Supplier",
            orientation="h",
            template="plotly_dark",
            title="Supplier Risk Ranking"
        )

        st.plotly_chart(fig_supplier, use_container_width=True)

    st.markdown("---")

    # ---------------- RISK HEAT MATRIX ----------------
    df["Demand Level"] = pd.qcut(df["Required"], 3, labels=["Low", "Medium", "High"])
    df["Risk Level"] = pd.qcut(df["Gap %"], 3, labels=["Low", "Medium", "High"])

    heat_data = df.groupby(["Demand Level", "Risk Level"]).size().reset_index(name="Count")

    fig_heat = px.density_heatmap(
        heat_data,
        x="Demand Level",
        y="Risk Level",
        z="Count",
        template="plotly_dark",
        title="Risk Heat Matrix"
    )

    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # ---------------- TOP RISK ITEMS ----------------
    top_risk = df.sort_values("Gap %", ascending=False).head(10)

    fig_top = px.bar(
        top_risk,
        x="Gap %",
        y="PART NAME",
        orientation="h",
        template="plotly_dark",
        title="Top 10 High Risk Parts"
    )

    st.plotly_chart(fig_top, use_container_width=True)

    st.markdown("---")

    # ---------------- ETA RISK ANALYSIS ----------------
    if "ETA" in df.columns:

        df["ETA Status"] = np.where(
            df["ETA"].isna(),
            "No ETA",
            "Has ETA"
        )

        eta_summary = df.groupby("ETA Status")["Shortage"].sum().reset_index()

        fig_eta = px.pie(
            eta_summary,
            names="ETA Status",
            values="Shortage",
            hole=0.6,
            template="plotly_dark",
            title="Shortage Exposure by ETA Status"
        )

        st.plotly_chart(fig_eta, use_container_width=True)

    st.markdown("### Executive Insight Summary")

    st.write(f"• {int((df['Gap %'] > 40).sum())} parts are critically exposed (>40% gap).")
    st.write(f"• {int((df['Gap %'] > 20).sum())} parts require immediate monitoring.")
    st.write(f"• Supplier risk concentration visible in ranking above.")
