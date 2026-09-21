import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from keep_alive import keep_alive  # Bắt buộc để Render không tắt bot

# =====================================================================
# 1. HÀM ĐỊNH DẠNG TIN NHẮN (UI RÚT GỌN)
# =====================================================================
def format_signal_message(ticker: str, signal_type: str, stop_loss: float = 0, reason: str = "", regime: int = 2) -> str:
    ticker = ticker.upper()
    if signal_type.upper() == "MUA":
        ty_trong = "100% tỷ trọng quy định" if regime == 2 else "50% quy mô chuẩn (Regime 1)"
        msg = (f"🟢 <b>MUA: {ticker}</b>\n"
               f"• Lý do: {reason if reason else 'Đạt RS ≥ 80, Vượt đỉnh 20 phiên, Vol nổ'}\n"
               f"• Giải ngân: {ty_trong}\n"
               f"• Cắt lỗ: Thủng {stop_loss}")
    elif signal_type.upper() in ["BAN", "BÁN"]:
        msg = (f"🔴 <b>BÁN: {ticker}</b>\n"
               f"• Lý do: {reason if reason else 'Vi phạm nguyên tắc nắm giữ'}\n"
               f"• Hành động: Đóng vị thế, đứng ngoài.")
    elif signal_type.upper() in ["GIU", "GIỮ"]:
        msg = (f"🟡 <b>GIỮ: {ticker}</b>\n"
               f"• Trạng thái: Đi ngang/Tích lũy. Chưa đủ điều kiện MUA.\n"
               f"• Hành động: Tiếp tục giữ, bán nếu thủng {stop_loss}")
    else:
        msg = "⚠️ Tín hiệu không hợp lệ."
    return msg

# =====================================================================
# 2. CÁC HÀM XỬ LÝ LỆNH BẮT BUỘC (MỨC 1)
# =====================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 <b>Chào mừng bạn đến với hệ thống Bot Theo Dõi Xu Hướng!</b>\n\n"
        "Hệ thống sử dụng chiến lược phân tích kỹ thuật 5 tầng (trend-following), "
        "kết hợp xếp hạng sức mạnh (RS) và bộ lọc Regime.\n\n"
        "Gõ /help để xem danh sách các lệnh hỗ trợ.\n\n"
        "<i>*Lưu ý: Đây là tín hiệu kỹ thuật, không phải tư vấn đầu tư cá nhân hóa và không đảm bảo xác nhận khớp lệnh. Người dùng tự chịu rủi ro.</i>"
    )
    await update.message.reply_text(msg, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📚 <b>DANH SÁCH LỆNH CƠ BẢN:</b>\n"
        "/start - Giới thiệu và lưu ý rủi ro\n"
        "/help - Xem danh sách lệnh\n"
        "/tinhieu - Xem danh sách tín hiệu MUA/BÁN hôm nay\n"
        "/tracuu [Mã CK] - Phân tích chi tiết 1 mã (VD: /tracuu FPT)\n"
        "/thitruong - Xem trạng thái Regime và độ rộng thị trường\n"
        "/dangky - Nhận cảnh báo tự động\n"
        "/huydangky - Tắt cảnh báo tự động"
    )
    await update.message.reply_text(msg, parse_mode='HTML')

async def tracuu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /tracuu FPT hoặc /signal FPT"""
    if not context.args:
        await update.message.reply_text("⚠️ Vui lòng nhập mã cổ phiếu. Ví dụ: /tracuu FPT")
        return
        
    ma_ck = context.args[0].upper()
    
    # [TÍNH TRƯỚC, TRA CỨU SAU] 
    # TODO: Kết nối Database hoặc đọc file CSV tại đây để lấy dữ liệu thay vì gọi API.
    # Dưới đây là dữ liệu giả lập:
    tin_hieu = "MUA"
    gia_stop_loss = 125.5
    trang_thai_regime = 2 
    ly_do = "Thỏa mãn 5 tầng lọc. RS=85."
    
    noi_dung = format_signal_message(ma_ck, tin_hieu, gia_stop_loss, ly_do, trang_thai_regime)
    disclaimer = "\n\n<i>*Dữ liệu tạm thời trong phiên. Tín hiệu chính thức xác nhận sau đóng cửa.</i>"
    
    await update.message.reply_text(text=noi_dung + disclaimer, parse_mode='HTML')

async def thitruong_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO: Lấy dữ liệu Regime từ Database/CSV
    msg = (
        "📊 <b>TRẠNG THÁI THỊ TRƯỜNG CHUNG</b>\n"
        "• Regime hiện tại: 2 (Thị trường thuận lợi - Risk on)\n"
        "• VN-Index: Nằm trên đường SMA200\n"
        "• Độ rộng thị trường: > 50% mã vượt SMA50\n"
        "👉 Gợi ý hành động: Tỷ trọng giải ngân 100% quy mô chuẩn."
    )
    await update.message.reply_text(msg, parse_mode='HTML')

async def feature_in_development(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hàm tạm cho các lệnh chưa code xong"""
    await update.message.reply_text("🚧 Tính năng đang được phát triển, vui lòng quay lại sau!")

# =====================================================================
# 3. KHỞI ĐỘNG BOT
# =====================================================================
def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Lỗi: Chưa thiết lập TELEGRAM_BOT_TOKEN")
        return
        
    print("Bot đang khởi động và sẵn sàng nhận lệnh...")
    
    app = Application.builder().token(token).build()
    
    # Khai báo các lệnh
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler(["tracuu", "signal"], tracuu_command))
    app.add_handler(CommandHandler("thitruong", thitruong_command))
    
    # Các lệnh đang chờ phát triển thêm (Mức 1 & 2)
    app.add_handler(CommandHandler(["tinhieu", "dangky", "huydangky", "giu", "bo", "danhmuc"], feature_in_development))
    
    app.run_polling()

if __name__ == "__main__":
    # Bật máy chủ ảo để Render không sleep Bot
    keep_alive() 
    main()