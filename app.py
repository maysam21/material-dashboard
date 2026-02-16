import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Material Planning Dashboard - Q4")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    # Read without header
    df_raw = pd.read_excel(file, header=None)

    # Header row is row 10 (index 10)
    df = pd.read_excel(file, header=10)

    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    # Remove empty rows
    df = df.dropna(how="all")

    st.write("Detected Columns:", df.columns.tolist())

    # ---- COLUMN MAPPING (BASED ON YOUR FILE) ----
    required_col = "PLAN"
    stock_col = "jd- STOCK"
    complete_col = "COMPLETE"

    # Ensure numeric
    for col in [required_col, stock_col, complete_col]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Calculate Shortage
    df["Shortage"] = df[required_col] - df[complete_col]

    # KPI
    total_required = df[required_col].sum()
    total_stock = df[stock_col].sum()
    total_shortage = df["Shortage"].sum()
    shortage_percent = (total_shortage / total_required * 100) if total_required else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Plan", f"{total_required:,.0f}")
    col2.metric("Total Stock", f"{total_stock:,.0f}")
    col3.metric("Total Shortage", f"{total_shortage:,.0f}")
    col4.metric("Shortage %", f"{shortage_percent:.1f}%")

    st.markdown("---")

    # Top Items by Shortage
    top_items = df.sort_values("Shortage", ascending=False).head(10)

    fig_bar = px.bar(
        top_items,
        x="Shortage",
        y=df.columns[0],
        orientation="h",
        template="plotly_dark",
        title="Top 10 Shortage Items"
    )

    st.plotly_chart(fig_bar, use_container_width=True)
