"""
tab_savings.py – Tab 3: Future Savings Plans (overview, mortgage, car, 401k).
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta

import plotly.express as px
import streamlit as st

from utils import fmt
from future_io import (
    load_future_latest,
    save_future,
    apply_future_to_state,
    FUTURE_DEFAULTS,
    _use_supabase,
)


def tab_future_savings() -> None:
    # ── Load defaults from CSV / Supabase once per session ───────────────────
    if not st.session_state.get("_future_loaded"):
        row = load_future_latest()
        if row:
            apply_future_to_state(row)
        st.session_state["_future_loaded"] = True

    st.header("🏦 Future Savings Plans")

    savings_tab, mortgage_tab, car_tab, k401_tab = st.tabs([
        "💰 Savings Overview",
        "🏠 Mortgage Down Payment",
        "🚗 Car Payment Schedule",
        "📈 401k Projections",
    ])

    # ─── Savings Overview ────────────────────────────────────────────────────
    with savings_tab:
        _savings_overview()

    # ─── Mortgage Down Payment ───────────────────────────────────────────────
    with mortgage_tab:
        _mortgage_calculator()

    # ─── Car Payment Schedule ────────────────────────────────────────────────
    with car_tab:
        _car_amortization()

    # ─── 401k Projections ────────────────────────────────────────────────────
    with k401_tab:
        _k401_projections()

    # ── Save button ──────────────────────────────────────────────────────────
    st.divider()
    if st.button("💾 Save Future Savings Defaults", key="save_future_btn", width='stretch'):
        save_future(st.session_state)
        backend = "☁️ Supabase" if _use_supabase() else "📄 future_data.csv"
        st.success(f"✅ Future Savings defaults saved to {backend}!")
    if _use_supabase():
        st.caption("☁️ Storage: **Supabase** (cloud)")
    else:
        st.caption("📄 Storage: **local CSV** (future_data.csv)")


# ─────────────────────────────────────────────────────────────────────────────
# Sub-sections
# ─────────────────────────────────────────────────────────────────────────────

def _savings_overview() -> None:
    import pandas as pd

    st.subheader("Current Accounts")
    col1, col2 = st.columns(2)
    with col1:
        ally      = st.number_input("Ally Savings ($)",     value=st.session_state.get("ally",         FUTURE_DEFAULTS["ally"]),         step=100.0, key="ally")
        burke     = st.number_input("Burke Savings ($)",    value=st.session_state.get("burke",        FUTURE_DEFAULTS["burke"]),        step=100.0, key="burke")
        robinhood = st.number_input("Robin Hood ($)",       value=st.session_state.get("rh",           FUTURE_DEFAULTS["rh"]),           step=100.0, key="rh")
        schwab    = st.number_input("Charles Schwab ($)",   value=st.session_state.get("schwab",       FUTURE_DEFAULTS["schwab"]),       step=100.0, key="schwab")
        merill    = st.number_input("Merrill (TJX) ($)",    value=st.session_state.get("merill",       FUTURE_DEFAULTS["merill"]),       step=100.0, key="merill")
    with col2:
        checking  = st.number_input("Checking ($)",         value=st.session_state.get("sav_checking", FUTURE_DEFAULTS["sav_checking"]), step=100.0, key="sav_checking")
        goal      = st.number_input("Savings Goal ($)",     value=st.session_state.get("sav_goal",     FUTURE_DEFAULTS["sav_goal"]),     step=1000.0, key="sav_goal")

    liquid         = ally + burke + robinhood
    total_liquid   = liquid + checking
    total_combined = total_liquid + schwab + merill

    st.divider()
    s1, s2, s3 = st.columns(3)
    s1.metric("Liquid Savings",                 fmt(liquid))
    s2.metric("Total Liquid (incl. Checking)",  fmt(total_liquid))
    s3.metric("Total Combined (all accounts)",  fmt(total_combined))

    goal_balance = total_liquid + schwab      # liquid + Schwab count toward goal
    remaining    = goal - goal_balance
    progress     = min(goal_balance / goal, 1.0) if goal > 0 else 0.0
    pct_reached  = progress * 100
    st.progress(progress,
                text=(
                    f"Savings Goal Progress: {fmt(goal_balance)} / {fmt(goal)} "
                    f"— {pct_reached:.1f}% reached  ({remaining:+,.2f} remaining)"
                ))

    fig = px.pie(
        values=[ally, burke, robinhood, schwab, merill, checking],
        names=["Ally Savings", "Burke Savings", "Robin Hood",
               "Charles Schwab", "Merrill (TJX)", "Checking"],
        title="Asset Allocation",
    )
    st.plotly_chart(fig, width='stretch')

    st.subheader("Monthly Savings Projections")
    monthly_save = st.number_input("Monthly Savings Amount ($)", value=st.session_state.get("monthly_save", FUTURE_DEFAULTS["monthly_save"]), step=50.0, key="monthly_save")
    months_ahead = st.slider("Months to Project", min_value=6, max_value=60, value=st.session_state.get("sav_months", FUTURE_DEFAULTS["sav_months"]), key="sav_months")

    today = date.today()
    rows  = []
    bal   = total_liquid
    for i in range(1, months_ahead + 1):
        future_month = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        bal += monthly_save
        rows.append({"Month": future_month.strftime("%b %Y"), "Projected Savings": bal})

    fut_df = pd.DataFrame(rows)
    fig2   = px.line(fut_df, x="Month", y="Projected Savings", markers=True,
                     title=f"Projected Liquid Savings over {months_ahead} months")
    fig2.add_hline(y=goal, line_dash="dash", line_color="green", annotation_text="Goal")
    st.plotly_chart(fig2, width='stretch')


def _mortgage_calculator() -> None:
    import pandas as pd

    st.subheader("🏠 Mortgage Down Payment Calculator")
    col1, col2 = st.columns(2)
    with col1:
        home_price      = st.number_input("Home Price ($)",      value=st.session_state.get("hp",         FUTURE_DEFAULTS["hp"]),         step=10000.0, key="hp")
        dp_pct          = st.slider("Down Payment %",            min_value=3, max_value=20, value=st.session_state.get("dp_pct",   FUTURE_DEFAULTS["dp_pct"]),   key="dp_pct")
        current_saved   = st.number_input("Currently Saved ($)", value=st.session_state.get("dp_saved",   FUTURE_DEFAULTS["dp_saved"]),   step=500.0, key="dp_saved")
        monthly_dp_save = st.number_input("Monthly Contribution to Down Payment ($)",
                                          value=st.session_state.get("dp_monthly", FUTURE_DEFAULTS["dp_monthly"]), step=50.0, key="dp_monthly")
    with col2:
        down_payment    = home_price * dp_pct / 100
        remaining_dp    = max(down_payment - current_saved, 0)
        months_to_goal  = int(remaining_dp / monthly_dp_save) + 1 if monthly_dp_save > 0 else 999

        st.metric("Required Down Payment", fmt(down_payment))
        st.metric("Already Saved",         fmt(current_saved))
        st.metric("Still Needed",          fmt(remaining_dp))
        st.metric("Months to Goal",        str(months_to_goal))

    st.subheader("Down Payment Targets by Price & %")
    prices    = [200_000, 250_000, 300_000, 350_000, 400_000, 450_000, 500_000, 550_000, 600_000]
    pcts      = [3, 5, 8, 10, 12, 20]
    dp_table  = pd.DataFrame(
        {f"{p}%": [fmt(pr * p / 100) for pr in prices] for p in pcts},
        index=[fmt(pr) for pr in prices],
    )
    dp_table.index.name = "Home Price"
    st.dataframe(dp_table, width='stretch')

    today     = date.today()
    save_rows = []
    bal       = current_saved
    for i in range(1, months_to_goal + 2):
        future_month = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        bal = min(bal + monthly_dp_save, down_payment * 1.1)
        save_rows.append({"Month": future_month.strftime("%b %Y"), "Saved": bal, "Target": down_payment})
    sr_df = pd.DataFrame(save_rows)
    fig3  = px.line(sr_df, x="Month", y=["Saved", "Target"],
                    title="Down Payment Savings Progress",
                    labels={"value": "Amount ($)", "variable": "Series"})
    st.plotly_chart(fig3, width='stretch')


def _car_amortization() -> None:
    st.subheader("🚗 Car Loan Amortization")
    col1, col2, col3 = st.columns(3)
    with col1:
        loan_balance = st.number_input("Current Loan Balance ($)", value=st.session_state.get("car_bal",   FUTURE_DEFAULTS["car_bal"]),   step=100.0, key="car_bal")
        annual_rate  = st.number_input("Annual Interest Rate (%)", value=st.session_state.get("car_rate",  FUTURE_DEFAULTS["car_rate"]),  step=0.1, format="%.2f", key="car_rate")
    with col2:
        monthly_payment = st.number_input("Monthly Payment ($)",           value=st.session_state.get("car_pay",   FUTURE_DEFAULTS["car_pay"]),   step=10.0,  key="car_pay")
        extra_annual    = st.number_input("Extra Annual Payment (Apr) ($)", value=st.session_state.get("car_extra", FUTURE_DEFAULTS["car_extra"]), step=100.0, key="car_extra")
    with col3:
        loan_start = st.date_input("Loan Start Date", value=st.session_state.get("car_start", date.fromisoformat(FUTURE_DEFAULTS["car_start"])), key="car_start")

    monthly_rate = annual_rate / 100 / 12
    balance      = loan_balance
    sched_rows   = []
    cur          = loan_start
    month_num    = 0

    while balance > 0.01:
        month_num += 1
        interest  = round(balance * monthly_rate, 2)
        payment   = monthly_payment + (extra_annual if cur.month == 4 and month_num > 1 else 0)
        payment   = min(payment, balance + interest)
        principal = round(payment - interest, 2)
        balance   = round(balance - principal, 2)
        sched_rows.append({
            "Month": month_num, "Date": cur.strftime("%b-%y"),
            "Payment": payment, "Interest": interest,
            "Principal": principal, "Remaining Balance": max(balance, 0),
        })
        cur = cur.replace(month=cur.month + 1) if cur.month < 12 else date(cur.year + 1, 1, 1)
        if month_num > 600:
            break

    import pandas as pd
    sched_df = pd.DataFrame(sched_rows)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Interest Paid", fmt(sched_df["Interest"].sum()))
    m2.metric("Payoff Date",         sched_df.iloc[-1]["Date"])
    m3.metric("Total Months",        str(len(sched_df)))

    fig_car = px.area(sched_df, x="Date", y=["Principal", "Interest"],
                      title="Car Loan: Principal vs Interest per Payment",
                      labels={"value": "Amount ($)", "variable": "Component"})
    st.plotly_chart(fig_car, width='stretch')

    fig_bal = px.line(sched_df, x="Date", y="Remaining Balance",
                      title="Remaining Loan Balance Over Time")
    st.plotly_chart(fig_bal, width='stretch')

    st.dataframe(
        sched_df.style.format({
            "Payment": "${:,.2f}", "Interest": "${:,.2f}",
            "Principal": "${:,.2f}", "Remaining Balance": "${:,.2f}",
        }),
        width='stretch', height=400,
    )


def _k401_projections() -> None:
    import pandas as pd

    # ── IRS contribution limits (2025-2026) ──────────────────────────────────
    BASE_LIMIT      = 24_500   # standard elective deferral
    CATCHUP_50      = 8_000    # extra catch-up age 50+  → total 32,500
    CATCHUP_60_63   = 11_250   # special catch-up age 60-63 → total 35,750
    TOTAL_LIMIT     = 72_000   # combined employee + employer cap

    def _elective_limit(age: int) -> tuple[int, str]:
        """Return (employee deferral cap, label) for a given age."""
        if 60 <= age <= 63:
            return BASE_LIMIT + CATCHUP_60_63, "Special catch-up (60-63)"
        if age >= 50:
            return BASE_LIMIT + CATCHUP_50, "Catch-up (50+)"
        return BASE_LIMIT, "Standard"

    st.subheader("📈 401k Retirement Projections")

    # ── IRS limits info box ──────────────────────────────────────────────────
    with st.expander("📋 IRS Contribution Limits (2025-2026)", expanded=False):
        lc1, lc2, lc3, lc4 = st.columns(4)
        lc1.metric("Standard Limit",             f"${BASE_LIMIT:,}")
        lc2.metric("Catch-up (Age 50+)",          f"${BASE_LIMIT + CATCHUP_50:,}")
        lc3.metric("Special Catch-up (Age 60-63)", f"${BASE_LIMIT + CATCHUP_60_63:,}")
        lc4.metric("Total Emp + Employer Cap",    f"${TOTAL_LIMIT:,}")
        st.caption(
            "Employee contributions are capped at the elective deferral limit for each age. "
            "Combined employee + employer contributions are capped at $72,000 per year."
        )

    col1, col2 = st.columns(2)
    with col1:
        current_401k       = st.number_input("Current 401k Balance ($)", value=st.session_state.get("k401_cur",    FUTURE_DEFAULTS["k401_cur"]),    step=100.0,  key="k401_cur")
        salary             = st.number_input("Current Salary ($)",        value=st.session_state.get("k401_sal",    FUTURE_DEFAULTS["k401_sal"]),    step=1000.0, key="k401_sal")
        contrib_pct        = st.slider("Contribution %",   min_value=1,  max_value=30, value=st.session_state.get("k401_pct",    FUTURE_DEFAULTS["k401_pct"]),    key="k401_pct")
        employer_match_pct = st.slider("Employer Match %", min_value=0,  max_value=10, value=st.session_state.get("k401_emp",    FUTURE_DEFAULTS["k401_emp"]),    key="k401_emp")
    with col2:
        growth_rate          = st.slider("Annual Growth Rate %", min_value=0, max_value=15, value=st.session_state.get("k401_growth", FUTURE_DEFAULTS["k401_growth"]), key="k401_growth")
        annual_bonus_contrib = st.number_input("Annual Bonus Contribution ($)", value=st.session_state.get("k401_bonus",  FUTURE_DEFAULTS["k401_bonus"]),  step=500.0,  key="k401_bonus")
        current_age          = st.number_input("Current Age",           value=st.session_state.get("k401_age",    FUTURE_DEFAULTS["k401_age"]),    step=1,      key="k401_age")
        retire_age           = st.number_input("Target Retirement Age", value=st.session_state.get("k401_retire", FUTURE_DEFAULTS["k401_retire"]), step=1,      key="k401_retire")

    years      = int(retire_age) - int(current_age)
    balance    = current_401k
    k_rows     = []
    cur_salary = salary

    for y in range(1, years + 1):
        age = int(current_age) + y

        # Employee contribution — capped at IRS elective deferral limit
        elective_cap, catchup_label = _elective_limit(age)
        raw_emp    = cur_salary * contrib_pct / 100
        emp_contrib = min(raw_emp, elective_cap)

        # Employer match (on uncapped salary pct — employer limits separate)
        er_contrib = cur_salary * employer_match_pct / 100

        # Combined cap: employee + employer + bonus ≤ TOTAL_LIMIT
        raw_total   = emp_contrib + er_contrib + annual_bonus_contrib
        scale       = min(TOTAL_LIMIT / raw_total, 1.0) if raw_total > 0 else 1.0
        if scale < 1.0:
            emp_contrib          = round(emp_contrib * scale, 2)
            er_contrib           = round(er_contrib  * scale, 2)
            annual_bonus_capped  = round(annual_bonus_contrib * scale, 2)
        else:
            annual_bonus_capped  = annual_bonus_contrib

        total_annual = emp_contrib + er_contrib + annual_bonus_capped
        balance      = round((balance + total_annual) * (1 + growth_rate / 100), 2)

        k_rows.append({
            "Year": y,
            "Age": age,
            "Salary": cur_salary,
            "Employee Contribution": emp_contrib,
            "Employer Match": er_contrib,
            "Bonus Contribution": annual_bonus_capped,
            "Total Annual Contributions": total_annual,
            "IRS Limit": elective_cap,
            "Limit Type": catchup_label,
            "EoY Balance (with growth)": balance,
        })
        cur_salary = salary if y == 1 else round(cur_salary * 1.02, 2)

    k_df = pd.DataFrame(k_rows)

    km1, km2, km3 = st.columns(3)
    km1.metric("Projected Balance at Retirement", fmt(balance))
    km2.metric("Years to Retirement",             str(years))
    km3.metric("Total Employee Contributions",    fmt(k_df["Employee Contribution"].sum()))

    fig_k = px.area(k_df, x="Age", y="EoY Balance (with growth)",
                    title=f"Projected 401k Growth to Age {int(retire_age)}",
                    labels={"EoY Balance (with growth)": "Balance ($)"})
    st.plotly_chart(fig_k, width='stretch')

    fig_k2 = px.bar(k_df, x="Age",
                    y=["Employee Contribution", "Employer Match", "Bonus Contribution"],
                    title="Annual Contributions Breakdown", barmode="stack",
                    color_discrete_map={
                        "Employee Contribution": "#1f77b4",
                        "Employer Match":        "#2ca02c",
                        "Bonus Contribution":    "#ff7f0e",
                    })
    # Overlay the IRS elective deferral limit line
    import plotly.graph_objects as go
    fig_k2.add_trace(go.Scatter(
        x=k_df["Age"], y=k_df["IRS Limit"],
        mode="lines", name="IRS Elective Limit",
        line=dict(color="red", width=2, dash="dash"),
    ))
    st.plotly_chart(fig_k2, width='stretch')

    st.dataframe(
        k_df.style.format({
            "Salary": "${:,.0f}",
            "Employee Contribution": "${:,.0f}",
            "Employer Match": "${:,.0f}",
            "Bonus Contribution": "${:,.0f}",
            "Total Annual Contributions": "${:,.0f}",
            "IRS Limit": "${:,.0f}",
            "EoY Balance (with growth)": "${:,.0f}",
        }),
        width='stretch', height=400,
    )
