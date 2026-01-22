import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Goal-Based Fund Planner", layout="wide")
st.title("💰 Goal-Based Financial Planning Tool")

st.markdown("""
### How to use this tool
- **Add** goals and investment sources using the buttons at the top  
- **Edit** any cell in the Inputs table → values save automatically when you finish editing (press Enter / Tab / click away)  
- Outputs update **live** as soon as edits are committed  
- Rename/delete sources in the Sources section (changes apply immediately)  
- Save or load your plan anytime using the top-right buttons
""")

# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────
def tenure_in_years(y, m):
    return y + m / 12.0

def future_value(amount, rate, years):
    if years <= 0:
        return amount
    return amount * ((1 + rate / 100) ** years)

def format_indian(n):
    try:
        n = int(round(n))
    except:
        return str(n)
    if n == 0:
        return "0"
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

# ────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────
INFLATION_OPTIONS = [0, 4, 6, 8, 10, 12, 15]
ROI_OPTIONS = [0, 4, 6, 8, 10, 12, 15, 18, 20]

# ────────────────────────────────────────────────
# Session State Initialization
# ────────────────────────────────────────────────
if "sources" not in st.session_state:
    st.session_state.sources = [
        {"name": "Cash", "roi": 0},
        {"name": "Bank FD", "roi": 4},
    ]

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame([{
        "Goal": "Marriage Fund",
        "Priority": 1,
        "Current Cost": 5000000,
        "Years": 5,
        "Months": 0,
        "Inflation %": 8,
        "New SIP ROI %": 12,
        "Cash": 1000000,
        "Bank FD": 500000,
    }])

# ────────────────────────────────────────────────
# Schema normalization
# ────────────────────────────────────────────────
def normalize_schema():
    base_cols = ["Goal", "Priority", "Current Cost", "Years", "Months",
                 "Inflation %", "New SIP ROI %"]
    for col in base_cols:
        if col not in st.session_state.df.columns:
            st.session_state.df[col] = 0 if col != "Goal" else "New Goal"

    for src in st.session_state.sources:
        if src["name"] not in st.session_state.df.columns:
            st.session_state.df[src["name"]] = 0

normalize_schema()

# ────────────────────────────────────────────────
# Top Action Bar
# ────────────────────────────────────────────────
cols = st.columns([1, 1, 1, 1, 1])

with cols[0]:
    if st.button("➕ Add Goal", use_container_width=True):
        new_row = {col: 0 for col in st.session_state.df.columns}
        new_row["Goal"] = f"Goal {len(st.session_state.df) + 1}"
        new_row["Priority"] = len(st.session_state.df) + 1
        new_row["Inflation %"] = 8
        new_row["New SIP ROI %"] = 12
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([new_row])], ignore_index=True
        )
        st.rerun()

with cols[1]:
    goal_list = [""] + st.session_state.df["Goal"].tolist()
    goal_to_delete = st.selectbox("Delete Goal", goal_list, index=0, label_visibility="collapsed")
    if goal_to_delete and st.button("❌ Delete", use_container_width=True):
        st.session_state.df = st.session_state.df[
            st.session_state.df["Goal"] != goal_to_delete
        ].reset_index(drop=True)
        st.rerun()

with cols[2]:
    if st.button("➕ Add Source", use_container_width=True):
        name = f"Source {len(st.session_state.sources) + 1}"
        st.session_state.sources.append({"name": name, "roi": 8})
        st.session_state.df[name] = 0
        st.rerun()

with cols[3]:
    if st.button("💾 Save Plan", use_container_width=True):
        payload = {
            "sources": st.session_state.sources,
            "df": st.session_state.df.to_dict(orient="records")
        }
        st.download_button(
            label="Download JSON",
            data=json.dumps(payload, indent=2),
            file_name="financial_plan.json",
            mime="application/json"
        )

with cols[4]:
    uploaded = st.file_uploader("📂 Load Plan", type=["json"], label_visibility="collapsed")
    if uploaded:
        try:
            data = json.load(uploaded)
            st.session_state.sources = data.get("sources", [])
            st.session_state.df = pd.DataFrame(data.get("df", []))
            normalize_schema()
            st.rerun()
        except Exception as e:
            st.error(f"Error loading file: {e}")

# ────────────────────────────────────────────────
# Sources Management (real-time rename/delete)
# ────────────────────────────────────────────────
st.subheader("Investment Sources")
st.caption("Rename or change ROI → press Enter. Delete with the button.")

