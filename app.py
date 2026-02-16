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

    # Keep valid numeric rows
    df = df[pd.to_numeric(df["PLAN"], errors="coerce").notnull()]

    for col in ["PLAN", "COMPLETE", "jd- STOCK"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Shortage"] = df["PLAN"] - df["COMPLETE"]
    df["Completion %"] = (df["COMPLETE"] / df["PLAN"] * 100).fillna(0)

    # ---------------- KPI SECTION ----------------
    total_plan = df["PLAN"].sum()
    total_complete = df["COMPLETE"].sum()
    total_shortage = df["Shortage"].sum()
    total_stock = df["jd- STOCK"].sum()

    completion_percent = (total_complete / total_plan * 100) if total_plan else 0
    shortage_percent = (total_shortage / total_plan * 100) if total_plan else 0
    stock_coverage = (total_stock / total_shortage * 100) if total_shortage else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Plan", f"{total_plan:,.0f}")
    col2.metric("Total Complete", f"{total_complete:,.0f}")
    col3.metric("Completion %", f"{completion_percent:.1f}%")
    col4.metric("Total Shortage", f"{total_shortage:,.0f}")
    col5.metric("Stock Coverage %", f"{stock_coverage:.1f}%")

    st.markdown("---")

    # ---------------- RISK ANALYSIS ----------------
    shortage_items = df[df["Shortage"] > 0]
    high_risk = df[df["Completion %"] < 80]

    colA, colB = st.columns(2)

    # Completion Distribution
    fig_hist = px.histogram(
        df,
        x="Completion %",
        nbins=20,
        template="plotly_dark",
        title="Completion % Distribution"
    )

    colA.plotly_chart(fig_hist, use_container_width=True)

    # Plan vs Complete Gap
    fig_gap = px.bar(
        df.sort_values("Shortage", ascending=False).head(10),
        x="Shortage",
        y=df.sort_values("Shortage", ascending=False).head(10).index,
        orientation="h",
        template="plotly_dark",
        title="Top 10 Shortage Gaps"
    )

    colB.plotly_chart(fig_gap, use_container_width=True)

    st.markdown("---")

    # ---------------- DONUT OVERVIEW ----------------
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

    # ---------------- INSIGHT TEXT ----------------
    st.markdown("### Executive Insights")

    st.write(f"• {len(shortage_items)} items currently in shortage.")
    st.write(f"• {len(high_risk)} items below 80% completion.")
    st.write(f"• Overall completion stands at {completion_percent:.1f}%.")
