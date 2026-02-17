import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import base64
import os

st.set_page_config(layout="wide")

# ---------------- PREMIUM KPI STYLE ----------------
st.markdown("""
<style>
.kpi-card {
    background: linear-gradient(135deg, #1f2937, #111827);
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    text-align: center;
    color: white;
}
.kpi-title {
    font-size: 14px;
    color: #9ca3af;
}
.kpi-value {
    font-size: 26px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SAFE LOGO ----------------
def load_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        return f"data:image/png;base64,{encoded}"
    return None

logo_data = load_logo("logo.png")

col_logo, col_title = st.columns([1, 4])

with col_logo:
    if logo_data:
        st.markdown(f'<img src="{logo_data}" width="120">', unsafe_allow_html=True)

with col_title:
    st.markdown(
        "<h2 style='padding-top:20px;'>SKU Wise – Production Intelligence Dashboard</h2>",
        unsafe_allow_html=True
    )

file = st.file_uploader("Upload Material Planning Excel", type=["xlsx"])

if file:

    excel = pd.ExcelFile(file)
    sheet = st.selectbox("Business Unit", excel.sheet_names)

    df = pd.read_excel(excel, sheet_name=sheet, header=1)
    df.columns = df.columns.str.strip()
    df = df[df["PART NAME"].notna()]

    sku_columns = [
        col for col in df.columns
        if any(x in col for x in [
            "Arista", "Asteria", "Eris", "Elara", "Cube", "ORION"
        ])
    ]

    selected_sku = st.selectbox("Select SKU", sku_columns)

    production_qty = pd.to_numeric(df.iloc[0][selected_sku], errors="coerce")

    df["TOTAL STOCK"] = pd.to_numeric(df["TOTAL STOCK"], errors="coerce").fillna(0)
    df["QTY PER M/C"] = pd.to_numeric(df["QTY PER M/C"], errors="coerce").fillna(0)

    sku_df = df[df[selected_sku].notna()].copy()
    sku_df["Required"] = pd.to_numeric(sku_df[selected_sku], errors="coerce")
    sku_df = sku_df[sku_df["Required"].notna()]

    if sku_df.empty:
        st.warning("No parts mapped for this SKU.")
        st.stop()

    sku_df["Shortage"] = sku_df["Required"] - sku_df["TOTAL STOCK"]
    sku_df["Shortage"] = sku_df["Shortage"].apply(lambda x: x if x > 0 else 0)

    # Convert to integers
    sku_df["Required"] = sku_df["Required"].astype(int)
    sku_df["TOTAL STOCK"] = sku_df["TOTAL STOCK"].astype(int)
    sku_df["Shortage"] = sku_df["Shortage"].astype(int)
    sku_df["QTY PER M/C"] = sku_df["QTY PER M/C"].astype(int)

    total_required = int(sku_df["Required"].sum())
    total_stock = int(sku_df["TOTAL STOCK"].sum())
    total_shortage = int(sku_df["Shortage"].sum())
    gap_percent = int((total_shortage / total_required * 100)) if total_required else 0

    # ---------------- PREMIUM KPI CARDS ----------------
    col1, col2, col3, col4, col5 = st.columns(5)

    def kpi_card(title, value):
        return f"""
        <div class="kpi-card">
            <div class="kpi-value">{value}</div>
            <div class="kpi-title">{title}</div>
        </div>
        """

    col1.markdown(kpi_card("JFM Production Plan",
                           int(production_qty) if not pd.isna(production_qty) else 0),
                  unsafe_allow_html=True)

    col2.markdown(kpi_card("Total Required", total_required), unsafe_allow_html=True)
    col3.markdown(kpi_card("Total Stock", total_stock), unsafe_allow_html=True)
    col4.markdown(kpi_card("Total Shortage", total_shortage), unsafe_allow_html=True)
    col5.markdown(kpi_card("Gap %", f"{gap_percent}%"), unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- TRUE FG LOGIC ----------------
    if (sku_df["TOTAL STOCK"] == 0).any():
        fg_buildable = 0
        production_status = "🔴 BLOCKED – At least one required part has zero stock."
    else:
        sku_df["Possible_FG_From_Part"] = np.floor(
            sku_df["TOTAL STOCK"] / sku_df["Required"]
        )
        fg_buildable = int(sku_df["Possible_FG_From_Part"].min())
        production_status = "🟢 Production Feasible"

    st.metric("FG Buildable", fg_buildable)
    st.write(production_status)

    if not pd.isna(production_qty):
        production_gap = int(production_qty) - fg_buildable
        if production_gap <= 0:
            st.success("🟢 Production Plan Achievable")
        else:
            st.error(f"🔴 Production Shortfall: {production_gap} Units")

    st.markdown("---")

    # ---------------- STOCK COVERAGE ----------------
    st.markdown("### Stock Coverage Analysis")

    sku_df["Coverage Ratio"] = (
        sku_df["TOTAL STOCK"] / sku_df["Required"]
    ).round(2)

    colA, colB = st.columns(2)
    colA.metric("Average Coverage", round(sku_df["Coverage Ratio"].mean(), 2))
    colB.metric("Minimum Coverage", round(sku_df["Coverage Ratio"].min(), 2))

    st.markdown("---")

    # ---------------- CRITICAL PARTS ----------------
    st.markdown("### Top Critical Parts")

    critical_parts = sku_df.sort_values(
        ["Shortage", "Coverage Ratio"],
        ascending=[False, True]
    ).head(5)

    st.dataframe(
        critical_parts[[
            "PART NAME",
            "Required",
            "TOTAL STOCK",
            "Shortage",
            "Coverage Ratio"
        ]],
        use_container_width=True
    )

    st.markdown("---")

    # ---------------- SHORTAGE CONTRIBUTION ----------------
    st.markdown("### Shortage Contribution (%)")

    if total_shortage > 0:
        sku_df["Shortage %"] = (
            sku_df["Shortage"] / total_shortage * 100
        ).round(1)

        top_contrib = sku_df.sort_values("Shortage %", ascending=False).head(10)

        fig_contrib = px.bar(
            top_contrib,
            x="Shortage %",
            y="PART NAME",
            orientation="h",
            template="plotly_dark"
        )

        st.plotly_chart(fig_contrib, use_container_width=True)
    else:
        st.success("No shortage – Fully Covered")

    st.markdown("---")

    # ---------------- PROCUREMENT PRIORITY ----------------
    st.markdown("### Procurement Priority Score")

    sku_df["Priority Score"] = sku_df["Shortage"] * sku_df["Required"]

    priority_parts = sku_df.sort_values(
        "Priority Score",
        ascending=False
    ).head(10)

    st.dataframe(
        priority_parts[[
            "PART NAME",
            "Shortage",
            "Required",
            "Priority Score",
            "Supplier"
        ]],
        use_container_width=True
    )

    st.markdown("---")

    # ---------------- PRODUCTION STABILITY INDEX ----------------
    st.markdown("### Production Stability Index")

    if not pd.isna(production_qty) and production_qty > 0:
        stability_index = int((fg_buildable / production_qty) * 100)
    else:
        stability_index = 0

    if stability_index >= 100:
        st.success(f"🟢 Stability Index: {stability_index}%")
    elif stability_index >= 70:
        st.warning(f"🟡 Stability Index: {stability_index}%")
    else:
        st.error(f"🔴 Stability Index: {stability_index}%")

    st.markdown("---")

    # ---------------- COLOR-CODED TABLE ----------------
    st.markdown("### Parts Required for This SKU")

    def color_stock(val, required):
        if val == 0:
            return "color: red;"
        elif val < required:
            return "color: orange;"
        else:
            return "color: lightgreen;"

    styled_df = sku_df[[
        "PART NAME",
        "QTY PER M/C",
        "Required",
        "TOTAL STOCK",
        "Shortage",
        "Supplier",
        "ETA"
    ]].style.apply(
        lambda row: [
            "",
            "",
            "",
            color_stock(row["TOTAL STOCK"], row["Required"]),
            "",
            "",
            ""
        ],
        axis=1
    )

    st.dataframe(styled_df, use_container_width=True)
