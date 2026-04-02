"""
sidebar.py – Sidebar UI: income, recurring expenses, credit cards.
"""
from __future__ import annotations

import streamlit as st
from utils import fmt
from config_io import load_latest, save_current, apply_to_state, is_cloud

# ─────────────────────────────────────────────────────────────────────────────
# Default values
# ─────────────────────────────────────────────────────────────────────────────

REC_DEFAULTS: dict[str, dict] = {
    "rec_rent":      {"label": "Rent",          "amount": 2898.00, "day": 2},
    "rec_parking":   {"label": "Parking",        "amount":   75.00, "day": 2},
    "rec_gas":       {"label": "Gas",            "amount":   85.00, "day": 2},
    "rec_elec":      {"label": "Electricity",    "amount":  100.00, "day": 2},
    "rec_water":     {"label": "Water",          "amount":   55.00, "day": 2},
    "rec_sewer":     {"label": "Sewage",         "amount":  120.00, "day": 2},
    "rec_student":   {"label": "Student Loans",  "amount":  423.00, "day": 10},
    "rec_internet":  {"label": "Internet",       "amount":   69.99, "day": 26},
    "rec_phone":     {"label": "Phone",          "amount":   90.04, "day": 29},
    "rec_insurance": {"label": "Insurance",      "amount":  150.00, "day":  3},
    "rec_subs":      {"label": "Subscriptions",  "amount":   47.00, "day": 24},
}

CC_DEFAULTS: list[dict] = [
    {"name": "Discover",   "statement_balance": 1213.97, "current_balance": 0.0, "pay_day": 8},
    {"name": "MasterCard", "statement_balance": 1288.45, "current_balance": 0.0, "pay_day": 17},
]


# ─────────────────────────────────────────────────────────────────────────────
# Session-state initialisation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _init_state() -> None:
    """Initialise all session_state keys that might not yet exist."""
    # ── Load from CSV once per session (only if state hasn't been set yet) ───
    if not st.session_state.get("_csv_loaded"):
        row = load_latest()
        if row:
            apply_to_state(row)
        st.session_state["_csv_loaded"] = True

    if "oe_rows" not in st.session_state:
        st.session_state.oe_rows = []
    if "add_income_rows" not in st.session_state:
        st.session_state.add_income_rows = []
    if "oe_expense_rows" not in st.session_state:
        st.session_state.oe_expense_rows = []
    if "cc_cards" not in st.session_state:
        st.session_state.cc_cards = [dict(c) for c in CC_DEFAULTS]

    # Ensure each recurring expense key exists and has the right shape
    for key, defaults in REC_DEFAULTS.items():
        existing = st.session_state.get(key)
        if not isinstance(existing, dict) or "day" not in existing:
            st.session_state[key] = {"amount": defaults["amount"], "day": defaults["day"]}

    # Migrate legacy card field names
    for card in st.session_state.cc_cards:
        if "last_statement" in card and "statement_balance" not in card:
            card["statement_balance"] = card.pop("last_statement")
        if "running" in card and "current_balance" not in card:
            card["current_balance"] = card.pop("running")


# ─────────────────────────────────────────────────────────────────────────────
# Sub-sections
# ─────────────────────────────────────────────────────────────────────────────

def _section_income() -> None:
    st.subheader("💵 Income")

    st.number_input(
        "Paycheck Amount ($)", min_value=0.0, step=10.0, format="%.2f",
        value=st.session_state.get("paycheck_amount", 1490.00),
        key="paycheck_amount",
    )

    pay_frequency = st.radio(
        "Pay Frequency", options=["Weekly", "Monthly"],
        index=0 if st.session_state.get("pay_frequency", "Weekly") == "Weekly" else 1,
        key="pay_frequency",
    )

    if pay_frequency == "Weekly":
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        pay_weekday = st.selectbox(
            "Payday (day of week)", options=weekday_names,
            index=st.session_state.get("pay_weekday_idx", 4),
            key="pay_weekday_name",
        )
        st.session_state["pay_weekday_idx"] = weekday_names.index(pay_weekday)
        st.caption(f"📅 Paydays: every **{pay_weekday}**")
    else:
        st.number_input(
            "Payday (day of month)", min_value=1, max_value=31, step=1,
            value=st.session_state.get("pay_monthly_day", 1),
            key="pay_monthly_day",
        )
        st.caption(f"📅 Payday: **day {int(st.session_state.get('pay_monthly_day', 1))}** of each month")

    st.caption(f"💵 Amount: **{fmt(st.session_state.get('paycheck_amount', 1490.0))}** per paycheck")


