import pandas as pd


def clean_data(df):

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    numeric_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df["Symbol"] = (
        df["Symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df = df.dropna(
        subset=[
            "Symbol",
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]
    )

    # Giá và volume hợp lệ
    df = df[
        (df["Open"] > 0)
        &
        (df["High"] > 0)
        &
        (df["Low"] > 0)
        &
        (df["Close"] > 0)
        &
        (df["Volume"] >= 0)
    ]

    # Quan hệ OHLC hợp lệ
    df = df[
        (df["High"] >= df["Low"])
        &
        (df["High"] >= df["Open"])
        &
        (df["High"] >= df["Close"])
        &
        (df["Low"] <= df["Open"])
        &
        (df["Low"] <= df["Close"])
    ]

    # Loại trùng
    df = df.drop_duplicates(
        subset=["Symbol", "Date"]
    )

    # GTGD
    df["GTGD"] = (
        df["Close"]
        *
        df["Volume"]
    )

    df = (
        df.sort_values(
            ["Symbol", "Date"]
        )
        .reset_index(drop=True)
    )

    return df


def check_data_sufficiency(df):

    if df is None or df.empty:
        return False

    counts = (
        df.groupby("Symbol")
        .size()
    )

    return counts >= 260