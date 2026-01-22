# Goal-Based Financial Planner (Open Source)

An open-source, India-first financial planning tool to plan multiple life goals using
inflation, ROI, SIPs, priorities, and dynamic funding sources.

This project aims to provide **transparent, explainable, and realistic** financial planning
— not black-box calculators.

---

## ✨ How to Use

**Step 1: Define Your Goals**

Each row represents one financial goal.

Example:

Goal	- Fund for marriage
Priority	- 1
Current Cost	- 50,00,000 (like the cost if you decide to get married today)
Years	- 5
Months	- 0
Inflation %	- 8% (if it costs 50 lacs today, surely it will not cost the same 5 years later)
New SIP ROI % - 10% (to achieve the goal you will invest somewhere, what ROI that somewhere will fetch?, if you contribute to marraige fund by putting money in FD, then enter 4.55% here (7% minus 35% tax))

Explanation:

Current Cost = cost in today’s money

Inflation % = how fast this goal’s cost grows

Priority = lower number = higher importance

New SIP ROI % = expected return on future SIPs

**Step 2 - Add Your Existing Money Sources**

You won't be spending 50 lacs on marriage if you don't have any savings already. So, sources represent where your money already is.

Examples:

Cash

Bank savings

Fixed deposits

Mutual funds

Stocks

Any custom source

Each source has its own ROI.

Example:

Source	ROI %
Cash	0
Bank	4
Equity MF	12

You can:

add sources

rename them

delete them

change ROI anytime
---
**Step 3: Allocate Existing Money to Goals**

Under each source column, enter how much money is already set aside for that goal.

Example (Marriage Fund):

Cash	- 10,00,000
Bank	- 10,00,000
Equity MF - 0

This means:

₹20 lakh already saved today

Each source grows at its own ROI

**Step 4: Apply Changes**

After editing goals or amounts:

👉 Click “Apply Changes”

This:
- saves your inputs
- recalculates everything
- prevents accidental data loss

****Step 5: Understand the Output**

For each goal, the tool shows:

|Output Column |	Meaning|
|Total Existing (Today)|	Money you already have for this goal (That's the sum of your sources)|
|Additional Lumpsum Required Today	| One-time amount needed now (If you want to invest lumpsum today)|
|Additional SIP Required / Month	| Monthly SIP needed if no extra lumpsum (If you have no lumpsum money right now, you can do monthly SIP to achieve your goal)|

_Example Interpretation -_

If you see:

Total Existing (Today): ₹20,00,000

Additional SIP Required / Month: ₹55,000

It means:

“Given my current savings and expected returns, I need to invest ₹55,000 per month to fully fund this goal.”**

## 🚀 Current Status

- Core calculations: ✅ Working
- UI/UX: 🟡 Improving
- Persistence: 🟡 Autosave in progress
- Documentation: 🟡 Improving

This is an **actively evolving project**.

---

## 🧠 Who Is This For?

- Financial planners
- Finance enthusiasts
- Developers interested in FinTech
- Students looking for real-world open-source projects

---

## 🛠️ Tech Stack

- Python
- Streamlit
- Pandas

---
## How to Access website?
- Linke -> https://goal-based-investment-planner.streamlit.app/

## 🧩 How to Run Locally

```bash
pip install -r requirements.txt
streamlit run pfapp.py
