import os
import asyncio
import pandas as pd

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from src.module_bot.chart import (
    create_candlestick_chart
)

from src.module_bot.analysis_cache import (
    get_latest_analysis,
    get_stock_analysis
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

    return f"{float(value):,.0f} đ"


def format_money(value):

    if value is None or pd.isna(value):
        return "N/A"

    value = float(value)

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} tỷ"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f} triệu"

    return f"{value:,.0f} đ"


# =========================================================
# KẾ HOẠCH GIAO DỊCH
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
            "target": None
        }

    stop = entry - SL_ATR_MULTIPLIER * atr

    target = (
        entry
        + TP_RR * (entry - stop)
    )

    return {
        "entry": entry,
        "stop": stop,
        "target": target
    }


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = (
        "👋 CHÀO MỪNG ĐẾN VỚI STOCK ANALYTICS BOT\n\n"

        "📊 Bot hỗ trợ:\n"
        "• Phân tích tín hiệu MUA / BÁN / GIỮ\n"
        "• Tra cứu cổ phiếu\n"
        "• Theo dõi tín hiệu thị trường\n"
        "• Xem biểu đồ nến\n\n"

        "📚 Gõ /help để xem toàn bộ lệnh.\n\n"

        "⚠️ Tín hiệu chỉ mang tính tham khảo, "
        "không phải lời khuyên đầu tư."
    )

    await update.message.reply_text(message)


# =========================================================
# /HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = (
        "📚 DANH SÁCH LỆNH\n\n"

        "/start\n"
        "Giới thiệu bot.\n\n"

        "/help\n"
        "Xem danh sách lệnh.\n\n"

        "/tinhieu\n"
        "Xem tín hiệu MUA / BÁN / GIỮ.\n\n"

        "/tracuu [Mã CK]\n"
        "Ví dụ: /tracuu FPT\n\n"

        "/bieudo [Mã CK]\n"
        "Ví dụ: /bieudo FPT\n\n"

        "⚠️ Tín hiệu chỉ mang tính tham khảo."
    )

    await update.message.reply_text(message)


# =========================================================
# BUILD ANALYSIS MESSAGE
# =========================================================

