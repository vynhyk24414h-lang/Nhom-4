# Import pandas để xử lý dữ liệu dạng bảng
import pandas as pd


# =========================================================
# HÀM HỖ TRỢ
# =========================================================

def calculate_wilder_rma(series, period):
    """
    Tính RMA (Wilder's Moving Average) cho một chuỗi dữ liệu.
    RMA được dùng để tính ATR14 và ATR22.
    """
    result = pd.Series(index=series.index, dtype="float64")

    if len(series) < period:
        return result

    # Giá trị RMA đầu tiên là trung bình của period phiên đầu
    first_value = series.iloc[:period].mean()
    result.iloc[period - 1] = first_value
    previous_value = first_value

    # Các giá trị tiếp theo dùng công thức Wilder
    for i in range(period, len(series)):
        current_value = (
            ((period - 1) * previous_value)
            + series.iloc[i]
        ) / period

        result.iloc[i] = current_value
        previous_value = current_value

    return result


def _to_dataframe(data_input, input_name):
    """
    Chấp nhận pandas DataFrame hoặc dữ liệu JSON dạng list/dict.
    FireAnt HistoricalQuotes trả JSON nên hàm này giúp Backtest
    dễ tích hợp với output của các module khác.
    """
    if data_input is None:
        raise ValueError(f"{input_name} chưa được truyền vào Backtest.")

    if isinstance(data_input, pd.DataFrame):
        return data_input.copy()

    if isinstance(data_input, (list, dict)):
        return pd.DataFrame(data_input)

    raise TypeError(
        f"{input_name} phải là pandas DataFrame, list hoặc dict."
    )


def _require_columns(data, required_columns, data_name="Dữ liệu"):
    """Kiểm tra các cột bắt buộc."""
    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{data_name} thiếu các cột bắt buộc: {missing_columns}"
        )


def _calculate_indicators(data):
    """
    Tính các biến mà Backtest cần trực tiếp từ dữ liệu lịch sử FireAnt:
    - avg_gtgd20: GTGD trung bình 20 phiên
    - atr14: ATR14 cho position sizing
    - atr22: ATR22 cho Chandelier Stop
    - chandelier_cs: Highest High 22 - 3 x ATR22
    """
    processed_groups = []

    for symbol, group in data.groupby("Symbol", sort=False):
        group = (
            group
            .sort_values("Date")
            .reset_index(drop=True)
            .copy()
        )

        # FireAnt có cột Value nhưng dữ liệu lịch sử có thể trả 0.
        # Nếu Value không hợp lệ thì dùng Close x Volume làm dự phòng.
        if "Value" in group.columns:
            group["gtgd"] = pd.to_numeric(
                group["Value"],
                errors="coerce"
            ).astype("float64")

            invalid_value = (
                group["gtgd"].isna()
                | (group["gtgd"] <= 0)
            )

            group.loc[
                invalid_value,
                "gtgd"
            ] = (
                group.loc[invalid_value, "Close"]
                * group.loc[invalid_value, "Volume"]
            )
        else:
            group["gtgd"] = (
                group["Close"]
                * group["Volume"]
            )

        group["avg_gtgd20"] = (
            group["gtgd"]
            .rolling(window=20, min_periods=20)
            .mean()
        )

        previous_close = group["Close"].shift(1)

        true_range = pd.concat(
            [
                group["High"] - group["Low"],
                (group["High"] - previous_close).abs(),
                (group["Low"] - previous_close).abs()
            ],
            axis=1
        ).max(axis=1)

        group["atr14"] = calculate_wilder_rma(true_range, 14)
        group["atr22"] = calculate_wilder_rma(true_range, 22)

        highest_high_22 = (
            group["High"]
            .rolling(window=22, min_periods=22)
            .max()
        )

        group["chandelier_cs"] = (
            highest_high_22
            - (3 * group["atr22"])
        )

        processed_groups.append(group)

    if not processed_groups:
        return data.iloc[0:0].copy()

    return pd.concat(processed_groups, ignore_index=True)


