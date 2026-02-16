import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    layout="wide",
    page_title="Material Planning Executive Dashboard"
)

# ---------------- PREMIUM DARK STYLE ----------------
st.markdown("""
<style>
body {
    background-color: #0b1c2d;
}
.block-container {
    padding-top: 1rem;
}
.metric-card {
    background: linear-gradient(145deg, #10243a, #0b1c2d);
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    color: white;
    box-shadow: 0px 5px 20px rgba(0,0,0,0.4);
}
.big-font {
    font-size: 32px;
    font-weight: bold;
}
.small-font {
    font-size: 14px;
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)

st.title("Material Planning – Investor Dashboard")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    # -------- Read Excel with Both Sheets --------
    excel_file = pd.ExcelFile(file)

    sheets = excel_file.sheet_names

    selected_sheet = st.selectbox("Select Business Unit", sheets)

    df = pd.read_excel(excel_file, sheet_name=selected_sheet, header=1)
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all")

    # Convert numeric safely
    for col in ["PLAN", "COMPLETE", "PENDING"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Shortage"] = df["PLAN"] - df["COMPLETE"]

    # ---------------- FILTERS ----------------
    colF1, colF2 = st.columns(2)

    min_shortage = colF1.slider(
        "Minimum Shortage",
        0,
        int(df["Shortage"].max()) if df["Shortage"].max() > 0 else 100,
        0
    )

    show_only_shortage = colF2.checkbox("Show Only Shortage Items")

    filtered_df = df.copy()

    if min_shortage > 0:
        filtered_df = filtered_df[filtered_df["Shortage"] >= min_shortage]

    if show_only_shortage:
        filtered_df = filtered_df[filtered_df["Shortage"] > 0]

    # ---------------- KPI ----------------
    total_plan = filtered_df["PLAN"].sum()
    total_complete = filtered_df["COMPLETE"].sum()
    total_shortage = filtered_df["Shortage"].sum()
    shortage_percent = (total_shortage / total_plan * 100) if total_plan else 0

    col1, col2, col3, col4 = st.columns(4)

    def metric_card(title, value, color="white"):
        return f"""
        <div class="metric-card">
            <div class="big-font" style="color:{color};">{value}</div>
            <div class="small-font">{title}</div>
        </div>
        """

    col1.markdown(metric_card("Total Plan", f"{total_plan:,.0f}"), unsafe_allow_html=True)
    col2.markdown(metric_card("Total Complete", f"{total_complete:,.0f}"), unsafe_allow_html=True)
    col3.markdown(metric_card("Total Shortage", f"{total_shortage:,.0f}", "#f87171"), unsafe_allow_html=True)
    col4.markdown(metric_card("Shortage %", f"{shortage_percent:.1f}%", "#22c55e"), unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- CHARTS ----------------
    colA, colB = st.columns(2)

    # Donut Chart
    fig_donut = go.Figure(data=[go.Pie(
        labels=["Complete", "Shortage"],
        values=[total_complete, total_shortage],
        hole=0.65
    )])

    fig_donut.update_layout(
        template="plotly_dark",
        title=f"{selected_sheet} – Completion vs Shortage"
    )

    colA.plotly_chart(fig_donut, use_container_width=True)

    # Model-wise Breakdown
    model_columns = df.columns[:10]

    model_data = []
    for model in model_columns:
        try:
            total = pd.to_numeric(df[model], errors="coerce").sum()
            if total > 0:
                model_data.append({"Model": model, "Total": total})
        except:
            continue

    model_df = pd.DataFrame(model_data)

    if not model_df.empty:
        fig_model = px.bar(
            model_df,
            x="Model",
            y="Total",
            template="plotly_dark",
            title=f"{selected_sheet} – Model-wise Planning"
        )
        colB.plotly_chart(fig_model, use_container_width=True)

    st.markdown("---")

    # Top Shortage Items
    top_rows = filtered_df.sort_values("Shortage", ascending=False).head(10)

    fig_bar = px.bar(
        top_rows,
        x="Shortage",
        y=top_rows.index,
        orientation="h",
        template="plotly_dark",
        title=f"{selected_sheet} – Top 10 Shortage Items"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### Detailed Data")
    st.dataframe(filtered_df, use_container_width=True)
