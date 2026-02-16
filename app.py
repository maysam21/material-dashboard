import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Material Planning Dashboard")

st.title("Material Planning Dashboard - Q4")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file is not None:

    # IMPORTANT: header row is 2nd row in your Excel
    df = pd.read_excel(file, header=1)

    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    # Keep only useful columns
    required_columns = ["PLAN", "COMPLETE", "PENDING"]

    for col in required_columns:
        if col not in df.columns:
            st.error(f"Column '{col}' not found in Excel.")
            st.write("Detected columns:", df.columns.tolist())
            st.stop()

    # Remove empty rows
    df = df.dropna(subset=["PLAN", "COMPLETE"], how="all")

    # Convert numeric safely
    df["PLAN"] = pd.to_numeric(df["PLAN"], errors="coerce").fillna(0)
    df["COMPLETE"] = pd.to_numeric(df["COMPLETE"], errors="coerce").fillna(0)

    # Calculate Shortage
    df["Shortage"] = df["PLAN"] - df["COMPLETE"]

    # ---------- KPI ----------
    total_plan = df["PLAN"].sum()
    total_complete = df["COMPLETE"].sum()
    total_shortage = df["Shortage"].sum()
    shortage_percent = (total_shortage / total_plan * 100) if total_plan else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Plan", f"{total_plan:,.0f}")
    col2.metric("Total Complete", f"{total_complete:,.0f}")
    col3.metric("Total Shortage", f"{total_shortage:,.0f}")
    col4.metric("Shortage %", f"{shortage_percent:.1f}%")

    st.markdown("---")

    # ---------- DONUT ----------
    fig_donut = go.Figure(data=[go.Pie(
        labels=["Complete", "Shortage"],
        values=[total_complete, total_shortage],
        hole=0.6
    )])

    fig_donut.update_layout(
        template="plotly_dark",
        title="Completion vs Shortage"
    )

    st.plotly_chart(fig_donut, use_container_width=True)

    # ---------- TOP SHORTAGE ROWS ----------
    top_rows = df.sort_values("Shortage", ascending=False).head(10)

    fig_bar = px.bar(
        top_rows,
        x="Shortage",
        y=top_rows.index,
        orientation="h",
        template="plotly_dark",
        title="Top 10 Shortage Rows"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### Detailed Data")
    st.dataframe(df[["PLAN", "COMPLETE", "Shortage"]], use_container_width=True)
