import streamlit as st
import pandas as pd

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
# Schema Normalization (CRITICAL)
# =================================================
def normalize_schema():
    base_cols = [
        "Goal", "Current Cost", "Years", "Months",
        "Inflation %", "New SIP ROI %"
    ]
    for col in base_cols:
        if col not in st.session_state.df.columns:
            st.session_state.df[col] = 0

    for src in st.session_state.sources:
        if src["name"] not in st.session_state.df.columns:
            st.session_state.df[src["name"]] = 0

normalize_schema()

# =================================================
# STRUCTURE CONTROLS
# =================================================
c1, c2, c3, c4 = st.columns(4)

if c1.button("➕ Add Goal"):
    row = {c: 0 for c in st.session_state.df.columns}
    row["Goal"] = f"Goal {len(st.session_state.df) + 1}"
    row["Inflation %"] = 8
    row["New SIP ROI %"] = 10
    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame([row])],
        ignore_index=True
    )

goal_del = c2.selectbox("Delete Goal", st.session_state.df["Goal"].tolist())
if c2.button("❌ Delete Goal"):
    st.session_state.df = (
        st.session_state.df[st.session_state.df["Goal"] != goal_del]
        .reset_index(drop=True)
    )
    st.rerun()

if c3.button("➕ Add Source"):
    name = f"Source {len(st.session_state.sources) + 1}"
    st.session_state.sources.append({"name": name, "roi": 8})
    st.session_state.df[name] = 0
    st.rerun()

if c4.button("🔄 Reset"):
    st.session_state.clear()
    st.rerun()

# =================================================
# SOURCE MANAGEMENT (FULLY DYNAMIC)
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

with left:
    st.subheader("🟦 Inputs")

    normalize_schema()

    input_cols = (
        ["Goal", "Current Cost", "Years", "Months",
         "Inflation %", "New SIP ROI %"]
        + [s["name"] for s in st.session_state.sources]
    )

    edited = st.data_editor(
        st.session_state.df[input_cols],
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "Inflation %": st.column_config.SelectboxColumn(options=INFLATION_OPTIONS),
            "New SIP ROI %": st.column_config.SelectboxColumn(options=ROI_OPTIONS),
        }
    )

    st.session_state.df[input_cols] = edited[input_cols]

with right:
    st.subheader("🟩 Outputs")

    rows = []

    for _, r in st.session_state.df.iterrows():
        tenure = tenure_in_years(r["Years"], r["Months"])

        fv_goal = future_value(
            r["Current Cost"],
            r["Inflation %"],
            tenure
        )

        fv_existing = sum(
            future_value(r[src["name"]], src["roi"], tenure)
            for src in st.session_state.sources
        )

        fv_gap = fv_goal - fv_existing

        lumpsum_today = (
            fv_gap / ((1 + r["New SIP ROI %"] / 100) ** tenure)
            if fv_gap > 0 else 0
        )

        r_m = r["New SIP ROI %"] / 100 / 12
        n = int(round(tenure * 12))

        sip_additional = (
            fv_gap * r_m / ((1 + r_m) ** n - 1)
            if fv_gap > 0 and n > 0 else 0
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
    out_df.index = out_df.index + 1

    st.dataframe(out_df, use_container_width=True)

st.caption(
    "Sources are fully dynamic • Add / Rename / Delete / ROI per source • Stable across reruns"
)
