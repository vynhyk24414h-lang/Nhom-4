# Import pandas để đọc và xử lý dữ liệu dạng bảng
import pandas as pd


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
    # =========================================================
    # CẤU HÌNH FILE DỮ LIỆU
    # =========================================================

    # =========================================================
    # CẤU HÌNH NGUỒN DỮ LIỆU BACKTEST
    # =========================================================

    # Kiểm tra các tham số cấu hình Backtest
    if initial_capital <= 0:
        raise ValueError("Vốn ban đầu phải lớn hơn 0.")

    if max_positions <= 0:
        raise ValueError("Số vị thế tối đa phải lớn hơn 0.")

    if lot_size <= 0:
        raise ValueError("Kích thước lô phải lớn hơn 0.")


    # =========================================================
    # NHẬN DỮ LIỆU ĐẦU VÀO
    # =========================================================

    # Backtest nhận dữ liệu tín hiệu trực tiếp từ
    # Module tính toán, xử lý dữ liệu
    if signal_data is None:
        raise ValueError(
            "Backtest chưa nhận được dữ liệu tín hiệu từ "
            "Module tính toán, xử lý dữ liệu."
        )

    data = signal_data.copy()


    # =========================================================
    # KIỂM TRA VÀ LÀM SẠCH DỮ LIỆU ĐẦU VÀO
    # =========================================================

    # Danh sách các cột bắt buộc phải có để Backtest hoạt động
    required_columns = [
        "date",
        "ticker",
        "open",
        "close",
        "signal",
        "atr14",
        "avg_gtgd20",
        "regime",
        "chandelier_cs"
    ]
    # Kiểm tra xem dữ liệu có thiếu cột bắt buộc hay không
    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]


    # Nếu thiếu cột bắt buộc thì dừng chương trình và báo lỗi rõ ràng
    if missing_columns:
        raise ValueError(
            f"Dữ liệu thiếu các cột bắt buộc: {missing_columns}"
        )

    # =========================================================
    # CHUẨN HÓA KIỂU DỮ LIỆU
    # =========================================================

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce"
    )

    data["open"] = pd.to_numeric(
        data["open"],
        errors="coerce"
    )

    data["close"] = pd.to_numeric(
        data["close"],
        errors="coerce"
    )

    data["atr14"] = pd.to_numeric(
        data["atr14"],
        errors="coerce"
    )

    data["avg_gtgd20"] = pd.to_numeric(
        data["avg_gtgd20"],
        errors="coerce"
    )

    data["regime"] = pd.to_numeric(
        data["regime"],
        errors="coerce"
    )

    data["chandelier_cs"] = pd.to_numeric(
        data["chandelier_cs"],
        errors="coerce"
    )
    # Loại bỏ dữ liệu thiếu trước khi chuẩn hóa chuỗi
    data = data.dropna(
        subset=[
            "date",
            "ticker",
            "open",
            "close",
            "signal",
            "atr14",
            "avg_gtgd20",
            "regime",
            "chandelier_cs"
        ]
    )
    # Chuẩn hóa mã cổ phiếu
    data["ticker"] = (
        data["ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
    )


    # Chuẩn hóa tín hiệu BUY / HOLD / SELL
    data["signal"] = (
        data["signal"]
        .astype(str)
        .str.strip()
        .str.upper()
    )


    # Chỉ giữ lại các tín hiệu hợp lệ
    valid_signals = [
        "BUY",
        "HOLD",
        "SELL"
    ]


    # Kiểm tra tín hiệu đầu vào
    invalid_signals = data.loc[
        ~data["signal"].isin(valid_signals),
        "signal"
    ].unique()

    if len(invalid_signals) > 0:
        raise ValueError(
            "Backtest chỉ nhận BUY, HOLD, SELL. "
            f"Tín hiệu không hợp lệ: {invalid_signals}"
        )


    # Loại bỏ các dòng có giá Open hoặc Close không hợp lệ
    data = data[
        (data["open"] > 0)
        & (data["close"] > 0)
    ].copy()


    # Loại bỏ dữ liệu trùng theo mã cổ phiếu và ngày
    data = data.drop_duplicates(
        subset=[
            "date",
            "ticker"
        ],
        keep="last"
    )


    # Sắp xếp dữ liệu theo mã cổ phiếu và thời gian
    data = data.sort_values(
        by=[
            "ticker",
            "date"
        ]
    ).reset_index(drop=True)


    # Kiểm tra xem sau khi làm sạch còn dữ liệu hay không
    if data.empty:
        raise ValueError(
            "Không còn dữ liệu hợp lệ sau khi làm sạch."
        )
# Kiểm tra dữ liệu phục vụ quản trị vị thế
    data = data[
        (data["atr14"] > 0)
        & (data["avg_gtgd20"] > 0)
        & (data["regime"].isin([0, 1, 2]))
    ].copy()

    if data.empty:
        raise ValueError(
        "Không còn dữ liệu hợp lệ sau khi kiểm tra "
        "ATR14, thanh khoản và Regime."
    )

    # Thông báo số dòng dữ liệu hợp lệ
    print(
        f"\nDữ liệu hợp lệ sau khi làm sạch: "
        f"{len(data)} dòng"
    )


    # Hiển thị dữ liệu để kiểm tra
    print(data)

    # Tạo danh sách để lưu các giao dịch đã hoàn thành
    trades = []


    # Tạo danh sách các lệnh sẽ được thực hiện tại phiên T+1
    events = []


    # Tạo các sự kiện BUY/SELL từ tín hiệu của từng mã cổ phiếu
    for ticker, group in data.groupby("ticker"):

        # Sắp xếp dữ liệu theo thời gian
        group = group.sort_values(by="date").reset_index(drop=True)

        # Không xét phiên cuối vì không còn phiên T+1 để khớp lệnh
        for i in range(len(group) - 1):

            row = group.iloc[i]
            next_row = group.iloc[i + 1]

            signal = row["signal"]

            # Tạo sự kiện cho mọi trạng thái BUY / HOLD / SELL
# để Backtest có thể cập nhật Chandelier Stop mỗi phiên
            events.append({
                "ticker": ticker,
                "signal": signal,
                "signal_date": row["date"],
                "execution_date": next_row["date"],
                "execution_price": next_row["open"],
                "signal_close": row["close"],
                "atr14": row["atr14"],
                "avg_gtgd20": row["avg_gtgd20"],
                "regime": int(row["regime"]),
                "chandelier_cs": row["chandelier_cs"]
            })


    # BUY xử lý sau để các lệnh SELL / Chandelier Stop
# giải phóng tiền mặt trước
    events = sorted(
        events,
        key=lambda x: (
            x["execution_date"],
            1 if x["signal"] == "BUY" else 0
        )
    )

    # Khởi tạo lượng tiền mặt ban đầu
    cash = initial_capital


    # Dictionary lưu các cổ phiếu đang nắm giữ
    positions = {}

    # Tạo danh sách để lưu các tín hiệu không được thực hiện
    skipped_signals = []

    # Duyệt lần lượt từng sự kiện theo thời gian
    for event in events:

        ticker = event["ticker"]
        signal = event["signal"]
        signal_date = event["signal_date"]
        execution_date = event["execution_date"]

        raw_execution_price = event["execution_price"]

        atr14 = event["atr14"]
        avg_gtgd20 = event["avg_gtgd20"]
        regime = event["regime"]
        signal_close = event["signal_close"]
        chandelier_cs = event["chandelier_cs"]


# =========================================================
# CẬP NHẬT CHANDELIER TRAILING STOP
# =========================================================

        stop_triggered = False

# Chỉ cập nhật Stop nếu đang nắm giữ cổ phiếu
        if ticker in positions:

            position = positions[ticker]

    # Chỉ bắt đầu cập nhật từ ngày đã mua trở đi
            if signal_date >= position["buy_date"]:

                previous_stop = position.get(
                    "trailing_stop"
                )

        # Ngày đầu tiên sau khi có vị thế:
        # khởi tạo Stop bằng Chandelier Stop hiện tại
                if previous_stop is None:
                    position["trailing_stop"] = chandelier_cs

        # Các ngày sau Stop chỉ được tăng, không được giảm
                else:
                    position["trailing_stop"] = max(
                        previous_stop,
                        chandelier_cs
                    )

        # Nếu Close thủng Stop → phát sinh SELL
                if (
                    signal_close
                    < position["trailing_stop"]
                ):
                    stop_triggered = True


# Chandelier Stop có quyền tạo SELL
# ngay cả khi processor đang trả HOLD
        effective_signal = (
            "SELL"
            if stop_triggered
            else signal
        )
        # =========================================================
        # XỬ LÝ LỆNH BÁN
        # =========================================================
        if effective_signal == "SELL" and ticker in positions:
            # Khi bán giả định bị trượt giá xuống
            price = raw_execution_price * (
                1 - slippage_rate
            )

            # Lấy thông tin vị thế đang nắm giữ
            position = positions[ticker]

            buy_signal_date = position["buy_signal_date"]
            buy_date = position["buy_date"]
            buy_price = position["buy_price"]
            shares = position["shares"]
            buy_value = position["buy_value"]
            buy_fee = position["buy_fee"]
            total_buy_cost = position["total_buy_cost"]


            # Tính tổng giá trị bán
            sell_value = shares * price

            # Tính phí giao dịch khi bán
            sell_fee = sell_value * transaction_fee_rate

            # Tính thuế khi bán
            sell_tax = sell_value * sell_tax_rate

            # Tính số tiền thực nhận sau phí và thuế
            net_sell_proceeds = (
                sell_value
                - sell_fee
                - sell_tax
            )

            # Cộng tiền bán cổ phiếu trở lại tiền mặt
            cash += net_sell_proceeds


            # Tính lợi nhuận gộp
            gross_return_pct = (
                (price - buy_price)
                / buy_price
            ) * 100


            # Tính lợi nhuận ròng bằng tiền
            net_profit = (
                net_sell_proceeds
                - total_buy_cost
            )


            # Tính tỷ suất lợi nhuận ròng
            return_pct = (
                net_profit
                / total_buy_cost
            ) * 100


            # Tổng phí và thuế của giao dịch
            transaction_cost = (
                buy_fee
                + sell_fee
                + sell_tax
            )


            # Lưu kết quả giao dịch
            trades.append({
                "ticker": ticker,
                "buy_signal_date": buy_signal_date,
                "buy_date": buy_date,
                "buy_price": buy_price,
                "shares": shares,
                "buy_value": buy_value,
                "sell_signal_date": signal_date,
                "sell_date": execution_date,
                "sell_price": price,
                "sell_value": sell_value,
                "gross_return_pct": gross_return_pct,
                "transaction_cost": transaction_cost,
                "net_profit": net_profit,
                "return_pct": return_pct
            })


            print(
                f"TÍN HIỆU BÁN {ticker} ngày {signal_date.date()} "
                f"→ BÁN {shares:,} cp ngày {execution_date.date()} "
                f"tại giá Open {price:,.0f} "
                f"| LN ròng: {return_pct:.2f}%"
            )


            # Xóa vị thế sau khi bán
            del positions[ticker]


        # =========================================================
        # XỬ LÝ LỆNH MUA
        # =========================================================
        elif effective_signal == "BUY" and ticker not in positions:

            # Chỉ mua nếu chưa vượt quá số vị thế tối đa
            if len(positions) < max_positions:

                # Giá mua có tính trượt giá
                price = raw_execution_price * (
                    1 + slippage_rate
                )


                # Regime = 0 theo chiến lược không được mở vị thế mới
                if regime == 0:

                    skipped_signals.append({
                        "ticker": ticker,
                        "signal": signal,
                        "signal_date": signal_date,
                        "execution_date": execution_date,
                        "reason": "Regime = 0, không mở vị thế mới"
                    })

                    continue


                # =========================================================
                # XÁC ĐỊNH GIÁ TRỊ DANH MỤC HIỆN TẠI
                # =========================================================

                portfolio_equity = cash

                for held_ticker, position in positions.items():

                    held_data = data[
                        (data["ticker"] == held_ticker)
                        & (data["date"] < execution_date)
                    ]

                    if not held_data.empty:

                        mark_price = (
                            held_data
                            .sort_values("date")
                            .iloc[-1]["close"]
                        )

                    else:

                        mark_price = position["buy_price"]


                    portfolio_equity += (
                        position["shares"]
                        * mark_price
                    )


                # =========================================================
                # QUẢN TRỊ RỦI RO THEO CHIẾN LƯỢC MỚI
                # =========================================================

                # Khoảng cách stop ban đầu xấp xỉ 3 ATR
                stop_distance = 3 * atr14


                # Rủi ro tối đa 1% vốn cho mỗi lệnh
                risk_budget = (
                    risk_per_trade
                    * portfolio_equity
                )


                # Số cổ phiếu tối đa theo rủi ro
                shares_by_risk = (
                    risk_budget
                    / stop_distance
                )


                # Tối đa 10% vốn cho mỗi mã
                max_position_value = (
                    max_position_pct
                    * portfolio_equity
                )

                shares_by_capital = (
                    max_position_value
                    / price
                )


                # Vị thế không vượt quá 5% GTGD trung bình 20 phiên
                max_liquidity_value = (
                    max_liquidity_pct
                    * avg_gtgd20
                )

                shares_by_liquidity = (
                    max_liquidity_value
                    / price
                )


                # Giới hạn theo lượng tiền mặt hiện có
                shares_by_cash = (
                    cash
                    / (
                        price
                        * (1 + transaction_fee_rate)
                    )
                )


                # Regime = 1 chỉ sử dụng 50% quy mô theo rủi ro
                if regime == 1:
                    shares_by_risk *= 0.5

# Chọn giới hạn chặt nhất
                raw_shares = min(
                    shares_by_risk,
                    shares_by_capital,
                    shares_by_liquidity,
                    shares_by_cash
                )


                # Làm tròn xuống theo lô 100 cổ phiếu
                shares = (
                    int(raw_shares // lot_size)
                    * lot_size
                )

                # Chỉ mua nếu đủ tiền mua ít nhất 1 lô
                if shares > 0:

                    # Giá trị mua cổ phiếu
                    buy_value = shares * price

                    # Phí mua
                    buy_fee = (
                        buy_value
                        * transaction_fee_rate
                    )

                    # Tổng số tiền thực chi
                    total_buy_cost = (
                        buy_value
                        + buy_fee
                    )


                    # Trừ tiền mua khỏi tiền mặt
                    cash -= total_buy_cost


                    # Lưu thông tin vị thế
                    positions[ticker] = {
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
                        f"TÍN HIỆU MUA {ticker} ngày {signal_date.date()} "
                        f"→ MUA {shares:,} cp ngày {execution_date.date()} "
                        f"tại giá Open {price:,.0f} "
                        f"| Tiền mặt còn lại: {cash:,.0f}"
                    )
                else:
                    # Ghi nhận trường hợp không đủ tiền mua tối thiểu 1 lô
                    skipped_signals.append({
                        "ticker": ticker,
                        "signal": signal,
                        "signal_date": signal_date,
                        "execution_date": execution_date,
                        "reason": "Không đủ tiền mua tối thiểu 1 lô"
                    })
            else:
                # Ghi nhận trường hợp không thể mua vì đã đủ số vị thế tối đa
                skipped_signals.append({
                    "ticker": ticker,
                    "signal": signal,
                    "signal_date": signal_date,
                    "execution_date": execution_date,
                    "reason": "Đã đạt số vị thế tối đa"
                })


    # Chuyển các tín hiệu bị bỏ qua thành DataFrame
    skipped_df = pd.DataFrame(skipped_signals)


    # Nếu có tín hiệu bị bỏ qua thì xuất ra file CSV
    if not skipped_df.empty:

        skipped_df.to_csv(
            "skipped_signals.csv",
            index=False,
            encoding="utf-8-sig"
        )

        print(
            "\nĐã xuất các tín hiệu không được thực hiện "
            "ra file skipped_signals.csv"
        )

    # Chuyển danh sách giao dịch thành DataFrame
    trades_df = pd.DataFrame(trades)


    # =========================================================
    # HIỂN THỊ VÀ XUẤT CHI TIẾT GIAO DỊCH
    # =========================================================

    print("\nKẾT QUẢ BACKTEST:")

    # Kiểm tra xem có giao dịch hoàn thành hay không
    if not trades_df.empty:

        # Hiển thị đầy đủ các giao dịch
        print(trades_df.to_string(index=False))

        # Xuất chi tiết giao dịch ra file CSV
        trades_df.to_csv(
            "trades.csv",
            index=False,
            encoding="utf-8-sig",
            float_format="%.2f"
        )

        print("\nĐã xuất kết quả giao dịch ra file trades.csv")

    else:
        print("Chưa có giao dịch nào hoàn thành.")


    # =========================================================
    # TÍNH GIÁ TRỊ CUỐI KỲ CỦA CÁC VỊ THẾ CÒN ĐANG NẮM GIỮ
    # =========================================================

    open_positions_value = 0


    # Duyệt qua các cổ phiếu vẫn còn trong danh mục
    for ticker, position in positions.items():

        # Lọc dữ liệu của từng mã cổ phiếu
        ticker_data = data[
            data["ticker"] == ticker
        ].sort_values(by="date")

        # Lấy giá đóng cửa cuối cùng của mã cổ phiếu
        last_close = ticker_data.iloc[-1]["close"]

        # Tính giá trị thị trường của vị thế còn đang nắm giữ
        market_value = (
            position["shares"]
            * last_close
        )

        # Cộng vào tổng giá trị các vị thế mở
        open_positions_value += market_value


    # =========================================================
    # TÍNH HIỆU QUẢ TOÀN DANH MỤC
    # =========================================================

    # Giá trị cuối cùng của danh mục
    # Bao gồm tiền mặt và giá trị các cổ phiếu còn đang nắm giữ
    final_portfolio_value = (
        cash
        + open_positions_value
    )


    # Tính lợi nhuận ròng của toàn danh mục bằng VNĐ
    net_profit_portfolio = (
        final_portfolio_value
        - initial_capital
    )


    # Tính tỷ suất lợi nhuận của toàn danh mục
    portfolio_return = (
        net_profit_portfolio
        / initial_capital
    ) * 100

    # =========================================================
    # TÍNH BENCHMARK VNINDEX
    # =========================================================

    # Gán giá trị mặc định nếu chưa có dữ liệu VNINDEX
    benchmark_return = None
    excess_return = None


    # =========================================================
    # NHẬN DỮ LIỆU BENCHMARK VNINDEX
    # =========================================================

    benchmark_data = None


  
    # VNINDEX được Data module truyền trực tiếp sang
    if benchmark_input is not None:

        benchmark_data = benchmark_input.copy()



    if benchmark_data is not None:
        # Chuyển cột ngày sang định dạng ngày tháng
        benchmark_data["date"] = pd.to_datetime(
            benchmark_data["date"]
        )

        # Loại bỏ các dòng thiếu dữ liệu quan trọng
        benchmark_data = benchmark_data.dropna(
            subset=["date", "close"]
        )

        # Sắp xếp dữ liệu theo thời gian
        benchmark_data = benchmark_data.sort_values(
            by="date"
        ).reset_index(drop=True)

        # Xác định khoảng thời gian Backtest
        backtest_start_date = data["date"].min()
        backtest_end_date = data["date"].max()

        # Chỉ giữ VNINDEX trong đúng khoảng thời gian Backtest
        benchmark_period = benchmark_data[
            (benchmark_data["date"] >= backtest_start_date)
            & (benchmark_data["date"] <= backtest_end_date)
        ].copy()

        # Chỉ tính nếu có đủ dữ liệu benchmark
        if len(benchmark_period) >= 2:

            # Lấy VNINDEX đầu kỳ
            benchmark_start = (
                benchmark_period.iloc[0]["close"]
            )

            # Lấy VNINDEX cuối kỳ
            benchmark_end = (
                benchmark_period.iloc[-1]["close"]
            )

            # Tính lợi nhuận VNINDEX
            benchmark_return = (
                (benchmark_end - benchmark_start)
                / benchmark_start
            ) * 100

            # Tính mức vượt trội của chiến lược so với VNINDEX
            excess_return = (
                portfolio_return
                - benchmark_return
            )
    # =========================================================
    # TÍNH CÁC CHỈ TIÊU GIAO DỊCH
    # =========================================================

    if not trades_df.empty:

        # Tổng số giao dịch đã hoàn thành
        number_of_trades = len(trades_df)

        # Số giao dịch thắng
        winning_trades = (
            trades_df["net_profit"] > 0
        ).sum()

        # Số giao dịch thua
        losing_trades = (
            trades_df["net_profit"] < 0
        ).sum()

        # Tỷ lệ thắng
        win_rate = (
            winning_trades
            / number_of_trades
        ) * 100

        # Lợi nhuận trung bình mỗi giao dịch
        average_return = (
            trades_df["return_pct"].mean()
        )

        # Giao dịch tốt nhất
        best_trade = (
            trades_df["return_pct"].max()
        )

        # Giao dịch tệ nhất
        worst_trade = (
            trades_df["return_pct"].min()
        )


        # Tổng lợi nhuận bằng tiền của các giao dịch thắng
        gross_profit = trades_df.loc[
            trades_df["net_profit"] > 0,
            "net_profit"
        ].sum()


        # Tổng mức lỗ tuyệt đối của các giao dịch thua
        gross_loss = abs(
            trades_df.loc[
                trades_df["net_profit"] < 0,
                "net_profit"
            ].sum()
        )


        # Tính Profit Factor
        if gross_loss > 0:
            profit_factor = (
                gross_profit
                / gross_loss
            )
        else:
            profit_factor = None


        # Tổng phí giao dịch và thuế
        total_transaction_cost = (
            trades_df["transaction_cost"].sum()
        )



    else:

        # Gán giá trị mặc định nếu không có giao dịch
        number_of_trades = 0
        winning_trades = 0
        losing_trades = 0
        win_rate = 0
        average_return = 0
        best_trade = 0
        worst_trade = 0
        profit_factor = None
        total_transaction_cost = 0

    # =========================================================
    # TÍNH GIÁ TRỊ DANH MỤC VÀ DRAWDOWN THEO TỪNG NGÀY
    # =========================================================

    # Tạo bảng giá Close của từng mã theo từng ngày
    close_matrix = data.pivot_table(
        index="date",
        columns="ticker",
        values="close",
        aggfunc="last"
    ).sort_index()


    # Nếu một mã không có giá ở một ngày nào đó,
    # sử dụng giá Close gần nhất trước đó
    close_matrix = close_matrix.ffill()


    # Danh sách lưu các dòng tiền phát sinh
    cash_flows = []


    # Danh sách lưu thời gian nắm giữ từng vị thế
    position_records = []


    # =========================================================
    # GHI NHẬN CÁC GIAO DỊCH ĐÃ HOÀN THÀNH
    # =========================================================

    if not trades_df.empty:

        for _, trade in trades_df.iterrows():

            # Tính phí mua
            buy_fee = (
                trade["buy_value"]
                * transaction_fee_rate
            )

            # Tổng tiền thực chi khi mua
            total_buy_cost = (
                trade["buy_value"]
                + buy_fee
            )


            # Tính phí bán
            sell_fee = (
                trade["sell_value"]
                * transaction_fee_rate
            )

            # Tính thuế bán
            sell_tax = (
                trade["sell_value"]
                * sell_tax_rate
            )

            # Số tiền thực nhận khi bán
            net_sell_proceeds = (
                trade["sell_value"]
                - sell_fee
                - sell_tax
            )


            # Ghi nhận dòng tiền mua
            cash_flows.append({
                "date": trade["buy_date"],
                "cash_flow": -total_buy_cost
            })


            # Ghi nhận dòng tiền bán
            cash_flows.append({
                "date": trade["sell_date"],
                "cash_flow": net_sell_proceeds
            })


            # Lưu khoảng thời gian nắm giữ
            position_records.append({
                "ticker": trade["ticker"],
                "buy_date": trade["buy_date"],
                "sell_date": trade["sell_date"],
                "shares": trade["shares"]
            })


    # =========================================================
    # GHI NHẬN CÁC VỊ THẾ CÒN MỞ CUỐI KỲ
    # =========================================================

    for ticker, position in positions.items():

        # Dòng tiền phát sinh khi mua
        cash_flows.append({
            "date": position["buy_date"],
            "cash_flow": -position["total_buy_cost"]
        })


        # Vị thế chưa có ngày bán
        position_records.append({
            "ticker": ticker,
            "buy_date": position["buy_date"],
            "sell_date": pd.NaT,
            "shares": position["shares"]
        })


    # =========================================================
    # TỔNG HỢP DÒNG TIỀN THEO NGÀY
    # =========================================================

    cash_flow_df = pd.DataFrame(cash_flows)


    if not cash_flow_df.empty:

        cash_flow_by_date = (
            cash_flow_df
            .groupby("date")["cash_flow"]
            .sum()
            .to_dict()
        )

    else:

        cash_flow_by_date = {}


    # =========================================================
    # TÍNH GIÁ TRỊ DANH MỤC TỪNG NGÀY
    # =========================================================

    # Ban đầu toàn bộ vốn là tiền mặt
    daily_cash = initial_capital


    # Danh sách lưu lịch sử danh mục
    portfolio_history = []


    # Duyệt từng ngày giao dịch
    for current_date in close_matrix.index:

        # Cập nhật tiền mặt theo các giao dịch trong ngày
        daily_cash += cash_flow_by_date.get(
            current_date,
            0
        )


        # Giá trị cổ phiếu đang nắm giữ
        holdings_value = 0


        # Kiểm tra từng vị thế
        for position in position_records:

            # Vị thế được xem là còn mở vào cuối ngày
            is_open = (
                position["buy_date"] <= current_date
                and (
                    pd.isna(position["sell_date"])
                    or current_date < position["sell_date"]
                )
            )


            if is_open:

                ticker = position["ticker"]

                if ticker in close_matrix.columns:

                    close_price = close_matrix.loc[
                        current_date,
                        ticker
                    ]

                    if pd.notna(close_price):

                        holdings_value += (
                            position["shares"]
                            * close_price
                        )


        # Tổng giá trị danh mục cuối ngày
        portfolio_value = (
            daily_cash
            + holdings_value
        )


        # Lưu kết quả
        portfolio_history.append({
            "date": current_date,
            "cash": daily_cash,
            "holdings_value": holdings_value,
            "portfolio_value": portfolio_value
        })


    # Chuyển thành DataFrame
    portfolio_history_df = pd.DataFrame(
        portfolio_history
    )


    # =========================================================
    # TÍNH DAILY RETURN VÀ MAXIMUM DRAWDOWN
    # =========================================================

    # Tính lợi nhuận danh mục từng ngày
    portfolio_history_df["daily_return_pct"] = (
        portfolio_history_df[
            "portfolio_value"
        ]
        .pct_change()
        .fillna(0)
        * 100
    )


    # Giá trị danh mục cao nhất từng đạt được
    portfolio_history_df["running_max"] = (
        portfolio_history_df[
            "portfolio_value"
        ].cummax()
    )


    # Drawdown từng ngày
    portfolio_history_df["drawdown_pct"] = (
        (
            portfolio_history_df[
                "portfolio_value"
            ]
            / portfolio_history_df[
                "running_max"
            ]
        )
        - 1
    ) * 100


    # Maximum Drawdown toàn danh mục
    max_drawdown = abs(
        portfolio_history_df[
            "drawdown_pct"
        ].min()
    )


    # =========================================================
    # XUẤT LỊCH SỬ DANH MỤC
    # =========================================================

    portfolio_history_df.to_csv(
        "portfolio_history.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.2f"
    )


    print(
        "\nĐã xuất lịch sử danh mục ra file "
        "portfolio_history.csv"
    )

    # =========================================================
    # HIỂN THỊ KẾT QUẢ TỔNG HỢP
    # =========================================================

    print("\nTỔNG HỢP KẾT QUẢ BACKTEST:")


    # Nhóm 1: Hiệu quả danh mục
    print(f"Vốn ban đầu: {initial_capital:,.0f} VNĐ")
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
    # Hiển thị kết quả benchmark nếu có dữ liệu VNINDEX
    if benchmark_return is not None:

        print(
            f"Lợi nhuận VNINDEX: "
            f"{benchmark_return:.2f}%"
        )

        print(
            f"Chênh lệch so với VNINDEX: "
            f"{excess_return:.2f}%"
        )

    else:

        print(
            "Benchmark VNINDEX: "
            "Chưa có dữ liệu"
        )
    print(f"Tiền mặt cuối kỳ: {cash:,.0f} VNĐ")
    print(
        f"Số vị thế còn mở: "
        f"{len(positions)}"
    )


    # Nhóm 2: Thống kê giao dịch
    print(f"\nSố giao dịch: {number_of_trades}")
    print(f"Số giao dịch thắng: {winning_trades}")
    print(f"Số giao dịch thua: {losing_trades}")
    print(f"Tỷ lệ thắng: {win_rate:.2f}%")


    # Nhóm 3: Hiệu quả giao dịch
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


    # Hiển thị Profit Factor
    if profit_factor is not None:
        print(
            f"Profit Factor: "
            f"{profit_factor:.2f}"
        )
    else:
        print(
            "Profit Factor: N/A "
            "(không có giao dịch thua)"
        )


    # Nhóm 4: Rủi ro và chi phí
    print(
        f"Maximum Drawdown: "
        f"{max_drawdown:.2f}%"
    )

    print(
        f"Tổng phí giao dịch và thuế: "
        f"{total_transaction_cost:,.0f} VNĐ"
    )


    # =========================================================
    # TẠO BẢNG TỔNG HỢP
    # =========================================================

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


    # Xuất bảng tổng hợp ra file CSV
    summary_df.to_csv(
        "backtest_summary.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.2f"
    )


    print(
        "\nĐã xuất bảng tổng hợp ra file "
        "backtest_summary.csv"
    )

    # =========================================================
    # TRẢ KẾT QUẢ CHO CÁC MODULE KHÁC
    # =========================================================

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

