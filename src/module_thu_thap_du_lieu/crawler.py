import requests
import pandas as pd


BASE_URL = "https://www.fireant.vn/api/Data/Markets"


def get_historical_data(symbol, start_date, end_date):
    url = f"{BASE_URL}/HistoricalQuotes"

    params = {
        "symbol": symbol,
        "startDate": start_date,
        "endDate": end_date
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    return df


def get_intraday_data(symbol):
    url = f"{BASE_URL}/IntradayQuotes"

    params = {
        "symbol": symbol
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    return df


def get_multiple_stocks(
    symbols,
    start_date,
    end_date
):
    """
    Tự động lấy dữ liệu lịch sử
    từ FireAnt cho nhiều mã.
    """

    all_data = []

    for symbol in symbols:

        symbol = str(symbol).strip().upper()

        try:
            print(f"Đang lấy dữ liệu: {symbol}")

            df = get_historical_data(
                symbol,
                start_date,
                end_date
            )

            if not df.empty:
                all_data.append(df)

        except Exception as e:
            print(
                f"Lỗi khi lấy {symbol}: {e}"
            )

    if not all_data:
        return pd.DataFrame()

    result = pd.concat(
        all_data,
        ignore_index=True
    )

    return result