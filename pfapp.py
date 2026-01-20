import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Current Lumpsum Fund Allocation", layout="wide")
st.title("💰 Current Lumpsum Fund Allocation (Excel-style)")

# =================================================
# Helper Functions (MINIMALLY FIXED)
# =================================================
def tenure_in_years(years, months):
    return years + months / 12

def future_value(cost, inflation, years):
    return cost * ((1 + inflation / 100) ** years)

def required_lumpsum(fv, roi, years):
    if years <= 0:
        return fv
    return fv / ((1 + roi / 100) ** years)

def required_sip(amount, roi, years):
    if amount <= 0:
        return 0

    months = int(years * 12)
    if months <= 0:
        return 0

    r = roi / 100 / 12
    if r == 0:
        return amount / months

    denom = (1 + r) ** months - 1
    if denom == 0:
        return 0

    return amount * r / denom

def format_indian(n):
    try:
        n = int(round(n))
    except:
        return n

    s = str(abs(n))
    if len(s) <= 3:
        res = s
    else:
        res = s[-3:]
        s = s[:-3]
        while s:
            res = s[-2:] + "," + res
            s = s[:-2]

    return ("-" if n < 0 else "") + res

# =================================================
# Dropdown Options
# =================================================
INFLATION_OPTIONS = [0, 4, 6, 8, 10, 12, 15]
ROI_OPTIONS = [0, 6, 8, 10, 12, 15, 18, 20]

# =================================================
# Columns
# =================================================
INPUT_COLS = [
    "Goal",
    "Current Cost",
    "Years",
    "Months",
    "Inflation %",
    "ROI %",
]

OUTPUT_COLS = [
    "Lumpsum Required Today",
    "Total Lumpsum Available",
    "Lumpsum Surplus / Deficit (Today)",
    "Monthly SIP Required",
]

# =================================================
# Session State Init
# =================================================
if "sources" not in st.session_state:
    st.session_state.sources = ["Source 1"]

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame([{
        "Goal": "Goal 1",
        "Current Cost": 100000,
        "Years": 1,
        "Months": 0,
        "Inflation %": 8,
        "ROI %": 10,
        "Source 1": 0,
        "Lumpsum Required Today": 0,
        "Total Lumpsum Available": 0,
        "Lumpsum Surplus / Deficit (Today)": 0,
        "Monthly SIP Required": 0,
    }])

# =================================================
# Ensure Columns (DO NOT OVERWRITE VALUES)
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
    new_row["Goal"] = f"Goal {len(st.session_state.df) + 1}"
    new_row["Inflation %"] = 8
    new_row["ROI %"] = 10
    for src in st.session_state.sources:
        new_row[src] = 0
    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame([new_row])],
        ignore_index=True
    )

if c2.button("➕ Add Source"):
    new_source = f"Source {len(st.session_state.sources) + 1}"
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
# Delete Goal / Source
# =================================================
g1, g2 = st.columns(2)

with g1:
    goal_to_delete = st.selectbox("Delete Goal", st.session_state.df["Goal"].tolist())
    if st.button("Delete Goal"):
        st.session_state.df = st.session_state.df[
            st.session_state.df["Goal"] != goal_to_delete
        ].reset_index(drop=True)

with g2:
    src_to_delete = st.selectbox("Delete Source", st.session_state.sources)
    if st.button("Delete Source"):
        st.session_state.sources.remove(src_to_delete)
        st.session_state.df.drop(columns=[src_to_delete], inplace=True)

# =================================================
# Rename Source
# =================================================
st.markdown("### Rename Source")

old = st.selectbox("Source", st.session_state.sources)
new = st.text_input("New Name")

if st.button("Rename Source") and new:
    st.session_state.df.rename(columns={old: new}, inplace=True)
    idx = st.session_state.sources.index(old)
    st.session_state.sources[idx] = new

# =================================================
# Main Editable Table (SINGLE TABLE)
# =================================================
ALL_COLS = INPUT_COLS + st.session_state.sources + OUTPUT_COLS
st.session_state.df = ensure_columns(st.session_state.df)

edited_df = st.data_editor(
    st.session_state.df[ALL_COLS],
    use_container_width=True,
    num_rows="fixed",
    key="main_table",
    column_config={
        "Inflation %": st.column_config.SelectboxColumn(options=INFLATION_OPTIONS),
        "ROI %": st.column_config.SelectboxColumn(options=ROI_OPTIONS),
    }
)

# =================================================
# Recalculate Outputs (SAFE)
# =================================================
for i, row in edited_df.iterrows():
    tenure = tenure_in_years(row["Years"], row["Months"])
    fv = future_value(row["Current Cost"], row["Inflation %"], tenure)
    lump = required_lumpsum(fv, row["ROI %"], tenure)

    total_sources = sum(row[src] for src in st.session_state.sources)
    surplus = total_sources - lump

    sip = required_sip(
        abs(surplus) if surplus < 0 else 0,
        row["ROI %"],
        tenure
    )

    edited_df.at[i, "Lumpsum Required Today"] = round(lump)
    edited_df.at[i, "Total Lumpsum Available"] = round(total_sources)
    edited_df.at[i, "Lumpsum Surplus / Deficit (Today)"] = round(surplus)
    edited_df.at[i, "Monthly SIP Required"] = round(sip)

st.session_state.df = edited_df

# =================================================
# Display (Indian Format)
# =================================================
st.dataframe(
    edited_df.style.format({
        "Current Cost": format_indian,
        "Lumpsum Required Today": format_indian,
        "Total Lumpsum Available": format_indian,
        "Lumpsum Surplus / Deficit (Today)": format_indian,
        "Monthly SIP Required": format_indian,
        **{src: format_indian for src in st.session_state.sources}
    }),
    use_container_width=True
)

st.caption("Indian number format • Single-table Excel-style financial planning")
