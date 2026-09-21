from src.module_bot.telegram_bot import main
from keep_alive import keep_alive

if __name__ == "__main__":
    keep_alive() # Khởi động máy chủ web giả để báo cáo với Render
    main()       # Khởi động Bot Telegram