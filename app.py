import streamlit as st
from datetime import date

from sidebar import build_sidebar
from tab_current import tab_current_month
from tab_next import tab_next_month
from tab_savings import tab_future_savings

st.set_page_config(page_title="Budget Dashboard", page_icon="💰", layout="wide")


def main() -> None:
    st.title("💰 Personal Budget Dashboard")
    st.caption(f"Today: {date.today().strftime('%A, %B %d, %Y')}")

    build_sidebar()

    tab1, tab2, tab3 = st.tabs(["📅 Current Month", "🗓️ Next Month", "🏦 Future Savings"])
    with tab1:
        tab_current_month()
    with tab2:
        tab_next_month()
    with tab3:
        tab_future_savings()


if __name__ == "__main__":
    main()
