# 📈 TELEGRAM BOT TÍN HIỆU ĐẦU TƯ CHỨNG KHOÁN (FINTECH BOT) - NHÓM 4

Dự án này là hệ thống Bot Telegram tự động thu thập dữ liệu chứng khoán realtime từ Vietcap, tính toán các chỉ báo kỹ thuật (FA, Trend, Momentum) và tự động lọc/gửi tín hiệu Mua/Bán trực tiếp đến người dùng qua Telegram.

---

## 🛠 1. Yêu cầu hệ thống (Prerequisites)
Trước khi cài đặt, máy tính của bạn cần có sẵn:
- **Python:** Phiên bản 3.9 trở lên (Khuyến nghị 3.10+). Tải tại [python.org](https://www.python.org/).
- **Trình soạn thảo:** Visual Studio Code (VS Code) hoặc bất kỳ IDE nào hỗ trợ Python.
- **Tài khoản Telegram:** Để tạo Bot và lấy Token xác thực.

---

## 🚀 2. Hướng dẫn cài đặt chi tiết (Dành cho người mới)

**Bước 1: Tải mã nguồn về máy**
Mở Terminal (hoặc Command Prompt) và chạy lệnh sau để kéo mã nguồn về máy tính:
```bash
git clone [https://github.com/vynhyk24414h-lang/Nhom-4.git](https://github.com/vynhyk24414h-lang/Nhom-4.git)
cd Nhom-4
```

**Bước 2: Cài đặt các thư viện cần thiết**
Bật Terminal bên trong VS Code, đảm bảo bạn đang ở đúng thư mục `Nhom-4`, sau đó chạy lệnh:
```bash
python -m pip install -r requirements.txt
```
*(Lệnh này sẽ tự động tải toàn bộ các công cụ cần thiết như pandas, python-telegram-bot, requests... để bot hoạt động).*

**Bước 3: Cấu hình biến môi trường (Bảo mật)**
Để Bot hoạt động và kết nối được với Vietcap, bạn cần cung cấp "chìa khóa". 
1. Tạo một file mới tinh ngay trong thư mục gốc `Nhom-4` và đặt tên là `.env` (lưu ý có dấu chấm ở đầu).
2. Mở file `.env` và dán nội dung sau vào:

```env
# Thay đoạn 'điền_token_vào_đây' bằng HTTP API Token lấy từ @BotFather trên Telegram
TELEGRAM_BOT_TOKEN=điền_token_vào_đây

# Cấu hình tài khoản hệ thống xác thực Vietcap (Giữ nguyên)
LOKI_USERNAME=loki
LOKI_PASSWORD=psz9uek1qfh%pjMg@g#K
```
3. Nhấn `Ctrl + S` để lưu file. **Tuyệt đối không gửi file .env này lên GitHub.**

---

## ▶️ 3. Khởi chạy Bot

Mở Terminal trong VS Code và gõ lệnh:
```bash
python main.py
```
Nếu màn hình Terminal hiện ra dòng chữ `Bot đang khởi động và sẵn sàng nhận lệnh...`, xin chúc mừng! Hệ thống của bạn đã chạy thành công. 

Bây giờ, hãy mở ứng dụng Telegram, tìm kiếm Bot của bạn và bấm **Start** (hoặc gõ `/start`) để trải nghiệm.

---

## 📂 4. Kiến trúc mã nguồn (Project Structure)
Dự án được thiết kế theo cấu trúc module độc lập để dễ bảo trì và mở rộng:

* `src/module_thu_thap_du_lieu/`: Gửi request đến API Vietcap, xử lý dữ liệu realtime và quản lý cơ chế xác thực Token tự động làm mới sau mỗi 55 phút.
* `src/module_tinh_toan_xu_ly/`: Đảm nhận việc xử lý dữ liệu thô, tính toán các chỉ báo kỹ thuật (ADX, ATR, EMA, MACD, RSI, SuperTrend) và lọc theo chiến lược 4 tầng.
* `src/module_bot/`: Giao diện tương tác người dùng qua Telegram, nhận lệnh từ người dùng và trả về tín hiệu trực quan.
* `src/module_backtest/`: Kiểm thử hiệu quả của chiến lược đầu tư dựa trên dữ liệu lịch sử.
* `main.py`: File khởi động trung tâm, điểm vào (entry point) của toàn bộ hệ thống.

---

## ⌨️ 5. Danh sách lệnh Bot hỗ trợ
Người dùng có thể tương tác trực tiếp với bot thông qua các nút bấm trên màn hình hoặc gõ tay các lệnh sau:
- `/start` : Bắt đầu và hiển thị Menu điều khiển.
- `/help` : Hướng dẫn chi tiết cách dùng.
- `/market`: Cập nhật bản tin thị trường (VNINDEX, Thanh khoản, Độ rộng).
- `/signal <Mã_CK>`: Tra cứu tín hiệu của một mã cụ thể (Ví dụ: `/signal FPT`).
- `/chart <Mã_CK>`: Xem biểu đồ phân tích kỹ thuật.
- `/alert <Mã_CK> <Giá>`: Đặt lệnh canh báo giá (Ví dụ: `/alert HPG 30`).