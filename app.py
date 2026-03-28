import streamlit as st

from src.config import DEFAULT_WATCHLIST, APP_TITLE
from src.scanner import run_stock_scanner

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.title(APP_TITLE)
st.caption("Find the best trend + momentum stocks for your trading style.")

with st.sidebar:
    st.header("Scanner Settings")

    custom_symbols = st.text_area(
        "Symbols to scan (comma-separated)",
        value=",".join(DEFAULT_WATCHLIST),
        height=120,
    )

    symbols = [s.strip().upper() for s in custom_symbols.split(",") if s.strip()]
    run_scan = st.button("Run Scanner", use_container_width=True)

st.markdown(
    """
### What this app does
This scanner ranks symbols using:
- VWAP position
- EMA 9 / 21 / 50 alignment
- Intraday % move
- Relative volume
- Trend efficiency
- Chop penalty
- Premarket / session gap %
- News flag
- Ready-now status
"""
)

if run_scan:
    with st.spinner("Scanning symbols..."):
        all_df, call_df, put_df, avoid_df, ranking_df, top_pick = run_stock_scanner(symbols)

    st.markdown("## Dashboard")

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("Symbols Scanned", len(all_df))

    with m2:
        st.metric("Best Calls", len(call_df))

    with m3:
        st.metric("Best Puts", len(put_df))

    with m4:
        ready_count = int((all_df["ready_now"] == "YES").sum()) if not all_df.empty else 0
        st.metric("Ready Now", ready_count)

    st.markdown("## Top Pick of the Day")

    if top_pick is not None:
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric("Symbol", top_pick["symbol"])

        with c2:
            st.metric("Bias", top_pick["signal_bias"])

        with c3:
            st.metric("Bull Score", f'{top_pick["bull_score"]:.2f}')

        with c4:
            st.metric("Bear Score", f'{top_pick["bear_score"]:.2f}')

        st.success(
            f"Top setup: {top_pick['symbol']} | "
            f"Ready Now: {top_pick['ready_now']} | "
            f"Gap %: {top_pick['gap_pct']} | "
            f"News: {top_pick['news_flag']}"
        )
    else:
        st.warning("No valid top pick found.")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### Best Call Candidates")
        st.dataframe(call_df, use_container_width=True)

    with c2:
        st.markdown("### Best Put Candidates")
        st.dataframe(put_df, use_container_width=True)

    with c3:
        st.markdown("### Choppy / Avoid")
        st.dataframe(avoid_df, use_container_width=True)

    st.markdown("### Full Ranking")
    st.dataframe(ranking_df, use_container_width=True)

    st.markdown("### How to use it")
    st.info(
        "Focus on symbols with high score, clean bias, and READY NOW = YES. "
        "Then wait for your actual algo entry signal before taking the trade."
    )

else:
    st.info("Enter your watchlist in the sidebar, then click Run Scanner.")
