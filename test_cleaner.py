from src.module_thu_thap_du_lieu.universe import (
    get_universe_data
)

from src.module_thu_thap_du_lieu.cleaner import (
    clean_data,
    check_data_sufficiency
)


print("Đang lấy dữ liệu từ FireAnt...")

df_raw = get_universe_data(
    "2025-01-01",
    "2026-08-28"
)


print("\n===== DỮ LIỆU RAW =====")

print(
    "Số dòng:",
    len(df_raw)
)

print(
    "Số mã:",
    df_raw["Symbol"].nunique()
)


print("\nĐang làm sạch dữ liệu...")

df = clean_data(df_raw)


print("\n===== SAU KHI CLEAN =====")

print(
    "Số dòng:",
    len(df)
)

print(
    "Số mã:",
    df["Symbol"].nunique()
)

print(
    "Ngày đầu:",
    df["Date"].min()
)

print(
    "Ngày cuối:",
    df["Date"].max()
)


print("\n===== SỐ PHIÊN TỪNG MÃ =====")

counts = (
    df.groupby("Symbol")
    .size()
    .sort_values()
)

print(counts.head(10))


print("\n===== KIỂM TRA 260 PHIÊN =====")

sufficient = check_data_sufficiency(df)

print(sufficient.head(10))