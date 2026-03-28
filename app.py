import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.config import DEFAULT_WATCHLIST, APP_TITLE
from src.scanner import run_stock_scanner

st.set_page_config(page_title=APP_TITLE, layout="wide")

# ===============================
# AUTO REFRESH
# ===============================
st_autorefresh(interval=3000, key="sniper_refresh")

# ===============================
# SESSION STATE
# ===============================
if "run_scan" not in st.session_state:
    st.session_state.run_scan = False

# ===============================
# STYLING
# ===============================
st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(180deg, #050816 0%, #0a1020 100%);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    .elite-title {
        font-size: 3rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 0.3rem;
        letter-spacing: -0.03em;
    }

    .elite-subtitle {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 1.4rem;
    }

    .elite-card {
        background: rgba(15, 23, 42, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        margin-bottom: 1rem;
    }

    .elite-card h3 {
        margin: 0 0 0.35rem 0;
        color: #f8fafc;
        font-size: 1.05rem;
    }

    .elite-muted {
        color: #94a3b8;
        font-size: 0.95rem;
    }

    .alert-call {
        background: linear-gradient(135deg, rgba(6,95,70,0.95), rgba(16,185,129,0.22));
        border: 1px solid rgba(16,185,129,0.50);
        border-radius: 16px;
        padding: 0.95rem 1rem;
        color: #ecfdf5;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    .alert-put {
        background: linear-gradient(135deg, rgba(127,29,29,0.95), rgba(239,68,68,0.18));
        border: 1px solid rgba(239,68,68,0.50);
        border-radius: 16px;
        padding: 0.95rem 1rem;
        color: #fef2f2;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    .alert-neutral {
        background: linear-gradient(135deg, rgba(30,41,59,0.95), rgba(59,130,246,0.12));
        border: 1px solid rgba(96,165,250,0.35);
        border-radius: 16px;
        padding: 0.95rem 1rem;
        color: #e2e8f0;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 750;
        color: #f8fafc;
        margin-top: 0.25rem;
        margin-bottom: 0.8rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.16);
        padding: 0.8rem 0.9rem;
        border-radius: 16px;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
    }

    .small-gap {
        height: 0.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===============================
# HEADER
# ===============================
st.markdown(f'<div class="elite-title">{APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="elite-subtitle">🚀 Sniper Elite UI: fast momentum, cleaner signals, better focus</div>',
    unsafe_allow_html=True,
)

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

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Run Scanner", use_container_width=True):
            st.session_state.run_scan = True

    with col_b:
        if st.button("Stop Scanner", use_container_width=True):
            st.session_state.run_scan = False

    st.markdown("---")
    st.caption("Best for 5m / 15m momentum hunting.")

# ===============================
# HELP / STATUS
# ===============================
if not st.session_state.run_scan:
    st.markdown(
        """
        <div class="elite-card">
            <h3>Waiting for Scanner</h3>
            <div class="elite-muted">
                Click <b>Run Scanner</b> in the sidebar to activate Sniper Elite mode.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ===============================
# RUN SCANNER
# ===============================
with st.spinner("Scanning live momentum..."):
    all_df, call_df, put_df, avoid_df, ranking_df, top_pick = run_stock_scanner(symbols)

# Safety for missing columns
for col in ["momentum_spike", "trigger_now", "ready_now"]:
    if col not in ranking_df.columns:
        ranking_df[col] = "NO"

# ===============================
# SNIPER FILTER
# ===============================
sniper_df = ranking_df[
    (ranking_df["momentum_spike"] == "YES") |
    (ranking_df["trigger_now"] != "NO")
].copy()

# ===============================
# ALERT BAR
# ===============================
alerts = sniper_df[sniper_df["trigger_now"] != "NO"].copy()

if not alerts.empty:
    top_alert = alerts.iloc[0]
    if top_alert["trigger_now"] == "CALL":
        st.markdown(
            f'<div class="alert-call">🚀 CALL ALERT: {top_alert["symbol"]} | '
            f'Trigger: {top_alert["trigger_now"]} | Momentum Spike: {top_alert["momentum_spike"]}</div>',
            unsafe_allow_html=True,
        )
    elif top_alert["trigger_now"] == "PUT":
        st.markdown(
            f'<div class="alert-put">🔻 PUT ALERT: {top_alert["symbol"]} | '
            f'Trigger: {top_alert["trigger_now"]} | Momentum Spike: {top_alert["momentum_spike"]}</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        '<div class="alert-neutral">No live CALL/PUT trigger right now. Stay patient.</div>',
        unsafe_allow_html=True,
    )

# ===============================
# DASHBOARD METRICS
# ===============================
st.markdown('<div class="section-title">Dashboard</div>', unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("Symbols", len(all_df))

with m2:
    st.metric("Calls", len(call_df))

with m3:
    st.metric("Puts", len(put_df))

with m4:
    ready_count = int((all_df["ready_now"] == "YES").sum()) if not all_df.empty else 0
    st.metric("Ready", ready_count)

with m5:
    spike_count = int((all_df["momentum_spike"] == "YES").sum()) if not all_df.empty else 0
    st.metric("Spikes", spike_count)

st.markdown('<div class="small-gap"></div>', unsafe_allow_html=True)

# ===============================
# TOP PICK CARD
# ===============================
st.markdown('<div class="section-title">Top Pick</div>', unsafe_allow_html=True)

if top_pick is not None:
    st.markdown(
        f"""
        <div class="elite-card">
            <h3>{top_pick.get("symbol", "N/A")}</h3>
            <div class="elite-muted">
                Bias: <b>{top_pick.get("signal_bias", "N/A")}</b> |
                Trigger: <b>{top_pick.get("trigger_now", "NO")}</b> |
                Momentum: <b>{top_pick.get("momentum_spike", "NO")}</b> |
                Ready: <b>{top_pick.get("ready_now", "NO")}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="elite-card">
            <h3>No top pick</h3>
            <div class="elite-muted">No valid setup detected yet.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===============================
# SNIPER MODE TABLE
# ===============================
st.markdown('<div class="section-title">🚨 Sniper Mode</div>', unsafe_allow_html=True)
st.dataframe(sniper_df, use_container_width=True, height=260)

# ===============================
# TABLES
# ===============================
left, right = st.columns(2)

with left:
    st.markdown('<div class="section-title">Best Calls</div>', unsafe_allow_html=True)
    st.dataframe(call_df, use_container_width=True, height=260)

    st.markdown('<div class="section-title">Choppy / Avoid</div>', unsafe_allow_html=True)
    st.dataframe(avoid_df, use_container_width=True, height=260)

with right:
    st.markdown('<div class="section-title">Best Puts</div>', unsafe_allow_html=True)
    st.dataframe(put_df, use_container_width=True, height=260)

    st.markdown('<div class="section-title">Full Ranking</div>', unsafe_allow_html=True)
    st.dataframe(ranking_df, use_container_width=True, height=260)

# ===============================
# GUIDE
# ===============================
st.markdown('<div class="section-title">Execution Guide</div>', unsafe_allow_html=True)
st.info(
    "Trade only when Trigger = CALL or PUT. "
    "Use Sniper Mode first, confirm on your chart, then enter and exit by your rule."
)
