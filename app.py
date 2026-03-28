import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.config import DEFAULT_WATCHLIST, APP_TITLE
from src.scanner import run_stock_scanner

st.set_page_config(page_title=APP_TITLE, layout="wide")
st_autorefresh(interval=3000, key="sniper_refresh")

if "run_scan" not in st.session_state:
    st.session_state.run_scan = False

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    .title {
        font-size: 2rem;
        font-weight: 800;
        color: white;
    }
    .subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }
    .call-alert {
        animation: pulseGreen 1s infinite;
        background: #065f46;
        color: #ecfdf5;
        padding: 12px;
        border-radius: 12px;
        font-weight: 700;
    }
    .put-alert {
        animation: pulseRed 1s infinite;
        background: #7f1d1d;
        color: #fee2e2;
        padding: 12px;
        border-radius: 12px;
        font-weight: 700;
    }
    .neutral-alert {
        background: #1e293b;
        color: #e2e8f0;
        padding: 12px;
        border-radius: 12px;
        font-weight: 600;
    }
    .badge {
        padding: 4px 10px;
        border-radius: 10px;
        font-size: 0.8rem;
        font-weight: 700;
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
    .grade-badge {
        background: #a855f7;
        color: white;
    }
    .news-badge {
        background: #f59e0b;
        color: white;
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
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(f'<div class="title">{APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">📰 Sniper Elite v4 News Catalyst Mode — promote fresh news with real momentum</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Scanner")

    custom_symbols = st.text_area(
        "Symbols",
        value=",".join(DEFAULT_WATCHLIST),
        height=100,
    )
    symbols = [s.strip().upper() for s in custom_symbols.split(",") if s.strip()]

    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶ Run", use_container_width=True):
            st.session_state.run_scan = True
    with c2:
        if st.button("⏹ Stop", use_container_width=True):
            st.session_state.run_scan = False

    st.caption("Fast 5m / 15m momentum + news catalyst bias.")

if not st.session_state.run_scan:
    st.info("Press ▶ Run to start Sniper Elite v4.")
    st.stop()

all_df, call_df, put_df, avoid_df, ranking_df, top_pick = run_stock_scanner(symbols)

required_cols = {
    "momentum_spike": "NO",
    "trigger_now": "NO",
    "ready_now": "NO",
    "setup_grade": "Avoid",
    "ai_score": 0.0,
    "fake_breakout": "NO",
    "news_catalyst": "NO",
}
for col, default in required_cols.items():
    if col not in ranking_df.columns:
        ranking_df[col] = default
    if col not in all_df.columns:
        all_df[col] = default

sniper_df = ranking_df[
    (ranking_df["trigger_now"] != "NO") |
    (ranking_df["setup_grade"].isin(["A+", "A"])) |
    (ranking_df["news_catalyst"] == "YES")
].copy()

alerts = sniper_df[sniper_df["trigger_now"] != "NO"]

if not alerts.empty:
    top = alerts.iloc[0]
    if top["trigger_now"] == "CALL":
        st.markdown(
            f'<div class="call-alert">🚀 CALL ALERT: {top["symbol"]} | Grade: {top["setup_grade"]} | AI Score: {top["ai_score"]} | News: {top["news_catalyst"]}</div>',
            unsafe_allow_html=True,
        )
    elif top["trigger_now"] == "PUT":
        st.markdown(
            f'<div class="put-alert">🔻 PUT ALERT: {top["symbol"]} | Grade: {top["setup_grade"]} | AI Score: {top["ai_score"]} | News: {top["news_catalyst"]}</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        '<div class="neutral-alert">No live CALL/PUT trigger right now. Stay patient.</div>',
        unsafe_allow_html=True,
    )

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("A+ / A Setups", int((all_df["setup_grade"].isin(["A+", "A"])).sum()) if not all_df.empty else 0)
m2.metric("Calls", len(call_df))
m3.metric("Puts", len(put_df))
m4.metric("News Catalysts", int((all_df["news_catalyst"] == "YES").sum()) if not all_df.empty else 0)
m5.metric("Fake Breakouts", int((all_df["fake_breakout"] == "YES").sum()) if not all_df.empty else 0)

st.markdown("### 🎯 Top Pick")
if top_pick is not None:
    badges = []

    if top_pick.get("trigger_now") == "CALL":
        badges.append('<span class="badge call-badge">🚀 CALL</span>')
    elif top_pick.get("trigger_now") == "PUT":
        badges.append('<span class="badge put-badge">🔻 PUT</span>')

    if top_pick.get("ready_now") == "YES":
        badges.append('<span class="badge ready-badge">READY</span>')

    badges.append(f'<span class="badge grade-badge">{top_pick.get("setup_grade", "Avoid")}</span>')

    if top_pick.get("news_catalyst") == "YES":
        badges.append('<span class="badge news-badge">📰 NEWS</span>')

    st.markdown(
        f"""
        **{top_pick.get("symbol", "N/A")}** {' '.join(badges)}  
        AI Score: **{top_pick.get("ai_score", 0.0)}**  
        Momentum Spike: **{top_pick.get("momentum_spike", "NO")}**  
        Fake Breakout: **{top_pick.get("fake_breakout", "NO")}**
        """,
        unsafe_allow_html=True,
    )

st.markdown("### 🚨 Sniper News Hits")
st.dataframe(sniper_df, use_container_width=True, height=260)

left, right = st.columns(2)
with left:
    st.markdown("### ✅ Best Calls")
    st.dataframe(call_df, use_container_width=True, height=240)

    st.markdown("### ⚠️ Avoid")
    st.dataframe(avoid_df, use_container_width=True, height=240)

with right:
    st.markdown("### 🔻 Best Puts")
    st.dataframe(put_df, use_container_width=True, height=240)

    st.markdown("### 📊 Full Ranking")
    st.dataframe(ranking_df, use_container_width=True, height=240)

st.warning("Only trade when Trigger = CALL or PUT. A+ / A setups with NEWS should get your attention first.")
