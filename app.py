import pandas as pd
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
    '''
### What this app does
This scanner ranks symbols using:
- VWAP position
- EMA 9 / 21 / 50 alignment
- Intraday % move
- Relative volume
- Trend efficiency
- Chop penalty
'''
)

if run_scan:
    with st.spinner("Scanning symbols..."):
        all_df, call_df, put_df, avoid_df = run_stock_scanner(symbols)

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
    ranking_df = all_df.copy()
    if not ranking_df.empty:
        ranking_df["max_score"] = ranking_df[["bull_score", "bear_score"]].max(axis=1)
        ranking_df = ranking_df.sort_values(by="max_score", ascending=False).drop(columns=["max_score"])
    st.dataframe(ranking_df, use_container_width=True)

    if not all_df.empty:
        st.markdown("### Top Setup")
        top_row = ranking_df.iloc[0]
        st.success(
            f"{top_row['symbol']} | Bias: {top_row['signal_bias']} | "
            f"Bull Score: {top_row['bull_score']} | Bear Score: {top_row['bear_score']}"
        )
else:
    st.info("Enter your watchlist in the sidebar, then click **Run Scanner**.")
