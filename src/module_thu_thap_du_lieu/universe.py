import pandas as pd

from src.module_thu_thap_du_lieu.crawler import (
    get_multiple_stocks
)


CSV_PATH = "DanhSachMaCoPhieu.csv"


def load_symbols():

    df = pd.read_csv(CSV_PATH)

    print("Các cột trong CSV:")
    print(df.columns.tolist())

    symbols = (
        df["MaCoPhieu"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .unique()
        .tolist()
    )

    return symbols


def get_universe_data(
    start_date="2025-01-01",
    end_date="2026-08-28"
):

    symbols = load_symbols()

    print(
        f"Tổng số mã cần lấy: {len(symbols)}"
    )

    data = get_multiple_stocks(
        symbols,
        start_date,
        end_date
    )

    return data