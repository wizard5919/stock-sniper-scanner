import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.config import DEFAULT_WATCHLIST, APP_TITLE
from src.scanner import run_stock_scanner

st.set_page_config(page_title=APP_TITLE, layout="wide")

# 🔄 AUTO REFRESH
st_autorefresh(interval=3000, key="sniper_refresh")

# ===============================
# STATE
# ===============================
if "run_scan" not in st.session_state:
    st.session_state.run_scan = False

# ===============================
# STYLING (FLASH + MOBILE)
# ===============================
st.markdown("""
<style>

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

.title {
    font-size: 2.2rem;
    font-weight: 800;
    color: white;
}

.subtitle {
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 1rem;
}

.alert-call {
    animation: pulseGreen 1s infinite;
    background: #065f46;
    color: #ecfdf5;
    padding: 12px;
    border-radius: 12px;
    font-weight: bold;
}

.alert-put {
    animation: pulseRed 1s infinite;
    background: #7f1d1d;
    color: #fee2e2;
    padding: 12px;
    border-radius: 12px;
    font-weight: bold;
}

@keyframes pulseGreen {
    0% {opacity: 1;}
    50% {opacity: 0.6;}
    100% {opacity: 1;}
}

@keyframes pulseRed {
    0% {opacity: 1;}
    50% {opacity: 0.6;}
    100% {opacity: 1;}
}

.badge {
    padding: 4px 10px;
    border-radius: 10px;
    font-size: 0.8rem;
    font-weight: bold;
}

.call-badge {
    background: #10b981;
    color: white;
}

.put-badge {
    background: #ef4444;
    color: white;
}

.ready-badge {
    background: #3b82f6;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# ===============================
# HEADER
# ===============================
st.markdown(f'<div class="title">{APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">🚀 Sniper Elite Mode — ultra fast momentum detection</div>', unsafe_allow_html=True)

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.header("Scanner")

    custom_symbols = st.text_area(
        "Symbols",
        value=",".join(DEFAULT_WATCHLIST),
        height=100,
    )

    symbols = [s.strip().upper() for s in custom_symbols.split(",") if s.strip()]

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶ Run", use_container_width=True):
            st.session_state.run_scan = True

    with col2:
        if st.button("⏹ Stop", use_container_width=True):
            st.session_state.run_scan = False

# ===============================
# WAIT STATE
# ===============================
if not st.session_state.run_scan:
    st.info("Press ▶ Run to start Sniper Mode")
    st.stop()

# ===============================
# RUN SCANNER
# ===============================
all_df, call_df, put_df, avoid_df, ranking_df, top_pick = run_stock_scanner(symbols)

# fallback safety
for col in ["momentum_spike", "trigger_now", "ready_now"]:
    if col not in ranking_df.columns:
        ranking_df[col] = "NO"

# ===============================
# SNIPER FILTER
# ===============================
sniper_df = ranking_df[
    (ranking_df["momentum_spike"] == "YES") |
    (ranking_df["trigger_now"] != "NO")
]

alerts = sniper_df[sniper_df["trigger_now"] != "NO"]

# ===============================
# 🚨 FLASH ALERT
# ===============================
if not alerts.empty:
    top = alerts.iloc[0]

    if top["trigger_now"] == "CALL":
        st.markdown(
            f'<div class="alert-call">🚀 CALL {top["symbol"]}</div>',
            unsafe_allow_html=True
        )
    elif top["trigger_now"] == "PUT":
        st.markdown(
            f'<div class="alert-put">🔻 PUT {top["symbol"]}</div>',
            unsafe_allow_html=True
        )

# ===============================
# TOP PICK
# ===============================
if top_pick:
    badge = ""

    if top_pick["trigger_now"] == "CALL":
        badge = '<span class="badge call-badge">CALL</span>'
    elif top_pick["trigger_now"] == "PUT":
        badge = '<span class="badge put-badge">PUT</span>'

    ready = '<span class="badge ready-badge">READY</span>' if top_pick["ready_now"] == "YES" else ""

    st.markdown(
        f"""
        **{top_pick['symbol']}** {badge} {ready}  
        Momentum: {top_pick['momentum_spike']}
        """,
        unsafe_allow_html=True
    )

# ===============================
# METRICS (COMPACT)
# ===============================
c1, c2, c3 = st.columns(3)

c1.metric("Calls", len(call_df))
c2.metric("Puts", len(put_df))
c3.metric("Spikes", int((all_df["momentum_spike"] == "YES").sum()))

# ===============================
# TABLES (MOBILE FRIENDLY)
# ===============================
st.markdown("### 🚨 Sniper Hits")
st.dataframe(sniper_df, use_container_width=True, height=250)

st.markdown("### 📊 Ranking")
st.dataframe(ranking_df, use_container_width=True, height=300)

# ===============================
# RULE
# ===============================
st.warning("ONLY trade when CALL or PUT appears. Ignore everything else.")
