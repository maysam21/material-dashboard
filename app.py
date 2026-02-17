import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import math

st.set_page_config(layout="wide")

st.title("SKU Production Dashboard")

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

    # ---------------- PRODUCTION QTY (JFM) ----------------
    # Row 0 contains production plan
    production_qty = pd.to_numeric(df.iloc[0][selected_sku], errors="coerce")

    # Convert stock safely
    df["TOTAL STOCK"] = pd.to_numeric(df["TOTAL STOCK"], errors="coerce").fillna(0)
    df["QTY PER M/C"] = pd.to_numeric(df["QTY PER M/C"], errors="coerce").fillna(0)

    # ---- Vertical logic: only parts used in selected SKU ----
    sku_df = df[df[selected_sku].notna()].copy()

    # -------- NEW FG LOGIC (As You Requested) --------
    total_stock_available = sku_df["TOTAL STOCK"].sum()
    total_qty_per_machine = sku_df["QTY PER M/C"].sum()

    fg_possible = math.floor(
        total_stock_available / total_qty_per_machine
    ) if total_qty_per_machine > 0 else 0

    # ---------------- KPI ----------------
    col1, col2, col3 = st.columns(3)

    col1.metric("JFM Production Plan", f"{int(production_qty) if not pd.isna(production_qty) else 0}")
    col2.metric("Total Stock Available", f"{int(total_stock_available)}")
    col3.metric("FG Buildable (Stock ÷ Total QTY/M/C)", fg_possible)

    st.markdown("---")

    # Show parts used
    st.markdown("### Parts Used for Selected SKU")

    st.dataframe(
        sku_df[[
            "PART NAME",
            "QTY PER M/C",
            "TOTAL STOCK",
            "Supplier",
            "ETA"
        ]],
        use_container_width=True
    )
