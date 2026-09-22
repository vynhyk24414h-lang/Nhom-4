from src.module_thu_thap_du_lieu.universe import (
    load_symbols,
    get_universe_data
)


# Kiểm tra đọc danh sách mã
symbols = load_symbols()

print("\n===== DANH SÁCH MÃ =====")
print("Số mã:", len(symbols))
print("5 mã đầu:", symbols[:5])


# Test trước 5 mã để tránh gọi API quá nhiều
test_symbols = symbols[:5]

print("\n===== TEST FIREANT =====")

from src.module_thu_thap_du_lieu.crawler import (
    get_multiple_stocks
)

df = get_multiple_stocks(
    test_symbols,
    "2025-01-01",
    "2026-08-28"
)

print("\n===== KẾT QUẢ =====")
print("Số dòng:", len(df))
print("Số mã:", df["Symbol"].nunique())
print("Các mã:", df["Symbol"].unique())