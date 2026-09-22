import os
import pandas as pd


SECTOR_FILE = "stock_sector.csv"


# Tên ngành tiếng Anh trong dataset → tên hiển thị tiếng Việt
SECTOR_VI = {
    "Commercial services": "Dịch vụ thương mại",
    "Communications": "Truyền thông",
    "Consumer durables": "Hàng tiêu dùng lâu bền",
    "Consumer non-durables": "Hàng tiêu dùng không lâu bền",
    "Consumer services": "Dịch vụ tiêu dùng",
    "Distribution services": "Dịch vụ phân phối",
    "Electronic technology": "Công nghệ điện tử",
    "Energy minerals": "Khoáng sản năng lượng",
    "Finance": "Tài chính",
    "Health services": "Dịch vụ y tế",
    "Health technology": "Công nghệ y tế",
    "Industrial services": "Dịch vụ công nghiệp",
    "Non-energy minerals": "Khoáng sản phi năng lượng",
    "Process industries": "Công nghiệp chế biến",
    "Producer manufacturing": "Sản xuất công nghiệp",
    "Retail trade": "Bán lẻ",
    "Technology services": "Dịch vụ công nghệ",
    "Transportation": "Vận tải",
    "Utilities": "Tiện ích",
    "Unknown": "Chưa phân loại",
}


def load_sector_data():
    if not os.path.exists(SECTOR_FILE):
        return pd.DataFrame()

    df = pd.read_csv(SECTOR_FILE)

    if df.empty:
        return pd.DataFrame()

    df["Symbol"] = (
        df["Symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["Sector"] = (
        df["Sector"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    return df


def translate_sector(sector):
    return SECTOR_VI.get(
        str(sector).strip(),
        "Chưa phân loại"
    )


def get_stock_sector(symbol):
    df = load_sector_data()

    if df.empty:
        return "Unknown"

    symbol = str(symbol).strip().upper()

    result = df[df["Symbol"] == symbol]

    if result.empty:
        return "Unknown"

    return result.iloc[0]["Sector"]


def get_stock_sector_vi(symbol):
    sector = get_stock_sector(symbol)
    return translate_sector(sector)


def get_sector_list():
    df = load_sector_data()

    if df.empty:
        return []

    sectors = (
        df.loc[df["Sector"] != "Unknown", "Sector"]
        .dropna()
        .unique()
        .tolist()
    )

    return sorted(sectors)


def get_sector_list_vi():
    sectors = get_sector_list()

    return [
        translate_sector(sector)
        for sector in sectors
    ]


def get_stocks_by_sector(sector):
    df = load_sector_data()

    if df.empty:
        return pd.DataFrame()

    return df[df["Sector"] == sector].copy()


def get_stocks_by_sector_vi(sector_vi):
    df = load_sector_data()

    if df.empty:
        return pd.DataFrame()

    for sector_en, sector_name_vi in SECTOR_VI.items():
        if sector_name_vi == sector_vi:
            return df[df["Sector"] == sector_en].copy()

    return pd.DataFrame()