import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Goal-Based Fund Planner", layout="wide")
st.title("💰 Goal-Based Lumpsum & SIP Planner")

# =================================================
# Helpers
# =================================================
def tenure_in_years(y, m):
    return y + m / 12

def future_value(amount, rate, years):
    return amount * ((1 + rate / 100) ** years)

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
# Options
# =================================================
INFLATION_OPTIONS = [0, 4, 6, 8, 10, 12, 15]
ROI_OPTIONS = [0, 4, 6, 8, 10, 12, 15, 18, 20]

# =================================================
# Session State Init
# =================================================
if "sources" not in st.session_state:
    st.session_state.sources = [
        {"name": "Cash", "roi": 0},
        {"name": "Bank", "roi": 4},
    ]

# Normalize legacy states
st.session_state.sources = [
    {"name": s, "roi": 0} if isinstance(s, str) else s
    for s in st.session_state.sources
]

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
# Schema normalization (ONLY BEFORE EDITOR)
# =================================================
def normalize_schema():
    base_cols = [
        "Goal", "Current Cost", "Years", "Months",
        "Inflation %", "New SIP ROI %"
    ]
    for c in base_cols:
        if c not in st.session_state.df.columns:
            st.session_state.df[c] = 0

    for src in st.session_state.sources:
        if src["name"] not in st.session_state.df.columns:
            st.session_state.df[src["name"]] = 0

normalize_schema()

# =================================================
# TOP ACTION BAR
# =================================================
a1, a2, a3, a4, a5 = st.columns(5)

# Add Goal
if a1.button("➕ Add Goal"):
    row = {c: 0 for c in st.session_state.df.columns}
    row["Goal"] = f"Goal {len(st.session_state.df) + 1}"
    row["Inflation %"] = 8
    row["New SIP ROI %"] = 10
    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame([row])],
        ignore_index=True
    )
    st.rerun()

# Delete Goal
goal_to_delete = a2.selectbox(
    "Delete Goal",
    st.session_state.df["Goal"].tolist(),
    label_visibility="collapsed"
)
if a2.button("❌ Delete Goal"):
    st.session_state.df = (
        st.session_state.df[
            st.session_state.df["Goal"] != goal_to_delete
        ].reset_index(drop=True)
    )
    st.rerun()

# Add Source
if a3.button("➕ Add Source"):
    name = f"Source {len(st.session_state.sources) + 1}"
    st.session_state.sources.append({"name": name, "roi": 8})
    st.session_state.df[name] = 0
    st.rerun()

# Save Client
if a4.button("💾 Save Client"):
    payload = {
        "sources": st.session_state.sources,
        "df": st.session_state.df.to_dict()
    }
    st.download_button(
        "Download Client File",
        data=json.dumps(payload),
        file_name="client_plan.json",
        mime="application/json"
    )

# Load Client
uploaded = a5.file_uploader("📂 Load Client", type="json")
if uploaded:
    data = json.load(uploaded)
    st.session_state.sources = data["sources"]
    st.session_state.df = pd.DataFrame(data["df"])
    normalize_schema()
    st.rerun()

# =================================================
# SOURCE MANAGEMENT (SAFE & DYNAMIC)
# =================================================
st.subheader("🟨 Sources (Dynamic)")

for i, src in enumerate(st.session_state.sources):
    c1, c2, c3 = st.columns([3, 2, 2])

    new_name = c1.text_input(
        "Source Name",
        src["name"],
        key=f"sname_{i}"
    )

    if new_name.strip() and new_name != src["name"]:
        st.session_state.df.rename(
            columns={src["name"]: new_name},
            inplace=True
        )
        src["name"] = new_name
        normalize_schema()
        st.rerun()

    src["roi"] = c2.selectbox(
        "ROI %",
        ROI_OPTIONS,
        index=ROI_OPTIONS.index(src["roi"])
        if src["roi"] in ROI_OPTIONS else 0,
        key=f"sroi_{i}"
    )

    if c3.button(f"❌ Delete {src['name']}", key=f"sdel_{i}"):
        st.session_state.df.drop(columns=[src["name"]], inplace=True)
        st.session_state.sources.pop(i)
        normalize_schema()
        st.rerun()

# =================================================
# TABLES
# =================================================
left, right = st.columns([3, 2])

# -----------------
# INPUT TABLE (ONLY PLACE WHERE DATA MUTATES)
# -----------------
with left:
    st.subheader("🟦 Inputs")

    input_cols = (
        ["Goal", "Current Cost", "Years", "Months",
         "Inflation %", "New SIP ROI %"]
        + [s["name"] for s in st.session_state.sources]
    )

    edited_df = st.data_editor(
        st.session_state.df[input_cols],
        use_container_width=True,
        num_rows="fixed",
        key="inputs_editor",
        column_config={
            "Inflation %": st.column_config.SelectboxColumn(options=INFLATION_OPTIONS),
            "New SIP ROI %": st.column_config.SelectboxColumn(options=ROI_OPTIONS),
        }
    )

    # ✅ FINAL FIX — unconditional assignment
    st.session_state.df[input_cols] = edited_df[input_cols]

    # Totals (read-only)
    totals = {
        s["name"]: format_indian(st.session_state.df[s["name"]].sum())
        for s in st.session_state.sources
    }
    st.dataframe(
        pd.DataFrame([{"Goal": "TOTAL", **totals}]),
        use_container_width=True
    )


# -----------------
# OUTPUT TABLE (READ-ONLY, CALCULATED FROM COPY)
# -----------------
with right:
    st.subheader("🟩 Outputs")

    calc_df = st.session_state.df.copy()
    rows = []

    total_existing = total_lump = total_sip = 0

    for _, r in calc_df.iterrows():
        tenure = tenure_in_years(r["Years"], r["Months"])

        # Future value of goal
        fv_goal = future_value(
            r["Current Cost"], r["Inflation %"], tenure
        )

        # Existing funds future value (per source ROI)
        fv_existing = sum(
            future_value(r[src["name"]], src["roi"], tenure)
            for src in st.session_state.sources
        )

        fv_gap = fv_goal - fv_existing

        # Option A: Additional lumpsum today
        lumpsum_today = (
            fv_gap / ((1 + r["New SIP ROI %"] / 100) ** tenure)
            if fv_gap > 0 and tenure > 0 else 0
        )

        # Option B: Additional SIP (safe)
        r_m = r["New SIP ROI %"] / 100 / 12
        n = int(round(tenure * 12))

        if fv_gap <= 0 or n <= 0:
            sip = 0
        elif r_m == 0:
            sip = fv_gap / n
        else:
            sip = fv_gap * r_m / ((1 + r_m) ** n - 1)

        # ✅ Goal-wise existing today
        total_existing_goal = sum(
            r[src["name"]] for src in st.session_state.sources
        )

        total_existing += total_existing_goal
        total_lump += lumpsum_today
        total_sip += sip

        rows.append({
            "Total Existing (Today)": format_indian(total_existing_goal),
            "Additional Lumpsum Required Today": format_indian(lumpsum_today),
            "Additional SIP Required / Month": format_indian(sip),
        })

    # 🔒 THESE MUST BE OUTSIDE THE LOOP
    out_df = pd.DataFrame(rows)
    out_df.index = out_df.index + 1  # S.No.

    st.dataframe(out_df, use_container_width=True)

    st.markdown(
        f"""
        **TOTALS**
        - Total Existing Today: ₹{format_indian(total_existing)}
        - Total Additional Lumpsum Needed: ₹{format_indian(total_lump)}
        - Total Monthly SIP Needed: ₹{format_indian(total_sip)}
        """
    )



