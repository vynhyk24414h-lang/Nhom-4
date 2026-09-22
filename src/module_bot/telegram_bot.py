import os
import asyncio

import pandas as pd
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from src.module_thu_thap_du_lieu.market_data import (
    get_market_data,
    get_stock_data
)

from src.module_tinh_toan_xu_ly.processor import (
    process_universe
)

from src.module_bot.chart import (
    create_candlestick_chart
)


# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)


# =========================================================
# CẤU HÌNH KẾ HOẠCH GIAO DỊCH
# =========================================================

SL_ATR_MULTIPLIER = 3
TP_RR = 2


# =========================================================
# FORMAT
# =========================================================

def format_price(value):

    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:,.0f} đ"


def format_money(value):

    if value is None or pd.isna(value):
        return "N/A"

    value = float(value)

    if value >= 1_000_000_000:

        return (
            f"{value / 1_000_000_000:.2f} tỷ"
        )

    if value >= 1_000_000:

        return (
            f"{value / 1_000_000:.2f} triệu"
        )

    return f"{value:,.0f} đ"


# =========================================================
# KẾ HOẠCH GIAO DỊCH
# CHỈ DÙNG KHI TÍN HIỆU = MUA
# =========================================================

def calculate_trade_plan(row):

    entry = row["Close"]
    atr = row["ATR14"]

    if (
        pd.isna(entry)
        or pd.isna(atr)
        or atr <= 0
    ):

        return {
            "entry": entry,
            "stop": None,
            "target": None,
        }

    stop = (
        entry
        - SL_ATR_MULTIPLIER * atr
    )

    target = (
        entry
        + TP_RR * (entry - stop)
    )

    return {
        "entry": entry,
        "stop": stop,
        "target": target,
    }


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = """
👋 CHÀO MỪNG ĐẾN VỚI STOCK ANALYTICS BOT

📊 Bot hỗ trợ:
• Phân tích tín hiệu MUA / BÁN / GIỮ
• Tra cứu cổ phiếu
• Theo dõi tín hiệu thị trường
• Xem biểu đồ nến

📚 Gõ /help để xem toàn bộ lệnh.

⚠️ LƯU Ý RỦI RO

Các tín hiệu được tạo dựa trên dữ liệu
và mô hình phân tích của hệ thống.

Thông tin chỉ mang tính tham khảo,
không phải lời khuyên đầu tư.
"""

    await update.message.reply_text(
        message
    )


# =========================================================
# /HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = """
📚 DANH SÁCH LỆNH CƠ BẢN

/start
Giới thiệu và lưu ý rủi ro.

/help
Xem danh sách lệnh.

/tinhieu
Xem danh sách tín hiệu MUA/BÁN hôm nay.

/tracuu [Mã CK]
Phân tích chi tiết 1 mã cổ phiếu.

Ví dụ:
/tracuu FPT

/bieudo [Mã CK]
Xem biểu đồ nến và các đường EMA/SMA.

Ví dụ:
/bieudo FPT

