import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Goal-Based Fund Planner", layout="wide")
st.title("💰 Goal-Based Financial Planning Tool")

st.markdown("""
**How to use**  
• Add goals & sources using the top buttons  
• Edit cells directly in the table → values save when you finish editing (Enter / Tab / click away)  
• Type **plain numbers only** (no commas, no ₹) in money fields  
• Outputs update automatically  
• Save/load plans using the top buttons
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
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    res = s[-3:]
    s = s[:-3]
    while s:
        res = s[-2:] + "," + res
        s = s[:-2]
    return sign + res

# ────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────
INFLATION_OPTIONS = [0, 4, 6, 8, 10, 12, 15]
ROI_OPTIONS = [0, 4, 6, 8, 10, 12, 15, 18, 20]

# ────────────────────────────────────────────────
# Session state init
# ────────────────────────────────────────────────
if "sources" not in st.session_state:
    st.session_state.sources = [
        {"name": "Cash", "roi": 0},
        {"name": "Bank FD", "roi": 6},
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
        "Bank FD": 800000,
    }])

# ────────────────────────────────────────────────
# Normalize schema
# ────────────────────────────────────────────────
def normalize_schema():
    base_cols = ["Goal", "Priority", "Current Cost", "Years", "Months",
                 "Inflation %", "New SIP ROI %"]
    for col in base_cols:
        if col not in st.session_state.df.columns:
            st.session_state.df[col] = "" if col == "Goal" else 0

    for src in st.session_state.sources:
        if src["name"] not in st.session_state.df.columns:
            st.session_state.df[src["name"]] = 0

normalize_schema()

# ────────────────────────────────────────────────
# Top action bar
# ────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    if st.button("➕ Add Goal"):
        row = {c: 0 for c in st.session_state.df.columns}
        row["Goal"] = f"Goal {len(st.session_state.df)+1}"
        row["Priority"] = len(st.session_state.df) + 1
        row["Inflation %"] = 8
        row["New SIP ROI %"] = 12
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([row])], ignore_index=True)
        st.rerun()

with c2:
    goal_to_del = st.selectbox("Delete Goal", [""] + st.session_state.df["Goal"].tolist(), label_visibility="collapsed")
    if goal_to_del and st.button("❌ Delete"):
        st.session_state.df = st.session_state.df[st.session_state.df["Goal"] != goal_to_del].reset_index(drop=True)
        st.rerun()

with c3:
    if st.button("➕ Add Source"):
        name = f"Source {len(st.session_state.sources)+1}"
        st.session_state.sources.append({"name": name, "roi": 10})
        st.session_state.df[name] = 0
        st.rerun()

with c4:
    if st.button("💾 Save Plan"):
        payload = {
            "sources": st.session_state.sources,
            "df": st.session_state.df.to_dict(orient="records")
        }
        st.download_button("Download JSON", json.dumps(payload, indent=2), "plan.json")

with c5:
    uploaded = st.file_uploader("📂 Load Plan", type="json", label_visibility="collapsed")
    if uploaded:
        try:
            data = json.load(uploaded)
            st.session_state.sources = data.get("sources", [])
            st.session_state.df = pd.DataFrame(data.get("df", []))
            normalize_schema()
            st.rerun()
        except Exception as e:
            st.error(f"Load error: {e}")

# ────────────────────────────────────────────────
# Sources section
# ────────────────────────────────────────────────
st.subheader("Investment Sources")
for i, src in enumerate(st.session_state.sources):
    c1, c2, c3 = st.columns([4, 2, 1])
    new_name = c1.text_input("Name", src["name"], key=f"sname_{i}")
    if new_name != src["name"] and new_name.strip():
        if new_name in [s["name"] for s in st.session_state.sources if s is not src]:
            c1.error("Duplicate name")
        else:
            st.session_state.df.rename(columns={src["name"]: new_name}, inplace=True)
            src["name"] = new_name
            st.rerun()

    src["roi"] = c2.selectbox("ROI %", ROI_OPTIONS, index=ROI_OPTIONS.index(src["roi"]) if src["roi"] in ROI_OPTIONS else 0, key=f"sroi_{i}")

    if c3.button("🗑", key=f"del_{i}"):
        name = st.session_state.sources.pop(i)["name"]
        if name in st.session_state.df.columns:
            st.session_state.df.drop(columns=[name], inplace=True)
        normalize_schema()
        st.rerun()

# ────────────────────────────────────────────────
# Main layout
# ────────────────────────────────────────────────
left, right = st.columns([3, 2])

# ─── INPUTS ───────────────────────────────────────
with left:
    st.subheader("Goal Inputs")

    # Define columns list first
    input_cols = ["Goal", "Priority", "Current Cost", "Years", "Months", "Inflation %", "New SIP ROI %"] + \
                 [s["name"] for s in st.session_state.sources]

    # Column config
    column_config = {
        "Goal": st.column_config.TextColumn("Goal", help="e.g. House, Education, Retirement"),
        "Priority": st.column_config.NumberColumn("Priority", min_value=1, step=1, format="%d"),
        "Current Cost": st.column_config.NumberColumn("Current Cost (₹)", min_value=0, step=10000, format=None),
        "Years": st.column_config.NumberColumn("Years", min_value=0, max_value=50, step=1, format="%d"),
        "Months": st.column_config.NumberColumn("Months", min_value=0, max_value=11, step=1, format="%d"),
        "Inflation %": st.column_config.SelectboxColumn("Inflation %", options=INFLATION_OPTIONS),
        "New SIP ROI %": st.column_config.SelectboxColumn("New SIP ROI %", options=ROI_OPTIONS),
    }
    for src in st.session_state.sources:
        column_config[src["name"]] = st.column_config.NumberColumn(f"{src['name']} (₹)", min_value=0, step=10000, format=None)

    # Safe update callback
    def update_df():
        if "goal_editor" in st.session_state:
            edited = st.session_state["goal_editor"]
            if isinstance(edited, pd.DataFrame) and not edited.empty:
                common = [c for c in input_cols if c in edited.columns]
                if common:
                    st.session_state.df[common] = edited[common]

    st.data_editor(
        st.session_state.df[input_cols].copy(),
        key="goal_editor",
        column_config=column_config,
        num_rows="fixed",
        use_container_width=True,
        on_change=update_df
    )

    # Totals
    totals = {s["name"]: format_indian(st.session_state.df[s["name"]].sum()) for s in st.session_state.sources}
    st.dataframe(pd.DataFrame([{"Goal": "TOTAL", **totals}]), use_container_width=True)

# ─── OUTPUTS ──────────────────────────────────────
with right:
    st.subheader("Results")

    if st.session_state.df.empty:
        st.info("Add goals to see calculations.")
    else:
        calc_df = st.session_state.df.copy().sort_values("Priority")
        rows = []
        tot_exist = tot_lump = tot_sip = 0

        for _, r in calc_df.iterrows():
            tenure = tenure_in_years(r["Years"], r["Months"])
            fv_goal = future_value(r["Current Cost"], r["Inflation %"], tenure)
            fv_exist = sum(future_value(r.get(s["name"], 0), s["roi"], tenure) for s in st.session_state.sources)
            gap = fv_goal - fv_exist

            lump = gap / ((1 + r["New SIP ROI %"]/100)**tenure) if gap > 0 and tenure > 0 else 0

            rm = r["New SIP ROI %"] / 100 / 12
            n = round(tenure * 12)
            sip = 0
            if gap > 0 and n > 0:
                if rm == 0:
                    sip = gap / n
                else:
                    sip = gap * rm / ((1 + rm)**n - 1)

            exist_today = sum(r.get(s["name"], 0) for s in st.session_state.sources)

            tot_exist += exist_today
            tot_lump += lump
            tot_sip += sip

            rows.append({
                "Goal": r["Goal"],
                "Priority": int(r["Priority"]),
                "Existing": format_indian(exist_today),
                "Lumpsum Today": format_indian(lump),
                "Monthly SIP": format_indian(sip),
            })

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown(f"""
        **Totals**  
        • Existing today: ₹{format_indian(tot_exist)}  
        • Additional Lumpsum needed: ₹{format_indian(tot_lump)}  
        • Additional Monthly SIP: ₹{format_indian(tot_sip)}
        """)

st.caption("Real-time editing • Dynamic sources • v2025")
