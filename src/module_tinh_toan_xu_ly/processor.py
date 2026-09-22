import pandas as pd

from src.module_thu_thap_du_lieu.cleaner import clean_data
from src.module_tinh_toan_xu_ly.indicators import calculate_indicators
from src.module_tinh_toan_xu_ly.rs import calculate_relative_strength
from src.module_bot.smartscore import add_smartscore


def process_universe(df):

    if df is None or df.empty:
        return pd.DataFrame()

    # =========================
    # 1. CLEAN DATA
    # =========================

    df = clean_data(df)

    if df.empty:
        return df

    # =========================
    # 2. INDICATORS
    # =========================

    df = calculate_indicators(df)

    # =========================
    # 3. LIQUIDITY
    # =========================

    df["Liquidity_ok"] = (
        (df["MedianGTGD20"] >= 10_000_000_000)
        & (df["SMA20Volume"] >= 100_000)
        & (df["Close"] >= 5_000)
    )

    # =========================
    # 4. RELATIVE STRENGTH
    # =========================

    df = calculate_relative_strength(df)

    # =========================
    # 5. ATR / TECHNICAL
    # =========================

    df["ATR14_Ratio"] = (
        df["ATR14"]
        / df["Close"].replace(0, pd.NA)
    )

    df["Technical_ok"] = (
        (df["ADX14"] >= 20)
        & (df["ATR14_Ratio"] <= 0.05)
    )

    # =========================
    # 6. TREND
    # =========================

    df["EMA_ok"] = (
        df["EMA20"] > df["EMA50"]
    )

    df["SMA200_ok"] = (
        df["Close"] > df["SMA200"]
    )

    df["Layer2_ok"] = (
        df["EMA_ok"]
        & df["SMA200_ok"]
    )

    # =========================
    # 7. DONCHIAN
    # =========================

    df["PreviousHigh20"] = (
        df.groupby("Symbol")["High"]
        .transform(
            lambda x:
            x.shift(1).rolling(20).max()
        )
    )

    df["Donchian_ok"] = (
        df["Close"]
        > df["PreviousHigh20"]
    )

    # =========================
    # 8. VOLUME BREAKOUT
    # =========================

    df["PreviousSMA20Volume"] = (
        df.groupby("Symbol")["Volume"]
        .transform(
            lambda x:
            x.shift(1).rolling(20).mean()
        )
    )

    df["VolumeBreakout_ok"] = (
        df["Volume"]
        >= 1.5 * df["PreviousSMA20Volume"]
    )

    # =========================
    # 9. CLV
    # =========================

    price_range = (
        df["High"] - df["Low"]
    )

    df["CLV"] = (
        (df["Close"] - df["Low"])
        / price_range.replace(0, pd.NA)
    )

    df["CLV_ok"] = (
        df["CLV"] >= 0.6
    )

    # =========================
    # 10. ANTI-CHASING
    # =========================

    df["AntiChasing"] = (
        (df["Close"] - df["EMA20"])
        / df["ATR14"].replace(0, pd.NA)
    )

    df["AntiChasing_ok"] = (
        df["AntiChasing"] <= 3
    )

    # =========================
    # 11. CHANDELIER STOP
    # =========================
    #
    # Chandelier được tính để sử dụng
    # trong quản lý vị thế/backtest.
    #
    # Không dùng trực tiếp để tạo tín hiệu
    # BÁN trong process_universe vì bot là
    # chiến lược long-only.
    # =========================

    df["HighestHigh22"] = (
        df.groupby("Symbol")["High"]
        .transform(
            lambda x:
            x.rolling(22).max()
        )
    )

    df["Chandelier"] = (
        df["HighestHigh22"]
        - 3 * df["ATR22"]
    )

    df["ChandelierStop"] = (
        df.groupby("Symbol")["Chandelier"]
        .cummax()
    )

    df["Chandelier_sell"] = (
        df["Close"]
        < df["ChandelierStop"]
    )

    # =========================
    # 12. TREND SCORE
    # =========================

    df["TrendScore"] = (
        df["ADX14"].ge(20).astype(int)
        + df["PriceNearHigh_ok"]
            .fillna(False)
            .astype(int)
        + df["Donchian_ok"]
            .fillna(False)
            .astype(int)
    )

    # =========================
    # 13. VOLUME SCORE
    # =========================

    df["VolumeScore"] = (
        df["VolumeBreakout_ok"]
            .fillna(False)
            .astype(int)
        + df["CLV_ok"]
            .fillna(False)
            .astype(int)
    )

    # =========================
    # 14. BUY
    # =========================
    #
    # Điều kiện:
    # - Thanh khoản đạt
    # - RS >= 60
    # - EMA20 > EMA50
    # - Close > SMA200
    # - Không chase giá
    # =========================

    df["BUY"] = (
        df["Liquidity_ok"]
        & (df["RS"] >= 60)
        & df["EMA_ok"]
        & df["SMA200_ok"]
        & df["AntiChasing_ok"]
    )

    # =========================
    # 15. SELL
    # =========================
    #
    # Chỉ BÁN khi:
    # - Giá đóng cửa dưới SMA200
    # HOẶC
    # - RS < 50
    #
    # Chandelier KHÔNG dùng để tạo SELL
    # toàn thị trường.
    # =========================

    df["SELL"] = (
        (df["Close"] < df["SMA200"])
        | (df["RS"] < 50)
    )

    # =========================
    # 16. SIGNAL
    # =========================

    df["Signal"] = "GIỮ"

    # MUA trước
    df.loc[
        df["BUY"],
        "Signal"
    ] = "MUA"

    # BÁN có ưu tiên cao nhất
    df.loc[
        df["SELL"],
        "Signal"
    ] = "BÁN"

    # =========================
    # 17. DATA SUFFICIENT
    # =========================

    data_count = (
        df.groupby("Symbol")["Date"]
        .transform("count")
    )

    df["DataSufficient"] = (
        data_count >= 260
    )

    df.loc[
        ~df["DataSufficient"],
        "Signal"
    ] = "THIẾU DỮ LIỆU"

    # =========================
    # 18. SMARTSCORE
    # =========================
    #
    # SmartScore là điểm đánh giá riêng,
    # không thay đổi BUY / SELL / Signal.
    # =========================

    df = add_smartscore(df)

    return df


