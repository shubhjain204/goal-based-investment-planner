import streamlit as st
import pandas as pd

st.set_page_config(page_title="Goal-Based Fund Planner", layout="wide")
st.title("💰 Goal-Based Lumpsum & SIP Planner")

# =================================================
# Helper functions
# =================================================
def tenure_in_years(years, months):
    return years + months / 12

def future_value(amount, rate, years):
    return amount * ((1 + rate / 100) ** years)

def sip_required(fv, roi, years):
    if fv <= 0:
        return 0
    months = int(round(years * 12))
    if months <= 0:
        return 0
    r = roi / 100 / 12
    if r == 0:
        return fv / months
    denom = (1 + r) ** months - 1
    if denom == 0:
        return 0
    return fv * r / denom

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
# Dropdown options
# =================================================
INFLATION_OPTIONS = [0, 4, 6, 8, 10, 12, 15]
ROI_OPTIONS = [0, 4, 6, 8, 10, 12, 15, 18, 20]

# =================================================
# Session state init
# =================================================
if "sources" not in st.session_state:
    st.session_state.sources = [
        {"name": "Cash", "roi": 0},
        {"name": "Bank", "roi": 4},
    ]

# Normalize legacy string sources
normalized_sources = []
for s in st.session_state.sources:
    if isinstance(s, str):
        normalized_sources.append({"name": s, "roi": 0})
    else:
        normalized_sources.append(s)
st.session_state.sources = normalized_sources

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame([{
        "Goal": "Marriage Fund",
        "Current Cost": 5_000_000,
        "Years": 5,
        "Months": 0,
        "Inflation %": 8,
        "New SIP ROI %": 10,
        "Cash": 1_000_000,
        "Bank": 1_000_000,
    }])

# =================================================
# Schema normalization (CRITICAL)
# =================================================
def normalize_df_schema():
    base_cols = [
        "Goal",
        "Current Cost",
        "Years",
        "Months",
        "Inflation %",
        "New SIP ROI %",
    ]

    for col in base_cols:
        if col not in st.session_state.df.columns:
            st.session_state.df[col] = 0

    for src in st.session_state.sources:
        if src["name"] not in st.session_state.df.columns:
            st.session_state.df[src["name"]] = 0

normalize_df_schema()

# =================================================
# STRUCTURE CONTROLS (Goals & Sources)
# =================================================
c1, c2, c3, c4 = st.columns(4)

# ➕ Add Goal
if c1.button("➕ Add Goal"):
    new_row = {c: 0 for c in st.session_state.df.columns}
    new_row["Goal"] = f"Goal {len(st.session_state.df) + 1}"
    new_row["Inflation %"] = 8
    new_row["New SIP ROI %"] = 10
    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame([new_row])],
        ignore_index=True
    )

# ❌ Delete Goal
goal_to_delete = c2.selectbox(
    "Delete Goal",
    st.session_state.df["Goal"].tolist(),
    label_visibility="collapsed"
)
if c2.button("❌ Delete Goal"):
    st.session_state.df = (
        st.session_state.df[
            st.session_state.df["Goal"] != goal_to_delete
        ].reset_index(drop=True)
    )

# ➕ Add Source
if c3.button("➕ Add Source"):
    name = f"Source {len(st.session_state.sources) + 1}"
    st.session_state.sources.append({"name": name, "roi": 8})
    st.session_state.df[name] = 0

# 🔄 Reset
if c4.button("🔄 Reset"):
    st.session_state.clear()
    st.experimental_rerun()

# =================================================
# SOURCE MANAGEMENT (Rename / ROI / Delete)
# =================================================
st.subheader("🟨 Existing Sources")

for i, src in enumerate(st.session_state.sources):
    c1, c2, c3 = st.columns([2, 2, 1])

    new_name = c1.text_input("Source Name", src["name"], key=f"sname_{i}")
    if new_name != src["name"]:
        st.session_state.df.rename(columns={src["name"]: new_name}, inplace=True)
        src["name"] = new_name
        normalize_df_schema()

    src["roi"] = c2.selectbox(
        "ROI %",
        ROI_OPTIONS,
        index=ROI_OPTIONS.index(src["roi"]) if src["roi"] in ROI_OPTIONS else 0,
        key=f"sroi_{i}"
    )

    if c3.button("❌", key=f"sdel_{i}"):
        st.session_state.df.drop(columns=[src["name"]], inplace=True)
        st.session_state.sources.pop(i)
        st.experimental_rerun()

# =================================================
# TABLES
# =================================================
left, right = st.columns([3, 2])

# -----------------
# INPUT TABLE
# -----------------
with left:
    st.subheader("🟦 Inputs")

    normalize_df_schema()

    input_cols = (
        ["Goal", "Current Cost", "Years", "Months", "Inflation %", "New SIP ROI %"]
        + [s["name"] for s in st.session_state.sources]
    )

    edited = st.data_editor(
        st.session_state.df[input_cols],
        use_container_width=True,
        num_rows="fixed",
        key="inputs",
        column_config={
            "Inflation %": st.column_config.SelectboxColumn(options=INFLATION_OPTIONS),
            "New SIP ROI %": st.column_config.SelectboxColumn(options=ROI_OPTIONS),
        }
    )

    st.session_state.df[input_cols] = edited[input_cols]

# -----------------
# OUTPUT TABLE
# -----------------
with right:
    st.subheader("🟩 Outputs")

    rows = []

    for _, r in st.session_state.df.iterrows():
        tenure = tenure_in_years(r["Years"], r["Months"])

        # FV of goal
        fv_goal = future_value(
            r["Current Cost"],
            r["Inflation %"],
            tenure
        )

        # FV of existing sources
        fv_existing = 0
        for src in st.session_state.sources:
            fv_existing += future_value(
                r[src["name"]],
                src["roi"],
                tenure
            )

        fv_gap = fv_goal - fv_existing

        # Option A
        lumpsum_today = (
            fv_gap / ((1 + r["New SIP ROI %"] / 100) ** tenure)
            if fv_gap > 0 else 0
        )

        # Option B
        sip_additional = (
            sip_required(fv_gap, r["New SIP ROI %"], tenure)
            if fv_gap > 0 else 0
        )

        rows.append({
            "Lumpsum Required in Future": format_indian(fv_goal),
            "Total Existing (Today)": format_indian(
                sum(r[src["name"]] for src in st.session_state.sources)
            ),
            "Additional Lumpsum Required Today": format_indian(lumpsum_today),
            "Additional SIP Required / Month": format_indian(sip_additional),
        })

    out_df = pd.DataFrame(rows)
    out_df.index = out_df.index + 1  # S.No.

    st.dataframe(out_df, use_container_width=True)

st.caption(
    "All structural controls preserved • Per-source ROI • Correct FV-based SIP logic"
)
