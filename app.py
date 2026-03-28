import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.config import DEFAULT_WATCHLIST, APP_TITLE
from src.scanner import run_stock_scanner

st.set_page_config(page_title=APP_TITLE, layout="wide")

# 🔥 AUTO REFRESH (REAL-TIME)
st_autorefresh(interval=3000, key="sniper_refresh")

st.title(APP_TITLE)
st.caption("🚀 Sniper Mode: Catch momentum BEFORE it explodes")

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
    run_scan = st.button("Run Scanner", use_container_width=True)

# ===============================
# RUN SCANNER
# ===============================
if run_scan:
    with st.spinner("Scanning symbols..."):
        all_df, call_df, put_df, avoid_df, ranking_df, top_pick = run_stock_scanner(symbols)

    # ===============================
    # 🚨 SNIPER MODE (NEW SECTION)
    # ===============================
    st.markdown("## 🚨 SNIPER MODE (REAL-TIME)")

    sniper_df = ranking_df[
        (ranking_df["momentum_spike"] == "YES") |
        (ranking_df["trigger_now"] != "NO")
    ]

    st.dataframe(sniper_df, use_container_width=True)

    # 🔥 ALERT SYSTEM
    alerts = sniper_df[sniper_df["trigger_now"] != "NO"]

    if not alerts.empty:
        top_alert = alerts.iloc[0]

        if top_alert["trigger_now"] == "CALL":
            st.success(f"🚀 CALL ALERT: {top_alert['symbol']}")

        elif top_alert["trigger_now"] == "PUT":
            st.error(f"🔻 PUT ALERT: {top_alert['symbol']}")

    # ===============================
    # DASHBOARD
    # ===============================
    st.markdown("## Dashboard")

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("Symbols", len(all_df))

    with m2:
        st.metric("Calls", len(call_df))

    with m3:
        st.metric("Puts", len(put_df))

    with m4:
        ready_count = int((all_df["ready_now"] == "YES").sum()) if not all_df.empty else 0
        st.metric("Ready", ready_count)

    # ===============================
    # TOP PICK
    # ===============================
    st.markdown("## Top Pick")

    if top_pick is not None:
        st.success(
            f"{top_pick['symbol']} | {top_pick['signal_bias']} | "
            f"Trigger: {top_pick['trigger_now']} | "
            f"Momentum: {top_pick['momentum_spike']}"
        )

    # ===============================
    # TABLES
    # ===============================
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### Calls")
        st.dataframe(call_df, use_container_width=True)

    with c2:
        st.markdown("### Puts")
        st.dataframe(put_df, use_container_width=True)

    with c3:
        st.markdown("### Avoid")
        st.dataframe(avoid_df, use_container_width=True)

    # ===============================
    # FULL RANKING
    # ===============================
    st.markdown("### Full Ranking")
    st.dataframe(ranking_df, use_container_width=True)

    # ===============================
    # GUIDE
    # ===============================
    st.info(
        "ONLY trade when Trigger = CALL or PUT.\n"
        "Ignore everything else.\n"
        "Confirm on chart → enter → exit on your rule."
    )

else:
    st.info("Click Run Scanner to activate Sniper Mode.")
