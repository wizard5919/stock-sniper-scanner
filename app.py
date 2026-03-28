import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.config import DEFAULT_WATCHLIST, APP_TITLE
from src.scanner import run_stock_scanner

st.set_page_config(page_title=APP_TITLE, layout="wide")

# Auto refresh
st_autorefresh(interval=3000, key="sniper_refresh")

st.title(APP_TITLE)
st.caption("🚀 Sniper Mode: Catch momentum BEFORE it explodes")

# ===============================
# STATE
# ===============================
if "run_scan" not in st.session_state:
    st.session_state.run_scan = False

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.header("Scanner Settings")

    custom_symbols = st.text_area(
        "Symbols to scan (comma-separated)",
        value=",".join(DEFAULT_WATCHLIST),
        height=120,
    )

    symbols = [s.strip().upper() for s in custom_symbols.split(",") if s.strip()]

    if st.button("Run Scanner"):
        st.session_state.run_scan = True

    if st.button("Stop Scanner"):
        st.session_state.run_scan = False

# ===============================
# RUN SCANNER
# ===============================
if st.session_state.run_scan:

    all_df, call_df, put_df, avoid_df, ranking_df, top_pick = run_stock_scanner(symbols)

    st.markdown("## 🚨 SNIPER MODE")

    sniper_df = ranking_df[
        (ranking_df["momentum_spike"] == "YES") |
        (ranking_df["trigger_now"] != "NO")
    ]

    st.dataframe(sniper_df, use_container_width=True)

    # Alerts
    alerts = sniper_df[sniper_df["trigger_now"] != "NO"]

    if not alerts.empty:
        top_alert = alerts.iloc[0]

        if top_alert["trigger_now"] == "CALL":
            st.success(f"🚀 CALL ALERT: {top_alert['symbol']}")
        elif top_alert["trigger_now"] == "PUT":
            st.error(f"🔻 PUT ALERT: {top_alert['symbol']}")

    st.markdown("## Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric("Calls", len(call_df))
    col2.metric("Puts", len(put_df))
    col3.metric("Symbols", len(all_df))

    st.markdown("### Full Ranking")
    st.dataframe(ranking_df, use_container_width=True)

else:
    st.info("Click Run Scanner to start.")
