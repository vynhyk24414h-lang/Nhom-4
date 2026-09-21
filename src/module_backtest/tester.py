# Import pandas để tạo dữ liệu kiểm thử
import pandas as pd

# Import hàm Backtest trong cùng thư mục
from backtest import run_backtest


# =========================================================
# TẠO DỮ LIỆU TEST GIẢ LẬP OUTPUT TỪ MODULE TÍNH TOÁN
# =========================================================
# Mục tiêu của bộ dữ liệu:
# - BUY xuất hiện ngày 05/01
# - Lệnh mua được khớp ở Open ngày 06/01
# - Các ngày sau processor vẫn trả HOLD
# - Chandelier Stop tăng dần
# - Ngày 08/01, Close thấp hơn trailing stop
# - Backtest phải tự tạo SELL và bán ở Open ngày 09/01

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
        103000,
        101000
    ],

    "close": [
        100000,
        102000,
        104000,
        105000,
        101000,
        102000
    ],

    "signal": [
        "HOLD",
        "BUY",
        "HOLD",
        "HOLD",
        "HOLD",
        "HOLD"
    ],

    # ATR14 dùng để tính quy mô vị thế
    "atr14": [
        2500,
        2500,
        2500,
        2500,
        2500,
        2500
    ],

    # Giá trị giao dịch trung bình 20 phiên
    "avg_gtgd20": [
        5_000_000_000,
        5_000_000_000,
        5_000_000_000,
        5_000_000_000,
        5_000_000_000,
        5_000_000_000
    ],

    # Regime = 2: thị trường thuận lợi
    "regime": [
        2,
        2,
        2,
        2,
        2,
        2
    ],

    # Chandelier Stop do Module tính toán truyền sang
    "chandelier_cs": [
        95000,
        96000,
        98000,
        102000,
        102000,
        102000
    ]
})


# =========================================================
# CHẠY THỬ MODULE BACKTEST
# =========================================================

result = run_backtest(
    signal_data=signal_data,
    benchmark_input=None,
    initial_capital=200_000_000
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


# =========================================================
# KIỂM TRA CHANDELIER STOP
# =========================================================

if len(result["trades"]) == 1:

    trade = result["trades"].iloc[0]

    print("\nTEST CHANDELIER STOP: THÀNH CÔNG")

    print(
        f"Mua ngày: "
        f"{trade['buy_date'].date()}"
    )

    print(
        f"Bán ngày: "
        f"{trade['sell_date'].date()}"
    )

else:

    print(
        "\nTEST CHANDELIER STOP: "
        "CHƯA ĐÚNG KỲ VỌNG"
    )