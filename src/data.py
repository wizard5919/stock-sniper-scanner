import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=120)
def fetch_intraday_data(symbol: str, period: str = "1d", interval: str = "5m") -> pd.DataFrame:
    try:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )

        if df is None or df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df.dropna().copy()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=600)
def fetch_prev_close(symbol: str) -> float | None:
    try:
        df = yf.download(
            symbol,
            period="5d",
            interval="1d",
            auto_adjust=True,
            progress=False,
        )

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna()

        if len(df) < 2:
            return None

        return float(df["Close"].iloc[-2])
    except Exception:
        return None


@st.cache_data(ttl=600)
def fetch_news_flag(symbol: str) -> str:
    try:
        ticker = yf.Ticker(symbol)
        news_items = getattr(ticker, "news", None)

        if news_items and len(news_items) > 0:
            return "YES"
        return "NO"
    except Exception:
        return "NO"
