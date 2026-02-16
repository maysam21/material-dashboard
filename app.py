import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("Material Planning Dashboard - Q4")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

    # READ FILE
    if file is not None:

    # Read correct header row
    df = pd.read_excel(file, header=2)

    # Clean column names
    df.columns = df.columns.str.strip()

    st.write("Detected Columns:", df.columns.tolist())

    # AUTO DETECT COLUMNS
    required_col = None
    stock_col = None
    shortage_col = None
    supplier_col = None
    part_col = None
    eta_col = None

    for col in df.columns:
        if "req" in col.lower():
            required_col = col
        if "stock" in col.lower() or "avail" in col.lower():
            stock_col = col
        if "short" in col.lower():
            shortage_col = col
        if "supplier" in col.lower():
            supplier_col = col
        if "part" in col.lower() or "material" in col.lower():
            part_col = col
        if "eta" in col.lower() or "month" in col.lower():
            eta_col = col

    if required_col and stock_col:

        total_required = df[required_col].sum()
        total_stock = df[stock_col].sum()
        total_shortage = total_required - total_stock
        shortage_percent = (total_shortage / total_required) * 100

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Required", f"{total_required:,.0f}")
        col2.metric("Total Stock", f"{total_stock:,.0f}")
        col3.metric("Total Shortage", f"{total_shortage:,.0f}")
        col4.metric("Shortage %", f"{shortage_percent:.1f}%")

        st.markdown("---")

        # Donut Chart
        if supplier_col and shortage_col:
            supplier_data = df.groupby(supplier_col)[shortage_col].sum().sort_values(ascending=False).head(10)

            fig_donut = go.Figure(data=[go.Pie(
                labels=supplier_data.index,
                values=supplier_data.values,
                hole=.6
            )])

            fig_donut.update_layout(template="plotly_dark",
                                    title="Shortage by Supplier (Top 10)")

            st.plotly_chart(fig_donut, use_container_width=True)

        # Area Chart
        if eta_col and shortage_col:
            trend = df.groupby(eta_col)[shortage_col].sum().reset_index()

            fig_area = px.area(trend,
                               x=eta_col,
                               y=shortage_col,
                               template="plotly_dark",
                               title="Shortage Trend vs ETA")

            st.plotly_chart(fig_area, use_container_width=True)

        # Top Parts
        if part_col and shortage_col:
            top_parts = df.sort_values(shortage_col, ascending=False).head(10)

            fig_bar = px.bar(top_parts,
                             x=shortage_col,
                             y=part_col,
                             orientation="h",
                             template="plotly_dark",
                             title="Top 10 Shortage Parts")

            st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.error("Required or Stock column not found in Excel.")


