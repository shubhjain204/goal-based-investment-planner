import streamlit as st
import pandas as pd

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(
    page_title="Goal-Based Investment Planner",
    layout="wide"
)

st.title("🎯 Goal-Based Investment Planner")
st.caption("Plan how much to invest monthly or as a lump sum to achieve multiple financial goals.")

# ----------------------------
# Helper Functions
# ----------------------------
def inflation_adjusted_value(fv, inflation, years):
    return fv / ((1 + inflation / 100) ** years)

def required_lumpsum(fv, roi, years):
    return fv / ((1 + roi / 100) ** years)

def required_sip(fv, roi, years):
    r = roi / 100 / 12
    n = years * 12
    return fv * r / ((1 + r) ** n - 1)

def sip_growth(monthly, roi, years):
    r = roi / 100 / 12
    corpus = 0
    invested = 0
    data = []

    for year in range(1, years + 1):
        for _ in range(12):
            corpus = corpus * (1 + r) + monthly
            invested += monthly
        data.append({
            "Year": year,
            "Invested": round(invested),
            "Corpus": round(corpus)
        })

    return pd.DataFrame(data)

def format_inr(x):
    return f"₹{x:,.0f}".replace(",", "_").replace("_", ",")

# ----------------------------
# Sidebar – Global Settings
# ----------------------------
st.sidebar.header("Global Settings")

default_inflation = st.sidebar.slider(
    "Default Inflation (%)",
    min_value=0.0,
    max_value=10.0,
    value=6.0,
    step=0.5
)

investment_mode = st.sidebar.radio(
    "Investment Mode (Display Preference)",
    ["Monthly SIP", "Lump Sum"]
)

# ----------------------------
# Sidebar – Goals Input
# ----------------------------
st.sidebar.header("Goals")

if "goals" not in st.session_state:
    st.session_state.goals = []

def add_goal():
    st.session_state.goals.append({
        "name": f"Goal {len(st.session_state.goals) + 1}",
        "target": 1000000,
        "years": 10,
        "roi": 10.0,
        "inflation": default_inflation
    })

if st.sidebar.button("➕ Add Goal"):
    add_goal()

# ----------------------------
# Goal Cards
# ----------------------------
for i, goal in enumerate(st.session_state.goals):
    with st.sidebar.expander(f"🎯 {goal['name']}", expanded=True):
        goal["name"] = st.text_input("Goal Name", goal["name"], key=f"name_{i}")
        goal["target"] = st.number_input(
            "Target Amount (Future ₹)",
            min_value=0,
            value=goal["target"],
            step=100000,
            key=f"target_{i}"
        )
        goal["years"] = st.slider(
            "Time Horizon (Years)",
            1, 40, goal["years"],
            key=f"years_{i}"
        )
        goal["roi"] = st.slider(
            "Expected ROI (%)",
            4.0, 15.0, goal["roi"],
            step=0.5,
            key=f"roi_{i}"
        )
        if st.checkbox("Override Inflation", key=f"inf_override_{i}"):
            goal["inflation"] = st.slider(
                "Inflation (%)",
                0.0, 10.0, goal["inflation"],
                step=0.5,
                key=f"inf_{i}"
            )
        else:
            goal["inflation"] = default_inflation

        if st.button("❌ Remove Goal", key=f"remove_{i}"):
            st.session_state.goals.pop(i)
            st.experimental_rerun()

# ----------------------------
# Calculations
# ----------------------------
rows = []
total_sip = 0
total_lumpsum = 0

for goal in st.session_state.goals:
    fv_today = inflation_adjusted_value(
        goal["target"],
        goal["inflation"],
        goal["years"]
    )
    sip = required_sip(fv_today, goal["roi"], goal["years"])
    lump = required_lumpsum(fv_today, goal["roi"], goal["years"])

    total_sip += sip
    total_lumpsum += lump

    rows.append({
        "Goal": goal["name"],
        "Years": goal["years"],
        "ROI (%)": goal["roi"],
        "Target (Today ₹)": round(fv_today),
        "Monthly SIP ₹": round(sip),
        "Lump Sum ₹": round(lump)
    })

df = pd.DataFrame(rows)

# ----------------------------
# Main Output
# ----------------------------
st.subheader("📊 Summary")

if not df.empty:
    st.dataframe(
        df.style.format({
            "Target (Today ₹)": format_inr,
            "Monthly SIP ₹": format_inr,
            "Lump Sum ₹": format_inr
        }),
        use_container_width=True
    )

    col1, col2 = st.columns(2)
    col1.metric("Total Monthly SIP", format_inr(total_sip))
    col2.metric("Total Lump Sum Required", format_inr(total_lumpsum))
else:
    st.info("Add at least one goal to see calculations.")

# ----------------------------
# Growth Chart
# ----------------------------
st.subheader("📈 Goal Growth Visualization")

if st.session_state.goals:
    selected_goal = st.selectbox(
        "Select Goal",
        [g["name"] for g in st.session_state.goals]
    )

    g = next(g for g in st.session_state.goals if g["name"] == selected_goal)

    fv_today = inflation_adjusted_value(g["target"], g["inflation"], g["years"])
    sip = required_sip(fv_today, g["roi"], g["years"])

    growth_df = sip_growth(sip, g["roi"], g["years"])

    st.line_chart(
        growth_df.set_index("Year")[["Corpus", "Invested"]]
    )
