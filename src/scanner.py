import numpy as np
import pandas as pd

from src.config import DEFAULT_WATCHLIST
from src.data import fetch_intraday_data, fetch_news_flag, fetch_prev_close
from src.indicators import add_indicators


def score_symbol(df: pd.DataFrame, prev_close: float | None, news_flag: str) -> dict:
    default_response = {
        "bull_score": 0.0,
        "bear_score": 0.0,
        "signal_bias": "No Data",
        "last_price": np.nan,
        "pct_change": np.nan,
        "gap_pct": np.nan,
        "rel_volume": np.nan,
        "trend_efficiency": np.nan,
        "news_flag": news_flag,
        "ready_now": "NO",
        "trend_side": "None",
    }

    if df is None or len(df) < 60:
        return default_response

    df = add_indicators(df).dropna()
    if df.empty:
        return default_response

    row = df.iloc[-1]
    session_open = float(df.iloc[0]["Open"])
    last_price = float(row["Close"])

    pct_change = ((last_price / session_open) - 1.0) * 100.0 if session_open else np.nan
    gap_pct = ((session_open / prev_close) - 1.0) * 100.0 if prev_close and prev_close != 0 else np.nan

    bull_score = 0.0
    bear_score = 0.0

    above_vwap = row["Close"] > row["VWAP"]
    below_vwap = row["Close"] < row["VWAP"]

    bull_aligned = row["EMA_9"] > row["EMA_21"] > row["EMA_50"]
    bear_aligned = row["EMA_9"] < row["EMA_21"] < row["EMA_50"]

    if above_vwap:
        bull_score += 25
    elif below_vwap:
        bear_score += 25

    if bull_aligned:
        bull_score += 25
    elif bear_aligned:
        bear_score += 25

    if pd.notna(pct_change):
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

    # New: detect short-term bearish structure shift
    if len(df) >= 5:
        last_3_lower_highs = (
            df["High"].iloc[-1] < df["High"].iloc[-2] < df["High"].iloc[-3]
        )

        last_3_lower_lows = (
            df["Low"].iloc[-1] < df["Low"].iloc[-2] < df["Low"].iloc[-3]
        )

        if last_3_lower_highs and last_3_lower_lows:
            bull_score -= 30
            bear_score += 20

    if news_flag == "YES":
        bull_score += 5
        bear_score += 5

    if bull_score >= 60 and bull_score > bear_score:
        bias = "Best Call Candidate"
        trend_side = "Bullish"
    elif bear_score >= 60 and bear_score > bull_score:
        bias = "Best Put Candidate"
        trend_side = "Bearish"
    else:
        bias = "Choppy / Avoid"
        trend_side = "Choppy"

    ready_now = "NO"

    if bias == "Best Call Candidate":
        if (
            above_vwap
            and bull_aligned
            and pd.notna(rv) and rv >= 1.2
            and pd.notna(te) and te >= 0.45
            and pd.notna(pct_change) and pct_change > 0
        ):
            ready_now = "YES"

    elif bias == "Best Put Candidate":
        if (
            below_vwap
            and bear_aligned
            and pd.notna(rv) and rv >= 1.2
            and pd.notna(te) and te >= 0.45
            and pd.notna(pct_change) and pct_change < 0
        ):
            ready_now = "YES"

    return {
        "bull_score": round(float(bull_score), 2),
        "bear_score": round(float(bear_score), 2),
        "signal_bias": bias,
        "last_price": round(last_price, 2),
        "pct_change": round(float(pct_change), 2) if pd.notna(pct_change) else np.nan,
        "gap_pct": round(float(gap_pct), 2) if pd.notna(gap_pct) else np.nan,
        "rel_volume": round(float(rv), 2) if pd.notna(rv) else np.nan,
        "trend_efficiency": round(float(te), 2) if pd.notna(te) else np.nan,
        "news_flag": news_flag,
        "ready_now": ready_now,
        "trend_side": trend_side,
    }


def run_stock_scanner(symbols=None):
    if symbols is None:
        symbols = DEFAULT_WATCHLIST

    results = []

    for symbol in symbols:
        df = fetch_intraday_data(symbol)
        prev_close = fetch_prev_close(symbol)
        news_flag = fetch_news_flag(symbol)

        scored = score_symbol(df, prev_close=prev_close, news_flag=news_flag)
        scored["symbol"] = symbol
        results.append(scored)

    result_df = pd.DataFrame(results)

    if result_df.empty:
        return result_df, result_df, result_df, result_df, result_df, None

    ordered_cols = [
        "symbol",
        "signal_bias",
        "ready_now",
        "trend_side",
        "bull_score",
        "bear_score",
        "last_price",
        "pct_change",
        "gap_pct",
        "rel_volume",
        "trend_efficiency",
        "news_flag",
    ]

    result_df = result_df[ordered_cols]

    call_df = result_df[result_df["signal_bias"] == "Best Call Candidate"].copy()
    call_df = call_df.sort_values(by=["ready_now", "bull_score"], ascending=[False, False])

    put_df = result_df[result_df["signal_bias"] == "Best Put Candidate"].copy()
    put_df = put_df.sort_values(by=["ready_now", "bear_score"], ascending=[False, False])

    avoid_df = result_df[result_df["signal_bias"] == "Choppy / Avoid"].copy()
    avoid_df = avoid_df.sort_values(by=["bull_score", "bear_score"], ascending=False)

    ranking_df = result_df.copy()
    ranking_df["primary_score"] = ranking_df[["bull_score", "bear_score"]].max(axis=1)
    ranking_df = ranking_df.sort_values(
        by=["ready_now", "primary_score", "trend_efficiency", "rel_volume"],
        ascending=[False, False, False, False],
    ).drop(columns=["primary_score"])

    top_pick = ranking_df.iloc[0].to_dict() if not ranking_df.empty else None

    return result_df, call_df, put_df, avoid_df, ranking_df, top_pick
