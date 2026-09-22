import io

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

from src.module_thu_thap_du_lieu.market_data import get_stock_data


def create_candlestick_chart(symbol, periods=120):
    symbol = str(symbol).strip().upper()

    df = get_stock_data(symbol)

    if df is None or df.empty:
        raise ValueError(f"Không tìm thấy dữ liệu cho {symbol}.")

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

    df = df.dropna(
        subset=[
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]
    )

    df = df.sort_values("Date")
    df = df.drop_duplicates(subset=["Date"])

    if len(df) < 20:
        raise ValueError(
            f"{symbol} chưa có đủ dữ liệu để vẽ biểu đồ."
        )

    # =========================
    # TÍNH CÁC ĐƯỜNG CHỈ BÁO
    # =========================

    df["EMA20"] = (
        df["Close"]
        .ewm(span=20, adjust=False)
        .mean()
    )

    df["EMA50"] = (
        df["Close"]
        .ewm(span=50, adjust=False)
        .mean()
    )

    df["SMA200"] = (
        df["Close"]
        .rolling(200)
        .mean()
    )

    # Chỉ lấy số phiên gần nhất
    df = df.tail(periods).copy()

    df = df.set_index("Date")

    # =========================
    # THÊM EMA / SMA
    # =========================

    addplots = []

    addplots.append(
        mpf.make_addplot(
            df["EMA20"],
            panel=0
        )
    )

    addplots.append(
        mpf.make_addplot(
            df["EMA50"],
            panel=0
        )
    )

    if df["SMA200"].notna().any():
        addplots.append(
            mpf.make_addplot(
                df["SMA200"],
                panel=0
            )
        )

    # =========================
    # STYLE
    # =========================

    market_style = mpf.make_mpf_style(
        base_mpf_style="yahoo",
        gridstyle=":"
    )

    # =========================
    # VẼ BIỂU ĐỒ
    # =========================

    fig, axes = mpf.plot(
        df[
            [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]
        ],
        type="candle",
        volume=True,
        addplot=addplots,
        style=market_style,
        figsize=(12, 8),
        title=f"{symbol} - Candlestick Chart",
        ylabel="Price",
        ylabel_lower="Volume",
        returnfig=True
    )

    # =========================
    # LƯU VÀO MEMORY
    # =========================

    image = io.BytesIO()

    fig.savefig(
        image,
        format="png",
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    image.seek(0)

    return image