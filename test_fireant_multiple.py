from src.module_thu_thap_du_lieu.crawler import (
    get_multiple_stocks
)


symbols = [
    "FPT",
    "VNM",
    "HPG",
    "VCB",
    "MWG"
]


df = get_multiple_stocks(
    symbols,
    "2025-01-01",
    "2026-08-28"
)


print("\n===== KẾT QUẢ =====")

print(df.head())

print("\nSố dòng:", len(df))

print(
    "\nSố mã:",
    df["Symbol"].nunique()
)

print(
    "\nDanh sách mã:",
    df["Symbol"].unique()
)

print(
    "\nSố cột:",
    len(df.columns)
)

print(
    "\nCác cột:",
    df.columns.tolist()
)