import numpy as np
import pandas as pd
from ta.trend import EMAIndicator


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    cum_vol = df["Volume"].cumsum()
    cum_tpv = (typical_price * df["Volume"]).cumsum()
    return cum_tpv / cum_vol.replace(0, np.nan)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["EMA_9"] = EMAIndicator(close=df["Close"], window=9).ema_indicator()
    df["EMA_21"] = EMAIndicator(close=df["Close"], window=21).ema_indicator()
    df["EMA_50"] = EMAIndicator(close=df["Close"], window=50).ema_indicator()
    df["VWAP"] = calculate_vwap(df)

    df["ret_1"] = df["Close"].pct_change()
    df["bar_range"] = df["High"] - df["Low"]
    df["body"] = (df["Close"] - df["Open"]).abs()

    avg_vol = df["Volume"].rolling(20).mean()
    df["rel_volume"] = df["Volume"] / avg_vol.replace(0, np.nan)

    net_move = (df["Close"] - df["Close"].shift(10)).abs()
    total_move = df["Close"].diff().abs().rolling(10).sum()
    df["trend_efficiency"] = net_move / total_move.replace(0, np.nan)

    return df
