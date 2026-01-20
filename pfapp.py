import streamlit as st
import pandas as pd

st.set_page_config(page_title="Current Lumpsum Fund Allocation", layout="wide")
st.title("💰 Current Lumpsum Fund Allocation")

# ----------------------------
# Helper Functions
# ----------------------------
def tenure_in_years(years, months):
    return years + months / 12

def future_value(current_cost, inflation, years):
    return current_cost * ((1 + inflation / 100) ** years)

def required_lumpsum(fv, roi, years):
    return fv / ((1 + roi / 100) ** years)

def required_sip(amount, roi, years):
    if amount <= 0:
        return 0
    r = roi / 100 / 12
    n = int(years * 12)
    return amount * r / ((1 + r) ** n - 1)

def format_inr(x):
    return f"₹{x:,.0f}".replace(",", "_").replace("_", ",")

# ----------------------------
# Session State
# ----------------------------
if "goals" not in st.session_state:
    st.session_state.goals = []

def add_goal():
    st.session_state.goals.append({
        "name": f"Goal {len(st.session_state.goals) + 1}",
        "current_cost": 100000,
        "years": 1,
        "months": 0,
        "inflation": 8.0,
        "roi": 10.0,
        "sources": []
    })

st.button("➕ Add Goal", on_click=add_goal)

# ----------------------------
# Goal Inputs
# ----------------------------
for gi, g in enumerate(st.session_state.goals):
    with st.expander(g["name"], expanded=True):
        col1, col2, col3 = st.columns(3)
        g["name"] = col1.text_input("Goal Name", g["name"], key=f"name_{gi}")
        g["current_cost"] = col2.number_input(
            "Current Cost (₹)", value=g["current_cost"], step=50000, key=f"cost_{gi}"
        )
        g["inflation"] = col3.slider(
            "Goal-based Inflation (%)", 0.0, 20.0, g["inflation"], 0.5, key=f"inf_{gi}"
        )

        col4, col5 = st.columns(2)
        g["years"] = col4.number_input("Years", min_value=0, value=g["years"], key=f"y_{gi}")
        g["months"] = col5.number_input("Months", min_value=0, max_value=11, value=g["months"], key=f"m_{gi}")

        g["roi"] = st.slider(
            "Tenure & Goal-based ROI (%)", 4.0, 20.0, g["roi"], 0.5, key=f"roi_{gi}"
        )

        # ----------------------------
        # Dynamic Lumpsum Sources
        # ----------------------------
        st.markdown("**Current Lumpsum Sources**")

        if st.button("➕ Add Source", key=f"add_src_{gi}"):
            g["sources"].append({"name": "Source", "amount": 0})

        for si, src in enumerate(g["sources"]):
            c1, c2, c3 = st.columns([3, 2, 1])
            src["name"] = c1.text_input(
                "Source Name", src["name"], key=f"src_name_{gi}_{si}"
            )
            src["amount"] = c2.number_input(
                "Amount (₹)", value=src["amount"], step=50000, key=f"src_amt_{gi}_{si}"
            )
            if c3.button("❌", key=f"del_src_{gi}_{si}"):
                g["sources"].pop(si)
                st.experimental_rerun()

        if st.button("❌ Remove Goal", key=f"del_goal_{gi}"):
            st.session_state.goals.pop(gi)
            st.experimental_rerun()

# ----------------------------
# Summary Table
# ----------------------------
rows = []

for g in st.session_state.goals:
    tenure = tenure_in_years(g["years"], g["months"])
    fv = future_value(g["current_cost"], g["inflation"], tenure)
    lumpsum_required = required_lumpsum(fv, g["roi"], tenure)

    total_sources = sum(s["amount"] for s in g["sources"])
    surplus_deficit = total_sources - lumpsum_required

    revised_sip = required_sip(
        abs(surplus_deficit) if surplus_deficit < 0 else 0,
        g["roi"],
        tenure
    )

    rows.append({
        "Goal": g["name"],
        "Current Cost": g["current_cost"],
        "Tenure": f"{g['years']}y {g['months']}m",
        "Inflation %": g["inflation"],
        "ROI %": g["roi"],
        "Lumpsum Required Today": round(lumpsum_required),
        "Total Lumpsum Available": round(total_sources),
        "Lumpsum Surplus / Deficit (Today)": round(surplus_deficit),
        "Monthly SIP Required": round(revised_sip)
    })

if rows:
    df = pd.DataFrame(rows)

    st.subheader("📊 Allocation Summary")
    st.dataframe(
        df.style.format({
            "Current Cost": format_inr,
            "Lumpsum Required Today": format_inr,
            "Total Lumpsum Available": format_inr,
            "Lumpsum Surplus / Deficit (Today)": format_inr,
            "Monthly SIP Required": format_inr,
        }),
        use_container_width=True
    )
else:
    st.info("Add at least one goal to see the allocation table.")
