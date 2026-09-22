<<<<<<< HEAD
# Import pandas để tạo dữ liệu kiểm thử
import pandas as pd

# Import hàm Backtest trong cùng thư mục
from backtest import run_backtest


# =========================================================
# TẠO DỮ LIỆU TEST THEO ĐÚNG CẤU TRÚC FIREANT
# =========================================================
# FireAnt HistoricalQuotes trả các cột:
# Date, Symbol, Open, High, Low, Close, Volume, Value, OpenInt
#
# Module tính toán bổ sung:
# signal, regime
#
# Bộ test dùng hơn 22 phiên để Backtest đủ dữ liệu tính:
# ATR14, GTGD20, ATR22 và Chandelier Stop.

dates = pd.bdate_range(
    start="2026-01-02",
    periods=35
)

rows = []

for i, current_date in enumerate(dates):

    # Tạo xu hướng tăng giả lập
    base_price = 100_000 + i * 1_000

    open_price = base_price
    high_price = base_price + 1_500
    low_price = base_price - 500
    close_price = base_price + 500

    # Tạo một phiên giảm mạnh để Close thủng Chandelier Stop
    if i == 29:
        open_price = 123_000
        high_price = 124_000
        low_price = 114_000
        close_price = 115_000

    # Các phiên sau cú giảm giữ giá ở vùng thấp hơn
    elif i > 29:
        base_price = 115_000 + (i - 30) * 500
        open_price = base_price
        high_price = base_price + 800
        low_price = base_price - 500
        close_price = base_price + 200

    # BUY sau giai đoạn khởi tạo chỉ báo
    signal = "BUY" if i == 24 else "HOLD"

    rows.append({
        "Date": current_date.strftime(
            "%Y-%m-%dT00:00:00Z"
        ),
        "Symbol": "FPT",
        "Open": open_price,
        "High": high_price,
        "Low": low_price,
        "Close": close_price,
        "Volume": 5_000_000,

        # Cố tình để Value = 0 để kiểm tra cơ chế fallback
        # GTGD = Close × Volume trong Backtest.
        "Value": 0.0,

        # FireAnt có OpenInt nhưng Backtest cổ phiếu không sử dụng.
        "OpenInt": 0,

        # Hai cột do Module tính toán bổ sung.
        "signal": signal,
        "regime": 2
    })


signal_data = pd.DataFrame(
    rows
)


# =========================================================
# TẠO BENCHMARK VNINDEX GIẢ LẬP THEO CẤU TRÚC FIREANT
# =========================================================

benchmark_rows = []

for i, current_date in enumerate(dates):
    benchmark_rows.append({
        "Date": current_date.strftime(
            "%Y-%m-%dT00:00:00Z"
        ),
        "Symbol": "VNINDEX",
        "Close": 1_300 + i * 2
    })

vnindex_data = pd.DataFrame(
    benchmark_rows
)


# =========================================================
# CHẠY THỬ MODULE BACKTEST
# =========================================================

result = run_backtest(
    signal_data=signal_data,
    benchmark_input=vnindex_data,
    initial_capital=200_000_000
)


# =========================================================
# KIỂM TRA KẾT QUẢ TRẢ VỀ
# =========================================================

print(
    "\nKIỂM TRA MODULE BACKTEST - FIREANT"
)

print(
    f"Portfolio Return: "
    f"{result['portfolio_return']:.2f}%"
)

print(
    f"Maximum Drawdown: "
    f"{result['max_drawdown']:.2f}%"
)

if result["benchmark_return"] is not None:
    print(
        f"VNINDEX Return: "
        f"{result['benchmark_return']:.2f}%"
    )

print(
    f"Số giao dịch hoàn thành: "
    f"{len(result['trades'])}"
)


# =========================================================
# KIỂM TRA EOD + OPEN T+1 + CHANDELIER STOP
# =========================================================

if len(result["trades"]) != 1:
    raise AssertionError(
        "Kỳ vọng đúng 1 giao dịch hoàn thành."
    )

trade = result["trades"].iloc[0]

if trade["symbol"] != "FPT":
    raise AssertionError(
        "Sai mã cổ phiếu trong kết quả Backtest."
    )

if trade["sell_reason"] != "CHANDELIER_STOP":
    raise AssertionError(
        "Chandelier Stop chưa kích hoạt đúng."
    )

if trade["buy_date"] <= trade["buy_signal_date"]:
    raise AssertionError(
        "Lệnh BUY chưa được thực hiện ở phiên T+1."
    )

if trade["sell_date"] <= trade["sell_signal_date"]:
    raise AssertionError(
        "Lệnh SELL chưa được thực hiện ở phiên T+1."
    )


print(
    "\nTEST FIREANT + EOD + CHANDELIER STOP: THÀNH CÔNG"
)

print(
    f"Tín hiệu mua: "
    f"{trade['buy_signal_date'].date()}"
)

print(
    f"Ngày mua T+1: "
    f"{trade['buy_date'].date()}"
)

print(
    f"Tín hiệu bán: "
    f"{trade['sell_signal_date'].date()}"
)

print(
    f"Ngày bán T+1: "
    f"{trade['sell_date'].date()}"
)

print(
    f"Lý do bán: "
    f"{trade['sell_reason']}"
)
=======
# Import pandas để tạo dữ liệu kiểm thử
import pandas as pd

