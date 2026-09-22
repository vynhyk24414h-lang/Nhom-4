import pandas as pd

from src.module_thu_thap_du_lieu.market_data import get_market_data
from src.module_tinh_toan_xu_ly.processor import process_universe
from src.module_backtest.backtest import run_backtest


print("==============================")
print("       CHẠY BACKTEST")
print("==============================")

# =========================
# 1. LẤY DỮ LIỆU
# =========================

print("\n[1/4] Đang lấy dữ liệu thị trường...")

df = get_market_data()

if df.empty:
    print("❌ Không có dữ liệu thị trường.")
    exit()

print(f"Đã lấy {len(df):,} dòng dữ liệu.")
print(f"Số mã: {df['Symbol'].nunique()}")


# =========================
# 2. TÍNH TÍN HIỆU
# =========================

print("\n[2/4] Đang tính toán tín hiệu...")

processed = process_universe(df)

debug = processed[
    (processed["Date"] == pd.Timestamp("2026-01-16", tz="UTC")) &
    (processed["Signal"] == "MUA")
].copy()


if processed.empty:
    print("❌ Không xử lý được dữ liệu.")
    exit()

print("Đã tính xong tín hiệu.")


# =========================
# 3. CHUẨN BỊ BACKTEST
# =========================

print("\n[3/4] Đang chuẩn bị dữ liệu backtest...")

backtest_data = processed[
    processed["DataSufficient"] == True
].copy()

backtest_data = backtest_data.sort_values(
    ["Date", "Symbol"]
).reset_index(drop=True)

print(
    f"Số dòng sử dụng: "
    f"{len(backtest_data):,}"
)


# =========================
# 4. CHẠY BACKTEST
# =========================

print("\n[4/4] Đang chạy backtest...")

result = run_backtest(
    signal_data=backtest_data,

    initial_capital=100_000_000,

    max_positions=10,

    lot_size=100,

    risk_per_trade=0.01,

    max_position_pct=0.10,

    max_liquidity_pct=0.05,

    transaction_fee_rate=0.001,

    sell_tax_rate=0.001,

    slippage_rate=0.001,
)


summary = result["summary"]
trades = result["trades"]
equity_curve = result["equity_curve"]


# =========================
# HIỂN THỊ KẾT QUẢ
# =========================

print("\n")
print("==============================")
print("       KẾT QUẢ BACKTEST")
print("==============================")


if summary.empty:

    print("❌ Không có kết quả backtest.")

else:

    row = summary.iloc[0]

    print(
        f"Vốn ban đầu: "
        f"{row['InitialCapital']:,.0f} VND"
    )

    print(
        f"Giá trị cuối kỳ: "
        f"{row['FinalPortfolioValue']:,.0f} VND"
    )

    print(
        f"Total Return: "
        f"{row['TotalReturn']:.2%}"
    )

    print(
        f"CAGR: "
        f"{row['CAGR']:.2%}"
    )

    print(
        f"Maximum Drawdown: "
        f"{row['MaxDrawdown']:.2%}"
    )

    print(
        f"Số giao dịch: "
        f"{int(row['TotalTrades'])}"
    )

    print(
        f"Win Rate: "
        f"{row['WinRate']:.2%}"
    )

    print(
        f"Profit Factor: "
        f"{row['ProfitFactor']:.2f}"
    )


# =========================
# LƯU FILE
# =========================

summary.to_csv(
    "backtest_summary.csv",
    index=False
)

trades.to_csv(
    "backtest_trades.csv",
    index=False
)

equity_curve.to_csv(
    "backtest_equity_curve.csv",
    index=False
)

print("\nĐã lưu:")

print(" - backtest_summary.csv")
print(" - backtest_trades.csv")
print(" - backtest_equity_curve.csv")

print("\n==============================")
print("       BACKTEST HOÀN TẤT")
print("==============================")