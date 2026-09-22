import pandas as pd


def calculate_relative_strength(df):

    df = df.copy()

    df = df.sort_values(
        ["Symbol", "Date"]
    ).reset_index(drop=True)

    grouped = df.groupby("Symbol")

    # =====================================
    # RETURNS
    # =====================================

    df["R63"] = (
        grouped["Close"].shift(5)
        / grouped["Close"].shift(68)
        - 1
    )

    df["R126"] = (
        grouped["Close"].shift(5)
        / grouped["Close"].shift(131)
        - 1
    )

    df["R252"] = (
        grouped["Close"].shift(5)
        / grouped["Close"].shift(257)
        - 1
    )

    # =====================================
    # XẾP HẠNG THEO NGÀY
    # =====================================

    df["PR63"] = pd.NA
    df["PR126"] = pd.NA
    df["PR252"] = pd.NA

    # Chỉ những mã có thanh khoản đạt yêu cầu
    eligible = df["Liquidity_ok"]

    for date, group in df.loc[eligible].groupby("Date"):

        # -----------------------------
        # R63
        # -----------------------------

        valid = group["R63"].notna()

        if valid.any():

            ranks = (
                group.loc[valid, "R63"]
                .rank(pct=True)
                * 100
            )

            df.loc[
                ranks.index,
                "PR63"
            ] = ranks

        # -----------------------------
        # R126
        # -----------------------------

        valid = group["R126"].notna()

        if valid.any():

            ranks = (
                group.loc[valid, "R126"]
                .rank(pct=True)
                * 100
            )

            df.loc[
                ranks.index,
                "PR126"
            ] = ranks

        # -----------------------------
        # R252
        # -----------------------------

        valid = group["R252"].notna()

        if valid.any():

            ranks = (
                group.loc[valid, "R252"]
                .rank(pct=True)
                * 100
            )

            df.loc[
                ranks.index,
                "PR252"
            ] = ranks

    # =====================================
    # RS
    # =====================================

    df["PR63"] = pd.to_numeric(
        df["PR63"],
        errors="coerce"
    )

    df["PR126"] = pd.to_numeric(
        df["PR126"],
        errors="coerce"
    )

    df["PR252"] = pd.to_numeric(
        df["PR252"],
        errors="coerce"
    )

    df["RS"] = (
        df["PR63"]
        + df["PR126"]
        + df["PR252"]
    ) / 3

    # =====================================
    # RS >= 60
    # =====================================

    df["RS_ok"] = (
        df["RS"] >= 60
    )

    # =====================================
    # GIÁ GẦN ĐỈNH 252 PHIÊN
    # =====================================

    df["PriceNearHigh_ok"] = (
        df["Close"]
        >= 0.85 * df["HighestHigh252"]
    )

    df["Layer1_ok"] = (
        df["RS_ok"]
        & df["PriceNearHigh_ok"]
    )

    return df