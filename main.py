import threading

from keep_alive import run_web
from src.module_bot.telegram_bot import run_bot


def start_web():
    run_web()


if __name__ == "__main__":
    # Chạy Flask ở thread riêng để Render nhận diện Web Service
    web_thread = threading.Thread(
        target=start_web,
        daemon=True
    )
    web_thread.start()

    # Chạy Telegram Bot như cũ
    run_bot()