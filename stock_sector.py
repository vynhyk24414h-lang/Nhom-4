import pandas as pd

# File danh sách mã của project
universe = pd.read_csv("DanhSachMaCoPhieu.csv")

# Dataset phân ngành
url = "https://huggingface.co/datasets/kjhq/Vietnam-Stock-Symbols-and-Metadata/resolve/main/vietnam.csv"
sector = pd.read_csv(url)

# Chuẩn hóa mã cổ phiếu
universe["Symbol"] = (
    universe["MaCoPhieu"]
    .astype(str)
    .str.strip()
    .str.upper()
)

sector["Symbol"] = (
    sector["ticker"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Chỉ lấy những mã thuộc universe của project
sector = sector[sector["Symbol"].isin(universe["Symbol"])]

# Đổi tên cột
sector = sector.rename(columns={
    "name": "Name",
    "market": "Market",
    "sector": "Sector"
})

# Chỉ giữ các cột cần thiết
sector = sector[
    ["Symbol", "Name", "Market", "Sector"]
]

# Loại mã trùng
sector = sector.drop_duplicates(subset=["Symbol"])

# Tạo đầy đủ 1.047 mã trong universe
result = universe[["Symbol"]].drop_duplicates().merge(
    sector,
    on="Symbol",
    how="left"
)

# Mã không có trong dataset → Unknown
result["Sector"] = result["Sector"].fillna("Unknown")

# Lưu file
result.to_csv("stock_sector.csv", index=False, encoding="utf-8-sig")

print("Đã tạo stock_sector.csv")
print(f"Tổng số mã: {len(result)}")
print(f"Có ngành: {(result['Sector'] != 'Unknown').sum()}")
print(f"Chưa có ngành: {(result['Sector'] == 'Unknown').sum()}")

print("\nMột số dòng đầu:")
print(result.head(10))