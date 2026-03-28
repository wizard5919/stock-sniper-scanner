import numpy as np
import pandas as pd

from src.config import DEFAULT_WATCHLIST
from src.data import fetch_intraday_data
from src.indicators import add_indicators


def score_symbol(df: pd.DataFrame) -> dict:
    if df is None or len(df) < 60:
        return {
            "bull_score": 0,
            "bear_score": 0,
            "signal_bias": "No Data",
            "last_price": np.nan,
            "pct_change": np.nan,
            "rel_volume": np.nan,
            "trend_efficiency": np.nan,
        }

    df = add_indicators(df).dropna()
    if df.empty:
        return {
            "bull_score": 0,
            "bear_score": 0,
            "signal_bias": "No Data",
            "last_price": np.nan,
            "pct_change": np.nan,
            "rel_volume": np.nan,
            "trend_efficiency": np.nan,
        }

    row = df.iloc[-1]
    session_open = df.iloc[0]["Open"]
    pct_change = ((row["Close"] / session_open) - 1.0) * 100.0

    bull_score = 0.0
    bear_score = 0.0

    if row["Close"] > row["VWAP"]:
        bull_score += 25
    elif row["Close"] < row["VWAP"]:
        bear_score += 25

    if row["EMA_9"] > row["EMA_21"] > row["EMA_50"]:
        bull_score += 25
    elif row["EMA_9"] < row["EMA_21"] < row["EMA_50"]:
        bear_score += 25

    if pct_change > 1.5:
        bull_score += min(20, pct_change * 4)
    elif pct_change < -1.5:
        bear_score += min(20, abs(pct_change) * 4)

    rv = row["rel_volume"]
    if pd.notna(rv):
        vol_points = min(20, max(0, (rv - 1.0) * 10))
        bull_score += vol_points
        bear_score += vol_points

    te = row["trend_efficiency"]
    if pd.notna(te):
        trend_points = min(15, te * 20)
        bull_score += trend_points
        bear_score += trend_points

        if te < 0.35:
            bull_score -= 15
            bear_score -= 15

    if bull_score >= 60 and bull_score > bear_score:
        bias = "Best Call Candidate"
    elif bear_score >= 60 and bear_score > bull_score:
        bias = "Best Put Candidate"
    else:
        bias = "Choppy / Avoid"

    return {
        "bull_score": round(float(bull_score), 2),
        "bear_score": round(float(bear_score), 2),
        "signal_bias": bias,
        "last_price": round(float(row["Close"]), 2),
        "pct_change": round(float(pct_change), 2),
        "rel_volume": round(float(rv), 2) if pd.notna(rv) else np.nan,
        "trend_efficiency": round(float(te), 2) if pd.notna(te) else np.nan,
    }


def run_stock_scanner(symbols=None):
    if symbols is None:
        symbols = DEFAULT_WATCHLIST

    results = []

    for symbol in symbols:
        df = fetch_intraday_data(symbol)
        scored = score_symbol(df)
        scored["symbol"] = symbol
        results.append(scored)

    result_df = pd.DataFrame(results)

    if result_df.empty:
        return result_df, result_df, result_df, result_df

    call_df = result_df[result_df["signal_bias"] == "Best Call Candidate"].sort_values(
        by="bull_score", ascending=False
    )
    put_df = result_df[result_df["signal_bias"] == "Best Put Candidate"].sort_values(
        by="bear_score", ascending=False
    )
    avoid_df = result_df[result_df["signal_bias"] == "Choppy / Avoid"].sort_values(
        by=["bull_score", "bear_score"], ascending=False
    )

    result_df = result_df[
        [
            "symbol",
            "signal_bias",
            "bull_score",
            "bear_score",
            "last_price",
            "pct_change",
            "rel_volume",
            "trend_efficiency",
        ]
    ]

    return result_df, call_df, put_df, avoid_df
