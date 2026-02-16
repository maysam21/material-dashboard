import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Material Planning Dashboard")

# ------------------- Dark Executive Style -------------------
st.markdown("""
<style>
body {
    background-color: #0b1c2d;
}
.metric-card {
    background: linear-gradient(145deg, #0e2238, #0b1c2d);
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    color: white;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
}
.big-font {
    font-size: 34px;
    font-weight: bold;
}
.small-font {
    font-size: 14px;
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)

st.title("Material Planning Dashboard - Q4")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file)

    # Clean column names (remove spaces)
df.columns = df.columns.str.strip()

# Try to auto-detect columns
required_col = None
stock_col = None
shortage_col = None

for col in df.columns:
    if "req" in col.lower():
        required_col = col
    if "stock" in col.lower() or "avail" in col.lower():
        stock_col = col
    if "short" in col.lower():
        shortage_col = col

if required_col and stock_col:
    total_required = df[required_col].sum()
    total_stock = df[stock_col].sum()
    total_shortage = total_required - total_stock
    shortage_percent = (total_shortage / total_required) * 100
else:
    st.error("Required or Stock column not found in Excel.")
    st.stop()

    total_shortage = total_required - total_stock
    shortage_percent = (total_shortage / total_required) * 100

    col1, col2, col3, col4 = st.columns(4)

    def metric(card_title, value, color="white"):
        return f"""
        <div class="metric-card">
            <div class="big-font" style="color:{color};">{value}</div>
            <div class="small-font">{card_title}</div>
        </div>
        """

    col1.markdown(metric("Total Required", f"{total_required:,.0f}"), unsafe_allow_html=True)
    col2.markdown(metric("Total Stock", f"{total_stock:,.0f}"), unsafe_allow_html=True)
    col3.markdown(metric("Total Shortage", f"{total_shortage:,.0f}"), unsafe_allow_html=True)
    col4.markdown(metric("Shortage %", f"{shortage_percent:.1f}%", "#22c55e"), unsafe_allow_html=True)

    st.markdown("---")

    colA, colB = st.columns(2)

    supplier_col = None

for col in df.columns:
    if "supplier" in col.lower():
        supplier_col = col

if supplier_col and shortage_col:
    supplier_data = df.groupby(supplier_col)[shortage_col].sum().sort_values(ascending=False).head(10)
else:
    st.warning("Supplier or Shortage column not found.")


    fig_donut = go.Figure(data=[go.Pie(
        labels=supplier_data.index,
        values=supplier_data.values,
        hole=.6
    )])

    fig_donut.update_layout(template="plotly_dark",
                            title="Shortage by Supplier (Top 10)")

    colA.plotly_chart(fig_donut, use_container_width=True)

    trend = df.groupby("ETA Month")["Shortage"].sum().reset_index()

    fig_area = px.area(trend,
                       x="ETA Month",
                       y="Shortage",
                       template="plotly_dark",
                       title="Shortage Trend vs ETA")

    colB.plotly_chart(fig_area, use_container_width=True)

    top_parts = df.sort_values("Shortage", ascending=False).head(10)

    fig_bar = px.bar(top_parts,
                     x="Shortage",
                     y="Part Name",
                     orientation="h",
                     template="plotly_dark",
                     title="Top 10 Shortage Parts")

    st.plotly_chart(fig_bar, use_container_width=True)
