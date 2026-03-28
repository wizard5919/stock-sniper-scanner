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

        df = df.dropna().copy()
        return df
    except Exception:
        return pd.DataFrame()
