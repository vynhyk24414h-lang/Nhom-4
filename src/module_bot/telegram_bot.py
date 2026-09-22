import io
import os

from dotenv import load_dotenv

load_dotenv()

import pandas as pd

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.module_thu_thap_du_lieu.market_data import get_stock_data
from src.module_tinh_toan_xu_ly.processor import process_universe
from src.module_bot.chart import create_candlestick_chart


# ============================================================
# CẤU HÌNH
# ============================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

SECTOR_FILE = "stock_sector.csv"


# ============================================================
# MAPPING NGÀNH
# ============================================================

SECTOR_VI = {
    "Commercial services": "Dịch vụ thương mại",
    "Communications": "Truyền thông",
    "Consumer durables": "Hàng tiêu dùng lâu bền",
    "Consumer non-durables": "Hàng tiêu dùng không lâu bền",
    "Consumer services": "Dịch vụ tiêu dùng",
    "Distribution services": "Dịch vụ phân phối",
    "Electronic technology": "Công nghệ điện tử",
    "Energy minerals": "Khoáng sản năng lượng",
    "Finance": "Tài chính",
    "Health services": "Dịch vụ y tế",
    "Health technology": "Công nghệ y tế",
    "Industrial services": "Dịch vụ công nghiệp",
    "Non-energy minerals": "Khoáng sản phi năng lượng",
    "Process industries": "Công nghiệp chế biến",
    "Producer manufacturing": "Sản xuất công nghiệp",
    "Retail trade": "Bán lẻ",
    "Technology services": "Dịch vụ công nghệ",
    "Transportation": "Vận tải",
    "Utilities": "Tiện ích",
    "Unknown": "Chưa phân loại",
}


# ============================================================
# HÀM FORMAT
# ============================================================

def format_price(value):
    if pd.isna(value):
        return "N/A"

    try:
        value = float(value)

        if value >= 1000:
            return f"{value:,.0f} đ"

        return f"{value:,.2f} đ"

    except Exception:
        return str(value)


def format_money(value):
    if pd.isna(value):
        return "N/A"

    try:
        value = float(value)

        if value >= 1_000_000_000_000:
            return f"{value / 1_000_000_000_000:.2f} nghìn tỷ"

        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f} tỷ"

        if value >= 1_000_000:
            return f"{value / 1_000_000:.2f} triệu"

        return f"{value:,.0f}"

    except Exception:
        return str(value)


def format_percent(value):
    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):.1f}%"
    except Exception:
        return str(value)


# ============================================================
# KEYBOARD
# ============================================================

