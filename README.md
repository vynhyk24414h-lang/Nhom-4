# 📈 XÂY DỰNG TELEGRAM BOT TÍN HIỆU ĐẦU TƯ CHỨNG KHOÁN (FINTECH BOT) - NHÓM 4

Dự án này là một hệ thống Fintech Bot tự động hóa hoàn toàn từ khâu thu thập dữ liệu thị trường (FireAnt), tính toán chỉ báo kỹ thuật (SMA, RS, ATR, Chandelier Stop), kiểm định chiến lược (Backtest) cho đến việc tự động bắn tín hiệu Mua/Bán qua ứng dụng Telegram.


## 🛠 Yêu cầu hệ thống (Prerequisites)
Để chạy được dự án này, máy tính của bạn cần cài đặt sẵn:
- **Python:** Phiên bản 3.9 trở lên.
- **Tài khoản Telegram:** Để tạo Bot và nhận tin nhắn.
- **Tài khoản FireAnt:** Để lấy Cookie xác thực API.

---

## ⚙️ Hướng dẫn cài đặt chi tiết (Installation)

### Bước 1: Cài đặt thư viện phụ thuộc
Mở Terminal (hoặc Command Prompt) tại thư mục chứa dự án và chạy lệnh sau để cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

### Bước 2: Thiết lập biến môi trường (File `.env`)
Trong thư mục gốc của dự án, bạn cần tạo một file có tên là `.env` (lưu ý có dấu chấm ở đầu) và điền các thông tin cấu hình theo mẫu sau:

```ini
# Cấu hình Telegram Bot
TELEGRAM_TOKEN=token_bot_cua_anh
TELEGRAM_CHAT_ID=chat_id_cua_anh

# Cấu hình FireAnt API (Bắt buộc để lấy dữ liệu)
FIREANT_COOKIE=cookie_fireant_cua_anh
```

**📌 Lưu ý về Token và Cookie:**
- **Telegram Token:** Thì anh tạo con bot Telegram khác, rồi anh lấy token anh đưa vào thôi.
- **FireAnt Cookie:** Còn cookie FireAnt thì anh tự đi lấy nhé.

---

## 🚀 Hướng dẫn sử dụng (Usage)

Dự án được chia thành các module độc lập. Bạn có thể chạy các tính năng tương ứng bằng các lệnh sau trên Terminal:

### 1. Thu thập dữ liệu
Nếu bạn chỉ muốn chạy riêng module cào dữ liệu mới nhất từ FireAnt và lưu ra file CSV:
```bash
python thu_thap_du_lieu.py
```

### 2. Chạy kiểm định chiến lược (Backtest)
Để xem hiệu suất của chiến lược trên dữ liệu lịch sử, tính toán Win Rate, Max Drawdown và lợi nhuận:
```bash
python run_backtest.py
```
*(Sau khi chạy xong, hệ thống sẽ tự động xuất ra các file báo cáo như `trades.csv`, `portfolio_history.csv`, `backtest_summary.csv`)*

### 3. Chạy Telegram Bot (Main)
Để hệ thống bắt đầu giám sát thị trường, tính toán tín hiệu và gửi cảnh báo trực tiếp về Telegram 24/7, hãy chạy file chính:
```bash
python main.py
```
Lúc này, bạn mở Telegram, nhắn `/start` với con Bot của bạn để bắt đầu tương tác và nhận nhận cảnh báo.

---

## 📂 Cấu trúc thư mục (Project Structure)

```text
Nhom_04_Project/
│
├── src/                               # Thư mục chứa mã nguồn cốt lõi (Core modules)
│   ├── data_fetcher/                  # Xử lý kết nối API Fireant và làm sạch dữ liệu
│   ├── processor/                     # Tính toán chỉ báo kỹ thuật (ATR, SMA, Chandelier)
│   ├── backtester/                    # Engine mô phỏng khớp lệnh và quản trị rủi ro
│   └── bot/                           # Logic điều phối và gửi tin nhắn Telegram Bot
│
├── DanhSachMaCoPhieu.csv              # Dữ liệu danh sách các mã cổ phiếu sàn HOSE/HNX
├── thu_thap_du_lieu.py                # Script thu thập dữ liệu độc lập
├── run_backtest.py                    # Script kích hoạt chạy Backtest
├── main.py                            # Script khởi chạy Bot Telegram
├── keep_alive.py                      # Script duy trì tiến trình chạy nền
├── .env                               # File chứa biến môi trường (Bảo mật)
├── requirements.txt                   # Danh sách thư viện Python cần cài đặt
└── README.md                          # Tài liệu hướng dẫn sử dụng (File này)
```

---
*Dự án được thực hiện phục vụ cho môn học Gói phần mềm ứng dụng trong Tài chính 1.*
