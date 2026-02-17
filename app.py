import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import math

st.set_page_config(layout="wide")

# --------- PREMIUM DARK UI ---------
st.markdown("""
<style>
body { background-color: #0b1c2d; }
.block-container { padding-top: 1rem; }

.kpi-card {
    background: linear-gradient(145deg, #13263c, #0b1c2d);
    padding: 20px;
    border-radius: 16px;
    text-align: center;
    color: white;
    box-shadow: 0px 8px 30px rgba(0,0,0,0.4);
}
.kpi-value {
    font-size: 28px;
    font-weight: bold;
}
.kpi-title {
    font-size: 14px;
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)

st.title("SKU Intelligence – AI Production Engine")

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    excel = pd.ExcelFile(file)
    sheet = st.selectbox("Business Unit", excel.sheet_names)

    df = pd.read_excel(excel, sheet_name=sheet, header=1)
    df.columns = df.columns.str.strip()
    df = df[df["PART NAME"].notna()]

    # Detect SKU columns
    sku_columns = [
        col for col in df.columns
        if any(x in col for x in [
            "Arista", "Asteria", "Eris", "Elara", "Cube", "ORION"
        ])
    ]

    selected_sku = st.selectbox("Select SKU", sku_columns)

    df["TOTAL STOCK"] = pd.to_numeric(df["TOTAL STOCK"], errors="coerce").fillna(0)

    # Only parts used in selected SKU (vertical check)
    sku_df = df[df[selected_sku].notna()].copy()

    sku_df["Required_per_FG"] = pd.to_numeric(
        sku_df[selected_sku], errors="coerce"
    )

    sku_df = sku_df[sku_df["Required_per_FG"].notna()]

    # -------- AI PRODUCTION FEASIBILITY --------
    sku_df["FG_Possible_From_Part"] = sku_df.apply(
        lambda row: math.floor(
            row["TOTAL STOCK"] / row["Required_per_FG"]
        ) if row["Required_per_FG"] > 0 else 0,
        axis=1
    )

    max_fg_possible = sku_df["FG_Possible_From_Part"].min()
    bottleneck_part = sku_df.loc[
        sku_df["FG_Possible_From_Part"].idxmin()
    ]["PART NAME"]

    # -------- KPI SECTION --------
    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{int(max_fg_possible)}</div>
        <div class="kpi-title">Max FG Buildable</div>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{bottleneck_part}</div>
        <div class="kpi-title">Bottleneck Part</div>
    </div>
    """, unsafe_allow_html=True)

    total_parts = len(sku_df)

    col3.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{total_parts}</div>
        <div class="kpi-title">Parts Used</div>
    </div>
    """, unsafe_allow_html=True)

    risk_parts = len(sku_df[sku_df["FG_Possible_From_Part"] == max_fg_possible])

    col4.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{risk_parts}</div>
        <div class="kpi-title">Critical Constraints</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # -------- VISUAL BOTTLENECK ANALYSIS --------
    top_constraints = sku_df.sort_values(
        "FG_Possible_From_Part"
    ).head(10)

    fig = px.bar(
        top_constraints,
        x="FG_Possible_From_Part",
        y="PART NAME",
        orientation="h",
        template="plotly_dark",
        title=f"Production Limiting Parts – {selected_sku}"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.markdown("### Detailed AI Breakdown")

    st.dataframe(
        sku_df[[
            "PART NAME",
            "Required_per_FG",
            "TOTAL STOCK",
            "FG_Possible_From_Part",
            "Supplier",
            "ETA"
        ]].sort_values("FG_Possible_From_Part"),
        use_container_width=True
    )
