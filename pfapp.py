import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Current Lumpsum Fund Allocation", layout="wide")
st.title("💰 Current Lumpsum Fund Allocation (Excel-style)")

# =================================================
# Helper Functions
# =================================================
def tenure_in_years(years, months):
    return years + months / 12

def future_value(cost, inflation, years):
    return cost * ((1 + inflation / 100) ** years)

def required_lumpsum(fv, roi, years):
    if years <= 0:
        return 0
    return fv / ((1 + roi / 100) ** years)

def required_sip(amount, roi, years):
    if amount <= 0 or years <= 0:
        return 0
    r = roi / 100 / 12
    n = int(years * 12)
    return amount * r / ((1 + r) ** n - 1)

# =================================================
# Column Definitions
# =================================================
INPUT_COLS = [
    "🎯 Goal",
    "🟦 Current Cost",
    "🟦 Years",
    "🟦 Months",
    "🟦 Inflation %",
    "🟦 ROI %",
]

OUTPUT_COLS = [
    "🟩 Lumpsum Required Today",
    "🟩 Total Lumpsum Available",
    "🟩 Lumpsum Surplus / Deficit (Today)",
    "🟩 Monthly SIP Required",
]

# =================================================
# Session State Init
# =================================================
if "sources" not in st.session_state:
    st.session_state.sources = ["🟨 Source 1"]

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame([{
        "🎯 Goal": "Goal 1",
        "🟦 Current Cost": 100000,
        "🟦 Years": 1,
        "🟦 Months": 0,
        "🟦 Inflation %": 8.0,
        "🟦 ROI %": 10.0,
        "🟨 Source 1": 0,
        "🟩 Lumpsum Required Today": 0,
        "🟩 Total Lumpsum Available": 0,
        "🟩 Lumpsum Surplus / Deficit (Today)": 0,
        "🟩 Monthly SIP Required": 0,
    }])

# =================================================
# Ensure missing columns ONLY (do not overwrite values)
# =================================================
def ensure_columns(df):
    for col in INPUT_COLS + OUTPUT_COLS:
        if col not in df.columns:
            df[col] = 0
    for src in st.session_state.sources:
        if src not in df.columns:
            df[src] = 0
    return df

st.session_state.df = ensure_columns(st.session_state.df)

# =================================================
# Controls
# =================================================
c1, c2, c3, c4 = st.columns(4)

if c1.button("➕ Add Goal"):
    new_row = {col: 0 for col in INPUT_COLS + OUTPUT_COLS}
    new_row["🎯 Goal"] = f"Goal {len(st.session_state.df) + 1}"
    for src in st.session_state.sources:
        new_row[src] = 0
    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame([new_row])],
        ignore_index=True
    )

if c2.button("➕ Add Source"):
    new_source = f"🟨 Source {len(st.session_state.sources) + 1}"
    st.session_state.sources.append(new_source)
    st.session_state.df[new_source] = 0

if c3.button("💾 Save"):
    data = {
        "sources": st.session_state.sources,
        "df": st.session_state.df.to_dict()
    }
    st.download_button(
        "Download Client File",
        json.dumps(data),
        file_name="client_allocation.json",
        mime="application/json"
    )

if c4.button("🔄 Reset"):
    st.session_state.clear()
    st.experimental_rerun()

# =================================================
# Delete Goal (SAFE)
# =================================================
st.markdown("### 🗑️ Manage Goals & Sources")

gc1, gc2 = st.columns(2)

with gc1:
    goal_to_delete = st.selectbox(
        "Delete Goal",
        st.session_state.df["🎯 Goal"].tolist()
    )
    if st.button("Delete Goal"):
        st.session_state.df = st.session_state.df[
            st.session_state.df["🎯 Goal"] != goal_to_delete
        ].reset_index(drop=True)

with gc2:
    src_to_delete = st.selectbox("Delete Source", st.session_state.sources)
    if st.button("Delete Source"):
        st.session_state.sources.remove(src_to_delete)
        st.session_state.df.drop(columns=[src_to_delete], inplace=True)

# =================================================
# Rename Source
# =================================================
st.markdown("### ✏️ Rename Source")

src_old = st.selectbox("Select Source", st.session_state.sources)
src_new = st.text_input("New Source Name")

if st.button("Rename Source") and src_new:
    new_col = f"🟨 {src_new}"
    st.session_state.df.rename(columns={src_old: new_col}, inplace=True)
    idx = st.session_state.sources.index(src_old)
    st.session_state.sources[idx] = new_col

# =================================================
# Single Editable Table
# =================================================
ALL_COLS = INPUT_COLS + st.session_state.sources + OUTPUT_COLS
st.session_state.df = ensure_columns(st.session_state.df)

edited_df = st.data_editor(
    st.session_state.df[ALL_COLS],
    use_container_width=True,
    num_rows="fixed",
    key="main_table"
)

# =================================================
# Recalculate Outputs (do NOT touch inputs)
# =================================================
for i, row in edited_df.iterrows():
    tenure = tenure_in_years(row["🟦 Years"], row["🟦 Months"])
    fv = future_value(row["🟦 Current Cost"], row["🟦 Inflation %"], tenure)
    lump = required_lumpsum(fv, row["🟦 ROI %"], tenure)

    total_sources = sum(row[src] for src in st.session_state.sources)
    surplus = total_sources - lump

    sip = required_sip(
        abs(surplus) if surplus < 0 else 0,
        row["🟦 ROI %"],
        tenure
    )

    edited_df.at[i, "🟩 Lumpsum Required Today"] = round(lump)
    edited_df.at[i, "🟩 Total Lumpsum Available"] = round(total_sources)
    edited_df.at[i, "🟩 Lumpsum Surplus / Deficit (Today)"] = round(surplus)
    edited_df.at[i, "🟩 Monthly SIP Required"] = round(sip)

# Persist edits
st.session_state.df = edited_df

st.caption("🟦 Inputs | 🟨 Existing Capital | 🟩 Computed Outputs — Excel-style financial modeling")