def process_stock(df):

    if df is None or df.empty:

        return {
            "status": "NO_DATA",
            "signal": None
        }

    symbol = (
        df["Symbol"]
        .iloc[0]
        .upper()
    )

    result = process_universe(df)

    if result.empty:

        return {
            "status": "NO_DATA",
            "signal": None
        }

    latest = (
        result
        .sort_values("Date")
        .iloc[-1]
    )

    if not latest["DataSufficient"]:

        return {
            "status": "INSUFFICIENT_DATA",
            "signal": "THIẾU DỮ LIỆU",
            "symbol": symbol
        }

    return {
        "status": "OK",
        "signal": latest["Signal"],
        "symbol": symbol,
        "close": latest["Close"],
        "rs": latest["RS"],
        "smartscore": latest["SmartScore"],
        "reason": build_reason(latest)
    }


def build_reason(row):

    if row["Signal"] == "BÁN":

        reasons = []

        if (
            pd.notna(row["SMA200"])
            and row["Close"] < row["SMA200"]
        ):

            reasons.append(
                "Giá đóng cửa dưới SMA200"
            )

        if (
            pd.notna(row["RS"])
            and row["RS"] < 50
        ):

            reasons.append(
                "RS dưới 50"
            )

        if not reasons:

            reasons.append(
                "Xuất hiện tín hiệu BÁN"
            )

        return "; ".join(reasons)

    if row["Signal"] == "MUA":

        return (
            "Thanh khoản đạt yêu cầu, "
            "RS tích cực, xu hướng tăng "
            "và giá không quá xa EMA20."
        )

    return (
        "Chưa đủ điều kiện MUA "
        "và chưa xuất hiện tín hiệu BÁN."
    )