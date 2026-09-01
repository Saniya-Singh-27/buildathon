"""
Dashboard (Phase 9).

Reads everything from SQLite - spending history, the verdicts the app has
given, what the user did about them, and the simulated checkouts.

On the charts:

Both are hand-rolled HTML bars rather than a plotting library. The app is
heavily custom-styled and a chart library would spend its life fighting
that theme for a result that's two bar charts; this way the marks follow
the same design language as everything else, with no extra dependency.

Colour decisions, deliberately (and validated, not eyeballed):
- Category spend is a nominal breakdown, so every bar is ONE hue rather
  than a darker-where-bigger ramp. A value-ramp on unordered categories
  double-encodes bar length as colour and burns the only free channel on
  information the chart already shows. The hue (#ec4899) was checked
  against this app's actual card surface for the lightness band, chroma
  floor and 3:1 contrast.
- The verdict breakdown is status data, so it uses fixed good/warning/
  critical colours. Red and green are ~4 Delta E apart under deuteranopia -
  effectively identical for a red-green colourblind reader - so every bar
  carries an icon and a written label. The colour is reinforcement, never
  the thing carrying the meaning.
- Both charts have a table view underneath, so no value is reachable only
  by looking at a mark.
"""

import html

import pandas as pd
import streamlit as st

import database
from data_loader import load_transactions, spend_by_category, total_spent
from spending_analyzer import remaining_discretionary_budget

BAR_HUE = "#ec4899"

# Fixed status palette - never themed, never reused for a non-status series.
STATUS_COLORS = {
    "BUY": "#0ca30c",
    "WAIT": "#fab219",
    "DONT_BUY": "#d03b3b",
}
VERDICT_DISPLAY = {
    "BUY": ("🟢", "Buy"),
    "WAIT": ("🟡", "Wait"),
    "DONT_BUY": ("🔴", "Don't buy"),
}

CATEGORY_LABELS_FALLBACK = str.title


def _rupees(value: float) -> str:
    return f"Rs {value:,.0f}"


def _bar_rows_html(rows: list[tuple[str, float, str]], max_value: float) -> str:
    """Build the HTML for a set of horizontal bars.

    rows: (label, value, colour). Every bar is direct-labelled with its
    value, so the chart is readable without hovering anything.
    """
    parts = []
    for label, value, color in rows:
        width = (value / max_value * 100) if max_value > 0 else 0
        safe_label = html.escape(str(label))
        parts.append(
            f'<div class="viz-row" title="{safe_label}: {_rupees(value)}">'
            f'<div class="viz-label">{safe_label}</div>'
            f'<div class="viz-track"><div class="viz-bar" '
            f'style="width:{width:.1f}%;background:{color};"></div></div>'
            f'<div class="viz-value">{_rupees(value)}</div>'
            f"</div>"
        )
    return f'<div class="viz-chart">{"".join(parts)}</div>'


def _count_rows_html(rows: list[tuple[str, int, str]], max_value: int) -> str:
    """Same bars, but for counts rather than money."""
    parts = []
    for label, value, color in rows:
        width = (value / max_value * 100) if max_value > 0 else 0
        safe_label = html.escape(str(label))
        parts.append(
            f'<div class="viz-row" title="{safe_label}: {value}">'
            f'<div class="viz-label">{safe_label}</div>'
            f'<div class="viz-track"><div class="viz-bar" '
            f'style="width:{width:.1f}%;background:{color};"></div></div>'
            f'<div class="viz-value">{value}</div>'
            f"</div>"
        )
    return f'<div class="viz-chart">{"".join(parts)}</div>'


def _stat_tile(label: str, value: str, note: str = "") -> str:
    note_html = f'<div class="stat-note">{html.escape(note)}</div>' if note else ""
    return (
        f'<div class="stat-tile"><div class="stat-label">{html.escape(label)}</div>'
        f'<div class="stat-value">{html.escape(value)}</div>{note_html}</div>'
    )


