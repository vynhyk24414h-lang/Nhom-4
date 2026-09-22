import pandas as pd

from src.module_thu_thap_du_lieu.market_data import (
    get_market_data
)

from src.module_tinh_toan_xu_ly.processor import (
    process_universe
)


print("Đang lấy dữ liệu thị trường...")

df = get_market_data()

if df.empty:
    print("❌ Không có dữ liệu.")
    exit()


print("Đang tính toán tín hiệu...")

result = process_universe(df)

if result.empty:
    print("❌ Không xử lý được dữ liệu.")
    exit()


# =========================
# LẤY PHIÊN MỚI NHẤT
# =========================

latest_date = result["Date"].max()

latest = result[
    result["Date"] == latest_date
].copy()


print("\n==============================")
print("      KẾT QUẢ TOÀN THỊ TRƯỜNG")
print("==============================")

print(
    f"Ngày dữ liệu: "
    f"{latest_date.strftime('%d/%m/%Y')}"
)

print(
    f"Tổng số mã: "
    f"{latest['Symbol'].nunique()}"
)


# =========================
# ĐẾM TÍN HIỆU
# =========================

signal_count = (
    latest["Signal"]
    .value_counts()
)


print("\n----- PHÂN BỔ TÍN HIỆU -----")

for signal in [
    "MUA",
    "GIỮ",
    "BÁN",
    "THIẾU DỮ LIỆU"
]:

    count = signal_count.get(
        signal,
        0
    )

    print(
        f"{signal}: {count}"
    )


# =========================
# DANH SÁCH MUA
# =========================

buy_list = latest[
    latest["Signal"] == "MUA"
].copy()

buy_list = buy_list.sort_values(
    "RS",
    ascending=False
)


print("\n----- CỔ PHIẾU MUA -----")

if buy_list.empty:

    print("Không có mã MUA.")

else:

    print(
        buy_list[
            [
                "Symbol",
                "Close",
                "RS",
                "TrendScore",
                "VolumeScore"
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


# =========================
# DANH SÁCH BÁN
# =========================

sell_list = latest[
    latest["Signal"] == "BÁN"
].copy()

sell_list = sell_list.sort_values(
    "RS",
    ascending=True
)


print("\n----- CỔ PHIẾU BÁN -----")

if sell_list.empty:

    print("Không có mã BÁN.")

else:

    print(
        sell_list[
            [
                "Symbol",
                "Close",
                "RS",
                "SMA200",
                "ChandelierStop"
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


# =========================
# DANH SÁCH GIỮ
# =========================

hold_list = latest[
    latest["Signal"] == "GIỮ"
].copy()


print("\n----- SỐ LƯỢNG CỔ PHIẾU GIỮ -----")

print(
    len(hold_list)
)


# =========================
# LƯU KẾT QUẢ
# =========================

latest.to_csv(
    "market_signals_latest.csv",
    index=False
)


print("\n==============================")
print(
    "Đã lưu kết quả vào "
    "market_signals_latest.csv"
)
print("==============================")