"""
Should I Buy This? - Streamlit app entrypoint.

Phase 1 scope: landing screen with product/price input, and a placeholder
verdict screen so the end-to-end click flow exists. There is no spending
data, no decision engine, and no AI yet - those arrive in later phases.
"""

import streamlit as st

from data_loader import load_transactions, summary
from styles import CUSTOM_CSS

st.set_page_config(page_title="Should I Buy This?", page_icon="💸", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "home"
if "product_name" not in st.session_state:
    st.session_state.product_name = ""
if "price" not in st.session_state:
    st.session_state.price = 0.0


def go_to_result():
    st.session_state.page = "result"


def go_home():
    st.session_state.page = "home"
    st.session_state.product_name = ""
    st.session_state.price = 0.0


def render_home():
    st.markdown('<div class="big-title">SHOULD I BUY THIS?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Your brutally honest, secretly supportive money friend.</div>',
        unsafe_allow_html=True,
    )

    try:
        df = load_transactions()
        stats = summary(df)
        st.caption(
            f"Data check: {stats['transaction_count']} transactions loaded • "
            f"Rs {stats['total_spent']:,.0f} total spend • "
            f"Rs {stats['current_month_spend']:,.0f} spent this month"
        )
    except FileNotFoundError:
        st.warning("No transaction data found. Run `python3 data/generate_data.py` first.")

    with st.container(border=True):
        st.markdown("**Upload what you're about to buy**")
        st.file_uploader(
            "Screenshot of the product or checkout page",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed",
        )
        st.caption("Screenshot understanding isn't wired up yet - it's coming in a later phase.")

    st.markdown('<div class="or-divider">OR</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**Enter it yourself**")
        product_name = st.text_input("Product", placeholder="e.g. Black blazer")
        price = st.number_input("Price (INR)", min_value=0.0, step=50.0, format="%.2f")

        judge_clicked = st.button("JUDGE ME", type="primary", use_container_width=True)

        if judge_clicked:
            if not product_name.strip():
                st.warning("Tell me what you're buying first.")
            elif price <= 0:
                st.warning("That price can't be real. Try again.")
            else:
                st.session_state.product_name = product_name.strip()
                st.session_state.price = price
                go_to_result()
                st.rerun()


def render_result():
    st.markdown(
        '<span class="placeholder-tag">PLACEHOLDER VERDICT - not calculated yet</span>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="verdict-banner verdict-wait">🟡 WAIT</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="price-tag">{st.session_state.product_name} — '
        f'₹{st.session_state.price:,.2f}</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("**Why I'm saying this (placeholder reasons):**")
        for reason in [
            "This is dummy data - the real spending analysis isn't built yet",
            "Once your transaction history is loaded, this will be a real calculation",
            "The verdict logic (BUY / WAIT / DON'T BUY) arrives in Phase 4",
        ]:
            st.markdown(f'<div class="reason-item">• {reason}</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="bestie-note">"Not gonna lie, I\'m just a placeholder right now. '
        'Come back after Phase 6 for the real commentary."</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.button("WAIT 72 HOURS", use_container_width=True, disabled=True)
    with col2:
        st.button("BUY ANYWAY 💀", use_container_width=True, disabled=True)
    st.caption("These buttons are disabled for now - they'll do something in a later phase.")

    st.button("← Judge something else", on_click=go_home)


if st.session_state.page == "home":
    render_home()
else:
    render_result()
