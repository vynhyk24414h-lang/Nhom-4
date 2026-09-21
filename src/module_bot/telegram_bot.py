import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from keep_alive import keep_alive

# Cố gắng import vnstock (bỏ qua nếu chạy test local chưa cài)
try:
    from vnstock import financial_ratio
except ImportError:
    financial_ratio = None

# --- [Giữ nguyên Hàm format_signal_message, start_command, help_command, tracuu_command, thitruong_command ở đây] ---
# (Để tiết kiệm không gian, tôi chỉ viết các hàm bắt buộc và lệnh mới. Bạn có thể tự nối các hàm cũ vào)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "👋 <b>Chào mừng bạn đến với Bot Theo Dõi Xu Hướng & FA!</b>\nGõ /help để xem lệnh."
    await update.message.reply_text(msg, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📚 <b>LỆNH BẮT BUỘC:</b>\n/tracuu [Mã] - Xem tín hiệu kỹ thuật\n/coban [Mã] - Xem Báo cáo tài chính"
    await update.message.reply_text(msg, parse_mode='HTML')

# =====================================================================
# LỆNH MỚI: TÍCH HỢP BÁO CÁO TÀI CHÍNH BẰNG VNSTOCK
# =====================================================================
async def coban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Vui lòng nhập mã cổ phiếu. VD: /coban FPT")
        return
        
    ma_ck = context.args[0].upper()
    
    # Báo cho người dùng bot đang xử lý (vì vnstock gọi API có thể mất 1-2 giây)
    processing_msg = await update.message.reply_text(f"⏳ Đang tra cứu Báo cáo tài chính cho {ma_ck}...")
    
    try:
        if financial_ratio is None:
            raise Exception("Chưa cài vnstock")
            
        # Lấy chỉ số tài chính theo năm
        df = financial_ratio(ma_ck, 'yearly', is_all=False)
        
        if df is not None and not df.empty:
            # Lấy dữ liệu của năm gần nhất
            pe = round(df['priceToEarning'].iloc[0], 2)
            pb = round(df['priceToBook'].iloc[0], 2)
            roe = round(df['roe'].iloc[0] * 100, 2)
            roa = round(df['roa'].iloc[0] * 100, 2)
            
            msg = (
                f"🏢 <b>GÓC NHÌN CƠ BẢN (FA): {ma_ck}</b>\n\n"
                f"📊 <b>Định giá & Hiệu quả:</b>\n"
                f"• P/E: {pe}\n"
                f"• P/B: {pb}\n"
                f"• ROE: {roe}%\n"
                f"• ROA: {roa}%\n\n"
                f"💡 <i>Nguồn: TCBS (cập nhật tự động)</i>"
            )
        else:
            msg = f"⚠️ Không tìm thấy dữ liệu BCTC cho {ma_ck}."
            
    except Exception as e:
        # Fallback nếu vnstock bị lỗi mạng hoặc mã sai
        msg = f"⚠️ Lỗi khi kéo dữ liệu tài chính cho {ma_ck}. Vui lòng thử lại sau."
        
    # Cập nhật trực tiếp vào tin nhắn "Đang tra cứu..." cho mượt mà
    await processing_msg.edit_text(msg, parse_mode='HTML')

# =====================================================================
# KHỞI ĐỘNG BOT
# =====================================================================
def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Lỗi: Chưa thiết lập TELEGRAM_BOT_TOKEN")
        return
        
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    # Thêm handler cho lệnh cơ bản
    app.add_handler(CommandHandler(["coban", "fa"], coban_command))
    
    app.run_polling()

if __name__ == "__main__":
    keep_alive() 
    main()