for i in range(len(st.session_state.sources)):
    src = st.session_state.sources[i]
    c1, c2, c3 = st.columns([4, 2, 1])

    new_name = c1.text_input(
        label="",
        value=src["name"],
        key=f"source_name_{i}",
        placeholder="Source name",
        label_visibility="collapsed"
    )
    if new_name.strip() and new_name != src["name"]:
        if new_name in [s["name"] for s in st.session_state.sources if s is not src]:
            c1.error("Duplicate name not allowed")
        else:
            old_name = src["name"]
            st.session_state.df.rename(columns={old_name: new_name}, inplace=True)
            src["name"] = new_name
            st.rerun()

    src["roi"] = c2.selectbox(
        label="",
        options=ROI_OPTIONS,
        index=ROI_OPTIONS.index(src["roi"]) if src["roi"] in ROI_OPTIONS else 0,
        key=f"source_roi_{i}",
        label_visibility="collapsed"
    )

    if c3.button("🗑", key=f"del_source_{i}", help="Delete this source"):
        old_name = st.session_state.sources.pop(i)["name"]
        if old_name in st.session_state.df.columns:
            st.session_state.df.drop(columns=[old_name], inplace=True)
        normalize_schema()
        st.rerun()

# ────────────────────────────────────────────────
# Main layout: Inputs + Outputs
# ────────────────────────────────────────────────
left, right = st.columns([3, 2])

# ─── INPUTS ───────────────────────────────────────
with left:
    st.subheader("Goal Inputs")
    st.caption("Edit any cell → changes are saved automatically when focus leaves (Enter / Tab / click elsewhere)")

    input_cols = (
        ["Goal", "Priority", "Current Cost", "Years", "Months",
         "Inflation %", "New SIP ROI %"]
        + [s["name"] for s in st.session_state.sources]
    )

    def on_goal_editor_change():
        key = "goal_editor"
        if key not in st.session_state:
            return
        edited = st.session_state[key]
        if not isinstance(edited, pd.DataFrame) or edited.empty:
            return
        # Update only existing columns → prevents shape mismatch
        common_cols = [c for c in input_cols if c in edited.columns]
        if common_cols:
            st.session_state.df[common_cols] = edited[common_cols]

    # Column config stays the same
    # ... your column_config dictionary here ...

    st.data_editor(
        st.session_state.df[input_cols].copy(),
        key="goal_editor",
        use_container_width=True,
        num_rows="fixed",
        hide_index=False,
        column_config=column_config,
        on_change=on_goal_editor_change
    )

    # Totals
    totals = {s["name"]: format_indian(st.session_state.df[s["name"]].sum())
              for s in st.session_state.sources}
    st.dataframe(
        pd.DataFrame([{"Goal": "TOTAL", **totals}]),
        use_container_width=True,
        hide_index=True
    )

# ─── OUTPUTS ──────────────────────────────────────
with right:
    st.subheader("Results & Requirements")
    st.caption("Sorted by priority — updates live")

    if st.session_state.df.empty:
        st.info("Add at least one goal to see results.")
    else:
        calc_df = st.session_state.df.copy().sort_values("Priority")

        rows = []
        total_existing = total_lump = total_sip = 0.0

        for _, r in calc_df.iterrows():
            tenure = tenure_in_years(r["Years"], r["Months"])
            fv_goal = future_value(r["Current Cost"], r["Inflation %"], tenure)

            fv_existing = sum(
                future_value(r.get(src["name"], 0), src["roi"], tenure)
                for src in st.session_state.sources
            )

            gap = fv_goal - fv_existing

            # Lumpsum required today
            if gap > 0 and tenure > 0:
                lumpsum = gap / ((1 + r["New SIP ROI %"] / 100) ** tenure)
            else:
                lumpsum = 0

            # Monthly SIP (future value of annuity formula)
            r_month = r["New SIP ROI %"] / 100 / 12
            n_months = round(tenure * 12)
            if gap <= 0 or n_months <= 0:
                sip = 0
            elif r_month == 0:
                sip = gap / n_months
            else:
                sip = gap * r_month / ((1 + r_month) ** n_months - 1)

            existing_today = sum(r.get(src["name"], 0) for src in st.session_state.sources)

            total_existing += existing_today
            total_lump += lumpsum
            total_sip += sip

            rows.append({
                "Goal": r["Goal"],
                "Priority": int(r["Priority"]),
                "Existing Today": format_indian(existing_today),
                "Lumpsum Today": format_indian(lumpsum),
                "Monthly SIP": format_indian(sip),
            })

        out_df = pd.DataFrame(rows)

        st.dataframe(
            out_df,
            use_container_width=True,
            hide_index=True,
            column_order=["Goal", "Priority", "Existing Today", "Lumpsum Today", "Monthly SIP"]
        )

        st.markdown("---")
        st.markdown(f"**Grand Totals**")
        st.markdown(f"- **Existing today**: ₹ {format_indian(total_existing)}")
        st.markdown(f"- **Additional lumpsum needed today**: ₹ {format_indian(total_lump)}")
        st.markdown(f"- **Additional monthly SIP needed**: ₹ {format_indian(total_sip)}")

st.caption("Real-time • Dynamic sources • Correct financial math • v2025.01")

