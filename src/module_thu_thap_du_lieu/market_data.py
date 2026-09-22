import os
import pandas as pd

from src.module_thu_thap_du_lieu.crawler import (
    get_multiple_stocks
)
from src.module_thu_thap_du_lieu.universe import load_symbols


CACHE_FILE = "fireant_universe.csv"

# Lấy dữ liệu khoảng 3 năm
START_DATE = "2023-01-01"

# Ngày kết thúc ban đầu
INITIAL_END_DATE = "2026-09-22"


def get_market_data():
    symbols = load_symbols()

    # ==========================================
    # 1. CHƯA CÓ CACHE
    # ==========================================
    if not os.path.exists(CACHE_FILE):

        print("Chưa có dữ liệu cache.")
        print(
            f"Đang lấy dữ liệu từ "
            f"{START_DATE} đến {INITIAL_END_DATE}..."
        )

        df = get_multiple_stocks(
            symbols,
            START_DATE,
            INITIAL_END_DATE
        )

        if df.empty:
            return pd.DataFrame()

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
    print("Đang đọc dữ liệu thị trường từ cache...")

    df = pd.read_csv(CACHE_FILE)

    if df.empty:
        return pd.DataFrame()

    # Chuyển Date về datetime
    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
        utc=True
    )

    # Bỏ timezone để tất cả ngày đều cùng kiểu
    df["Date"] = df["Date"].dt.tz_localize(None)

    # Ngày cuối cùng trong cache
    last_date = df["Date"].max()

    print(
        f"Dữ liệu hiện có đến: "
        f"{last_date.strftime('%d/%m/%Y')}"
    )

    # ==========================================
    # 3. NGÀY HIỆN TẠI
    # ==========================================
    today = pd.Timestamp.today().normalize()

    # ==========================================
    # 4. CẬP NHẬT DỮ LIỆU MỚI
    # ==========================================
    if last_date < today:

        update_start = last_date + pd.Timedelta(days=1)

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

            new_data["Date"] = pd.to_datetime(
                new_data["Date"],
                errors="coerce",
                utc=True
            )

            new_data["Date"] = (
                new_data["Date"]
                .dt.tz_localize(None)
            )

            df = pd.concat(
                [df, new_data],
                ignore_index=True
            )

            df = df.drop_duplicates(
                subset=["Symbol", "Date"]
            )

            df = df.sort_values(
                ["Symbol", "Date"]
            ).reset_index(drop=True)

            df.to_csv(
                CACHE_FILE,
                index=False
            )

        print("Dữ liệu đã được cập nhật.")

    else:
        print("Cache đã có dữ liệu mới nhất.")

    return df