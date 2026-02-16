import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("Material Planning – Executive Dashboard")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    excel = pd.ExcelFile(file)
    selected_sheet = st.selectbox("Select Business Unit", excel.sheet_names)

    # Use correct header row
    df = pd.read_excel(excel, sheet_name=selected_sheet, header=1)

    df.columns = df.columns.astype(str).str.strip()

    # Keep only real data rows (where PLAN is numeric)
    df = df[pd.to_numeric(df["PLAN"], errors="coerce").notnull()]

    # Convert numeric properly
    numeric_cols = ["PLAN", "COMPLETE", "PENDING", "jd- STOCK"]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Calculate Shortage properly
    df["Shortage"] = df["PLAN"] - df["COMPLETE"]

    # ---------------- KPIs ----------------
    total_plan = df["PLAN"].sum()
    total_complete = df["COMPLETE"].sum()
    total_stock = df["jd- STOCK"].sum() if "jd- STOCK" in df.columns else 0
    total_shortage = df["Shortage"].sum()

    shortage_percent = (total_shortage / total_plan * 100) if total_plan else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Plan", f"{total_plan:,.0f}")
    col2.metric("Total Complete", f"{total_complete:,.0f}")
    col3.metric("Total Stock", f"{total_stock:,.0f}")
    col4.metric("Shortage %", f"{shortage_percent:.1f}%")

    st.markdown("---")

    # ---------------- DONUT ----------------
    fig_donut = go.Figure(data=[go.Pie(
        labels=["Complete", "Shortage"],
        values=[total_complete, total_shortage],
        hole=0.65
    )])

    fig_donut.update_layout(
        template="plotly_dark",
        title=f"{selected_sheet} – Completion vs Shortage"
    )

    st.plotly_chart(fig_donut, use_container_width=True)

    # ---------------- TOP SHORTAGE ----------------
    top_shortage = df.sort_values("Shortage", ascending=False).head(10)

    fig_bar = px.bar(
        top_shortage,
        x="Shortage",
        y=top_shortage.index,
        orientation="h",
        template="plotly_dark",
        title="Top 10 Shortage Rows"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### Detailed Data")
    st.dataframe(df[["PLAN", "COMPLETE", "Shortage"]], use_container_width=True)