def _section_additional_income() -> None:
    def _add():
        st.session_state.add_income_rows.append({"description": "", "amount": 0.0, "day": 1})

    def _del(i: int):
        st.session_state.add_income_rows.pop(i)

    with st.expander("💸 Additional Income", expanded=False):
        st.caption("One-time income this month (bonus, side work, reimbursement, etc.).")
        for i, row in enumerate(st.session_state.add_income_rows):
            st.markdown(f"**Income #{i + 1}**")
            ca, cb = st.columns([3, 2])
            with ca:
                st.session_state.add_income_rows[i]["description"] = st.text_input(
                    "Description", value=row["description"],
                    key=f"ai_desc_{i}", placeholder="e.g. Bonus",
                    label_visibility="collapsed",
                )
            with cb:
                st.session_state.add_income_rows[i]["amount"] = st.number_input(
                    "Amount ($)", value=float(row["amount"]),
                    min_value=0.0, step=1.0, format="%.2f",
                    key=f"ai_amt_{i}", label_visibility="collapsed",
                )
            st.session_state.add_income_rows[i]["day"] = st.number_input(
                "Day of month", value=int(row["day"]),
                min_value=1, max_value=31, step=1, key=f"ai_day_{i}",
            )
            st.button("🗑️ Remove", key=f"ai_del_{i}", on_click=_del, args=(i,))
            st.divider()

        st.button("➕ Add Income", on_click=_add, key="add_income_btn")
        if st.session_state.add_income_rows:
            total_ai = sum(r["amount"] for r in st.session_state.add_income_rows)
            st.caption(f"Total additional income: **{fmt(total_ai)}**")


def _section_recurring_expenses() -> None:
    st.subheader("📉 Recurring Expenses")

    with st.expander("🏠 Housing & Utilities", expanded=False):
        st.caption("Amount and day-of-month each bill is due.")
        for key in ["rec_rent", "rec_parking", "rec_gas", "rec_elec", "rec_water", "rec_sewer"]:
            lbl   = REC_DEFAULTS[key]["label"]
            entry = st.session_state[key]
            ca, cd = st.columns([2, 1])
            with ca:
                new_amt = st.number_input(f"{lbl} ($)", value=float(entry["amount"]),
                                          step=1.0, format="%.2f", key=f"{key}_amt")
            with cd:
                new_day = st.number_input("Day", value=int(entry["day"]),
                                          min_value=1, max_value=31, step=1, key=f"{key}_day")
            st.session_state[key] = {"amount": new_amt, "day": new_day}

    with st.expander("📡 Bills & Subscriptions", expanded=False):
        for key in ["rec_student", "rec_internet", "rec_phone", "rec_insurance", "rec_subs"]:
            lbl   = REC_DEFAULTS[key]["label"]
            entry = st.session_state[key]
            ca, cd = st.columns([2, 1])
            with ca:
                new_amt = st.number_input(f"{lbl} ($)", value=float(entry["amount"]),
                                          step=0.01, format="%.2f", key=f"{key}_amt")
            with cd:
                new_day = st.number_input("Day", value=int(entry["day"]),
                                          min_value=1, max_value=31, step=1, key=f"{key}_day")
            st.session_state[key] = {"amount": new_amt, "day": new_day}


