import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =====================================================================
# 1. HÀM TẠO TIN NHẮN TÍN HIỆU
# =====================================================================
def format_signal_message(ticker: str, signal_type: str, stop_loss: float = 0, reason: str = "", regime: int = 2) -> str:
    ticker = ticker.upper()
    disclaimer = "\n\n<i>*Lưu ý: Tín hiệu từ Bot, NĐT tự chịu rủi ro khi giao dịch.</i>"
    
    if signal_type.upper() == "MUA":
        ty_trong = "1% vốn" if regime == 2 else "Giải ngân 50% quy mô chuẩn (Regime 1)"
        default_reason = "Đạt RS ≥ 80, vượt đỉnh 20 phiên, Vol nổ."
        msg = (
            f"🟢 <b>MUA: {ticker}</b>\n"
            f"• Lý do: {reason if reason else default_reason}\n"
            f"• Tỷ trọng: {ty_trong}\n"
            f"• Cắt lỗ: Thủng {stop_loss}"
        )
        return msg + disclaimer
        
    elif signal_type.upper() in ["BAN", "BÁN"]:
        default_reason = "Vi phạm nguyên tắc (Gãy SMA200 / Thủng Chandelier / RS < 50 / Regime 0)."
        msg = (
            f"🔴 <b>BÁN: {ticker}</b>\n"
            f"• Lý do: {reason if reason else default_reason}\n"
            f"• Hành động: Đóng toàn bộ vị thế. Đứng ngoài."
        )
        return msg + disclaimer
        
    elif signal_type.upper() in ["GIU", "GIỮ"]:
        msg = (
            f"🟡 <b>GIỮ: {ticker}</b>\n"
            f"• Trạng thái: Chưa vi phạm Bán, chưa đủ điều kiện Mua.\n"
            f"• Hành động: Tiếp tục giữ. Cài sẵn bán nếu thủng {stop_loss}."
        )
        return msg + disclaimer
        
    else:
        return "⚠️ Tín hiệu không hợp lệ."

# =====================================================================
# 2. HÀM XỬ LÝ LỆNH /signal
# =====================================================================
async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Vui lòng nhập mã cổ phiếu. Ví dụ: /signal FPT")
        return
        
    ma_ck = context.args[0].upper()
    
    # Dữ liệu giả lập (Sau này nhóm bạn thay bằng code gọi module xử lý thật)
    tin_hieu = "MUA"
    gia_stop_loss = 125.5
    trang_thai_regime = 2 
    
    noi_dung = format_signal_message(
        ticker=ma_ck, 
        signal_type=tin_hieu, 
        stop_loss=gia_stop_loss, 
        regime=trang_thai_regime
    )
    
    await update.message.reply_text(text=noi_dung, parse_mode='HTML')

# =====================================================================
# 3. HÀM MAIN KHỞI ĐỘNG BOT
# =====================================================================
def main():
    # Lấy token từ biến môi trường (Render)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("Lỗi: Chưa thiết lập TELEGRAM_BOT_TOKEN")
        return
        
    print("Bot đang khởi động và sẵn sàng nhận lệnh...")
    
    # Khởi tạo Application
    app = Application.builder().token(token).build()
    
    # Đăng ký lệnh /signal
    app.add_handler(CommandHandler("signal", signal_command))
    
    # Bắt đầu chạy ngầm để nhận tin nhắn
    app.run_polling()

if __name__ == "__main__":
    main()