# Import hàm Backtest trong cùng thư mục
from backtest import run_backtest


# =========================================================
# TẠO DỮ LIỆU TEST THEO ĐÚNG CẤU TRÚC FIREANT
# =========================================================
# FireAnt HistoricalQuotes trả các cột:
# Date, Symbol, Open, High, Low, Close, Volume, Value, OpenInt
#
# Module tính toán bổ sung:
# signal, regime
#
# Bộ test dùng hơn 22 phiên để Backtest đủ dữ liệu tính:
# ATR14, GTGD20, ATR22 và Chandelier Stop.

dates = pd.bdate_range(
    start="2026-01-02",
    periods=35
)

rows = []

for i, current_date in enumerate(dates):

    # Tạo xu hướng tăng giả lập
    base_price = 100_000 + i * 1_000

    open_price = base_price
    high_price = base_price + 1_500
    low_price = base_price - 500
    close_price = base_price + 500

    # Tạo một phiên giảm mạnh để Close thủng Chandelier Stop
    if i == 29:
        open_price = 123_000
        high_price = 124_000
        low_price = 114_000
        close_price = 115_000

    # Các phiên sau cú giảm giữ giá ở vùng thấp hơn
    elif i > 29:
        base_price = 115_000 + (i - 30) * 500
        open_price = base_price
        high_price = base_price + 800
        low_price = base_price - 500
        close_price = base_price + 200

    # BUY sau giai đoạn khởi tạo chỉ báo
    signal = "BUY" if i == 24 else "HOLD"

    rows.append({
        "Date": current_date.strftime(
            "%Y-%m-%dT00:00:00Z"
        ),
        "Symbol": "FPT",
        "Open": open_price,
        "High": high_price,
        "Low": low_price,
        "Close": close_price,
        "Volume": 5_000_000,

        # Cố tình để Value = 0 để kiểm tra cơ chế fallback
        # GTGD = Close × Volume trong Backtest.
        "Value": 0.0,

        # FireAnt có OpenInt nhưng Backtest cổ phiếu không sử dụng.
        "OpenInt": 0,

        # Hai cột do Module tính toán bổ sung.
        "signal": signal,
        "regime": 2
    })


signal_data = pd.DataFrame(
    rows
)


# =========================================================
# TẠO BENCHMARK VNINDEX GIẢ LẬP THEO CẤU TRÚC FIREANT
# =========================================================

benchmark_rows = []

for i, current_date in enumerate(dates):
    benchmark_rows.append({
        "Date": current_date.strftime(
            "%Y-%m-%dT00:00:00Z"
        ),
        "Symbol": "VNINDEX",
        "Close": 1_300 + i * 2
    })

vnindex_data = pd.DataFrame(
    benchmark_rows
)


# =========================================================
# CHẠY THỬ MODULE BACKTEST
# =========================================================

result = run_backtest(
    signal_data=signal_data,
    benchmark_input=vnindex_data,
    initial_capital=200_000_000
)


# =========================================================
# KIỂM TRA KẾT QUẢ TRẢ VỀ
# =========================================================

print(
    "\nKIỂM TRA MODULE BACKTEST - FIREANT"
)

print(
    f"Portfolio Return: "
    f"{result['portfolio_return']:.2f}%"
)

print(
    f"Maximum Drawdown: "
    f"{result['max_drawdown']:.2f}%"
)

if result["benchmark_return"] is not None:
    print(
        f"VNINDEX Return: "
        f"{result['benchmark_return']:.2f}%"
    )

print(
    f"Số giao dịch hoàn thành: "
    f"{len(result['trades'])}"
)


# =========================================================
# KIỂM TRA EOD + OPEN T+1 + CHANDELIER STOP
# =========================================================

if len(result["trades"]) != 1:
    raise AssertionError(
        "Kỳ vọng đúng 1 giao dịch hoàn thành."
    )

trade = result["trades"].iloc[0]

if trade["symbol"] != "FPT":
    raise AssertionError(
        "Sai mã cổ phiếu trong kết quả Backtest."
    )

if trade["sell_reason"] != "CHANDELIER_STOP":
    raise AssertionError(
        "Chandelier Stop chưa kích hoạt đúng."
    )

if trade["buy_date"] <= trade["buy_signal_date"]:
    raise AssertionError(
        "Lệnh BUY chưa được thực hiện ở phiên T+1."
    )

if trade["sell_date"] <= trade["sell_signal_date"]:
    raise AssertionError(
        "Lệnh SELL chưa được thực hiện ở phiên T+1."
    )


print(
    "\nTEST FIREANT + EOD + CHANDELIER STOP: THÀNH CÔNG"
)

print(
    f"Tín hiệu mua: "
    f"{trade['buy_signal_date'].date()}"
)

print(
    f"Ngày mua T+1: "
    f"{trade['buy_date'].date()}"
)

print(
    f"Tín hiệu bán: "
    f"{trade['sell_signal_date'].date()}"
)

print(
    f"Ngày bán T+1: "
    f"{trade['sell_date'].date()}"
)

print(
    f"Lý do bán: "
    f"{trade['sell_reason']}"
)
>>>>>>> d42c5a28b326b26d4f856a1b2f95f459820842cb
