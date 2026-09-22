import pandas as pd

from src.module_thu_thap_du_lieu.market_data import get_market_data
from src.module_tinh_toan_xu_ly.processor import process_universe

print("Đang lấy dữ liệu...")
df = get_market_data()

print("\n===== DATA GỐC =====")
print("Số dòng:", len(df))
print("Số mã:", df["Symbol"].nunique())
print("Ngày:", df["Date"].min(), "->", df["Date"].max())


print("\nĐang xử lý...")
processed = process_universe(df)

print("\n===== SAU KHI XỬ LÝ =====")
print("Số dòng:", len(processed))
print("Số mã:", processed["Symbol"].nunique())


print("\n===== DATA SUFFICIENT =====")
print(
    processed["DataSufficient"]
    .value_counts(dropna=False)
)


print("\n===== SIGNAL =====")
print(
    processed["Signal"]
    .value_counts(dropna=False)
)


print("\n===== MUA =====")
buy = processed[processed["Signal"] == "MUA"]

print("Tổng số dòng MUA:", len(buy))

if not buy.empty:
    print(
        buy[
            [
                "Date",
                "Symbol",
                "Close",
                "RS",
                "EMA20",
                "EMA50",
                "SMA200",
                "Liquidity_ok",
                "AntiChasing_ok",
                "Signal"
            ]
        ].tail(20).to_string(index=False)
    )


print("\n===== BÁN =====")
sell = processed[processed["Signal"] == "BÁN"]

print("Tổng số dòng BÁN:", len(sell))


print("\n===== CÁC ĐIỀU KIỆN MUA =====")

conditions = {
    "Liquidity_ok": processed["Liquidity_ok"],
    "RS >= 60": processed["RS"] >= 60,
    "EMA20 > EMA50": processed["EMA_ok"],
    "Close > SMA200": processed["SMA200_ok"],
    "AntiChasing_ok": processed["AntiChasing_ok"],
}

for name, condition in conditions.items():
    print(
        f"{name}: "
        f"{condition.fillna(False).sum()} dòng đạt / "
        f"{len(processed)} dòng"
    )


print("\n===== GIAO DỊCH THEO NGÀY =====")

daily_buy = (
    buy.groupby("Date")
    .size()
    .sort_values(ascending=False)
)

print(daily_buy.head(20))
print("\n===== KIỂM TRA ANTICHASING =====")

check = processed[
    [
        "Symbol",
        "Date",
        "Close",
        "EMA20",
        "ATR14",
        "AntiChasing",
        "AntiChasing_ok"
    ]
].dropna()

print(check.tail(20).to_string(index=False))

print("\nThống kê AntiChasing:")
print(check["AntiChasing"].describe())

print("\nAntiChasing <= 3:")
print((check["AntiChasing"] <= 3).sum())

print("\nAntiChasing <= 5:")
print((check["AntiChasing"] <= 5).sum())

print("\nAntiChasing <= 10:")
print((check["AntiChasing"] <= 10).sum())
print("\n===== KIỂM TRA GIAO NHAU CÁC ĐIỀU KIỆN =====")

c1 = processed["Liquidity_ok"].fillna(False)
c2 = (processed["RS"] >= 60).fillna(False)
c3 = processed["EMA_ok"].fillna(False)
c4 = processed["SMA200_ok"].fillna(False)
c5 = processed["AntiChasing_ok"].fillna(False)

print("Liquidity:", c1.sum())
print("Liquidity + RS:", (c1 & c2).sum())
print("Liquidity + RS + EMA:", (c1 & c2 & c3).sum())
print("Liquidity + RS + EMA + SMA200:", (c1 & c2 & c3 & c4).sum())
print("Tất cả 5:", (c1 & c2 & c3 & c4 & c5).sum())


print("\n===== KIỂM TRA RS =====")

rs_check = processed[
    ["Symbol", "Date", "Close", "R63", "R126", "R252",
     "PR63", "PR126", "PR252", "RS", "Liquidity_ok"]
].dropna(subset=["R63", "R126", "R252"])

print("Số dòng có đủ R63/R126/R252:", len(rs_check))
print("Số dòng có RS:", processed["RS"].notna().sum())

print("\nPhân phối RS:")
print(processed["RS"].describe())

print("\nTop RS:")
print(
    processed[
        ["Symbol", "Date", "RS", "Liquidity_ok",
         "EMA_ok", "SMA200_ok", "AntiChasing_ok"]
    ]
    .dropna(subset=["RS"])
    .sort_values("RS", ascending=False)
    .head(20)
    .to_string(index=False)
)