import io

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

from src.module_thu_thap_du_lieu.market_data import get_market_data


# =========================================================
# TẠO BIỂU ĐỒ NẾN
# =========================================================

def create_candlestick_chart(symbol, periods=120):

    symbol = symbol.strip().upper()

    # Lấy dữ liệu thị trường
    df = get_market_data()

    if df is None or df.empty:
        raise ValueError(
            "Không có dữ liệu thị trường."
        )

    # Chỉ lấy mã cần vẽ
    df = df[
        df["Symbol"]
        .astype(str)
        .str.upper()
        == symbol
    ].copy()

    if df.empty:
        raise ValueError(
            f"Không tìm thấy dữ liệu cho {symbol}."
        )

    # =====================================================
    # XỬ LÝ DỮ LIỆU
    # =====================================================

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    for column in columns:

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

    # Xóa ngày trùng
    df = df.drop_duplicates(
        subset=["Date"]
    )

    if len(df) < 20:
        raise ValueError(
            f"{symbol} chưa có đủ dữ liệu để vẽ biểu đồ."
        )

    # =====================================================
    # TÍNH CHỈ BÁO
    # =====================================================

    df["EMA20"] = (
        df["Close"]
        .ewm(
            span=20,
            adjust=False
        )
        .mean()
    )

    df["EMA50"] = (
        df["Close"]
        .ewm(
            span=50,
            adjust=False
        )
        .mean()
    )

    df["SMA200"] = (
        df["Close"]
        .rolling(200)
        .mean()
    )

    # =====================================================
    # LẤY 120 PHIÊN GẦN NHẤT
    # =====================================================

    df = df.tail(periods).copy()

    df = df.set_index("Date")

    # =====================================================
    # TẠO ADDPLOT
    # =====================================================

    addplots = []

    # EMA20
    addplots.append(
        mpf.make_addplot(
            df["EMA20"],
            panel=0
        )
    )

    # EMA50
    addplots.append(
        mpf.make_addplot(
            df["EMA50"],
            panel=0
        )
    )

    # SMA200
    if df["SMA200"].notna().any():

        addplots.append(
            mpf.make_addplot(
                df["SMA200"],
                panel=0
            )
        )

    # =====================================================
    # STYLE
    # =====================================================

    market_style = mpf.make_mpf_style(
        base_mpf_style="yahoo",
        gridstyle=":"
    )

    # =====================================================
    # VẼ BIỂU ĐỒ
    # =====================================================

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

    # =====================================================
    # LƯU VÀO MEMORY
    # =====================================================

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