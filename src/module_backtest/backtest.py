import pandas as pd
import math


def run_backtest(
    signal_data,
    initial_capital=100_000_000,
    max_positions=10,
    lot_size=100,
    risk_per_trade=0.01,
    max_position_pct=0.10,
    max_liquidity_pct=0.05,
    transaction_fee_rate=0.001,
    sell_tax_rate=0.001,
    slippage_rate=0.001,
):

    if signal_data is None or signal_data.empty:
        return {
            "summary": pd.DataFrame(),
            "trades": pd.DataFrame(),
            "equity_curve": pd.DataFrame()
        }

    df = signal_data.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    for col in [
        "Open",
        "Close",
        "Volume",
        "GTGD",
        "ATR14",
        "RS",
        "SMA200",
        "Chandelier"
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # GTGD trung bình 20 phiên
    df["GTGD20Avg"] = (
        df.groupby("Symbol")["GTGD"]
        .transform(
            lambda x: x.rolling(20).mean()
        )
    )

    df = (
        df.sort_values(
            ["Date", "Symbol"]
        )
        .reset_index(drop=True)
    )

    dates = sorted(
        df["Date"].unique()
    )

    cash = float(initial_capital)

    positions = {}

    pending_buys = {}

    pending_sells = set()

    trades = []

    equity_records = []

    for i, current_date in enumerate(dates):

        today = df[
            df["Date"] == current_date
        ]

        # ==================================================
        # 1. THỰC HIỆN LỆNH BÁN Ở GIÁ MỞ CỬA NGÀY TIẾP THEO
        # ==================================================

        for symbol in list(pending_sells):

            if symbol not in positions:
                continue

            row = today[
                today["Symbol"] == symbol
            ]

            if row.empty:
                continue

            row = row.iloc[0]

            open_price = float(
                row["Open"]
            )

            sell_price = (
                open_price
                * (1 - slippage_rate)
            )

            position = positions[symbol]

            quantity = position["quantity"]

            gross_value = (
                sell_price
                * quantity
            )

            fee = (
                gross_value
                * transaction_fee_rate
            )

            tax = (
                gross_value
                * sell_tax_rate
            )

            net_value = (
                gross_value
                - fee
                - tax
            )

            cash += net_value

            pnl = (
                net_value
                - position["buy_cost"]
            )

            trades.append({
                "Symbol": symbol,
                "BuyDate": position["buy_date"],
                "SellDate": current_date,
                "BuyPrice": position["buy_price"],
                "SellPrice": sell_price,
                "Quantity": quantity,
                "BuyValue": position["buy_cost"],
                "SellValue": net_value,
                "PnL": pnl,
                "ReturnPct": (
                    pnl
                    / position["buy_cost"]
                ),
            })

            del positions[symbol]

        pending_sells.clear()

        # ==================================================
        # 2. THỰC HIỆN LỆNH MUA Ở GIÁ MỞ CỬA NGÀY TIẾP THEO
        # ==================================================

        for symbol, order in list(
            pending_buys.items()
        ):

            if symbol in positions:
                continue

            if len(positions) >= max_positions:
                break

            row = today[
                today["Symbol"] == symbol
            ]

            if row.empty:
                continue

            row = row.iloc[0]

            open_price = float(
                row["Open"]
            )

            buy_price = (
                open_price
                * (1 + slippage_rate)
            )

            atr = order["ATR14"]

            if pd.isna(atr) or atr <= 0:
                continue

            gtgd20 = order["GTGD20Avg"]

            if (
                pd.isna(gtgd20)
                or gtgd20 <= 0
            ):
                continue

            # ----------------------------------------------
            # Position sizing theo rủi ro
            # ----------------------------------------------

            risk_money = (
                initial_capital
                * risk_per_trade
            )

            risk_per_share = (
                3 * atr
            )

            qty_risk = math.floor(
                risk_money
                / risk_per_share
                / lot_size
            ) * lot_size

            # ----------------------------------------------
            # Giới hạn 10% vốn / mã
            # ----------------------------------------------

            max_value = (
                initial_capital
                * max_position_pct
            )

            qty_capital = math.floor(
                max_value
                / buy_price
                / lot_size
            ) * lot_size

            # ----------------------------------------------
            # Giới hạn thanh khoản
            # ----------------------------------------------

            max_liquidity_value = (
                gtgd20
                * max_liquidity_pct
            )

            qty_liquidity = math.floor(
                max_liquidity_value
                / buy_price
                / lot_size
            ) * lot_size

            quantity = min(
                qty_risk,
                qty_capital,
                qty_liquidity
            )

            if quantity <= 0:
                continue

            # ----------------------------------------------
            # Kiểm tra tiền mặt
            # ----------------------------------------------

            gross_value = (
                buy_price
                * quantity
            )

            fee = (
                gross_value
                * transaction_fee_rate
            )

            total_cost = (
                gross_value
                + fee
            )

            if total_cost > cash:

                qty_cash = math.floor(
                    cash
                    / (
                        buy_price
                        * (
                            1
                            + transaction_fee_rate
                        )
                    )
                    / lot_size
                ) * lot_size

                quantity = min(
                    quantity,
                    qty_cash
                )

                if quantity <= 0:
                    continue

                gross_value = (
                    buy_price
                    * quantity
                )

                fee = (
                    gross_value
                    * transaction_fee_rate
                )

                total_cost = (
                    gross_value
                    + fee
                )

            cash -= total_cost

            positions[symbol] = {
                "buy_date": current_date,
                "buy_price": buy_price,
                "quantity": quantity,
                "buy_cost": total_cost,
                "stop": order.get(
                    "Chandelier"
                ),
            }

        pending_buys.clear()

        # ==================================================
        # 3. CẬP NHẬT VỊ THẾ + KIỂM TRA SELL
        # ==================================================

        for symbol, position in list(
            positions.items()
        ):

            row = today[
                today["Symbol"] == symbol
            ]

            if row.empty:
                continue

            row = row.iloc[0]

            close = float(
                row["Close"]
            )

            # ----------------------------------------------
            # Vẫn cập nhật Chandelier để lưu dữ liệu
            # Nhưng KHÔNG dùng làm điều kiện SELL
            # ----------------------------------------------

            chandelier = row.get(
                "Chandelier",
                None
            )

            if pd.notna(chandelier):

                if (
                    position["stop"] is None
                    or pd.isna(
                        position["stop"]
                    )
                ):
                    position["stop"] = float(
                        chandelier
                    )

                else:
                    position["stop"] = max(
                        position["stop"],
                        float(chandelier)
                    )

            # ----------------------------------------------
            # SELL chỉ dựa trên:
            # 1. Close < SMA200
            # 2. RS < 50
            # ----------------------------------------------

            sell_signal = False

            if (
                pd.notna(
                    row.get("SMA200")
                )
                and close < row["SMA200"]
            ):
                sell_signal = True

            if (
                pd.notna(
                    row.get("RS")
                )
                and row["RS"] < 50
            ):
                sell_signal = True

            if sell_signal:
                pending_sells.add(
                    symbol
                )

        # ==================================================
        # 4. TẠO LỆNH MUA CHO NGÀY TIẾP THEO
        # ==================================================

        if i < len(dates) - 1:

            # Chỉ lấy các mã có tín hiệu MUA
            buy_candidates = today[
                (today["Signal"] == "MUA")
                & (
                    ~today["Symbol"].isin(
                        positions.keys()
                    )
                )
                & (
                    ~today["Symbol"].isin(
                        pending_sells
                    )
                )
                & (
                    today["ATR14"].notna()
                )
                & (
                    today["GTGD20Avg"].notna()
                )
                & (
                    today["RS"].notna()
                )
            ].copy()

            # ----------------------------------------------
            # ƯU TIÊN CỔ PHIẾU CÓ RS CAO NHẤT
            # Nếu RS bằng nhau thì ưu tiên thanh khoản cao hơn
            # ----------------------------------------------

            buy_candidates = (
                buy_candidates
                .sort_values(
                    [
                        "RS",
                        "MedianGTGD20"
                    ],
                    ascending=[
                        False,
                        False
                    ]
                )
            )

            # ----------------------------------------------
            # Số vị thế còn có thể mở
            # ----------------------------------------------

            available_slots = (
                max_positions
                - len(positions)
            )

            if available_slots > 0:

                buy_candidates = (
                    buy_candidates
                    .head(
                        available_slots
                    )
                )

                for _, row in (
                    buy_candidates.iterrows()
                ):

                    symbol = row["Symbol"]

                    pending_buys[symbol] = {
                        "ATR14": row["ATR14"],
                        "GTGD20Avg": row["GTGD20Avg"],
                        "Chandelier": row.get(
                            "Chandelier"
                        ),
                    }

        # ==================================================
        # 5. TÍNH GIÁ TRỊ DANH MỤC
        # ==================================================

        portfolio_value = cash

        for symbol, position in (
            positions.items()
        ):

            row = today[
                today["Symbol"] == symbol
            ]

            if row.empty:
                continue

            close = float(
                row.iloc[0]["Close"]
            )

            portfolio_value += (
                close
                * position["quantity"]
            )

        equity_records.append({
            "Date": current_date,
            "Cash": cash,
            "PortfolioValue": portfolio_value,
            "NumberOfPositions": len(
                positions
            ),
        })

    # ======================================================
    # 6. TẠO EQUITY CURVE + TRADE DATA
    # ======================================================

    equity_curve = pd.DataFrame(
        equity_records
    )

    trades_df = pd.DataFrame(
        trades
    )

    if equity_curve.empty:

        return {
            "summary": pd.DataFrame(),
            "trades": trades_df,
            "equity_curve": equity_curve
        }

    # ======================================================
    # 7. MAXIMUM DRAWDOWN
    # ======================================================

    equity_curve["Peak"] = (
        equity_curve["PortfolioValue"]
        .cummax()
    )

    equity_curve["Drawdown"] = (
        equity_curve["PortfolioValue"]
        / equity_curve["Peak"]
        - 1
    )

    # ======================================================
    # 8. PERFORMANCE
    # ======================================================

    initial_value = initial_capital

    final_value = float(
        equity_curve.iloc[-1][
            "PortfolioValue"
        ]
    )

    total_return = (
        final_value
        / initial_value
        - 1
    )

    max_drawdown = float(
        equity_curve["Drawdown"].min()
    )

    start_date = (
        equity_curve["Date"].iloc[0]
    )

    end_date = (
        equity_curve["Date"].iloc[-1]
    )

    days = (
        end_date
        - start_date
    ).days

    if (
        days > 0
        and final_value > 0
    ):

        years = days / 365

        cagr = (
            final_value
            / initial_value
        ) ** (
            1 / years
        ) - 1

    else:

        cagr = 0

    # ======================================================
    # 9. TRADE STATISTICS
    # ======================================================

    if not trades_df.empty:

        wins = trades_df[
            trades_df["PnL"] > 0
        ]

        losses = trades_df[
            trades_df["PnL"] < 0
        ]

        win_rate = (
            len(wins)
            / len(trades_df)
        )

        gross_profit = wins[
            "PnL"
        ].sum()

        gross_loss = abs(
            losses["PnL"].sum()
        )

        if gross_loss > 0:

            profit_factor = (
                gross_profit
                / gross_loss
            )

        else:

            profit_factor = 0

    else:

        win_rate = 0
        profit_factor = 0

    # ======================================================
    # 10. SUMMARY
    # ======================================================

    summary = pd.DataFrame([{
        "InitialCapital":
            initial_capital,

        "FinalPortfolioValue":
            final_value,

        "TotalReturn":
            total_return,

        "CAGR":
            cagr,

        "MaxDrawdown":
            max_drawdown,

        "TotalTrades":
            len(trades_df),

        "WinRate":
            win_rate,

        "ProfitFactor":
            profit_factor,
    }])

    return {
        "summary": summary,
        "trades": trades_df,
        "equity_curve": equity_curve,
    }