# Bot Cảnh Báo Ngày Đại Kị — Telegram

## Logic: Đồng phase 3 tầng

| Tầng | Điều kiện | Ví dụ (Kỷ Sửu 2009, mệnh Hỏa) |
|------|-----------|-------------------------------|
| T1 | Can/Chi ngày khắc **mệnh nạp âm** | Can Nhâm/Quý (Thủy) khắc Hỏa |
| T2 | Chi ngày **xung** Chi năm sinh | Chi Mùi, Thìn, Tuất xung Sửu |
| T3 | Can ngày khắc **Can năm sinh** | Can Giáp/Ất (Mộc) khắc Kỷ (Thổ) |

- Score **≥ 2** → Đại kị → bot gửi cảnh báo
- Score **3** → Đại kị tuyệt đối 🔴
- Score **2** → Đại kị nặng 🟠
- Score **1** → Ngày kị nhẹ (không cảnh báo tự động)

---

## Cài đặt

### 1. Tạo Bot Token
1. Mở Telegram → tìm **@BotFather**
2. Gõ `/newbot` → đặt tên → lấy token dạng `123456:ABCdef...`

### 2. Cài môi trường

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Set token

```bash
export BOT_TOKEN="123456:ABCdef..."   # Linux/Mac
# set BOT_TOKEN=123456:ABCdef...      # Windows CMD
```

Hoặc sửa trực tiếp dòng này trong `bot.py`:
```python
BOT_TOKEN = "123456:ABCdef..."
```

### 4. Chạy

```bash
python bot.py
```

---

## Deploy 24/7 (miễn phí)

### Option A — Railway.app
1. Push code lên GitHub
2. Vào [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add variable: `BOT_TOKEN = your_token`
4. Deploy

### Option B — VPS (Ubuntu)

```bash
# Chạy nền với screen
screen -S dai_ki_bot
python bot.py
# Ctrl+A, D để detach

# Hoặc dùng systemd service
```

### Option C — Render.com
1. New Web Service → kết nối GitHub
2. Start command: `python bot.py`
3. Add env var: `BOT_TOKEN`

---

## Các lệnh Bot

| Lệnh | Mô tả |
|------|-------|
| `/start` | Đăng ký năm sinh, xem hồ sơ mệnh |
| `/homnay` | Check ngày hôm nay |
| `/thongke` | Xem toàn bộ ngày kị trong tháng |
| `/doi` | Đổi năm sinh |
| `/help` | Hướng dẫn |

---

## Lưu ý

- File `users.json` lưu dữ liệu người dùng (tự tạo khi chạy lần đầu)
- Nếu deploy lên cloud, dùng database thật (SQLite/PostgreSQL) thay `users.json`
- Timezone mặc định: **Asia/Ho_Chi_Minh (UTC+7)**
