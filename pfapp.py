import streamlit as st
import pandas as pd

st.set_page_config(page_title="Current Lumpsum Fund Allocation", layout="wide")
st.title("💰 Current Lumpsum Fund Allocation")

# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def tenure_in_years(years, months):
    return years + months / 12

def future_value(current_cost, inflation, years):
    return current_cost * ((1 + inflation / 100) ** years)

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
        return f"₹{x:,.0f}".replace(",", "_").replace("_", ",")
    except:
        return x

# -------------------------------------------------
# Column schema (SINGLE SOURCE OF TRUTH)
# -------------------------------------------------
BASE_INPUT_COLS = [
    "Goal",
    "Current Cost",
    "Years",
    "Months",
    "Inflation %",
    "ROI %",
]

CALC_COLS = [
    "Lumpsum Savings Required",
    "SIP Required",
    "Total Lumpsum Available",
    "Lumpsum Surplus / Deficit (Today)",
]

# -------------------------------------------------
# Session state init
# -------------------------------------------------
if "source_cols" not in st.session_state:
    st.session_state.source_cols = ["Source 1"]

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame([{
        "Goal": "Goal 1",
        "Current Cost": 100000,
        "Years": 1,
        "Months": 0,
        "Inflation %": 8.0,
        "ROI %": 10.0,
        "Source 1": 0,
    }])

# -------------------------------------------------
# SCHEMA NORMALIZATION (CRITICAL FIX)
# -------------------------------------------------
def normalize_dataframe(df):
    # Add missing base columns
    for col in BASE_INPUT_COLS:
        if col not in df.columns:
            df[col] = 0

    # Add missing calculated columns
    for col in CALC_COLS:
        if col not in df.columns:
            df[col] = 0

    # Add missing source columns
    for src in st.session_state.source_cols:
        if src not in df.columns:
            df[src] = 0

    return df

st.session_state.df = normalize_dataframe(st.session_state.df)

# -------------------------------------------------
# Controls
# -------------------------------------------------
c1, c2 = st.columns(2)

if c1.button("➕ Add Goal"):
    new_row = {col: 0 for col in BASE_INPUT_COLS + CALC_COLS}
    new_row["Goal"] = f"Goal {len(st.session_state.df) + 1}"
    for src in st.session_state.source_cols:
        new_row[src] = 0

    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame([new_row])],
        ignore_index=True
    )

if c2.button("➕ Add Source"):
    new_source = f"Source {len(st.session_state.source_cols) + 1}"
    st.session_state.source_cols.append(new_source)
    st.session_state.df[new_source] = 0

# -------------------------------------------------
# Final column order (ONE TABLE)
# -------------------------------------------------
ALL_COLS = (
    BASE_INPUT_COLS
    + ["Lumpsum Savings Required", "SIP Required"]
    + st.session_state.source_cols
    + ["Total Lumpsum Available", "Lumpsum Surplus / Deficit (Today)"]
)

# -------------------------------------------------
# Editable table
# -------------------------------------------------
edited_df = st.data_editor(
    st.session_state.df[ALL_COLS],
    use_container_width=True,
    num_rows="fixed"
)

# -------------------------------------------------
# Recalculate derived columns
# -------------------------------------------------
for i, row in edited_df.iterrows():
    tenure = tenure_in_years(row["Years"], row["Months"])

    fv = future_value(
        row["Current Cost"],
        row["Inflation %"],
        tenure
    )

    lumpsum_required = required_lumpsum(
        fv,
        row["ROI %"],
        tenure
    )

    total_available = sum(row[src] for src in st.session_state.source_cols)
    surplus_deficit = total_available - lumpsum_required

    sip_required = required_sip(
        abs(surplus_deficit) if surplus_deficit < 0 else 0,
        row["ROI %"],
        tenure
    )

    edited_df.at[i, "Lumpsum Savings Required"] = round(lumpsum_required)
    edited_df.at[i, "Total Lumpsum Available"] = round(total_available)
    edited_df.at[i, "Lumpsum Surplus / Deficit (Today)"] = round(surplus_deficit)
    edited_df.at[i, "SIP Required"] = round(sip_required)

# Persist
st.session_state.df = edited_df

# -------------------------------------------------
# Display
# -------------------------------------------------
st.subheader("📊 Allocation Table (Editable like Excel)")

st.dataframe(
    edited_df.style.format({
        "Current Cost": format_inr,
        "Lumpsum Savings Required": format_inr,
        "SIP Required": format_inr,
        "Total Lumpsum Available": format_inr,
        "Lumpsum Surplus / Deficit (Today)": format_inr,
        **{src: format_inr for src in st.session_state.source_cols}
    }),
    use_container_width=True
)
