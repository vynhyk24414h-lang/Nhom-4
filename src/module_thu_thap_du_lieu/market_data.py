import os
import pandas as pd

from src.module_thu_thap_du_lieu.crawler import (
    get_multiple_stocks,
    get_historical_data
)

from src.module_thu_thap_du_lieu.universe import (
    load_symbols
)


# =========================================================
# CACHE
# =========================================================

CACHE_FILE = "fireant_universe.csv"

STOCK_CACHE_DIR = "stock_cache"


# Lấy dữ liệu khoảng 3 năm
START_DATE = "2023-01-01"

# Ngày kết thúc ban đầu
INITIAL_END_DATE = "2026-09-22"


# =========================================================
# CHUẨN HÓA DATE
# =========================================================

def normalize_date(df):

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
        utc=True
    )

    df["Date"] = (
        df["Date"]
        .dt.tz_localize(None)
    )

    return df


# =========================================================
# LẤY TOÀN BỘ DỮ LIỆU THỊ TRƯỜNG
# DÙNG CHO /TINHIEU
# =========================================================

def get_market_data():

    symbols = load_symbols()

    # ==========================================
    # 1. CHƯA CÓ CACHE
    # ==========================================

    if not os.path.exists(CACHE_FILE):

        print("Chưa có dữ liệu cache.")

        print(
            f"Đang lấy dữ liệu từ "
            f"{START_DATE} đến "
            f"{INITIAL_END_DATE}..."
        )

        df = get_multiple_stocks(
            symbols,
            START_DATE,
            INITIAL_END_DATE
        )

        if df.empty:
            return pd.DataFrame()

        df = normalize_date(df)

        df.to_csv(
            CACHE_FILE,
            index=False
        )

        print(
            f"Đã lưu cache: "
            f"{len(df):,} dòng."
        )

        return df

    # ==========================================
    # 2. ĐÃ CÓ CACHE
    # ==========================================

    print(
        "Đang đọc dữ liệu thị trường từ cache..."
    )

    df = pd.read_csv(
        CACHE_FILE
    )

    if df.empty:
        return pd.DataFrame()

    df = normalize_date(df)

    # ==========================================
    # 3. TÌM NGÀY CUỐI CÙNG
    # ==========================================

    last_date = df["Date"].max()

    if pd.isna(last_date):

        print(
            "❌ Không xác định được ngày cuối "
            "trong cache."
        )

        return df

    print(
        f"Dữ liệu hiện có đến: "
        f"{last_date.strftime('%d/%m/%Y')}"
    )

    # ==========================================
    # 4. NGÀY HIỆN TẠI
    # ==========================================

    today = pd.Timestamp.today().normalize()

    # ==========================================
    # 5. CẬP NHẬT DỮ LIỆU MỚI
    # ==========================================

    if last_date < today:

        update_start = (
            last_date
            + pd.Timedelta(days=1)
        )

        print(
            f"Đang cập nhật từ "
            f"{update_start.strftime('%d/%m/%Y')} "
            f"đến "
            f"{today.strftime('%d/%m/%Y')}..."
        )

        new_data = get_multiple_stocks(
            symbols,
            update_start.strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d")
        )

        if not new_data.empty:

            new_data = normalize_date(
                new_data
            )

            df = pd.concat(
                [df, new_data],
                ignore_index=True
            )

            df = df.drop_duplicates(
                subset=[
                    "Symbol",
                    "Date"
                ]
            )

            df = df.sort_values(
                [
                    "Symbol",
                    "Date"
                ]
            ).reset_index(
                drop=True
            )

            df.to_csv(
                CACHE_FILE,
                index=False
            )

            print(
                f"Đã thêm "
                f"{len(new_data):,} dòng mới."
            )

        else:

            print(
                "Không có dữ liệu mới."
            )

        print(
            "Dữ liệu đã được cập nhật."
        )

    else:

        print(
            "Cache đã có dữ liệu mới nhất."
        )

    return df


# =========================================================
# LẤY DỮ LIỆU RIÊNG MỘT MÃ
# DÙNG CHO /BIEUDO
# =========================================================

def get_stock_data(symbol):

    symbol = str(
        symbol
    ).strip().upper()

    if not symbol:
        return pd.DataFrame()

    # ==========================================
    # TẠO THƯ MỤC CACHE RIÊNG CHO TỪNG MÃ
    # ==========================================

    os.makedirs(
        STOCK_CACHE_DIR,
        exist_ok=True
    )

    stock_cache_file = os.path.join(
        STOCK_CACHE_DIR,
        f"{symbol}.csv"
    )

    # ==========================================
    # 1. CHƯA CÓ CACHE RIÊNG
    # ==========================================

    if not os.path.exists(stock_cache_file):

        print(
            f"Chưa có cache riêng cho {symbol}."
        )

        print(
            f"Đang lấy dữ liệu {symbol} "
            f"từ {START_DATE} đến "
            f"{INITIAL_END_DATE}..."
        )

        df = get_historical_data(
            symbol,
            START_DATE,
            INITIAL_END_DATE
        )

        if df is None or df.empty:

            print(
                f"Không có dữ liệu cho {symbol}."
            )

            return pd.DataFrame()

        df = normalize_date(df)

        df.to_csv(
            stock_cache_file,
            index=False
        )

        print(
            f"Đã lưu cache {symbol}: "
            f"{len(df):,} dòng."
        )

        return df.sort_values(
            "Date"
        ).reset_index(
            drop=True
        )

    # ==========================================
    # 2. ĐÃ CÓ CACHE RIÊNG
    # ==========================================

    print(
        f"Đang đọc cache riêng của {symbol}..."
    )

    df = pd.read_csv(
        stock_cache_file
    )

    if df.empty:
        return pd.DataFrame()

    df = normalize_date(df)

    # ==========================================
    # 3. TÌM NGÀY CUỐI CÙNG
    # ==========================================

    last_date = df["Date"].max()

    if pd.isna(last_date):

        print(
            f"❌ Không xác định được ngày cuối "
            f"của {symbol}."
        )

        return df

    # ==========================================
    # 4. CẬP NHẬT DỮ LIỆU MỚI
    # ==========================================

    today = pd.Timestamp.today().normalize()

    if last_date < today:

        update_start = (
            last_date
            + pd.Timedelta(days=1)
        )

        print(
            f"Cập nhật {symbol} từ "
            f"{update_start.strftime('%d/%m/%Y')} "
            f"đến "
            f"{today.strftime('%d/%m/%Y')}..."
        )

        new_data = get_historical_data(
            symbol,
            update_start.strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d")
        )

        if new_data is not None and not new_data.empty:

            new_data = normalize_date(
                new_data
            )

            df = pd.concat(
                [df, new_data],
                ignore_index=True
            )

            df = df.drop_duplicates(
                subset=[
                    "Symbol",
                    "Date"
                ]
            )

            df = df.sort_values(
                [
                    "Symbol",
                    "Date"
                ]
            ).reset_index(
                drop=True
            )

            df.to_csv(
                stock_cache_file,
                index=False
            )

            print(
                f"Đã cập nhật {symbol}: "
                f"{len(new_data):,} dòng mới."
            )

        else:

            print(
                f"Không có dữ liệu mới cho {symbol}."
            )

    else:

        print(
            f"Cache {symbol} đã có dữ liệu mới nhất."
        )

    return df.sort_values(
        "Date"
    ).reset_index(
        drop=True
    )