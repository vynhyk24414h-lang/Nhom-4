import pandas as pd


def rma(series, period):
    result = pd.Series(
        index=series.index,
        dtype="float64"
    )

    if len(series) < period:
        return result

    first_value = series.iloc[:period].mean()
    result.iloc[period - 1] = first_value

    for i in range(period, len(series)):
        result.iloc[i] = (
            (period - 1) * result.iloc[i - 1]
            + series.iloc[i]
        ) / period

    return result


def calculate_indicators(df):
    df = df.copy()
    df = df.sort_values(["Symbol", "Date"]).reset_index(drop=True)

    # =========================
    # MOVING AVERAGES
    # =========================

    df["EMA20"] = df.groupby("Symbol")["Close"].transform(
        lambda x: x.ewm(span=20, adjust=False).mean()
    )

    df["EMA50"] = df.groupby("Symbol")["Close"].transform(
        lambda x: x.ewm(span=50, adjust=False).mean()
    )

    df["SMA200"] = df.groupby("Symbol")["Close"].transform(
        lambda x: x.rolling(200).mean()
    )

    df["SMA20Volume"] = df.groupby("Symbol")["Volume"].transform(
        lambda x: x.rolling(20).mean()
    )

    # =========================
    # LIQUIDITY
    # =========================

    df["GTGD"] = df["Close"] * df["Volume"]

    df["MedianGTGD20"] = df.groupby("Symbol")["GTGD"].transform(
        lambda x: x.rolling(20).median()
    )

    # =========================
    # TRUE RANGE
    # =========================

    previous_close = df.groupby("Symbol")["Close"].shift(1)

    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - previous_close).abs()
    tr3 = (df["Low"] - previous_close).abs()

    df["TR"] = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    # =========================
    # ATR
    # =========================

    df["ATR14"] = df.groupby("Symbol")["TR"].transform(
        lambda x: rma(x, 14)
    )

    df["ATR22"] = df.groupby("Symbol")["TR"].transform(
        lambda x: rma(x, 22)
    )

    # =========================
    # DIRECTIONAL MOVEMENT
    # =========================

    previous_high = df.groupby("Symbol")["High"].shift(1)
    previous_low = df.groupby("Symbol")["Low"].shift(1)

    up_move = df["High"] - previous_high
    down_move = previous_low - df["Low"]

    df["+DM"] = 0.0
    df["-DM"] = 0.0

    df.loc[
        (up_move > down_move) & (up_move > 0),
        "+DM"
    ] = up_move

    df.loc[
        (down_move > up_move) & (down_move > 0),
        "-DM"
    ] = down_move

    # =========================
    # RMA DM
    # =========================

    plus_dm_rma = df.groupby("Symbol")["+DM"].transform(
        lambda x: rma(x, 14)
    )

    minus_dm_rma = df.groupby("Symbol")["-DM"].transform(
        lambda x: rma(x, 14)
    )

    # =========================
    # DI
    # =========================

    atr14_safe = df["ATR14"].replace(0, pd.NA)

    df["+DI14"] = (
        100 * plus_dm_rma / atr14_safe
    )

    df["-DI14"] = (
        100 * minus_dm_rma / atr14_safe
    )

    df["+DI14"] = df["+DI14"].fillna(0)
    df["-DI14"] = df["-DI14"].fillna(0)

    # =========================
    # DX
    # =========================

    di_sum = df["+DI14"] + df["-DI14"]
    di_diff = (
        df["+DI14"] - df["-DI14"]
    ).abs()

    df["DX"] = (
        100 * di_diff / di_sum.replace(0, pd.NA)
    )

    df["DX"] = df["DX"].fillna(0)

    # =========================
    # ADX
    # =========================

    df["ADX14"] = df.groupby("Symbol")["DX"].transform(
        lambda x: rma(x, 14)
    )

    # =========================
    # 252-DAY HIGH
    # =========================

    df["HighestHigh252"] = df.groupby("Symbol")["High"].transform(
        lambda x: x.rolling(252).max()
    )

    return df