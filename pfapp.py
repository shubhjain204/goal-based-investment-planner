import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Lumpsum Fund Allocation", layout="wide")
st.title("💰 Current Lumpsum Fund Allocation")

# =================================================
# Helper Functions
# =================================================
def tenure_in_years(y, m):
    return y + m / 12

def future_value(cost, inf, yrs):
    return cost * ((1 + inf / 100) ** yrs)

def required_lumpsum(fv, roi, yrs):
    if yrs <= 0:
        return fv
    return fv / ((1 + roi / 100) ** yrs)

def required_sip(amount, roi, yrs):
    if amount <= 0:
        return 0
    months = int(yrs * 12)
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
# Session State
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
    }])

def ensure_columns():
    base_cols = ["Goal","Current Cost","Years","Months","Inflation %","ROI %"]
    for c in base_cols:
        if c not in st.session_state.df.columns:
            st.session_state.df[c] = 0
    for s in st.session_state.sources:
        if s not in st.session_state.df.columns:
            st.session_state.df[s] = 0

ensure_columns()

# =================================================
# Controls
# =================================================
c1, c2, c3, c4 = st.columns(4)

if c1.button("➕ Add Goal"):
    new = {c: 0 for c in st.session_state.df.columns}
    new["Goal"] = f"Goal {len(st.session_state.df) + 1}"
    new["Inflation %"] = 8
    new["ROI %"] = 10
    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame([new])],
        ignore_index=True
    )

if c2.button("➕ Add Source"):
    src = f"Source {len(st.session_state.sources) + 1}"
    st.session_state.sources.append(src)
    st.session_state.df[src] = 0

if c3.button("💾 Save"):
    st.download_button(
        "Download client file",
        json.dumps({
            "sources": st.session_state.sources,
            "df": st.session_state.df.to_dict()
        }),
        file_name="client_data.json",
        mime="application/json"
    )

if c4.button("🔄 Reset"):
    st.session_state.clear()
    st.experimental_rerun()

# =================================================
# Rename / Delete Source
# =================================================
s1, s2 = st.columns(2)

with s1:
    src_old = st.selectbox("Rename Source", st.session_state.sources)
    src_new = st.text_input("New Source Name")
    if st.button("Rename") and src_new:
        st.session_state.df.rename(columns={src_old: src_new}, inplace=True)
        st.session_state.sources[
            st.session_state.sources.index(src_old)
        ] = src_new

with s2:
    src_del = st.selectbox("Delete Source", st.session_state.sources)
    if st.button("Delete"):
        st.session_state.sources.remove(src_del)
        st.session_state.df.drop(columns=[src_del], inplace=True)

# =================================================
# Delete Goal
# =================================================
goal_del = st.selectbox("Delete Goal", st.session_state.df["Goal"].tolist())
if st.button("Delete Goal"):
    st.session_state.df = (
        st.session_state.df[
            st.session_state.df["Goal"] != goal_del
        ]
        .reset_index(drop=True)
    )

# =================================================
# SIDE-BY-SIDE TABLES
# =================================================
left, right = st.columns([3, 2])

with left:
    st.subheader("🟦 Inputs")

    input_cols = (
        ["Goal","Current Cost","Years","Months","Inflation %","ROI %"]
        + st.session_state.sources
    )

    edited = st.data_editor(
        st.session_state.df[input_cols],
        use_container_width=True,
        num_rows="fixed",
        key="inputs",
        column_config={
            "Inflation %": st.column_config.SelectboxColumn(
                options=INFLATION_OPTIONS
            ),
            "ROI %": st.column_config.SelectboxColumn(
                options=ROI_OPTIONS
            ),
        }
    )

    st.session_state.df[input_cols] = edited[input_cols]

with right:
    st.subheader("🟩 Outputs")

    rows = []

    for idx, r in st.session_state.df.iterrows():
        tenure = tenure_in_years(r["Years"], r["Months"])

        fv = future_value(
            r["Current Cost"],
            r["Inflation %"],
            tenure
        )

        lumpsum_required = required_lumpsum(
            fv,
            r["ROI %"],
            tenure
        )

        sip_from_zero = required_sip(
            lumpsum_required,
            r["ROI %"],
            tenure
        )

        total_available = sum(
            r[s] for s in st.session_state.sources
        )

        surplus = total_available - lumpsum_required

        additional_sip = (
            required_sip(abs(surplus), r["ROI %"], tenure)
            if surplus < 0 else 0
        )

        rows.append({
            "S.No.": idx + 1,  # 👈 FIXED (starts from 1)
            "Lumpsum Required Today": format_indian(lumpsum_required),
            "Total Lumpsum Available": format_indian(total_available),
            "SIP Required (From Zero)": format_indian(sip_from_zero),
            "Additional SIP Required": format_indian(additional_sip),
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True
    )

st.caption(
    "🟦 Editable Inputs | 🟩 Calculated Outputs | Indian number format | Institutional-grade logic"
)
