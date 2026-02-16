import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Material Planning Dashboard")

st.title("Material Planning Dashboard - Q4")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])


# -------- FUNCTION TO AUTO-DETECT HEADER ROW --------
def read_excel_smart(uploaded_file):
    for i in range(6):  # Try first 6 rows as header
        try:
            df_test = pd.read_excel(uploaded_file, header=i)
            cols = df_test.columns.astype(str)

            # If at least one useful column name found → return
            if any("req" in c.lower() or "stock" in c.lower() or "supplier" in c.lower() for c in cols):
                return df_test
        except:
            continue
    return None


if file is not None:

    df = read_excel_smart(file)

    if df is None:
        st.error("Could not detect proper header row. Please check Excel format.")
        st.stop()

    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    # -------- AUTO DETECT COLUMNS --------
    required_col = None
    stock_col = None
    shortage_col = None
    supplier_col = None
    part_col = None
    eta_col = None

    for col in df.columns:
        col_lower = col.lower()

        if "req" in col_lower:
            required_col = col
        if "stock" in col_lower or "avail" in col_lower:
            stock_col = col
        if "short" in col_lower:
            shortage_col = col
        if "supplier" in col_lower or "vendor" in col_lower:
            supplier_col = col
        if "part" in col_lower or "material" in col_lower or "item" in col_lower:
            part_col = col
        if "eta" in col_lower or "month" in col_lower or "date" in col_lower:
            eta_col = col

    if required_col is None or stock_col is None:
        st.error("Required or Stock column not found in Excel.")
        st.write("Detected Columns:", df.columns.tolist())
        st.stop()

    # Convert numeric columns safely
    df[required_col] = pd.to_numeric(df[required_col], errors="coerce").fillna(0)
    df[stock_col] = pd.to_numeric(df[stock_col], errors="coerce").fillna(0)

    if shortage_col:
        df[shortage_col] = pd.to_numeric(df[shortage_col], errors="coerce").fillna(0)
    else:
        df["Shortage_Calc"] = df[required_col] - df[stock_col]
        shortage_col = "Shortage_Calc"

    # -------- KPI CALCULATION --------
    total_required = df[required_col].sum()
    total_stock = df[stock_col].sum()
    total_shortage = df[shortage_col].sum()
    shortage_percent = (total_shortage / total_required * 100) if total_required != 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Required", f"{total_required:,.0f}")
    col2.metric("Total Stock", f"{total_stock:,.0f}")
    col3.metric("Total Shortage", f"{total_shortage:,.0f}")
    col4.metric("Shortage %", f"{shortage_percent:.1f}%")

    st.markdown("---")

    # -------- DONUT CHART --------
    if supplier_col:
        supplier_data = (
            df.groupby(supplier_col)[shortage_col]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        fig_donut = go.Figure(data=[go.Pie(
            labels=supplier_data.index,
            values=supplier_data.values,
            hole=0.6
        )])

        fig_donut.update_layout(
            template="plotly_dark",
            title="Shortage by Supplier (Top 10)"
        )

        st.plotly_chart(fig_donut, use_container_width=True)

    # -------- AREA TREND --------
    if eta_col:
        trend = df.groupby(eta_col)[shortage_col].sum().reset_index()

        fig_area = px.area(
            trend,
            x=eta_col,
            y=shortage_col,
            template="plotly_dark",
            title="Shortage Trend vs ETA"
        )

        st.plotly_chart(fig_area, use_container_width=True)

    # -------- TOP PARTS --------
    if part_col:
        top_parts = df.sort_values(shortage_col, ascending=False).head(10)

        fig_bar = px.bar(
            top_parts,
            x=shortage_col,
            y=part_col,
            orientation="h",
            template="plotly_dark",
            title="Top 10 Shortage Parts"
        )

        st.plotly_chart(fig_bar, use_container_width=True)
