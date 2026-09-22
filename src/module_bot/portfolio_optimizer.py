import pandas as pd

from src.module_thu_thap_du_lieu.market_data import get_stock_data
from src.module_tinh_toan_xu_ly.processor import process_universe


MAX_WEIGHT = 0.30
MIN_WEIGHT = 0.05


def get_stock_row(symbol):
    """
    Lấy dòng dữ liệu mới nhất của một mã cổ phiếu.
    """
    symbol = str(symbol).strip().upper()

    if not symbol:
        return None

    try:
        df = get_stock_data(symbol)

        if df is None or df.empty:
            return None

        result = process_universe(df)

        if result is None or result.empty:
            return None

        result = result.sort_values("Date")

        return result.iloc[-1]

    except Exception as e:
        print(f"Lỗi xử lý {symbol}: {e}")
        return None


def calculate_stock_score(row):
    """
    Tính điểm dùng cho phân bổ danh mục.

    Điểm cơ sở:
    - SmartScore

    Sau đó điều chỉnh theo mức biến động:
    - ATR14 / Close

    Biến động càng cao thì điểm điều chỉnh càng thấp.
    """

    smartscore = row.get("SmartScore")

    if pd.isna(smartscore):
        smartscore = row.get("smartscore")

    if pd.isna(smartscore):
        smartscore = 0

    try:
        smartscore = float(smartscore)
    except Exception:
        smartscore = 0

    close = row.get("Close")
    atr14 = row.get("ATR14")

    if pd.isna(close) or pd.isna(atr14):
        return 0

    try:
        close = float(close)
        atr14 = float(atr14)
    except Exception:
        return 0

    if close <= 0 or atr14 <= 0:
        return 0

    volatility = atr14 / close

    if volatility <= 0:
        return 0

    # Điều chỉnh điểm theo biến động.
    # Biến động càng cao -> điểm càng thấp.
    adjusted_score = smartscore / volatility

    return adjusted_score


def optimize_weights(stock_data):
    """
    Tính tỷ trọng cho danh mục.

    stock_data:
        List các dictionary có:
        symbol
        score
        close
        signal
        smartscore
        volatility
    """

    if not stock_data:
        return []

    valid_data = [
        item
        for item in stock_data
        if item.get("score", 0) > 0
    ]

    if not valid_data:
        return []

    total_score = sum(
        item["score"]
        for item in valid_data
    )

    if total_score <= 0:
        return []

    for item in valid_data:
        item["raw_weight"] = (
            item["score"] / total_score
        )

    # Giới hạn tỷ trọng tối đa.
    for item in valid_data:
        item["weight"] = min(
            item["raw_weight"],
            MAX_WEIGHT
        )

    total_weight = sum(
        item["weight"]
        for item in valid_data
    )

    if total_weight <= 0:
        return []

    # Chuẩn hóa lại về 100%.
    for item in valid_data:
        item["weight"] = (
            item["weight"] / total_weight
        )

    return valid_data


def optimize_portfolio(symbols, capital):
    """
    Tối ưu hóa danh mục từ danh sách mã cổ phiếu.

    Parameters
    ----------
    symbols : list
        Danh sách mã cổ phiếu.

    capital : float
        Tổng số vốn.

    Returns
    -------
    dict
        Kết quả tối ưu danh mục.
    """

    if not symbols:
        return {
            "success": False,
            "message": "Chưa có mã cổ phiếu."
        }

    try:
        capital = float(capital)
    except Exception:
        return {
            "success": False,
            "message": "Số vốn không hợp lệ."
        }

    if capital <= 0:
        return {
            "success": False,
            "message": "Số vốn phải lớn hơn 0."
        }

    cleaned_symbols = []

    for symbol in symbols:
        symbol = str(symbol).strip().upper()

        if not symbol:
            continue

        if not symbol.isalnum():
            continue

        if symbol not in cleaned_symbols:
            cleaned_symbols.append(symbol)

    if not cleaned_symbols:
        return {
            "success": False,
            "message": "Không có mã cổ phiếu hợp lệ."
        }

    stock_data = []
    invalid_symbols = []

    for symbol in cleaned_symbols:

        print(
            f"Đang phân tích danh mục: {symbol}"
        )

        row = get_stock_row(symbol)

        if row is None:
            invalid_symbols.append(symbol)
            continue

        close = row.get("Close")
        atr14 = row.get("ATR14")
        signal = str(
            row.get("Signal", "GIỮ")
        )

        smartscore = row.get("SmartScore")

        if pd.isna(smartscore):
            smartscore = row.get("smartscore")

        if pd.isna(smartscore):
            smartscore = 0

        try:
            smartscore = float(smartscore)
        except Exception:
            smartscore = 0

        if pd.isna(close):
            invalid_symbols.append(symbol)
            continue

        try:
            close = float(close)
        except Exception:
            invalid_symbols.append(symbol)
            continue

        if pd.isna(atr14):
            invalid_symbols.append(symbol)
            continue

        try:
            atr14 = float(atr14)
        except Exception:
            invalid_symbols.append(symbol)
            continue

        volatility = 0

        if close > 0:
            volatility = atr14 / close

        score = calculate_stock_score(row)

        stock_data.append({
            "symbol": symbol,
            "close": close,
            "atr14": atr14,
            "smartscore": smartscore,
            "signal": signal,
            "volatility": volatility,
            "score": score,
        })

    if not stock_data:
        return {
            "success": False,
            "message": (
                "Không tìm thấy dữ liệu phù hợp "
                "cho các mã đã nhập."
            ),
            "invalid_symbols": invalid_symbols,
        }

    optimized = optimize_weights(stock_data)

    if not optimized:
        return {
            "success": False,
            "message": (
                "Không thể tính tỷ trọng "
                "cho danh mục."
            ),
            "invalid_symbols": invalid_symbols,
        }

    # Tính số tiền.
    for item in optimized:
        item["amount"] = (
            capital * item["weight"]
        )

    total_weight = sum(
        item["weight"]
        for item in optimized
    )

    total_amount = sum(
        item["amount"]
        for item in optimized
    )

    return {
        "success": True,
        "capital": capital,
        "stocks": optimized,
        "invalid_symbols": invalid_symbols,
        "total_weight": total_weight,
        "total_amount": total_amount,
    }