def build_analysis_message(row):

    symbol = str(row["Symbol"]).upper()
    signal = row["Signal"]

    close = row["Close"]
    rs = row["RS"]
    ema20 = row["EMA20"]
    ema50 = row["EMA50"]
    sma200 = row["SMA200"]
    atr14 = row["ATR14"]
    adx14 = row["ADX14"]
    gtgd = row["MedianGTGD20"]

    # -----------------------------------------------------
    # ICON
    # -----------------------------------------------------

    icon = {
        "MUA": "🟢",
        "BÁN": "🔴",
        "GIỮ": "🟡"
    }.get(signal, "⚪")

    # -----------------------------------------------------
    # XU HƯỚNG
    # -----------------------------------------------------

    if (
        pd.notna(close)
        and pd.notna(sma200)
        and pd.notna(ema20)
        and pd.notna(ema50)
        and close > sma200
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

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    message = (
        f"📊 PHÂN TÍCH {symbol}\n"
        f"📅 Ngày: "
        f"{pd.to_datetime(row['Date']).strftime('%d/%m/%Y')}\n\n"

        f"{icon} TÍN HIỆU: {signal}\n"
        f"💰 Giá: {format_price(close)}\n"
        f"{trend}\n\n"

        "📐 CHỈ BÁO KỸ THUẬT\n"
        f"• EMA20: {format_price(ema20)}\n"
        f"• EMA50: {format_price(ema50)}\n"
        f"• SMA200: {format_price(sma200)}\n"
        f"• ATR14: {format_price(atr14)}\n"
        f"• ADX14: {adx14:.2f}\n"
        f"• RS: {rs:.1f}\n\n"

        "💧 THANH KHOẢN\n"
        f"• Median GTGD20: {format_money(gtgd)}\n"
    )

    if bool(row.get("Liquidity_ok", False)):
        message += "• Trạng thái: ✅ Đạt yêu cầu\n"
    else:
        message += "• Trạng thái: ❌ Chưa đạt\n"

    # -----------------------------------------------------
    # XÁC NHẬN
    # -----------------------------------------------------

    message += "\n📊 XÁC NHẬN TÍN HIỆU\n"

    checks = [
        ("EMA20 > EMA50", "EMA_ok"),
        ("Giá > SMA200", "SMA200_ok"),
        ("Donchian breakout", "Donchian_ok"),
        ("Volume breakout", "VolumeBreakout_ok"),
        ("CLV ≥ 0.6", "CLV_ok"),
        ("Anti-chasing", "AntiChasing_ok")
    ]

    for name, column in checks:

        if bool(row.get(column, False)):
            message += f"• {name}: ✅\n"
        else:
            message += f"• {name}: ❌\n"

    if pd.notna(row.get("TrendScore")):
        message += (
            f"\n📈 Trend Score: "
            f"{int(row['TrendScore'])}/3\n"
        )

    if pd.notna(row.get("VolumeScore")):
        message += (
            f"📊 Volume Score: "
            f"{int(row['VolumeScore'])}/2\n"
        )

    # -----------------------------------------------------
    # KẾ HOẠCH
    # -----------------------------------------------------

    if signal == "MUA":

        plan = calculate_trade_plan(row)

        message += (
            "\n🎯 KẾ HOẠCH GIAO DỊCH\n"
            f"• Điểm vào: {format_price(plan['entry'])}\n"
            f"• Stop Loss: {format_price(plan['stop'])}\n"
            f"• Mục tiêu: {format_price(plan['target'])}\n"
        )

    elif signal == "BÁN":

        message += (
            "\n🔴 KẾ HOẠCH XỬ LÝ\n"
            f"• Giá hiện tại: {format_price(close)}\n"
            "• Ưu tiên thoát vị thế.\n"
            "• Không mở vị thế mua mới theo tín hiệu hiện tại.\n"
        )

    else:

        message += (
            "\n🟡 TRẠNG THÁI\n"
            f"• Giá hiện tại: {format_price(close)}\n"
            "• Chưa đủ điều kiện mở vị thế mới.\n"
        )

    # -----------------------------------------------------
    # NHẬN ĐỊNH
    # -----------------------------------------------------

    if signal == "MUA":

        message += (
            "\n📝 NHẬN ĐỊNH\n"
            "Các điều kiện thanh khoản, relative strength "
            "và xu hướng đang hỗ trợ tín hiệu MUA."
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
                "\n📝 NHẬN ĐỊNH\n"
                "Tín hiệu BÁN do "
                + " và ".join(reasons)
                + "."
            )
        else:
            message += (
                "\n📝 NHẬN ĐỊNH\n"
                "Xuất hiện điều kiện BÁN theo hệ thống."
            )

    else:

        message += (
            "\n📝 NHẬN ĐỊNH\n"
            "Chưa đủ điều kiện để phát sinh "
            "tín hiệu MUA hoặc BÁN."
        )

    message += (
        "\n\n⚠️ Đây là kết quả phân tích tự động, "
        "không phải khuyến nghị đầu tư."
    )

    return message


# =========================================================
# /TINHIEU
# =========================================================

async def tinhieu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    status = await update.message.reply_text(
        "🔎 Đang kiểm tra tín hiệu..."
    )

    try:

        # analysis_cache sẽ tự quyết định:
        # - đọc cache nếu đã có
        # - process_universe nếu cần tính mới

        result = await asyncio.to_thread(
            get_latest_analysis
        )

        if result is None or result.empty:

            await status.edit_text(
                "❌ Không có dữ liệu phân tích."
            )

            return

        # -------------------------------------------------
        # MUA
        # -------------------------------------------------

        buy_list = result[
            result["Signal"] == "MUA"
        ].sort_values(
            "RS",
            ascending=False
        )

        # -------------------------------------------------
        # BÁN
        # -------------------------------------------------

        sell_list = result[
            result["Signal"] == "BÁN"
        ].sort_values(
            "RS",
            ascending=False
        )

        latest_date = result["Date"].max()

        message = (
            "📊 TÍN HIỆU THỊ TRƯỜNG\n"
            f"📅 Ngày: "
            f"{pd.to_datetime(latest_date).strftime('%d/%m/%Y')}\n\n"
        )

        # -------------------------------------------------
        # MUA
        # -------------------------------------------------

        message += "🟢 TÍN HIỆU MUA\n"

        if buy_list.empty:

            message += "Không có tín hiệu MUA.\n"

        else:

            for _, row in buy_list.head(15).iterrows():

                message += (
                    f"• {row['Symbol']} "
                    f"| Giá: {format_price(row['Close'])} "
                    f"| RS: {row['RS']:.1f}\n"
                )

        # -------------------------------------------------
        # BÁN
        # -------------------------------------------------

        message += "\n🔴 TÍN HIỆU BÁN\n"

        if sell_list.empty:

            message += "Không có tín hiệu BÁN.\n"

        else:

            for _, row in sell_list.head(15).iterrows():

                message += (
                    f"• {row['Symbol']} "
                    f"| Giá: {format_price(row['Close'])} "
                    f"| RS: {row['RS']:.1f}\n"
                )

        message += (
            "\n💡 /tracuu [Mã CK] "
            "để xem phân tích chi tiết."
        )

        message += (
            "\n💡 /bieudo [Mã CK] "
            "để xem biểu đồ."
        )

        message += (
            "\n\n⚠️ Tín hiệu chỉ mang tính tham khảo."
        )

        await status.edit_text(message)

    except Exception as e:

        print(f"Lỗi /tinhieu: {e}")

        await status.edit_text(
            f"❌ Không thể lấy tín hiệu:\n{e}"
        )


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
            "Ví dụ: /tracuu FPT"
        )

        return

    symbol = context.args[0].strip().upper()

    status = await update.message.reply_text(
        f"🔎 Đang tra cứu {symbol}..."
    )

    try:

        # Đọc kết quả đã tính từ analysis cache
        row = await asyncio.to_thread(
            get_stock_analysis,
            symbol
        )

        if row is None:

            await status.edit_text(
                f"❌ Không tìm thấy dữ liệu phân tích "
                f"cho {symbol}."
            )

            return

        if not bool(
            row.get(
                "DataSufficient",
                False
            )
        ):

            await status.edit_text(
                f"⚠️ {symbol} chưa có đủ dữ liệu "
                "để phân tích."
            )

            return

        message = build_analysis_message(row)

        await status.edit_text(message)

    except Exception as e:

        print(
            f"Lỗi /tracuu {symbol}: {e}"
        )

        await status.edit_text(
            f"❌ Có lỗi khi phân tích {symbol}:\n{e}"
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
            "Ví dụ: /bieudo FPT"
        )

        return

    symbol = context.args[0].strip().upper()

    status = await update.message.reply_text(
        f"🕯️ Đang tạo biểu đồ {symbol}..."
    )

    try:

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

        await status.delete()

    except Exception as e:

        print(
            f"Lỗi /bieudo {symbol}: {e}"
        )

        await status.edit_text(
            f"❌ Không thể tạo biểu đồ {symbol}.\n"
            f"Lỗi: {e}"
        )


# =========================================================
# CHẠY BOT
# =========================================================

def run_bot():

    if not TELEGRAM_BOT_TOKEN:

        raise ValueError(
            "Chưa cấu hình TELEGRAM_BOT_TOKEN."
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

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("tinhieu", tinhieu)
    )

    application.add_handler(
        CommandHandler("tracuu", tracuu)
    )

    application.add_handler(
        CommandHandler("bieudo", bieudo)
    )

    print("🤖 Telegram Bot đang chạy...")

    application.run_polling(
        drop_pending_updates=True
    )