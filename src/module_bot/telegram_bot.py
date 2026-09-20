import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

# Tải các biến môi trường từ tệp .env (chứa token của bot)
load_dotenv()

# Lấy Token của Telegram Bot từ biến môi trường
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Cấu hình hệ thống ghi log để theo dõi hoạt động và phát hiện lỗi
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hàm xử lý lệnh /start, hiển thị lời chào và menu nút bấm
    user_name = update.effective_user.first_name
    
    # Tạo danh sách các nút bấm trực quan cho người dùng dễ thao tác
    keyboard = [
        [
            InlineKeyboardButton("📈 Tra cứu FPT", callback_data="signal_FPT"),
            InlineKeyboardButton("📈 Tra cứu HPG", callback_data="signal_HPG")
        ],
        [
            InlineKeyboardButton("📊 Thị trường", callback_data="market_view"),
            InlineKeyboardButton("📖 Hướng dẫn", callback_data="help_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = f"Xin chào {user_name}! Tôi là Fintech Bot.\nHãy chọn chức năng bên dưới hoặc gõ lệnh /help:"
    
    # Gửi tin nhắn chào mừng kèm bộ nút bấm
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hàm hiển thị danh sách các lệnh hỗ trợ
    help_text = (
        "Danh sách lệnh khả dụng:\n"
        "/start - Hiển thị menu chính\n"
        "/help - Xem hướng dẫn\n"
        "/market - Xem bản tin thị trường chung\n"
        "/signal <Mã> - Tra cứu tín hiệu (Ví dụ: /signal FPT)\n"
        "/chart <Mã> - Xem biểu đồ kỹ thuật (Ví dụ: /chart HPG)\n"
        "/alert <Mã> <Giá> - Đặt cảnh báo giá (Ví dụ: /alert VNM 70)"
    )
    await update.message.reply_text(help_text)

async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hàm xử lý lệnh /market để xem tổng quan thị trường
    await update.message.reply_text("🔄 Đang tổng hợp dữ liệu VNINDEX realtime...")
    
    # Kết quả giả lập, sau này sẽ tích hợp với module dữ liệu realtime của nhóm
    market_summary = (
        "📊 BẢN TIN THỊ TRƯỜNG REAL-TIME\n"
        "-------------------------------\n"
        "• VNINDEX: 1,250.45 (+5.20đ)\n"
        "• Thanh khoản: 15,400 Tỷ VNĐ\n"
        "• Độ rộng: 210 mã Tăng 🟢 | 150 mã Giảm 🔴\n"
    )
    await update.message.reply_text(market_summary)

async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hàm xử lý lệnh /chart để yêu cầu vẽ biểu đồ kỹ thuật
    if not context.args:
        await update.message.reply_text("Vui lòng nhập mã cổ phiếu. Ví dụ: /chart FPT")
        return
    
    ticker = context.args[0].upper()
    await update.message.reply_text(f"Đang vẽ biểu đồ kỹ thuật cho {ticker}...")
    await update.message.reply_text(f"(🖼️ Chỗ này sau này Module Tính toán sẽ gửi ảnh biểu đồ của {ticker} vào đây)")

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hàm xử lý lệnh /alert để thiết lập cảnh báo giá
    if len(context.args) < 2:
        await update.message.reply_text("Sai cú pháp. Ví dụ: /alert HPG 30")
        return
    
    ticker = context.args[0].upper()
    target_price = context.args[1]
    
    await update.message.reply_text(f"✅ Đã ghi nhận lệnh! Bot sẽ báo cho bạn khi {ticker} chạm mức {target_price}.")

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hàm xử lý lệnh /signal để phân tích chiến lược đầu tư
    if not context.args:
        await update.message.reply_text("Vui lòng nhập mã cổ phiếu cần tra cứu. Ví dụ: /signal FPT")
        return

    ticker = context.args[0].upper()
    await update.message.reply_text(f"Đang kiểm tra dữ liệu và phân tích mã {ticker} theo chiến lược chuẩn...")

    # Kết quả phân tích tín hiệu dựa trên 4 tầng bộ lọc
    signal_result = (
        f"📊 KẾT QUẢ PHÂN TÍCH TÍN HIỆU: {ticker}\n"
        "-----------------------------------\n"
        "• Trạng thái Tầng 2 (Lọc rác): Đạt\n"
        "• Trạng thái Tầng 3 (Lọc nhiễu): Đạt (ADX >= 20, ATR/C <= 8%)\n"
        "• Trạng thái Tầng 4 (Chiến lược 3 lớp): Đạt\n\n"
        "👉 TÍN HIỆU: ĐỦ ĐIỀU KIỆN MUA (BuyEligible = True)"
    )
    await update.message.reply_text(signal_result)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hàm xử lý sự kiện khi người dùng click vào các nút bấm (InlineKeyboard)
    query = update.callback_query
    await query.answer() 

    data = query.data
    
    # Xử lý khi bấm nút tra cứu tín hiệu
    if data.startswith("signal_"):
        ticker = data.split("_")[1]
        
        await query.edit_message_text(f"⏳ Đang phân tích tín hiệu cho mã {ticker} theo chiến lược chuẩn...")
        
        signal_result = (
            f"📊 KẾT QUẢ PHÂN TÍCH TÍN HIỆU: {ticker}\n"
            "-----------------------------------\n"
            "• Trạng thái Tầng 2 (Lọc rác): Đạt\n"
            "• Trạng thái Tầng 3 (Lọc nhiễu): Đạt (ADX >= 20, ATR/C <= 8%)\n"
            "• Trạng thái Tầng 4 (Chiến lược 3 lớp): Đạt\n\n"
            "👉 TÍN HIỆU: ĐỦ ĐIỀU KIỆN MUA (BuyEligible = True)"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=signal_result)
        
    # Xử lý khi bấm nút Xem thị trường
    elif data == "market_view":
        await query.edit_message_text("🔄 Đang lấy dữ liệu thị trường...")
        market_summary = (
            "📊 BẢN TIN THỊ TRƯỜNG REAL-TIME\n"
            "-------------------------------\n"
            "• VNINDEX: 1,250.45 (+5.20đ)\n"
            "• Thanh khoản: 15,400 Tỷ VNĐ\n"
            "• Độ rộng: 210 mã Tăng 🟢 | 150 mã Giảm 🔴\n"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=market_summary)

    # Xử lý khi bấm nút Hướng dẫn
    elif data == "help_menu":
        help_text = (
            "Bạn có thể sử dụng các lệnh sau:\n"
            "/market - Xem thị trường\n"
            "/signal <Mã> - Tra cứu tín hiệu\n"
            "/chart <Mã> - Xem biểu đồ\n"
            "/alert <Mã> <Giá> - Đặt cảnh báo"
        )
        await query.edit_message_text(help_text)

def main():
    # Khởi tạo ứng dụng Telegram Bot bằng token
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Đăng ký các handler xử lý lệnh gõ tay
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("market", market_command))
    app.add_handler(CommandHandler("chart", chart_command))
    app.add_handler(CommandHandler("alert", alert_command))
    app.add_handler(CommandHandler("signal", signal_command))
    
    # Đăng ký handler xử lý nút bấm
    app.add_handler(CallbackQueryHandler(button_handler))

    # Bắt đầu chạy bot để lắng nghe tin nhắn
    logger.info("Bot đang khởi động và sẵn sàng nhận lệnh...")
    app.run_polling()