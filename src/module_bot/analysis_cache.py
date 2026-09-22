import os
import pandas as pd

from src.module_thu_thap_du_lieu.market_data import (
    get_market_data
)

from src.module_tinh_toan_xu_ly.processor import (
    process_universe
)


# =========================================================
# FILE CACHE KẾT QUẢ PHÂN TÍCH
# =========================================================

ANALYSIS_CACHE_FILE = "latest_analysis.csv"


# =========================================================
# KIỂM TRA CACHE CÓ HỢP LỆ KHÔNG
# =========================================================

def load_analysis_cache():

    if not os.path.exists(
        ANALYSIS_CACHE_FILE
    ):
        return pd.DataFrame()

    try:

        df = pd.read_csv(
            ANALYSIS_CACHE_FILE
        )

        if df.empty:
            return pd.DataFrame()

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

        return df

    except Exception as e:

        print(
            f"Lỗi đọc analysis cache: {e}"
        )

        return pd.DataFrame()


# =========================================================
# LẤY NGÀY DỮ LIỆU THỊ TRƯỜNG MỚI NHẤT
# =========================================================

def get_latest_market_date():

    market_data = get_market_data()

    if market_data is None or market_data.empty:

        return None

    market_data["Date"] = pd.to_datetime(
        market_data["Date"],
        errors="coerce"
    )

    latest_date = market_data["Date"].max()

    return latest_date


# =========================================================
# LẤY KẾT QUẢ PHÂN TÍCH MỚI NHẤT
# =========================================================

def get_latest_analysis():

    # ==========================================
    # 1. ĐỌC CACHE PHÂN TÍCH
    # ==========================================

    cached = load_analysis_cache()

    # ==========================================
    # 2. LẤY DỮ LIỆU THỊ TRƯỜNG
    # ==========================================

    market_data = get_market_data()

    if market_data is None or market_data.empty:

        return pd.DataFrame()

    market_data["Date"] = pd.to_datetime(
        market_data["Date"],
        errors="coerce"
    )

    latest_market_date = market_data["Date"].max()

    # ==========================================
    # 3. NẾU CACHE ĐÃ CÓ ĐÚNG NGÀY
    #    → KHÔNG TÍNH LẠI
    # ==========================================

    if not cached.empty:

        latest_cached_date = cached["Date"].max()

        if (
            pd.notna(latest_cached_date)
            and latest_cached_date
            == latest_market_date
        ):

            print(
                "Đã có analysis cache "
                f"cho ngày {latest_market_date.strftime('%d/%m/%Y')}."
            )

            return cached

    # ==========================================
    # 4. CHƯA CÓ CACHE / DỮ LIỆU MỚI
    #    → CHẠY PROCESS_UNIVERSE
    # ==========================================

    print(
        "Chưa có analysis cache mới."
    )

    print(
        "Đang chạy phân tích toàn bộ universe..."
    )

    result = process_universe(
        market_data
    )

    if result is None or result.empty:

        return pd.DataFrame()

    result["Date"] = pd.to_datetime(
        result["Date"],
        errors="coerce"
    )

    # ==========================================
    # 5. CHỈ LƯU NGÀY MỚI NHẤT
    # ==========================================

    latest_date = result["Date"].max()

    latest_result = result[
        result["Date"] == latest_date
    ].copy()

    # ==========================================
    # 6. LƯU CACHE
    # ==========================================

    latest_result.to_csv(
        ANALYSIS_CACHE_FILE,
        index=False
    )

    print(
        f"Đã lưu analysis cache: "
        f"{len(latest_result):,} mã."
    )

    return latest_result


# =========================================================
# TRA CỨU MỘT MÃ TỪ ANALYSIS CACHE
# =========================================================

def get_stock_analysis(symbol):

    symbol = str(
        symbol
    ).strip().upper()

    if not symbol:

        return None

    analysis = get_latest_analysis()

    if analysis is None or analysis.empty:

        return None

    analysis["Symbol"] = (
        analysis["Symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    stock = analysis[
        analysis["Symbol"] == symbol
    ]

    if stock.empty:

        return None

    return stock.iloc[-1]