def main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                "🔎 TRA CỨU",
                callback_data="search"
            )
        ],
        [
            InlineKeyboardButton(
                "❓ HƯỚNG DẪN",
                callback_data="help"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def stock_detail_keyboard(symbol):
    """
    Các chức năng sau khi đã tra một mã.
    Tất cả đều gắn với đúng mã đang xem.
    """

    symbol = str(symbol).strip().upper()

    keyboard = [
        [
            InlineKeyboardButton(
                "⭐ SMARTSCORE",
                callback_data=f"smartscore:{symbol}"
            ),
            InlineKeyboardButton(
                "🏭 NGÀNH",
                callback_data=f"sector:{symbol}"
            ),
        ],
        [
            InlineKeyboardButton(
                "📈 BIỂU ĐỒ",
                callback_data=f"chart:{symbol}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔎 MÃ KHÁC",
                callback_data="search_other"
            ),
            InlineKeyboardButton(
                "🏠 TRANG CHỦ",
                callback_data="home"
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def back_to_stock_keyboard(symbol):
    symbol = str(symbol).strip().upper()

    keyboard = [
        [
            InlineKeyboardButton(
                "⭐ SMARTSCORE",
                callback_data=f"smartscore:{symbol}"
            ),
            InlineKeyboardButton(
                "🏭 NGÀNH",
                callback_data=f"sector:{symbol}"
            ),
        ],
        [
            InlineKeyboardButton(
                "📈 BIỂU ĐỒ",
                callback_data=f"chart:{symbol}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔎 MÃ KHÁC",
                callback_data="search_other"
            ),
            InlineKeyboardButton(
                "🏠 TRANG CHỦ",
                callback_data="home"
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ============================================================
# /START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "📊 FINBOT\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Xin chào! 👋\n\n"
        "FINBOT hỗ trợ phân tích cổ phiếu dựa trên "
        "dữ liệu thị trường và bộ tiêu chí của hệ thống.\n\n"
        "🔎 Tra cứu một mã cổ phiếu để xem:\n"
        "• Tín hiệu MUA / BÁN / GIỮ\n"
        "• Kế hoạch xử lý\n"
        "• SmartScore\n"
        "• Ngành\n"
        "• Biểu đồ kỹ thuật\n\n"
        "⚠️ Kết quả là phân tích tự động, "
        "không phải khuyến nghị đầu tư."
    )

    await update.message.reply_text(
        message,
        reply_markup=main_keyboard()
    )


# ============================================================
# /HELP
# ============================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "❓ HƯỚNG DẪN FINBOT\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🔎 TRA CỨU\n"
        "Nhập:\n"
        "/tracuu [Mã CK]\n\n"
        "Ví dụ:\n"
        "/tracuu MCH\n\n"
        "Sau khi phân tích, bạn có thể chọn:\n"
        "⭐ SmartScore — xem điểm của mã\n"
        "🏭 Ngành — xem ngành của mã\n"
        "📈 Biểu đồ — xem biểu đồ kỹ thuật\n\n"
        "⚠️ Đây là kết quả phân tích tự động, "
        "không phải khuyến nghị đầu tư."
    )

    await update.message.reply_text(
        message,
        reply_markup=main_keyboard()
    )


# ============================================================
# LẤY DỮ LIỆU + PHÂN TÍCH MỘT MÃ
# ============================================================

def get_latest_stock(symbol):

    symbol = str(symbol).strip().upper()

    if not symbol:
        return None

    df = get_stock_data(symbol)

    if df is None or df.empty:
        return None

    try:
        result = process_universe(df)
    except Exception as e:
        print(f"Lỗi process {symbol}: {e}")
        return None

    if result is None or result.empty:
        return None

    result = result.sort_values("Date")

    row = result.iloc[-1]

    return row


# ============================================================
# TÍNH KẾ HOẠCH GIAO DỊCH
# ============================================================

def calculate_trade_plan(row):

    close = row.get("Close")
    atr14 = row.get("ATR14")
    signal = str(row.get("Signal", "GIỮ"))

    if pd.isna(close):
        return (
            "📌 KẾ HOẠCH GIAO DỊCH\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Chưa đủ dữ liệu để tính kế hoạch."
        )

    try:
        close = float(close)
    except Exception:
        return (
            "📌 KẾ HOẠCH GIAO DỊCH\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Giá hiện tại không hợp lệ."
        )

    if pd.isna(atr14) or float(atr14) <= 0:
        return (
            "📌 KẾ HOẠCH GIAO DỊCH\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"• Điểm vào tham chiếu: {format_price(close)}\n"
            "• Chưa đủ dữ liệu ATR14 để tính cắt lỗ và mục tiêu."
        )

    atr14 = float(atr14)

    # ========================================================
    # KẾ HOẠCH CHO TÍN HIỆU MUA
    # ========================================================

    if signal == "MUA":

        entry_price = close

        # Cắt lỗ = 3 ATR
        stop_loss = entry_price - (3 * atr14)

        # R:R = 1:2
        target_price = entry_price + (6 * atr14)

        # Không cho giá cắt lỗ âm
        stop_loss = max(stop_loss, 0)

        risk_amount = entry_price - stop_loss
        target_profit = target_price - entry_price

        if entry_price > 0:

            risk_percent = (
                risk_amount / entry_price
            ) * 100

            target_percent = (
                target_profit / entry_price
            ) * 100

        else:

            risk_percent = 0
            target_percent = 0

        return (
            "📌 KẾ HOẠCH GIAO DỊCH\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"🟢 Điểm vào: {format_price(entry_price)}\n"
            f"🛑 Cắt lỗ: {format_price(stop_loss)}\n"
            f"🎯 Mục tiêu: {format_price(target_price)}\n\n"
            f"📉 Rủi ro: {risk_percent:.2f}%\n"
            f"📈 Lợi nhuận mục tiêu: {target_percent:.2f}%\n"
            "⚖️ Risk/Reward: 1:2\n\n"
            "Cắt lỗ được xác định theo 3 × ATR14."
        )

    # ========================================================
    # KẾ HOẠCH CHO TÍN HIỆU GIỮ
    # ========================================================

    if signal == "GIỮ":

        entry_price = close

        stop_loss = entry_price - (3 * atr14)
        target_price = entry_price + (6 * atr14)

        stop_loss = max(stop_loss, 0)

        risk_percent = (
            (entry_price - stop_loss)
            / entry_price
            * 100
        )

        target_percent = (
            (target_price - entry_price)
            / entry_price
            * 100
        )

        return (
            "📌 KẾ HOẠCH THAM CHIẾU\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"• Điểm tham chiếu: {format_price(entry_price)}\n"
            f"• Cắt lỗ tham khảo: {format_price(stop_loss)}\n"
            f"• Mục tiêu tham khảo: {format_price(target_price)}\n\n"
            f"• Rủi ro: {risk_percent:.2f}%\n"
            f"• Lợi nhuận mục tiêu: {target_percent:.2f}%\n"
            "• Risk/Reward: 1:2\n\n"
            "⚠️ Chưa có tín hiệu MUA."
        )

    # ========================================================
    # KẾ HOẠCH CHO TÍN HIỆU BÁN
    # ========================================================

    if signal == "BÁN":

        return (
            "📌 KẾ HOẠCH XỬ LÝ\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"🔴 Trạng thái: Ưu tiên thoát vị thế\n"
            f"💰 Giá hiện tại: {format_price(close)}\n\n"
            "Hệ thống đang phát tín hiệu BÁN nên "
            "không thiết lập điểm vào mua mới."
        )

    return (
        "📌 KẾ HOẠCH GIAO DỊCH\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Giá hiện tại: {format_price(close)}\n"
        "Chưa xác định được kế hoạch giao dịch."
    )
# ============================================================
# NỘI DUNG PHÂN TÍCH
# ============================================================

def build_analysis_message(row):

    symbol = str(row.get("Symbol", "")).upper()

    close = row.get("Close")
    ema20 = row.get("EMA20")
    ema50 = row.get("EMA50")
    sma200 = row.get("SMA200")
    rs = row.get("RS")
    adx = row.get("ADX14")
    atr_ratio = row.get("ATR14_Ratio")
    liquidity = row.get("Liquidity_ok")
    signal = str(row.get("Signal", "GIỮ"))

    if signal == "MUA":
        signal_icon = "🟢"
    elif signal == "BÁN":
        signal_icon = "🔴"
    else:
        signal_icon = "🟡"

    lines = [
        f"📊 PHÂN TÍCH — {symbol}",
        "━━━━━━━━━━━━━━━━━━",
        "",
        f"💰 Giá hiện tại: {format_price(close)}",
        "",
        f"{signal_icon} TÍN HIỆU: {signal}",
        "",
    ]

    if signal == "MUA":
        reason = []

        if not pd.isna(rs) and float(rs) >= 60:
            reason.append("RS đạt điều kiện")

        if (
            not pd.isna(ema20)
            and not pd.isna(ema50)
            and float(ema20) > float(ema50)
        ):
            reason.append("EMA20 > EMA50")

        if (
            not pd.isna(close)
            and not pd.isna(sma200)
            and float(close) > float(sma200)
        ):
            reason.append("Giá > SMA200")

        if reason:
            lines.append("📝 NHẬN ĐỊNH")
            lines.append("Tín hiệu MUA do " + ", ".join(reason) + ".")

    elif signal == "BÁN":

        if not pd.isna(close) and not pd.isna(sma200):
            if float(close) < float(sma200):
                lines.append("📝 NHẬN ĐỊNH")
                lines.append("Tín hiệu BÁN do giá đóng cửa dưới SMA200.")
            elif not pd.isna(rs) and float(rs) < 50:
                lines.append("📝 NHẬN ĐỊNH")
                lines.append("Tín hiệu BÁN do RS dưới 50.")

    else:
        lines.append("📝 NHẬN ĐỊNH")
        lines.append(
            "Chưa xuất hiện đầy đủ điều kiện để phát tín hiệu MUA hoặc BÁN."
        )

    lines.append("")

    lines.append(calculate_trade_plan(row))

    lines.append("")
    lines.append(
        "⚠️ Đây là kết quả phân tích tự động, "
        "không phải khuyến nghị đầu tư."
    )

    return "\n".join(lines)


# ============================================================
# SMARTSCORE
# ============================================================

def build_stock_smartscore(row):

    symbol = str(row.get("Symbol", "")).upper()

    score = row.get("SmartScore")

    if pd.isna(score):
        score = row.get("smartscore")

    if pd.isna(score):
        score = 0

    try:
        score = float(score)
    except Exception:
        score = 0

    rs_score = 0
    ema_score = 0
    sma_score = 0
    liquidity_score = 0
    adx_score = 0
    anti_score = 0
    high_score = 0

    rs = row.get("RS")
    ema20 = row.get("EMA20")
    ema50 = row.get("EMA50")
    close = row.get("Close")
    sma200 = row.get("SMA200")
    liquidity = row.get("Liquidity_ok")
    adx = row.get("ADX14")
    anti_chasing = row.get("AntiChasing")
    near_high = row.get("PriceNearHigh_ok")

    # --------------------------------------------------------
    # Relative Strength — 30 điểm
    # --------------------------------------------------------

    if not pd.isna(rs):
        try:
            rs_score = min(max(float(rs) / 100 * 30, 0), 30)
        except Exception:
            rs_score = 0

    # --------------------------------------------------------
    # EMA20 / EMA50 — 20 điểm
    # --------------------------------------------------------

    if (
        not pd.isna(ema20)
        and not pd.isna(ema50)
        and float(ema20) > float(ema50)
    ):
        ema_score = 20

    # --------------------------------------------------------
    # SMA200 — 15 điểm
    # --------------------------------------------------------

    if (
        not pd.isna(close)
        and not pd.isna(sma200)
        and float(close) > float(sma200)
    ):
        sma_score = 15

    # --------------------------------------------------------
    # Liquidity — 15 điểm
    # --------------------------------------------------------

    if bool(liquidity):
        liquidity_score = 15

    # --------------------------------------------------------
    # ADX — 10 điểm
    # --------------------------------------------------------

    if not pd.isna(adx):

        try:
            adx_value = float(adx)

            if adx_value >= 20:
                adx_score = 10
            else:
                adx_score = max(adx_value / 20 * 10, 0)

        except Exception:
            adx_score = 0

    # --------------------------------------------------------
    # Anti-chasing — 5 điểm
    # --------------------------------------------------------

    if not pd.isna(anti_chasing):

        try:
            anti_value = float(anti_chasing)

            if anti_value <= 3:
                anti_score = 5
            elif anti_value <= 5:
                anti_score = 2.5

        except Exception:
            anti_score = 0

    # --------------------------------------------------------
    # Near 252-high — 5 điểm
    # --------------------------------------------------------

    if bool(near_high):
        high_score = 5

    calculated_score = (
        rs_score
        + ema_score
        + sma_score
        + liquidity_score
        + adx_score
        + anti_score
        + high_score
    )

    # Nếu module smartscore đã tính điểm thì ưu tiên điểm đó.
    # Nếu không có thì dùng điểm tính lại ở trên.
    if pd.isna(row.get("SmartScore")):
        score = calculated_score

    message = (
        f"⭐ SMARTSCORE — {symbol}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 Tổng điểm: {score:.1f}/100\n\n"
        "Chi tiết:\n"
        f"• Relative Strength: {rs_score:.1f}/30\n"
        f"• EMA20 / EMA50: {ema_score:.1f}/20\n"
        f"• SMA200: {sma_score:.1f}/15\n"
        f"• Thanh khoản: {liquidity_score:.1f}/15\n"
        f"• ADX: {adx_score:.1f}/10\n"
        f"• Anti-chasing: {anti_score:.1f}/5\n"
        f"• Gần đỉnh 252 phiên: {high_score:.1f}/5\n\n"
        "SmartScore được tính theo bộ tiêu chí của hệ thống."
    )

    return message


# ============================================================
# ĐỌC FILE NGÀNH
# ============================================================

def load_sector_data():

    if not os.path.exists(SECTOR_FILE):
        print(f"Không tìm thấy file: {SECTOR_FILE}")
        return pd.DataFrame()

    try:

        df = pd.read_csv(
            SECTOR_FILE,
            low_memory=False
        )

        if df.empty:
            return pd.DataFrame()

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )

        return df

    except Exception as e:

        print(f"Lỗi đọc {SECTOR_FILE}: {e}")

        return pd.DataFrame()


def get_sector_column(df):

    possible_columns = [
        "sector_vi",
        "Sector_VI",
        "sector",
        "Sector",
        "nganh",
        "Nganh",
        "Ngành",
    ]

    for column in possible_columns:
        if column in df.columns:
            return column

    return None


def get_symbol_column(df):

    possible_columns = [
        "ticker",
        "Ticker",
        "Symbol",
        "symbol",
        "MaCoPhieu",
        "MaCK",
        "ma_ck",
        "Mã cổ phiếu",
        "Mã CK",
    ]

    for column in possible_columns:
        if column in df.columns:
            return column

    return None


def get_stock_sector(symbol):

    symbol = str(symbol).strip().upper()

    df = load_sector_data()

    if df.empty:
        return None

    sector_column = get_sector_column(df)
    symbol_column = get_symbol_column(df)

    if sector_column is None or symbol_column is None:

        print("Không tìm thấy cột mã hoặc cột ngành.")

        print("Các cột hiện có:")
        print(df.columns.tolist())

        return None

    matched = df[
        df[symbol_column]
        .astype(str)
        .str.strip()
        .str.upper()
        == symbol
    ]

    if matched.empty:
        return None

    sector = matched.iloc[0][sector_column]

    if pd.isna(sector):
        return None

    sector = str(sector).strip()

    if not sector:
        return None

    # Nếu file đã chứa tiếng Việt
    if sector in SECTOR_VI.values():
        return sector

    # Nếu file chứa tiếng Anh
    if sector in SECTOR_VI:
        return SECTOR_VI[sector]

    if sector.lower() == "unknown":
        return "Chưa phân loại"

    return sector


# ============================================================
# HIỂN THỊ NGÀNH CỦA MÃ
# ============================================================

def build_sector_message(symbol):

    symbol = str(symbol).strip().upper()

    sector = get_stock_sector(symbol)

    if sector is None:

        return (
            f"🏭 NGÀNH — {symbol}\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Chưa tìm thấy thông tin ngành cho mã này."
        )

    return (
        f"🏭 NGÀNH — {symbol}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 Ngành: {sector}\n\n"
        f"Mã {symbol} thuộc nhóm {sector}."
    )


# ============================================================
# /TRACUU
# ============================================================

async def tracuu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "🔎 TRA CỨU CỔ PHIẾU\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Nhập mã cổ phiếu sau lệnh /tracuu.\n\n"
            "Ví dụ:\n"
            "/tracuu MCH"
        )

        return

    symbol = context.args[0].strip().upper()

    # Chỉ nhận mã đơn giản
    if not symbol.isalnum():

        await update.message.reply_text(
            "⚠️ Mã cổ phiếu không hợp lệ.\n\n"
            "Ví dụ: /tracuu MCH"
        )

        return

    await update.message.reply_text(
        f"🔎 Đang phân tích {symbol}..."
    )

    try:

        row = get_latest_stock(symbol)

    except Exception as e:

        print(f"Lỗi tra cứu {symbol}: {e}")

        await update.message.reply_text(
            f"❌ Không thể phân tích {symbol}.\n\n"
            f"Chi tiết lỗi: {e}"
        )

        return

    if row is None:

        await update.message.reply_text(
            f"❌ Không tìm thấy dữ liệu phù hợp cho {symbol}.\n\n"
            "Kiểm tra lại mã cổ phiếu và thử lại."
        )

        return

    # Đảm bảo mã hiển thị đúng
    if "Symbol" not in row.index:
        row["Symbol"] = symbol

    message = build_analysis_message(row)

    await update.message.reply_text(
        message,
        reply_markup=stock_detail_keyboard(symbol)
    )


# ============================================================
# XỬ LÝ BUTTON
# ============================================================

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data

    # --------------------------------------------------------
    # TRA CỨU
    # --------------------------------------------------------

    if data == "search":

        await query.message.reply_text(
            "🔎 TRA CỨU CỔ PHIẾU\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Nhập:\n"
            "/tracuu [Mã CK]\n\n"
            "Ví dụ:\n"
            "/tracuu MCH"
        )

        return

    # --------------------------------------------------------
    # HƯỚNG DẪN
    # --------------------------------------------------------

    if data == "help":

        message = (
            "❓ HƯỚNG DẪN FINBOT\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🔎 TRA CỨU\n"
            "Dùng lệnh:\n"
            "/tracuu [Mã CK]\n\n"
            "Ví dụ:\n"
            "/tracuu MCH\n\n"
            "Sau khi có kết quả, bạn có thể chọn:\n\n"
            "⭐ SMARTSCORE\n"
            "Xem điểm số của chính mã đang tra cứu.\n\n"
            "🏭 NGÀNH\n"
            "Xem ngành của chính mã đang tra cứu.\n\n"
            "📈 BIỂU ĐỒ\n"
            "Xem biểu đồ nến và các đường EMA/SMA.\n\n"
            "⚠️ Kết quả là phân tích tự động, "
            "không phải khuyến nghị đầu tư."
        )

        await query.message.reply_text(
            message,
            reply_markup=main_keyboard()
        )

        return

    # --------------------------------------------------------
    # SMARTSCORE
    # --------------------------------------------------------

    if data.startswith("smartscore:"):

        symbol = data.split(":", 1)[1].strip().upper()

        await query.message.reply_text(
            f"⭐ Đang tính SmartScore {symbol}..."
        )

        try:

            row = get_latest_stock(symbol)

        except Exception as e:

            print(f"Lỗi SmartScore {symbol}: {e}")

            await query.message.reply_text(
                f"❌ Không thể lấy SmartScore cho {symbol}."
            )

            return

        if row is None:

            await query.message.reply_text(
                f"❌ Không tìm thấy dữ liệu {symbol}."
            )

            return

        await query.message.reply_text(
            build_stock_smartscore(row),
            reply_markup=back_to_stock_keyboard(symbol)
        )

        return

    # --------------------------------------------------------
    # NGÀNH
    # --------------------------------------------------------

    if data.startswith("sector:"):

        symbol = data.split(":", 1)[1].strip().upper()

        message = build_sector_message(symbol)

        await query.message.reply_text(
            message,
            reply_markup=back_to_stock_keyboard(symbol)
        )

        return

    # --------------------------------------------------------
    # BIỂU ĐỒ
    # --------------------------------------------------------

    if data.startswith("chart:"):

        symbol = data.split(":", 1)[1].strip().upper()

        await query.message.reply_text(
            f"📈 Đang tạo biểu đồ {symbol}..."
        )

        try:

            image = create_candlestick_chart(
                symbol,
                periods=120
            )

            await query.message.reply_photo(
                photo=image,
                caption=(
                    f"📊 {symbol} - Biểu đồ nến 120 phiên\n"
                    "EMA20 • EMA50 • SMA200"
                ),
                reply_markup=back_to_stock_keyboard(symbol)
            )

        except Exception as e:

            print(f"Lỗi tạo chart {symbol}: {e}")

            await query.message.reply_text(
                f"❌ Không thể tạo biểu đồ {symbol}.\n\n"
                f"Chi tiết: {e}",
                reply_markup=back_to_stock_keyboard(symbol)
            )

        return

    # --------------------------------------------------------
    # MÃ KHÁC
    # --------------------------------------------------------

    if data == "search_other":

        await query.message.reply_text(
            "🔎 TRA CỨU MÃ KHÁC\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Nhập mã cổ phiếu cần phân tích.\n\n"
            "Ví dụ:\n"
            "/tracuu VIC"
        )

        return

    # --------------------------------------------------------
    # TRANG CHỦ
    # --------------------------------------------------------

    if data == "home":

        await query.message.reply_text(
            "🏠 FINBOT\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Chọn chức năng:",
            reply_markup=main_keyboard()
        )

        return


# ============================================================
# NHẬN TIN NHẮN TEXT
# ============================================================

async def text_stock_search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    if not text:
        return

    # Cho phép người dùng nhập trực tiếp:
    # MCH
    # VIC
    # FPT
    #
    # Nhưng không xử lý các câu quá dài.

    if len(text) > 10:
        return

    symbol = text.upper()

    if not symbol.isalnum():
        return

    await update.message.reply_text(
        f"🔎 Đang phân tích {symbol}..."
    )

    try:

        row = get_latest_stock(symbol)

    except Exception as e:

        print(f"Lỗi tra cứu {symbol}: {e}")

        await update.message.reply_text(
            f"❌ Không thể phân tích {symbol}."
        )

        return

    if row is None:

        await update.message.reply_text(
            f"❌ Không tìm thấy dữ liệu cho {symbol}.\n\n"
            "Bạn có thể thử lại bằng:\n"
            f"/tracuu {symbol}"
        )

        return

    message = build_analysis_message(row)

    await update.message.reply_text(
        message,
        reply_markup=stock_detail_keyboard(symbol)
    )


# ============================================================
# RUN BOT
# ============================================================

def run_bot():

    if not TOKEN:

        raise ValueError(
            "Chưa có TELEGRAM_BOT_TOKEN trong Environment Variables."
        )

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    # Commands
    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("tracuu", tracuu)
    )

    # Buttons
    application.add_handler(
        CallbackQueryHandler(button_callback)
    )

    # Text search
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_stock_search
        )
    )

    print("FINBOT đang chạy...")

    application.run_polling()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_bot()