⚠️ Tín hiệu chỉ mang tính tham khảo,
không phải khuyến nghị đầu tư.
"""

    await update.message.reply_text(
        message
    )


# =========================================================
# /TINHIEU
# =========================================================

async def tinhieu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🔎 Đang cập nhật và phân tích tín hiệu hôm nay..."
    )

    try:

        # -------------------------------------------------
        # Lấy dữ liệu toàn bộ thị trường
        # Dùng cho tính RS và tín hiệu toàn universe
        # -------------------------------------------------

        df = await asyncio.to_thread(
            get_market_data
        )

        if df is None or df.empty:

            await update.message.reply_text(
                "❌ Không có dữ liệu thị trường."
            )

            return

        # -------------------------------------------------
        # Xử lý dữ liệu
        # -------------------------------------------------

        result = await asyncio.to_thread(
            process_universe,
            df
        )

        if result.empty:

            await update.message.reply_text(
                "❌ Không thể phân tích dữ liệu."
            )

            return

        latest_date = result["Date"].max()

        latest = result[
            (result["Date"] == latest_date)
            & (result["DataSufficient"])
        ].copy()

        # -------------------------------------------------
        # MUA
        # -------------------------------------------------

        buy_list = latest[
            latest["Signal"] == "MUA"
        ].sort_values(
            "RS",
            ascending=False
        )

        # -------------------------------------------------
        # BÁN
        # -------------------------------------------------

        sell_list = latest[
            latest["Signal"] == "BÁN"
        ].sort_values(
            "RS",
            ascending=False
        )

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        message = (
            "📊 TÍN HIỆU THỊ TRƯỜNG\n"
            f"📅 Ngày: "
            f"{latest_date.strftime('%d/%m/%Y')}\n\n"
        )

        # -------------------------------------------------
        # DANH SÁCH MUA
        # -------------------------------------------------

        message += "🟢 TÍN HIỆU MUA\n"

        if buy_list.empty:

            message += (
                "Không có tín hiệu MUA.\n"
            )

        else:

            for _, row in buy_list.head(15).iterrows():

                message += (
                    f"• {row['Symbol']} "
                    f"| Giá: {format_price(row['Close'])} "
                    f"| RS: {row['RS']:.1f}\n"
                )

        # -------------------------------------------------
        # DANH SÁCH BÁN
        # -------------------------------------------------

        message += "\n🔴 TÍN HIỆU BÁN\n"

        if sell_list.empty:

            message += (
                "Không có tín hiệu BÁN.\n"
            )

        else:

            for _, row in sell_list.head(15).iterrows():

                message += (
                    f"• {row['Symbol']} "
                    f"| Giá: {format_price(row['Close'])} "
                    f"| RS: {row['RS']:.1f}\n"
                )

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------

        message += (
            "\n💡 Dùng /tracuu [Mã CK] "
            "để xem phân tích chi tiết."
        )

        message += (
            "\n💡 Dùng /bieudo [Mã CK] "
            "để xem biểu đồ nến."
        )

        message += (
            "\n\n⚠️ Tín hiệu chỉ mang tính tham khảo."
        )

        await update.message.reply_text(
            message
        )

    except Exception as e:

        print(
            f"Lỗi /tinhieu: {e}"
        )

        await update.message.reply_text(
            f"❌ Không thể lấy tín hiệu:\n{e}"
        )


# =========================================================
# LẤY DỮ LIỆU MỘT MÃ
# =========================================================

def get_latest_stock(symbol):

    symbol = symbol.strip().upper()

    # -----------------------------------------------------
    # Lấy riêng dữ liệu của mã
    # Không gọi get_market_data() nữa
    # -----------------------------------------------------

    df = get_stock_data(
        symbol
    )

    if df is None or df.empty:
        return None

    # -----------------------------------------------------
    # Xử lý dữ liệu
    # -----------------------------------------------------

    result = process_universe(
        df
    )

    if result.empty:
        return None

    result = result.sort_values(
        "Date"
    )

    return result.iloc[-1]


# =========================================================
# TẠO NỘI DUNG PHÂN TÍCH
# =========================================================

def build_analysis_message(row):

    symbol = str(
        row["Symbol"]
    ).upper()

    signal = row["Signal"]

    close = row["Close"]

    rs = row["RS"]

    ema20 = row["EMA20"]

    ema50 = row["EMA50"]

    sma200 = row["SMA200"]

    atr14 = row["ATR14"]

    adx14 = row["ADX14"]

    gtgd = row["MedianGTGD20"]

    trend_score = row.get(
        "TrendScore",
        None
    )

    volume_score = row.get(
        "VolumeScore",
        None
    )

    # =====================================================
    # ICON
    # =====================================================

    if signal == "MUA":

        signal_icon = "🟢"

    elif signal == "BÁN":

        signal_icon = "🔴"

    elif signal == "GIỮ":

        signal_icon = "🟡"

    else:

        signal_icon = "⚪"

    # =====================================================
    # XU HƯỚNG
    # =====================================================

    if (
        pd.notna(close)
        and pd.notna(sma200)
        and close > sma200
        and pd.notna(ema20)
        and pd.notna(ema50)
        and ema20 > ema50
    ):

        trend = "📈 Xu hướng tăng"

    elif (
        pd.notna(close)
        and pd.notna(sma200)
        and close < sma200
    ):

        trend = "📉 Xu hướng giảm"

    else:

        trend = "↔️ Xu hướng chưa rõ"

    # =====================================================
    # HEADER
    # =====================================================

    message = (
        f"📊 PHÂN TÍCH {symbol}\n"
        f"📅 Ngày: "
        f"{pd.to_datetime(row['Date']).strftime('%d/%m/%Y')}\n\n"

        f"{signal_icon} TÍN HIỆU: {signal}\n"
        f"💰 Giá hiện tại: {format_price(close)}\n"
        f"{trend}\n\n"

        "📐 CHỈ BÁO KỸ THUẬT\n"
        f"• EMA20: {format_price(ema20)}\n"
        f"• EMA50: {format_price(ema50)}\n"
        f"• SMA200: {format_price(sma200)}\n"
        f"• ATR14: {format_price(atr14)}\n"
        f"• ADX14: {adx14:.2f}\n"
    )

    if pd.notna(rs):

        message += (
            f"• RS: {rs:.1f}\n"
        )

    # =====================================================
    # THANH KHOẢN
    # =====================================================

    message += "\n💧 THANH KHOẢN\n"

    message += (
        f"• Median GTGD20: "
        f"{format_money(gtgd)}\n"
    )

    if bool(
        row.get(
            "Liquidity_ok",
            False
        )
    ):

        message += (
            "• Trạng thái: ✅ Đạt yêu cầu\n"
        )

    else:

        message += (
            "• Trạng thái: ❌ Chưa đạt\n"
        )

    # =====================================================
    # XÁC NHẬN TÍN HIỆU
    # =====================================================

    message += (
        "\n📊 XÁC NHẬN TÍN HIỆU\n"
    )

    if bool(
        row.get(
            "EMA_ok",
            False
        )
    ):

        message += (
            "• EMA20 > EMA50: ✅\n"
        )

    else:

        message += (
            "• EMA20 > EMA50: ❌\n"
        )

    if bool(
        row.get(
            "SMA200_ok",
            False
        )
    ):

        message += (
            "• Giá > SMA200: ✅\n"
        )

    else:

        message += (
            "• Giá > SMA200: ❌\n"
        )

    if bool(
        row.get(
            "Donchian_ok",
            False
        )
    ):

        message += (
            "• Donchian breakout: ✅\n"
        )

    else:

        message += (
            "• Donchian breakout: ❌\n"
        )

    if bool(
        row.get(
            "VolumeBreakout_ok",
            False
        )
    ):

        message += (
            "• Volume breakout: ✅\n"
        )

    else:

        message += (
            "• Volume breakout: ❌\n"
        )

    if bool(
        row.get(
            "CLV_ok",
            False
        )
    ):

        message += (
            "• CLV ≥ 0.6: ✅\n"
        )

    else:

        message += (
            "• CLV ≥ 0.6: ❌\n"
        )

    if bool(
        row.get(
            "AntiChasing_ok",
            False
        )
    ):

        message += (
            "• Anti-chasing: ✅\n"
        )

    else:

        message += (
            "• Anti-chasing: ❌\n"
        )

    if pd.notna(trend_score):

        message += (
            f"\n📈 Trend Score: "
            f"{int(trend_score)}/3\n"
        )

    if pd.notna(volume_score):

        message += (
            f"📊 Volume Score: "
            f"{int(volume_score)}/2\n"
        )

    # =====================================================
    # KẾ HOẠCH THEO TÍN HIỆU
    # =====================================================

    if signal == "MUA":

        plan = calculate_trade_plan(
            row
        )

        message += (
            "\n🎯 KẾ HOẠCH GIAO DỊCH\n"
        )

        message += (
            f"• Điểm vào: "
            f"{format_price(plan['entry'])}\n"
            f"• Stop Loss: "
            f"{format_price(plan['stop'])}\n"
            f"• Mục tiêu: "
            f"{format_price(plan['target'])}\n"
        )

    elif signal == "BÁN":

        message += (
            "\n🔴 KẾ HOẠCH XỬ LÝ\n"
        )

        message += (
            f"• Giá hiện tại: "
            f"{format_price(close)}\n"
            "• Trạng thái: Ưu tiên thoát vị thế\n"
            "• Không mở vị thế mua mới theo tín hiệu hiện tại.\n"
        )

    elif signal == "GIỮ":

        message += (
            "\n🟡 TRẠNG THÁI\n"
        )

        message += (
            f"• Giá hiện tại: "
            f"{format_price(close)}\n"
            "• Chưa đủ điều kiện để mở vị thế mới.\n"
        )

    # =====================================================
    # NHẬN ĐỊNH
    # =====================================================

    message += "\n📝 NHẬN ĐỊNH\n"

    if signal == "MUA":

        message += (
            "Các điều kiện thanh khoản, "
            "relative strength và xu hướng "
            "đang hỗ trợ tín hiệu MUA."
        )

    elif signal == "BÁN":

        reasons = []

        if (
            pd.notna(sma200)
            and close < sma200
        ):

            reasons.append(
                "giá đóng cửa dưới SMA200"
            )

        if (
            pd.notna(rs)
            and rs < 50
        ):

            reasons.append(
                "RS dưới 50"
            )

        if reasons:

            message += (
                "Tín hiệu BÁN do "
                + " và ".join(reasons)
                + "."
            )

        else:

            message += (
                "Xuất hiện điều kiện BÁN "
                "theo hệ thống."
            )

    elif signal == "GIỮ":

        message += (
            "Chưa đủ điều kiện để phát sinh "
            "tín hiệu MUA hoặc BÁN."
        )

    else:

        message += (
            "Dữ liệu chưa đủ để đưa ra tín hiệu."
        )

    # =====================================================
    # CẢNH BÁO
    # =====================================================

    message += (
        "\n\n⚠️ Đây là kết quả phân tích tự động, "
        "không phải khuyến nghị đầu tư."
    )

    return message


# =========================================================
# /TRACUU
# =========================================================

async def tracuu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "❗ Vui lòng nhập mã cổ phiếu.\n\n"
            "Ví dụ:\n"
            "/tracuu FPT"
        )

        return

    symbol = context.args[0].upper()

    await update.message.reply_text(
        f"🔎 Đang phân tích {symbol}..."
    )

    try:

        # -------------------------------------------------
        # Lấy riêng dữ liệu mã cổ phiếu
        # và chạy ở thread riêng
        # -------------------------------------------------

        row = await asyncio.to_thread(
            get_latest_stock,
            symbol
        )

        if row is None:

            await update.message.reply_text(
                f"❌ Không tìm thấy dữ liệu "
                f"cho {symbol}."
            )

            return

        if not bool(
            row.get(
                "DataSufficient",
                False
            )
        ):

            await update.message.reply_text(
                f"⚠️ {symbol} chưa có đủ dữ liệu "
                "để phân tích."
            )

            return

        message = build_analysis_message(
            row
        )

        await update.message.reply_text(
            message
        )

    except Exception as e:

        print(
            f"Lỗi /tracuu {symbol}: {e}"
        )

        await update.message.reply_text(
            f"❌ Có lỗi khi phân tích "
            f"{symbol}:\n{e}"
        )


# =========================================================
# /BIEUDO
# =========================================================

async def bieudo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "❗ Vui lòng nhập mã cổ phiếu.\n\n"
            "Ví dụ:\n"
            "/bieudo FPT"
        )

        return

    symbol = context.args[0].upper()

    await update.message.reply_text(
        f"🕯️ Đang tạo biểu đồ {symbol}..."
    )

    try:

        # -------------------------------------------------
        # Chạy việc lấy dữ liệu + vẽ chart
        # ở thread riêng để bot không bị đứng
        # -------------------------------------------------

        image = await asyncio.to_thread(
            create_candlestick_chart,
            symbol
        )

        await update.message.reply_photo(
            photo=image,
            caption=(
                f"🕯️ BIỂU ĐỒ {symbol}\n\n"
                "• Nến OHLC\n"
                "• EMA20\n"
                "• EMA50\n"
                "• SMA200\n"
                "• Volume\n\n"
                "📌 120 phiên gần nhất."
            )
        )

    except Exception as e:

        print(
            f"Lỗi /bieudo {symbol}: {e}"
        )

        await update.message.reply_text(
            f"❌ Không thể tạo biểu đồ "
            f"{symbol}.\n\n"
            f"Lỗi: {e}"
        )


# =========================================================
# CHẠY BOT
# =========================================================

def run_bot():

    if not TELEGRAM_BOT_TOKEN:

        raise ValueError(
            "Chưa cấu hình TELEGRAM_BOT_TOKEN "
            "trong biến môi trường."
        )

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(60)
        .write_timeout(60)
        .pool_timeout(60)
        .build()
    )

    # =====================================================
    # COMMANDS
    # =====================================================

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CommandHandler(
            "tinhieu",
            tinhieu
        )
    )

    application.add_handler(
        CommandHandler(
            "tracuu",
            tracuu
        )
    )

    application.add_handler(
        CommandHandler(
            "bieudo",
            bieudo
        )
    )

    # =====================================================
    # START BOT
    # =====================================================

    print(
        "🤖 Telegram Bot đang chạy..."
    )

    application.run_polling(
        drop_pending_updates=True
    )