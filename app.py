import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    layout="wide",
    page_title="Material Planning Dashboard"
)

st.title("Material Planning Dashboard - Q4")

file = st.file_uploader("Upload Clean Material Planning Excel", type=["xlsx"])

if file is not None:

    # Read clean structured file
    df = pd.read_excel(file)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Ensure required columns exist
    required_columns = ["Item", "Plan", "Complete", "Stock", "Shortage"]

    for col in required_columns:
        if col not in df.columns:
            st.error(f"Column '{col}' not found in Excel.")
            st.stop()

    # Convert numeric safely
    for col in ["Plan", "Complete", "Stock", "Shortage"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ---------------- KPI SECTION ----------------
    total_plan = df["Plan"].sum()
    total_complete = df["Complete"].sum()
    total_stock = df["Stock"].sum()
    total_shortage = df["Shortage"].sum()

    shortage_percent = (total_shortage / total_plan * 100) if total_plan != 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Plan", f"{total_plan:,.0f}")
    col2.metric("Total Complete", f"{total_complete:,.0f}")
    col3.metric("Total Stock", f"{total_stock:,.0f}")
    col4.metric("Shortage %", f"{shortage_percent:.1f}%")

    st.markdown("---")

    # ---------------- DONUT CHART ----------------
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

    # ---------------- TOP SHORTAGE ITEMS ----------------
    top_items = df.sort_values("Shortage", ascending=False).head(10)

    fig_bar = px.bar(
        top_items,
        x="Shortage",
        y="Item",
        orientation="h",
        template="plotly_dark",
        title="Top 10 Shortage Items"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # ---------------- DATA TABLE ----------------
    st.markdown("### Detailed Data")
    st.dataframe(df, use_container_width=True)
