import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Current Lumpsum Fund Allocation", layout="wide")
st.title("💰 Current Lumpsum Fund Allocation")

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

def format_inr(x):
    try:
        return f"₹{int(x):,}".replace(",", "_").replace("_", ",")
    except:
        return x

# =================================================
# Schema
# =================================================
INPUT_COLS = ["🎯 Goal", "🟦 Current Cost", "🟦 Years", "🟦 Months", "🟦 Inflation %", "🟦 ROI %"]
OUTPUT_COLS = [
    "🟩 Lumpsum Required Today",
    "🟩 Total Lumpsum Available",
    "🟩 Lumpsum Surplus / Deficit (Today)",
    "🟩 Monthly SIP Required"
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
        "🟨 Source 1": 0
    }])

# =================================================
# Controls
# =================================================
c1, c2, c3, c4 = st.columns(4)

if c1.button("➕ Add Goal"):
    new_row = {col: 0 for col in INPUT_COLS + OUTPUT_COLS}
    new_row["🎯 Goal"] = f"Goal {len(st.session_state.df) + 1}"
    for s in st.session_state.sources:
        new_row[s] = 0
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)

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
# Rename / Delete Source
# =================================================
st.markdown("### 🧩 Manage Sources")

sc1, sc2 = st.columns(2)

with sc1:
    source_to_rename = st.selectbox("Rename Source", st.session_state.sources)
    new_name = st.text_input("New Name")
    if st.button("Rename"):
        if new_name:
            idx = st.session_state.sources.index(source_to_rename)
            st.session_state.sources[idx] = f"🟨 {new_name}"
            st.session_state.df.rename(columns={source_to_rename: f"🟨 {new_name}"}, inplace=True)

with sc2:
    source_to_delete = st.selectbox("Delete Source", st.session_state.sources)
    if st.button("Delete"):
        st.session_state.sources.remove(source_to_delete)
        st.session_state.df.drop(columns=[source_to_delete], inplace=True)

# =================================================
# Single Editable Table (Inputs + Outputs)
# =================================================
ALL_COLS = INPUT_COLS + st.session_state.sources + OUTPUT_COLS

edited_df = st.data_editor(
    st.session_state.df[ALL_COLS],
    use_container_width=True,
    num_rows="fixed"
)

# =================================================
# Recalculate Outputs
# =================================================
for i, row in edited_df.iterrows():
    tenure = tenure_in_years(row["🟦 Years"], row["🟦 Months"])
    fv = future_value(row["🟦 Current Cost"], row["🟦 Inflation %"], tenure)
    lump = required_lumpsum(fv, row["🟦 ROI %"], tenure)

    total_sources = sum(row[s] for s in st.session_state.sources)
    surplus = total_sources - lump

    sip = required_sip(abs(surplus) if surplus < 0 else 0, row["🟦 ROI %"], tenure)

    edited_df.at[i, "🟩 Lumpsum Required Today"] = round(lump)
    edited_df.at[i, "🟩 Total Lumpsum Available"] = round(total_sources)
    edited_df.at[i, "🟩 Lumpsum Surplus / Deficit (Today)"] = round(surplus)
    edited_df.at[i, "🟩 Monthly SIP Required"] = round(sip)

st.session_state.df = edited_df

# =================================================
# Footer
# =================================================
st.caption(
    "🟦 Inputs | 🟨 Existing Capital | 🟩 Computed Outputs — Excel-style financial modeling"
)
