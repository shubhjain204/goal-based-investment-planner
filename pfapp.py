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
# Session state
# -------------------------------------------------
if "source_cols" not in st.session_state:
    st.session_state.source_cols = ["Source 1"]

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame([
        {
            "Goal": "Goal 1",
            "Current Cost": 100000,
            "Years": 1,
            "Months": 0,
            "Inflation %": 8.0,
            "ROI %": 10.0,
            "Lumpsum Savings Required": 0,
            "SIP Required": 0,
            "Source 1": 0,
            "Total Lumpsum Available": 0,
            "Lumpsum Surplus / Deficit (Today)": 0
        }
    ])

# -------------------------------------------------
# Controls
# -------------------------------------------------
c1, c2 = st.columns(2)

if c1.button("➕ Add Goal"):
    new_row = {
        "Goal": f"Goal {len(st.session_state.df) + 1}",
        "Current Cost": 0,
        "Years": 0,
        "Months": 0,
        "Inflation %": 0.0,
        "ROI %": 0.0,
        "Lumpsum Savings Required": 0,
        "SIP Required": 0,
        "Total Lumpsum Available": 0,
        "Lumpsum Surplus / Deficit (Today)": 0,
    }
    for s in st.session_state.source_cols:
        new_row[s] = 0

    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame([new_row])],
        ignore_index=True
    )

if c2.button("➕ Add Source"):
    new_source = f"Source {len(st.session_state.source_cols) + 1}"
    st.session_state.source_cols.append(new_source)
    st.session_state.df[new_source] = 0

# -------------------------------------------------
# Column order (single table)
# -------------------------------------------------
base_cols = [
    "Goal",
    "Current Cost",
    "Years",
    "Months",
    "Inflation %",
    "ROI %",
    "Lumpsum Savings Required",
    "SIP Required",
]

end_cols = [
    "Total Lumpsum Available",
    "Lumpsum Surplus / Deficit (Today)"
]

all_cols = base_cols + st.session_state.source_cols + end_cols

# -------------------------------------------------
# Editable table
# -------------------------------------------------
edited_df = st.data_editor(
    st.session_state.df[all_cols],
    use_container_width=True,
    num_rows="fixed"
)

# -------------------------------------------------
# Recalculate (overwrite derived columns)
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

    total_available = sum(row[s] for s in st.session_state.source_cols)
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

# Persist state
st.session_state.df = edited_df

# -------------------------------------------------
# Display formatted table
# -------------------------------------------------
st.subheader("📊 Allocation Table")

st.dataframe(
    edited_df.style.format({
        "Current Cost": format_inr,
        "Lumpsum Savings Required": format_inr,
        "SIP Required": format_inr,
        "Total Lumpsum Available": format_inr,
        "Lumpsum Surplus / Deficit (Today)": format_inr,
        **{s: format_inr for s in st.session_state.source_cols}
    }),
    use_container_width=True
)