def _section_one_time_expenses() -> None:
    def _add():
        st.session_state.oe_expense_rows.append({"name": "", "amount": 0.0, "day": 1})

    def _del(i: int):
        st.session_state.oe_expense_rows.pop(i)

    with st.expander("🧾 Additional One-time Expenses", expanded=False):
        st.caption("Non-recurring expenses this month (car repair, medical bill, etc.).")
        for i, row in enumerate(st.session_state.oe_expense_rows):
            st.markdown(f"**Expense #{i + 1}**")
            ca, cb = st.columns([3, 2])
            with ca:
                st.session_state.oe_expense_rows[i]["name"] = st.text_input(
                    "Name", value=row["name"],
                    key=f"oe_name_{i}", placeholder="e.g. Car Repair",
                    label_visibility="collapsed",
                )
            with cb:
                st.session_state.oe_expense_rows[i]["amount"] = st.number_input(
                    "Amount ($)", value=float(row["amount"]),
                    min_value=0.0, step=1.0, format="%.2f",
                    key=f"oe_amt_{i}", label_visibility="collapsed",
                )
            st.session_state.oe_expense_rows[i]["day"] = st.number_input(
                "Day of month", value=int(row["day"]),
                min_value=1, max_value=31, step=1, key=f"oe_day_{i}",
            )
            st.button("🗑️ Remove", key=f"oe_del_{i}", on_click=_del, args=(i,))
            st.divider()

        st.button("➕ Add Expense", on_click=_add, key="add_oe_expense_btn")
        if st.session_state.oe_expense_rows:
            total_oe = sum(r["amount"] for r in st.session_state.oe_expense_rows)
            st.caption(f"Total one-time expenses: **{fmt(total_oe)}**")


def _section_credit_cards() -> None:
    st.subheader("💳 Credit Cards")

    def _add_card():
        st.session_state.cc_cards.append(
            {"name": "New Card", "statement_balance": 0.0, "current_balance": 0.0, "pay_day": 15}
        )

    def _del_card(i: int):
        st.session_state.cc_cards.pop(i)

    for i, card in enumerate(st.session_state.cc_cards):
        stmt  = float(card.get("statement_balance", 0.0))
        curr  = float(card.get("current_balance",  0.0))
        carry = max(curr - stmt, 0.0) if curr > 0 else 0.0

        with st.expander(f"💳 {card['name']}", expanded=False):
            st.session_state.cc_cards[i]["name"] = st.text_input(
                "Card Name", value=card["name"], key=f"cc_name_{i}")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state.cc_cards[i]["statement_balance"] = st.number_input(
                    "Statement Balance ($)",
                    help="Amount on your last statement — due this month.",
                    value=stmt, min_value=0.0, step=0.01, format="%.2f", key=f"cc_stmt_{i}")
            with c2:
                st.session_state.cc_cards[i]["current_balance"] = st.number_input(
                    "Current Balance ($)",
                    help="Your live balance right now. Leave 0 if same as statement.",
                    value=curr, min_value=0.0, step=0.01, format="%.2f", key=f"cc_curr_{i}")
            with c3:
                st.session_state.cc_cards[i]["pay_day"] = st.number_input(
                    "Due Day",
                    help="Day of month the statement balance is due.",
                    value=int(card.get("pay_day", 15)),
                    min_value=1, max_value=31, step=1, key=f"cc_day_{i}")

            if carry > 0:
                st.caption(f"⚠️ Carry-over to next month: **{fmt(carry)}** (current − statement)")
            else:
                st.caption("✅ No carry-over balance for next month.")

            st.button("🗑️ Remove Card", key=f"cc_del_{i}", on_click=_del_card, args=(i,))

    st.button("➕ Add Card", on_click=_add_card, key="add_card_btn")

    total_stmt  = sum(c.get("statement_balance", 0.0) for c in st.session_state.cc_cards)
    total_carry = sum(
        max(c.get("current_balance", 0.0) - c.get("statement_balance", 0.0), 0.0)
        for c in st.session_state.cc_cards
    )
    st.caption(f"📋 Statement total (due this month): **{fmt(total_stmt)}**")
    if total_carry > 0:
        st.caption(f"⏭️ Carry-over total (due next month): **{fmt(total_carry)}**")


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def build_sidebar() -> None:
    """Render the full sidebar and initialise all session_state keys."""
    _init_state()

    with st.sidebar:
        _section_income()
        st.divider()
        _section_additional_income()
        st.divider()
        _section_recurring_expenses()
        st.divider()
        _section_one_time_expenses()
        st.divider()
        _section_credit_cards()
        st.divider()

        if st.button("💾 Save All Changes", key="save_all_changes_btn", use_container_width=True):
            save_current(st.session_state)
            backend = "☁️ Supabase" if is_cloud() else "📄 current_data.csv"
            st.success(f"✅ All changes saved to {backend}!")
        # Show which backend is active
        if is_cloud():
            st.caption("☁️ Storage: **Supabase** (cloud)")
        else:
            st.caption("📄 Storage: **local CSV**")
