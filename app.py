import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Material Planning Executive Dashboard")

# ---------------- DARK STYLE ----------------
st.markdown("""
<style>
body { background-color: #0b1c2d; }
.block-container { padding-top: 1rem; }
.metric-container {
    background: linear-gradient(145deg, #10243a, #0b1c2d);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("Material Planning Executive Dashboard")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    # Read correct header row
    df = pd.read_excel(file, header=1)
    df.columns = df.columns.astype(str).str.strip()

    # Drop empty rows
    df = df.dropna(how="all")

    # Ensure numeric conversion
    for col in ["PLAN", "COMPLETE", "PENDING"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Calculate Shortage
    df["Shortage"] = df["PLAN"] - df["COMPLETE"]

    # ---------------- FILTER SECTION ----------------
    colF1, colF2 = st.columns(2)

    model_filter = colF1.selectbox("Select Model", ["All"] + list(df.columns[:10]))
    min_shortage = colF2.slider("Minimum Shortage Filter", 0, int(df["Shortage"].max()), 0)

    filtered_df = df.copy()

    if min_shortage > 0:
        filtered_df = filtered_df[filtered_df["Shortage"] >= min_shortage]

    # ---------------- KPI SECTION ----------------
    total_plan = filtered_df["PLAN"].sum()
    total_complete = filtered_df["COMPLETE"].sum()
    total_shortage = filtered_df["Shortage"].sum()
    shortage_percent = (total_shortage / total_plan * 100) if total_plan else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Plan", f"{total_plan:,.0f}")
    col2.metric("Total Complete", f"{total_complete:,.0f}")
    col3.metric("Total Shortage", f"{total_shortage:,.0f}")
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

    # ---------------- MODEL-WISE BREAKDOWN ----------------
    model_columns = df.columns[:10]

    model_data = []
    for model in model_columns:
        try:
            value = pd.to_numeric(df[model], errors="coerce").sum()
            model_data.append({"Model": model, "Total": value})
        except:
            continue

    model_df = pd.DataFrame(model_data)

    fig_model = px.bar(
        model_df,
        x="Model",
        y="Total",
        template="plotly_dark",
        title="Model-wise Total Planning"
    )

    st.plotly_chart(fig_model, use_container_width=True)

    # ---------------- TOP SHORTAGE ITEMS ----------------
    top_rows = filtered_df.sort_values("Shortage", ascending=False).head(10)

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
    st.dataframe(filtered_df, use_container_width=True)
