# Import pandas để tạo dữ liệu kiểm thử
import pandas as pd

# Import hàm Backtest trong cùng module
from backtest import run_backtest


# =========================================================
# TẠO DỮ LIỆU TEST GIẢ LẬP OUTPUT TỪ MODULE TÍNH TOÁN
# =========================================================

signal_data = pd.DataFrame({
    "date": [
        "2026-01-02",
        "2026-01-05",
        "2026-01-06",
        "2026-01-07",
        "2026-01-08",
        "2026-01-09"
    ],

    "ticker": [
        "FPT",
        "FPT",
        "FPT",
        "FPT",
        "FPT",
        "FPT"
    ],

    "open": [
        99500,
        101000,
        102500,
        104000,
        106000,
        107500
    ],

    "close": [
        100000,
        102000,
        103000,
        105000,
        108000,
        107000
    ],

    "signal": [
        "HOLD",
        "BUY",
        "HOLD",
        "HOLD",
        "SELL",
        "HOLD"
    ]
})


# =========================================================
# CHẠY THỬ MODULE BACKTEST
# =========================================================

result = run_backtest(
    signal_data=signal_data,
    benchmark_input=None
)


# =========================================================
# KIỂM TRA KẾT QUẢ TRẢ VỀ
# =========================================================

print("\nKIỂM TRA MODULE BACKTEST")

print(
    f"Portfolio Return: "
    f"{result['portfolio_return']:.2f}%"
)

print(
    f"Maximum Drawdown: "
    f"{result['max_drawdown']:.2f}%"
)

print(
    f"Số giao dịch hoàn thành: "
    f"{len(result['trades'])}"
)