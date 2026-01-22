```python
import streamlit as st
import pandas as pd
import json
st.set_page_config(page_title="Goal-Based Fund Planner", layout="wide")
st.title("💰 Financial Planning Tool")

# Brief instructions for user-friendliness
st.markdown("""
This tool helps you plan your financial goals. 
- Add goals and sources using the buttons above.
- Edit the inputs table directly – changes update live!
- Sources can be renamed, ROI adjusted, or deleted below.
- Outputs update automatically as you edit.
- Save/load your plan using the buttons.
""")

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
# Ensure sources are dicts
st.session_state.sources = [
    {"name": s, "roi": 0} if isinstance(s, str) else s
    for s in st.session_state.sources
]

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame([{
        "Goal": "Marriage Fund",
        "Priority": 1,
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
        "Goal",
        "Priority",
        "Current Cost",
        "Years",
        "Months",
        "Inflation %",
        "New SIP ROI %",
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
if a1.button("➕ Add Goal", help="Add a new financial goal"):
    row = {c: 0 for c in st.session_state.df.columns}
    row["Goal"] = f"Goal {len(st.session_state.df) + 1}"
    row["Priority"] = len(st.session_state.df) + 1
    row["Inflation %"] = 8
    row["New SIP ROI %"] = 10
    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame([row])],
        ignore_index=True
    )
    st.rerun()

# Delete Goal
goal_to_delete = a2.selectbox(
    "Select Goal to Delete",
    [""] + st.session_state.df["Goal"].tolist(),
    label_visibility="visible",
    help="Select a goal and click delete"
)
if goal_to_delete and a2.button("❌ Delete Goal", help="Delete the selected goal"):
    st.session_state.df = (
        st.session_state.df[
            st.session_state.df["Goal"] != goal_to_delete
        ].reset_index(drop=True)
    )
    st.rerun()

# Add Source
if a3.button("➕ Add Source", help="Add a new investment source"):
    name = f"Source {len(st.session_state.sources) + 1}"
    st.session_state.sources.append({"name": name, "roi": 8})
    st.session_state.df[name] = 0
    st.rerun()

# Save Client
if a4.button("💾 Save Plan", help="Download your current plan as JSON"):
    payload = {
        "sources": st.session_state.sources,
        "df": st.session_state.df.to_dict(orient="records")
    }
    st.download_button(
        "Download Plan File",
        data=json.dumps(payload),
        file_name="client_plan.json",
        mime="application/json",
        help="Click to download"
    )

# Load Client
uploaded = a5.file_uploader("📂 Load Plan", type="json", help="Upload a previously saved JSON plan")
if uploaded:
    data = json.load(uploaded)
    st.session_state.sources = data["sources"]
    st.session_state.df = pd.DataFrame(data["df"])
    normalize_schema()
    st.rerun()

# =================================================
# SOURCE MANAGEMENT (Real-time updates)
# =================================================
st.subheader("🟨 Investment Sources")
st.markdown("Edit source names (press Enter to apply), ROI, or delete. Changes apply immediately.")

for i in range(len(st.session_state.sources)):
    src = st.session_state.sources[i]
    c1, c2, c3 = st.columns([3, 2, 1])
    new_name = c1.text_input(
        f"Source Name {i+1}",
        value=src["name"],
        key=f"sname_{i}",
        help="Name of the source (e.g., Stocks, FD). Press Enter to rename."
    )
    if new_name.strip() and new_name != src["name"]:
        if new_name in [s["name"] for s in st.session_state.sources if s != src]:
            c1.error(f"Duplicate name '{new_name}' not allowed.")
        else:
            st.session_state.df.rename(
                columns={src["name"]: new_name},
                inplace=True
            )
            src["name"] = new_name
            st.rerun()
    
    src["roi"] = c2.selectbox(
        f"ROI % {i+1}",
        ROI_OPTIONS,
        index=ROI_OPTIONS.index(src["roi"]) if src["roi"] in ROI_OPTIONS else 0,
        key=f"sroi_{i}",
        help="Expected annual return for this source"
    )
    
    if c3.button(f"❌", key=f"sdel_{i}", help=f"Delete {src['name']} source"):
        old_name = st.session_state.sources.pop(i)["name"]
        if old_name in st.session_state.df.columns:
            st.session_state.df.drop(columns=[old_name], inplace=True)
        normalize_schema()
        st.rerun()

# =================================================
# TABLES
# =================================================
left, right = st.columns([3, 2])

# -----------------
# INPUT TABLE (Real-time editing)
# -----------------
with left:
    st.subheader("🟦 Goal Inputs")
    st.markdown("Edit cells directly. Outputs update live as you change values.")
    input_cols = (
        ["Goal", "Priority", "Current Cost", "Years", "Months",
         "Inflation %", "New SIP ROI %"]
        + [s["name"] for s in st.session_state.sources]
    )
    column_config = {
        "Goal": st.column_config.TextColumn(
            help="Name your goal (e.g., House Purchase)"
        ),
        "Priority": st.column_config.NumberColumn(
            help="Lower number = higher priority (used for sorting)"
        ),
        "Current Cost": st.column_config.NumberColumn(
            help="Today's estimated cost of the goal (in ₹)"
        ),
        "Years": st.column_config.NumberColumn(
            help="Number of years until goal"
        ),
        "Months": st.column_config.NumberColumn(
            help="Additional months until goal (0-11)"
        ),
        "Inflation %": st.column_config.SelectboxColumn(
            options=INFLATION_OPTIONS,
            help="Annual inflation rate for this goal"
        ),
        "New SIP ROI %": st.column_config.SelectboxColumn(
            options=ROI_OPTIONS,
            help="Expected return on new monthly investments (SIP)"
        ),
    }
    for s in st.session_state.sources:
        column_config[s["name"]] = st.column_config.NumberColumn(
            help=f"Current amount allocated from {s['name']} (in ₹)"
        )
    
    edited_df = st.data_editor(
        st.session_state.df[input_cols],
        use_container_width=True,
        num_rows="fixed",
        hide_index=False,
        column_config=column_config
    )
    # Persist changes immediately for real-time
    st.session_state.df[input_cols] = edited_df
    
    # Totals (read-only, using edited_df for consistency)
    totals = {
        s["name"]: format_indian(edited_df[s["name"]].sum())
        for s in st.session_state.sources
    }
    st.dataframe(
        pd.DataFrame([{"Goal": "TOTAL", **totals}]),
        use_container_width=True,
        hide_index=True
    )

# -----------------
# OUTPUT TABLE (Updates live)
# -----------------
with right:
    st.subheader("🟩 Calculated Outputs")
    st.markdown("Sorted by priority. Shows requirements for each goal.")
    calc_df = edited_df.copy().sort_values("Priority")
    rows = []
    total_existing = total_lump = total_sip = 0
    for _, r in calc_df.iterrows():
        tenure = tenure_in_years(r["Years"], r["Months"])
        fv_goal = future_value(
            r["Current Cost"], r["Inflation %"], tenure
        )
        fv_existing = sum(
            future_value(r[src["name"]], src["roi"], tenure)
            for src in st.session_state.sources
        )
        fv_gap = fv_goal - fv_existing
        lumpsum_today = (
            fv_gap / ((1 + r["New SIP ROI %"] / 100) ** tenure)
            if fv_gap > 0 and tenure > 0 else 0
        )
        r_m = r["New SIP ROI %"] / 100 / 12
        n = int(round(tenure * 12))
        if fv_gap <= 0 or n <= 0:
            sip = 0
        elif r_m == 0:
            sip = fv_gap / n
        else:
            sip = fv_gap * r_m / ((1 + r_m) ** n - 1)
        total_existing_goal = sum(
            r[src["name"]] for src in st.session_state.sources
        )
        total_existing += total_existing_goal
        total_lump += lumpsum_today
        total_sip += sip
        rows.append({
            "Goal": r["Goal"],
            "Priority": int(r["Priority"]),
            "Total Existing (Today)": format_indian(total_existing_goal),
            "Additional Lumpsum Required Today": format_indian(lumpsum_today),
            "Additional SIP Required / Month": format_indian(sip),
        })
    out_df = pd.DataFrame(rows)
    st.dataframe(out_df, use_container_width=True, hide_index=True)
    st.markdown(
        f"""
        **Overall Totals**
        - Total Existing Today: ₹{format_indian(total_existing)}
        - Total Additional Lumpsum Needed: ₹{format_indian(total_lump)}
        - Total Monthly SIP Needed: ₹{format_indian(total_sip)}
        """
    )

st.caption(
    "Real-time updates • User-friendly with helps • Dynamic sources • Correct calculations • Client-ready"
)
```
