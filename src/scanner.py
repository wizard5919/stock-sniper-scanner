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
        "momentum_spike": "NO",
        "trigger_now": "NO",
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

    # 🔴 Bearish structure shift
    if len(df) >= 5:
        if (
            df["High"].iloc[-1] < df["High"].iloc[-2] < df["High"].iloc[-3]
            and df["Low"].iloc[-1] < df["Low"].iloc[-2] < df["Low"].iloc[-3]
        ):
            bull_score -= 30
            bear_score += 20

    # ===============================
    # 🚀 SNIPER MODE (NEW)
    # ===============================
    momentum_spike = "NO"
    trigger_now = "NO"

    if len(df) >= 6:
        recent_return = (df["Close"].iloc[-1] / df["Close"].iloc[-3] - 1) * 100
        volume_spike = row["rel_volume"] >= 1.5 if pd.notna(row["rel_volume"]) else False

        # 🔥 Momentum spike
        if abs(recent_return) > 0.4 and volume_spike:
            momentum_spike = "YES"

            if recent_return > 0:
                bull_score += 40
                bear_score -= 20
            else:
                bear_score += 40
                bull_score -= 20

        # 🔥 Acceleration
        move_now = df["Close"].iloc[-1] - df["Close"].iloc[-2]
        move_prev = df["Close"].iloc[-2] - df["Close"].iloc[-3]

        if move_now > move_prev > 0:
            bull_score += 15
        elif move_now < move_prev < 0:
            bear_score += 15

        # 🔥 Breakout
        recent_high = df["High"].iloc[-10:-1].max()
        recent_low = df["Low"].iloc[-10:-1].min()

        if row["Close"] > recent_high:
            bull_score += 30
        elif row["Close"] < recent_low:
            bear_score += 30

        # 🔥 Trigger
        if momentum_spike == "YES":
            if recent_return > 0 and above_vwap:
                trigger_now = "CALL"
            elif recent_return < 0 and below_vwap:
                trigger_now = "PUT"

    if news_flag == "YES":
        bull_score += 5
        bear_score += 5

    # 🔥 Bias AFTER sniper logic
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
        if above_vwap and bull_aligned and pd.notna(rv) and rv >= 1.2:
            ready_now = "YES"

    elif bias == "Best Put Candidate":
        if below_vwap and bear_aligned and pd.notna(rv) and rv >= 1.2:
            ready_now = "YES"

    return {
        "symbol": "",
        "trigger_now": trigger_now,
        "momentum_spike": momentum_spike,
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
        "trigger_now",
        "momentum_spike",
        "ready_now",
        "signal_bias",
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

    # 🔥 SNIPER PRIORITY SORT
    ranking_df = result_df.sort_values(
        by=["trigger_now", "momentum_spike", "rel_volume"],
        ascending=[False, False, False],
    )

    call_df = result_df[result_df["signal_bias"] == "Best Call Candidate"]
    put_df = result_df[result_df["signal_bias"] == "Best Put Candidate"]
    avoid_df = result_df[result_df["signal_bias"] == "Choppy / Avoid"]

    top_pick = ranking_df.iloc[0].to_dict() if not ranking_df.empty else None

    return result_df, call_df, put_df, avoid_df, ranking_df, top_pick