def _prepare_data(signal_data):
    """
    Chuẩn bị dữ liệu đầu vào theo đúng cấu trúc FireAnt.

    FireAnt cung cấp:
    Date, Symbol, Open, High, Low, Close, Volume, Value, OpenInt

    Module tính toán cần bổ sung:
    signal, regime
    """
    data = _to_dataframe(signal_data, "signal_data")

    required_columns = [
        "Date",
        "Symbol",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "signal",
        "regime"
    ]

    _require_columns(
        data,
        required_columns,
        data_name="Dữ liệu Backtest"
    )

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce",
        utc=True
    ).dt.tz_convert(None)

    numeric_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "regime"
    ]

    if "Value" in data.columns:
        numeric_columns.append("Value")

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    data = data.dropna(
        subset=[
            "Date",
            "Symbol",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "signal",
            "regime"
        ]
    ).copy()

    data["Symbol"] = (
        data["Symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    data["signal"] = (
        data["signal"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    valid_signals = ["BUY", "HOLD", "SELL"]

    invalid_signals = data.loc[
        ~data["signal"].isin(valid_signals),
        "signal"
    ].unique()

    if len(invalid_signals) > 0:
        raise ValueError(
            "Backtest chỉ nhận BUY, HOLD, SELL. "
            f"Tín hiệu không hợp lệ: {invalid_signals}"
        )

    data = data[
        (data["Open"] > 0)
        & (data["High"] > 0)
        & (data["Low"] > 0)
        & (data["Close"] > 0)
        & (data["Volume"] >= 0)
        & (data["regime"].isin([0, 1, 2]))
    ].copy()

    data = data.drop_duplicates(
        subset=["Date", "Symbol"],
        keep="last"
    )

    data = (
        data
        .sort_values(by=["Symbol", "Date"])
        .reset_index(drop=True)
    )

    if data.empty:
        raise ValueError(
            "Không còn dữ liệu hợp lệ sau khi làm sạch."
        )

    data = _calculate_indicators(data)

    data = data.dropna(
        subset=[
            "atr14",
            "avg_gtgd20",
            "chandelier_cs"
        ]
    ).copy()

    data = data[
        (data["atr14"] > 0)
        & (data["avg_gtgd20"] > 0)
    ].copy()

    if data.empty:
        raise ValueError(
            "Không còn dữ liệu hợp lệ sau khi tính "
            "ATR14, GTGD20 và Chandelier Stop. "
            "Cần ít nhất khoảng 22 phiên dữ liệu cho mỗi mã."
        )

    return data.reset_index(drop=True)


def _build_events(data):
    """
    Tạo sự kiện theo dữ liệu EOD:
    tín hiệu ngày T được thực hiện tại Open phiên T+1.
    """
    events = []

    for symbol, group in data.groupby("Symbol", sort=False):
        group = (
            group
            .sort_values("Date")
            .reset_index(drop=True)
        )

        for i in range(len(group) - 1):
            row = group.iloc[i]
            next_row = group.iloc[i + 1]

            events.append({
                "symbol": symbol,
                "signal": row["signal"],
                "signal_date": row["Date"],
                "execution_date": next_row["Date"],
                "execution_price": next_row["Open"],
                "signal_close": row["Close"],
                "atr14": row["atr14"],
                "avg_gtgd20": row["avg_gtgd20"],
                "regime": int(row["regime"]),
                "chandelier_cs": row["chandelier_cs"]
            })

    return sorted(
        events,
        key=lambda event: (
            event["execution_date"],
            1 if event["signal"] == "BUY" else 0
        )
    )


def _mark_to_market(data, positions, execution_date, cash):
    """Tính giá trị danh mục tại thời điểm chuẩn bị mở vị thế mới."""
    portfolio_equity = cash

    for held_symbol, position in positions.items():
        held_data = data[
            (data["Symbol"] == held_symbol)
            & (data["Date"] < execution_date)
        ]

        if held_data.empty:
            mark_price = position["buy_price"]
        else:
            mark_price = (
                held_data
                .sort_values("Date")
                .iloc[-1]["Close"]
            )

        portfolio_equity += (
            position["shares"]
            * mark_price
        )

    return portfolio_equity


def _build_portfolio_history(
    data,
    trades_df,
    positions,
    initial_capital,
    transaction_fee_rate,
    sell_tax_rate
):
    """Tính equity curve theo từng ngày để đo daily return và drawdown."""
    close_matrix = data.pivot_table(
        index="Date",
        columns="Symbol",
        values="Close",
        aggfunc="last"
    ).sort_index()

    close_matrix = close_matrix.ffill()

    cash_flows = []
    position_records = []

    if not trades_df.empty:
        for _, trade in trades_df.iterrows():
            buy_fee = (
                trade["buy_value"]
                * transaction_fee_rate
            )

            total_buy_cost = (
                trade["buy_value"]
                + buy_fee
            )

            sell_fee = (
                trade["sell_value"]
                * transaction_fee_rate
            )

            sell_tax = (
                trade["sell_value"]
                * sell_tax_rate
            )

            net_sell_proceeds = (
                trade["sell_value"]
                - sell_fee
                - sell_tax
            )

            cash_flows.append({
                "date": trade["buy_date"],
                "cash_flow": -total_buy_cost
            })

            cash_flows.append({
                "date": trade["sell_date"],
                "cash_flow": net_sell_proceeds
            })

            position_records.append({
                "symbol": trade["symbol"],
                "buy_date": trade["buy_date"],
                "sell_date": trade["sell_date"],
                "shares": trade["shares"]
            })

    for symbol, position in positions.items():
        cash_flows.append({
            "date": position["buy_date"],
            "cash_flow": -position["total_buy_cost"]
        })

        position_records.append({
            "symbol": symbol,
            "buy_date": position["buy_date"],
            "sell_date": pd.NaT,
            "shares": position["shares"]
        })

    cash_flow_df = pd.DataFrame(cash_flows)

    if cash_flow_df.empty:
        cash_flow_by_date = {}
    else:
        cash_flow_by_date = (
            cash_flow_df
            .groupby("date")["cash_flow"]
            .sum()
            .to_dict()
        )

    daily_cash = initial_capital
    portfolio_history = []

    for current_date in close_matrix.index:
        daily_cash += cash_flow_by_date.get(
            current_date,
            0
        )

        holdings_value = 0

        for position in position_records:
            is_open = (
                position["buy_date"] <= current_date
                and (
                    pd.isna(position["sell_date"])
                    or current_date < position["sell_date"]
                )
            )

            if not is_open:
                continue

            symbol = position["symbol"]

            if symbol not in close_matrix.columns:
                continue

            close_price = close_matrix.loc[
                current_date,
                symbol
            ]

            if pd.notna(close_price):
                holdings_value += (
                    position["shares"]
                    * close_price
                )

        portfolio_history.append({
            "date": current_date,
            "cash": daily_cash,
            "holdings_value": holdings_value,
            "portfolio_value": daily_cash + holdings_value
        })

    portfolio_history_df = pd.DataFrame(
        portfolio_history
    )

    portfolio_history_df["daily_return_pct"] = (
        portfolio_history_df["portfolio_value"]
        .pct_change()
        .fillna(0)
        * 100
    )

    portfolio_history_df["running_max"] = (
        portfolio_history_df["portfolio_value"]
        .cummax()
    )

    portfolio_history_df["drawdown_pct"] = (
        (
            portfolio_history_df["portfolio_value"]
            / portfolio_history_df["running_max"]
        )
        - 1
    ) * 100

    return portfolio_history_df


def _calculate_benchmark_return(
    data,
    benchmark_input,
    portfolio_return
):
    """
    Tính benchmark từ dữ liệu FireAnt của VNINDEX.
    benchmark_input có thể là DataFrame hoặc JSON list/dict của FireAnt.
    """
    if benchmark_input is None:
        return None, None

    benchmark_data = _to_dataframe(
        benchmark_input,
        "benchmark_input"
    )

    _require_columns(
        benchmark_data,
        ["Date", "Close"],
        data_name="Dữ liệu benchmark"
    )

    benchmark_data["Date"] = pd.to_datetime(
        benchmark_data["Date"],
        errors="coerce",
        utc=True
    ).dt.tz_convert(None)

    benchmark_data["Close"] = pd.to_numeric(
        benchmark_data["Close"],
        errors="coerce"
    )

    benchmark_data = (
        benchmark_data
        .dropna(subset=["Date", "Close"])
        .sort_values("Date")
        .reset_index(drop=True)
    )

    benchmark_period = benchmark_data[
        (benchmark_data["Date"] >= data["Date"].min())
        & (benchmark_data["Date"] <= data["Date"].max())
    ]

    if len(benchmark_period) < 2:
        return None, None

    benchmark_start = benchmark_period.iloc[0]["Close"]
    benchmark_end = benchmark_period.iloc[-1]["Close"]

    if benchmark_start <= 0:
        return None, None

    benchmark_return = (
        (benchmark_end - benchmark_start)
        / benchmark_start
    ) * 100

    excess_return = (
        portfolio_return
        - benchmark_return
    )

    return benchmark_return, excess_return


# =========================================================
# HÀM BACKTEST CHÍNH
# =========================================================

def run_backtest(
    signal_data,
    benchmark_input=None,
    initial_capital=100_000_000,
    max_positions=10,
    lot_size=100,
    risk_per_trade=0.01,
    max_position_pct=0.10,
    max_liquidity_pct=0.05,
    transaction_fee_rate=0.001,
    sell_tax_rate=0.001,
    slippage_rate=0.001
):
    """
    Chạy Backtest theo dữ liệu EOD FireAnt.

    signal_data bắt buộc có:
    Date, Symbol, Open, High, Low, Close, Volume, signal, regime

    Value là cột tùy chọn.
    benchmark_input có thể truyền dữ liệu FireAnt của VNINDEX.
    """

    if initial_capital <= 0:
        raise ValueError(
            "Vốn ban đầu phải lớn hơn 0."
        )

    if max_positions <= 0:
        raise ValueError(
            "Số vị thế tối đa phải lớn hơn 0."
        )

    if lot_size <= 0:
        raise ValueError(
            "Kích thước lô phải lớn hơn 0."
        )

    for parameter_name, parameter_value in {
        "risk_per_trade": risk_per_trade,
        "max_position_pct": max_position_pct,
        "max_liquidity_pct": max_liquidity_pct,
        "transaction_fee_rate": transaction_fee_rate,
        "sell_tax_rate": sell_tax_rate,
        "slippage_rate": slippage_rate
    }.items():
        if parameter_value < 0:
            raise ValueError(
                f"{parameter_name} không được âm."
            )

    if slippage_rate >= 1:
        raise ValueError(
            "slippage_rate phải nhỏ hơn 1."
        )

    data = _prepare_data(
        signal_data
    )

    print(
        f"\nDữ liệu hợp lệ sau khi làm sạch "
        f"và tính chỉ báo: {len(data)} dòng"
    )

    trades = []
    skipped_signals = []

    events = _build_events(
        data
    )

    cash = initial_capital
    positions = {}

    for event in events:
        symbol = event["symbol"]
        signal = event["signal"]
        signal_date = event["signal_date"]
        execution_date = event["execution_date"]
        raw_execution_price = event["execution_price"]
        atr14 = event["atr14"]
        avg_gtgd20 = event["avg_gtgd20"]
        regime = event["regime"]
        signal_close = event["signal_close"]
        chandelier_cs = event["chandelier_cs"]

        stop_triggered = False

        if symbol in positions:
            position = positions[symbol]

            if signal_date >= position["buy_date"]:
                previous_stop = position.get(
                    "trailing_stop"
                )

                if previous_stop is None:
                    position["trailing_stop"] = chandelier_cs
                else:
                    position["trailing_stop"] = max(
                        previous_stop,
                        chandelier_cs
                    )

                if (
                    signal_close
                    < position["trailing_stop"]
                ):
                    stop_triggered = True

        effective_signal = (
            "SELL"
            if stop_triggered
            else signal
        )

        if (
            effective_signal == "SELL"
            and symbol in positions
        ):
            price = (
                raw_execution_price
                * (1 - slippage_rate)
            )

            position = positions[symbol]

            buy_signal_date = position["buy_signal_date"]
            buy_date = position["buy_date"]
            buy_price = position["buy_price"]
            shares = position["shares"]
            buy_value = position["buy_value"]
            buy_fee = position["buy_fee"]
            total_buy_cost = position["total_buy_cost"]

            sell_value = shares * price
            sell_fee = (
                sell_value
                * transaction_fee_rate
            )
            sell_tax = (
                sell_value
                * sell_tax_rate
            )

            net_sell_proceeds = (
                sell_value
                - sell_fee
                - sell_tax
            )

            cash += net_sell_proceeds

            gross_return_pct = (
                (price - buy_price)
                / buy_price
            ) * 100

            net_profit = (
                net_sell_proceeds
                - total_buy_cost
            )

            return_pct = (
                net_profit
                / total_buy_cost
            ) * 100

            transaction_cost = (
                buy_fee
                + sell_fee
                + sell_tax
            )

            sell_reason = (
                "CHANDELIER_STOP"
                if stop_triggered
                else "SIGNAL"
            )

            trades.append({
                "symbol": symbol,
                "buy_signal_date": buy_signal_date,
                "buy_date": buy_date,
                "buy_price": buy_price,
                "shares": shares,
                "buy_value": buy_value,
                "sell_signal_date": signal_date,
                "sell_date": execution_date,
                "sell_price": price,
                "sell_value": sell_value,
                "sell_reason": sell_reason,
                "gross_return_pct": gross_return_pct,
                "transaction_cost": transaction_cost,
                "net_profit": net_profit,
                "return_pct": return_pct
            })

            print(
                f"SELL {symbol} | tín hiệu "
                f"{signal_date.date()} -> "
                f"bán {shares:,} cp ngày "
                f"{execution_date.date()} "
                f"tại {price:,.0f} | "
                f"Lợi nhuận ròng {return_pct:.2f}% | "
                f"Lý do: {sell_reason}"
            )

            del positions[symbol]

        elif (
            effective_signal == "BUY"
            and symbol not in positions
        ):
            if len(positions) >= max_positions:
                skipped_signals.append({
                    "symbol": symbol,
                    "signal": signal,
                    "signal_date": signal_date,
                    "execution_date": execution_date,
                    "reason": "Đã đạt số vị thế tối đa"
                })
                continue

            if regime == 0:
                skipped_signals.append({
                    "symbol": symbol,
                    "signal": signal,
                    "signal_date": signal_date,
                    "execution_date": execution_date,
                    "reason": "Regime = 0, không mở vị thế mới"
                })
                continue

            price = (
                raw_execution_price
                * (1 + slippage_rate)
            )

            portfolio_equity = _mark_to_market(
                data,
                positions,
                execution_date,
                cash
            )

            stop_distance = (
                3 * atr14
            )

            if stop_distance <= 0:
                skipped_signals.append({
                    "symbol": symbol,
                    "signal": signal,
                    "signal_date": signal_date,
                    "execution_date": execution_date,
                    "reason": "ATR14 không hợp lệ"
                })
                continue

            risk_budget = (
                risk_per_trade
                * portfolio_equity
            )

            shares_by_risk = (
                risk_budget
                / stop_distance
            )

            if regime == 1:
                shares_by_risk *= 0.5

            shares_by_capital = (
                max_position_pct
                * portfolio_equity
                / price
            )

            shares_by_liquidity = (
                max_liquidity_pct
                * avg_gtgd20
                / price
            )

            shares_by_cash = (
                cash
                / (
                    price
                    * (1 + transaction_fee_rate)
                )
            )

            raw_shares = min(
                shares_by_risk,
                shares_by_capital,
                shares_by_liquidity,
                shares_by_cash
            )

            shares = (
                int(raw_shares // lot_size)
                * lot_size
            )

            if shares <= 0:
                skipped_signals.append({
                    "symbol": symbol,
                    "signal": signal,
                    "signal_date": signal_date,
                    "execution_date": execution_date,
                    "reason": "Không đủ điều kiện mua tối thiểu 1 lô"
                })
                continue

            buy_value = (
                shares
                * price
            )

            buy_fee = (
                buy_value
                * transaction_fee_rate
            )

            total_buy_cost = (
                buy_value
                + buy_fee
            )

            if total_buy_cost > cash:
                skipped_signals.append({
                    "symbol": symbol,
                    "signal": signal,
                    "signal_date": signal_date,
                    "execution_date": execution_date,
                    "reason": "Không đủ tiền mặt sau phí mua"
                })
                continue

            cash -= total_buy_cost

            positions[symbol] = {
                "buy_signal_date": signal_date,
                "buy_date": execution_date,
                "buy_price": price,
                "shares": shares,
                "buy_value": buy_value,
                "buy_fee": buy_fee,
                "total_buy_cost": total_buy_cost,
                "trailing_stop": None
            }

            print(
                f"BUY {symbol} | tín hiệu "
                f"{signal_date.date()} -> "
                f"mua {shares:,} cp ngày "
                f"{execution_date.date()} "
                f"tại {price:,.0f} | "
                f"Tiền mặt còn {cash:,.0f}"
            )

    skipped_df = pd.DataFrame(
        skipped_signals
    )

    if not skipped_df.empty:
        skipped_df.to_csv(
            "skipped_signals.csv",
            index=False,
            encoding="utf-8-sig"
        )

        print(
            "\nĐã xuất skipped_signals.csv"
        )

    trades_df = pd.DataFrame(
        trades
    )

    print(
        "\nKẾT QUẢ BACKTEST:"
    )

    if trades_df.empty:
        print(
            "Chưa có giao dịch nào hoàn thành."
        )
    else:
        print(
            trades_df.to_string(
                index=False
            )
        )

        trades_df.to_csv(
            "trades.csv",
            index=False,
            encoding="utf-8-sig",
            float_format="%.2f"
        )

        print(
            "\nĐã xuất trades.csv"
        )

    open_positions_value = 0

    for symbol, position in positions.items():
        symbol_data = data[
            data["Symbol"] == symbol
        ].sort_values("Date")

        last_close = (
            symbol_data
            .iloc[-1]["Close"]
        )

        open_positions_value += (
            position["shares"]
            * last_close
        )

    final_portfolio_value = (
        cash
        + open_positions_value
    )

    net_profit_portfolio = (
        final_portfolio_value
        - initial_capital
    )

    portfolio_return = (
        net_profit_portfolio
        / initial_capital
    ) * 100

    (
        benchmark_return,
        excess_return
    ) = _calculate_benchmark_return(
        data,
        benchmark_input,
        portfolio_return
    )

    if trades_df.empty:
        number_of_trades = 0
        winning_trades = 0
        losing_trades = 0
        win_rate = 0
        average_return = 0
        best_trade = 0
        worst_trade = 0
        profit_factor = None
        total_transaction_cost = 0
    else:
        number_of_trades = len(
            trades_df
        )

        winning_trades = (
            trades_df["net_profit"] > 0
        ).sum()

        losing_trades = (
            trades_df["net_profit"] < 0
        ).sum()

        win_rate = (
            winning_trades
            / number_of_trades
        ) * 100

        average_return = (
            trades_df["return_pct"]
            .mean()
        )

        best_trade = (
            trades_df["return_pct"]
            .max()
        )

        worst_trade = (
            trades_df["return_pct"]
            .min()
        )

        gross_profit = trades_df.loc[
            trades_df["net_profit"] > 0,
            "net_profit"
        ].sum()

        gross_loss = abs(
            trades_df.loc[
                trades_df["net_profit"] < 0,
                "net_profit"
            ].sum()
        )

        if gross_loss > 0:
            profit_factor = (
                gross_profit
                / gross_loss
            )
        else:
            profit_factor = None

        total_transaction_cost = (
            trades_df[
                "transaction_cost"
            ].sum()
        )

    portfolio_history_df = (
        _build_portfolio_history(
            data,
            trades_df,
            positions,
            initial_capital,
            transaction_fee_rate,
            sell_tax_rate
        )
    )

    max_drawdown = abs(
        portfolio_history_df[
            "drawdown_pct"
        ].min()
    )

    portfolio_history_df.to_csv(
        "portfolio_history.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.2f"
    )

    print(
        "\nĐã xuất portfolio_history.csv"
    )

    print(
        "\nTỔNG HỢP KẾT QUẢ BACKTEST:"
    )

    print(
        f"Vốn ban đầu: "
        f"{initial_capital:,.0f} VNĐ"
    )

    print(
        f"Giá trị danh mục cuối kỳ: "
        f"{final_portfolio_value:,.0f} VNĐ"
    )

    print(
        f"Lợi nhuận ròng danh mục: "
        f"{net_profit_portfolio:,.0f} VNĐ"
    )

    print(
        f"Tỷ suất lợi nhuận danh mục: "
        f"{portfolio_return:.2f}%"
    )

    if benchmark_return is None:
        print(
            "Benchmark VNINDEX: "
            "Chưa có dữ liệu"
        )
    else:
        print(
            f"Lợi nhuận VNINDEX: "
            f"{benchmark_return:.2f}%"
        )

        print(
            f"Chênh lệch so với VNINDEX: "
            f"{excess_return:.2f}%"
        )

    print(
        f"Tiền mặt cuối kỳ: "
        f"{cash:,.0f} VNĐ"
    )

    print(
        f"Số vị thế còn mở: "
        f"{len(positions)}"
    )

    print(
        f"Số giao dịch: "
        f"{number_of_trades}"
    )

    print(
        f"Số giao dịch thắng: "
        f"{winning_trades}"
    )

    print(
        f"Số giao dịch thua: "
        f"{losing_trades}"
    )

    print(
        f"Tỷ lệ thắng: "
        f"{win_rate:.2f}%"
    )

    print(
        f"Lợi nhuận trung bình/giao dịch: "
        f"{average_return:.2f}%"
    )

    print(
        f"Giao dịch tốt nhất: "
        f"{best_trade:.2f}%"
    )

    print(
        f"Giao dịch tệ nhất: "
        f"{worst_trade:.2f}%"
    )

    if profit_factor is None:
        print(
            "Profit Factor: N/A"
        )
    else:
        print(
            f"Profit Factor: "
            f"{profit_factor:.2f}"
        )

    print(
        f"Maximum Drawdown: "
        f"{max_drawdown:.2f}%"
    )

    print(
        f"Tổng phí giao dịch và thuế: "
        f"{total_transaction_cost:,.0f} VNĐ"
    )

    summary_df = pd.DataFrame({
        "metric": [
            "Initial Capital (VND)",
            "Final Portfolio Value (VND)",
            "Net Profit (VND)",
            "Portfolio Return (%)",
            "Cash Remaining (VND)",
            "Open Positions",
            "Number of Trades",
            "Winning Trades",
            "Losing Trades",
            "Win Rate (%)",
            "Average Return per Trade (%)",
            "Best Trade (%)",
            "Worst Trade (%)",
            "Profit Factor",
            "Maximum Drawdown (%)",
            "VNINDEX Return (%)",
            "Excess Return vs VNINDEX (%)",
            "Fees and Sell Tax (VND)"
        ],

        "value": [
            initial_capital,
            final_portfolio_value,
            net_profit_portfolio,
            portfolio_return,
            cash,
            len(positions),
            number_of_trades,
            winning_trades,
            losing_trades,
            win_rate,
            average_return,
            best_trade,
            worst_trade,
            profit_factor,
            max_drawdown,
            benchmark_return,
            excess_return,
            total_transaction_cost
        ]
    })

    summary_df.to_csv(
        "backtest_summary.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.2f"
    )

    print(
        "\nĐã xuất backtest_summary.csv"
    )

    return {
        "trades": trades_df,
        "summary": summary_df,
        "portfolio_history": portfolio_history_df,
        "skipped_signals": skipped_df,
        "final_portfolio_value": final_portfolio_value,
        "portfolio_return": portfolio_return,
        "max_drawdown": max_drawdown,
        "benchmark_return": benchmark_return,
        "excess_return": excess_return
    }
