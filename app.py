import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("Material Planning – Analytical Executive Dashboard")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    excel = pd.ExcelFile(file)
    selected_sheet = st.selectbox("Business Unit", excel.sheet_names)

    df = pd.read_excel(excel, sheet_name=selected_sheet, header=1)
    df.columns = df.columns.astype(str).str.strip()

    # -------- AUTO DETECT IMPORTANT COLUMNS --------
    plan_col = None
    complete_col = None
    stock_col = None

    for col in df.columns:
        lower = col.lower()

        if "plan" in lower:
            plan_col = col
        if "complete" in lower:
            complete_col = col
        if "stock" in lower:
            stock_col = col

    if plan_col is None or complete_col is None:
        st.error("PLAN or COMPLETE column not found.")
        st.write("Detected columns:", df.columns.tolist())
        st.stop()

    # Keep only valid numeric rows
    df = df[pd.to_numeric(df[plan_col], errors="coerce").notnull()]

    df[plan_col] = pd.to_numeric(df[plan_col], errors="coerce").fillna(0)
    df[complete_col] = pd.to_numeric(df[complete_col], errors="coerce").fillna(0)

    if stock_col:
        df[stock_col] = pd.to_numeric(df[stock_col], errors="coerce").fillna(0)
    else:
        df["Stock_Auto"] = 0
        stock_col = "Stock_Auto"

    # -------- CALCULATIONS --------
    df["Shortage"] = df[plan_col] - df[complete_col]
    df["Completion %"] = (df[complete_col] / df[plan_col] * 100).fillna(0)

    total_plan = df[plan_col].sum()
    total_complete = df[complete_col].sum()
    total_stock = df[stock_col].sum()
    total_shortage = df["Shortage"].sum()

    completion_percent = (total_complete / total_plan * 100) if total_plan else 0
    stock_coverage = (total_stock / total_shortage * 100) if total_shortage else 0

    # -------- KPI --------
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Plan", f"{total_plan:,.0f}")
    col2.metric("Total Complete", f"{total_complete:,.0f}")
    col3.metric("Completion %", f"{completion_percent:.1f}%")
    col4.metric("Total Shortage", f"{total_shortage:,.0f}")
    col5.metric("Stock Coverage %", f"{stock_coverage:.1f}%")

    st.markdown("---")

    # -------- RISK DISTRIBUTION --------
    colA, colB = st.columns(2)

    fig_hist = px.histogram(
        df,
        x="Completion %",
        nbins=20,
        template="plotly_dark",
        title="Completion % Distribution"
    )

    colA.plotly_chart(fig_hist, use_container_width=True)

    top_shortage = df.sort_values("Shortage", ascending=False).head(10)

    fig_gap = px.bar(
        top_shortage,
        x="Shortage",
        y=top_shortage.index,
        orientation="h",
        template="plotly_dark",
        title="Top 10 Shortage Gaps"
    )

    colB.plotly_chart(fig_gap, use_container_width=True)

    st.markdown("---")

    # -------- OVERALL PROGRESS --------
    fig_donut = go.Figure(data=[go.Pie(
        labels=["Completed", "Remaining"],
        values=[total_complete, total_shortage],
        hole=0.7
    )])

    fig_donut.update_layout(
        template="plotly_dark",
        title=f"{selected_sheet} – Overall Progress"
    )

    st.plotly_chart(fig_donut, use_container_width=True)

    # -------- INSIGHTS --------
    st.markdown("### Executive Insights")

    shortage_items = len(df[df["Shortage"] > 0])
    high_risk = len(df[df["Completion %"] < 80])

    st.write(f"• {shortage_items} items currently in shortage.")
    st.write(f"• {high_risk} items below 80% completion.")
    st.write(f"• Overall completion stands at {completion_percent:.1f}%.")