def render_dashboard(monthly_budget, discretionary_budget, essential_categories, category_labels):
    st.markdown('<div class="big-title">THE DAMAGE REPORT</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">every verdict, every category, every time you ignored me.</div>',
        unsafe_allow_html=True,
    )

    df = load_transactions()
    if df.empty:
        st.warning(
            "No transaction history yet. Run `python3 data/generate_data.py` and restart."
        )
        return

    checks = database.get_purchase_checks()
    reference_date = df["date"].max()
    remaining = remaining_discretionary_budget(
        df, discretionary_budget, essential_categories, reference_date
    )
    this_month = df[
        (df["date"].dt.year == reference_date.year)
        & (df["date"].dt.month == reference_date.month)
    ]["amount"].sum()

    # --- headline numbers: a KPI row, not a chart. -------------------------
    tiles = [
        _stat_tile("Spent this month", _rupees(this_month), f"of {_rupees(monthly_budget)} budget"),
        _stat_tile(
            "Fun budget left",
            _rupees(remaining) if remaining > 0 else f"-{_rupees(abs(remaining))}",
            "cooked" if remaining <= 0 else "still breathing",
        ),
        _stat_tile("Tracked spend", _rupees(total_spent(df)), f"{len(df)} transactions"),
        _stat_tile("Verdicts given", str(len(checks)), "times you asked me"),
    ]
    st.markdown(f'<div class="stat-row">{"".join(tiles)}</div>', unsafe_allow_html=True)

    # --- where the money goes ---------------------------------------------
    st.markdown("### Where your money actually goes")
    st.caption(f"All {len(df)} transactions, by category.")
    category_spend = spend_by_category(df)
    rows = [
        (category_labels.get(cat, CATEGORY_LABELS_FALLBACK(cat)), float(amount), BAR_HUE)
        for cat, amount in category_spend.items()
    ]
    st.markdown(
        _bar_rows_html(rows, max_value=float(category_spend.max())), unsafe_allow_html=True
    )
    with st.expander("See the numbers"):
        st.dataframe(
            pd.DataFrame(
                {
                    "Category": [r[0] for r in rows],
                    "Spent": [round(r[1]) for r in rows],
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    # --- what the app has been telling them --------------------------------
    st.markdown("### What I've been telling you")
    if checks.empty:
        st.info("No verdicts yet. Go judge something and come back.")
        return

    verdict_counts = checks["verdict"].value_counts()
    verdict_rows = []
    for verdict in ("BUY", "WAIT", "DONT_BUY"):
        icon, name = VERDICT_DISPLAY[verdict]
        verdict_rows.append(
            (f"{icon} {name}", int(verdict_counts.get(verdict, 0)), STATUS_COLORS[verdict])
        )
    st.markdown(
        _count_rows_html(verdict_rows, max_value=max(r[1] for r in verdict_rows) or 1),
        unsafe_allow_html=True,
    )

    # --- the receipts -------------------------------------------------------
    st.markdown("### The receipts")
    display = checks.copy()
    display["verdict"] = display["verdict"].map(lambda v: " ".join(VERDICT_DISPLAY[v]))
    display["user_decision"] = display["user_decision"].fillna("no answer")
    display = display.rename(
        columns={
            "id": "#",
            "product": "Product",
            "price": "Price",
            "category": "Category",
            "verdict": "Verdict",
            "user_decision": "You did",
            "timestamp": "When",
        }
    )
    st.dataframe(
        display[["#", "Product", "Price", "Category", "Verdict", "You did", "When"]],
        hide_index=True,
        use_container_width=True,
    )

    # --- the ones they ignored ---------------------------------------------
    ignored = checks[
        (checks["verdict"].isin(["DONT_BUY", "WAIT"]))
        & (checks["user_decision"] == "bought_anyway")
    ]
    st.markdown("### Times you ignored me")
    if ignored.empty:
        st.success("zero. genuinely unserious behaviour has not been detected. proud of you.")
    else:
        ignored_total = ignored["price"].sum()
        st.markdown(
            f'<div class="bestie-note">you overruled me <strong>{len(ignored)}</strong> '
            f"time(s), for <strong>{_rupees(ignored_total)}</strong> total. "
            "no judgement, just keeping receipts.</div>",
            unsafe_allow_html=True,
        )
        ignored_display = ignored[["id", "product", "price", "verdict"]].copy()
        ignored_display["verdict"] = ignored_display["verdict"].map(
            lambda v: " ".join(VERDICT_DISPLAY[v])
        )
        st.dataframe(
            ignored_display.rename(
                columns={"id": "#", "product": "Product", "price": "Price", "verdict": "I said"}
            ),
            hide_index=True,
            use_container_width=True,
        )

    # --- simulated checkouts -------------------------------------------------
    payments_df = database.get_payments()
    st.markdown("### Test checkouts")
    st.caption("Simulated Razorpay test payments only - no real money has ever moved here.")
    if payments_df.empty:
        st.info("No test payments recorded yet.")
    else:
        st.dataframe(
            payments_df.rename(
                columns={
                    "id": "#",
                    "purchase_check_id": "Check #",
                    "amount": "Amount",
                    "status": "Status",
                    "reference": "Reference",
                    "timestamp": "When",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
