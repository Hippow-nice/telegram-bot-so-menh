"""
Telegram Bot - Cảnh báo Ngày Đại Kị
Logic: Đồng phase 3 tầng (Mệnh Hỏa / Chi xung / Can khắc)
Multi-user, tự đăng ký năm sinh qua /start
Gửi cảnh báo 7:00 sáng hằng ngày nếu là ngày đại kị
"""

import os
import json
import asyncio
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters, JobQueue
)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DB_FILE   = "users.json"
TZ        = ZoneInfo("Asia/Ho_Chi_Minh")
ALERT_HOUR   = 7
ALERT_MINUTE = 0

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# NGŨ HÀNH - DỮ LIỆU NỀN
# ─────────────────────────────────────────────

# Can: index 0-9 → Giáp Ất Bính Đinh Mậu Kỷ Canh Tân Nhâm Quý
CAN_NAMES  = ["Giáp","Ất","Bính","Đinh","Mậu","Kỷ","Canh","Tân","Nhâm","Quý"]
CAN_HANH   = ["Mộc","Mộc","Hỏa","Hỏa","Thổ","Thổ","Kim","Kim","Thủy","Thủy"]

# Chi: index 0-11 → Tý Sửu Dần Mão Thìn Tị Ngọ Mùi Thân Dậu Tuất Hợi
CHI_NAMES  = ["Tý","Sửu","Dần","Mão","Thìn","Tị","Ngọ","Mùi","Thân","Dậu","Tuất","Hợi"]
CHI_HANH   = ["Thủy","Thổ","Mộc","Mộc","Thổ","Hỏa","Hỏa","Thổ","Kim","Kim","Thổ","Thủy"]

# Nạp âm (60 hoa giáp) — index = (can*12 + chi) / 2, lấy từ bảng chuẩn
# Encode: list 30 phần tử, mỗi phần tử là mệnh cho 2 năm liên tiếp
NAP_AM_TABLE = [
    "Kim","Kim","Thủy","Thủy","Hỏa","Hỏa",
    "Mộc","Mộc","Thổ","Thổ","Kim","Kim",
    "Thủy","Thủy","Hỏa","Hỏa","Thổ","Thổ",
    "Mộc","Mộc","Kim","Kim","Thủy","Thủy",
    "Hỏa","Hỏa","Mộc","Mộc","Thổ","Thổ",
]
# Bảng nạp âm chi tiết theo thứ tự 60 hoa giáp
NAP_AM_60 = [
    "Kim","Kim","Thủy","Thủy","Hỏa","Hỏa","Mộc","Mộc","Thổ","Thổ",
    "Kim","Kim","Thủy","Thủy","Hỏa","Hỏa","Thổ","Thổ","Mộc","Mộc",
    "Kim","Kim","Thủy","Thủy","Hỏa","Hỏa","Mộc","Mộc","Thổ","Thổ",
    "Kim","Kim","Thủy","Thủy","Hỏa","Hỏa","Thổ","Thổ","Mộc","Mộc",
    "Kim","Kim","Thủy","Thủy","Hỏa","Hỏa","Mộc","Mộc","Thổ","Thổ",
    "Kim","Kim","Thủy","Thủy","Hỏa","Hỏa","Thổ","Thổ","Mộc","Mộc",
]

# Bảng nạp âm chuẩn 60 hoa giáp (thứ tự Giáp Tý = 0)
NAPAM_CORRECT = {
    0:"Kim",1:"Kim",2:"Thủy",3:"Thủy",4:"Hỏa",5:"Hỏa",
    6:"Mộc",7:"Mộc",8:"Thổ",9:"Thổ",10:"Kim",11:"Kim",
    12:"Thủy",13:"Thủy",14:"Hỏa",15:"Hỏa",16:"Thổ",17:"Thổ",
    18:"Mộc",19:"Mộc",20:"Kim",21:"Kim",22:"Thủy",23:"Thủy",
    24:"Hỏa",25:"Hỏa",26:"Mộc",27:"Mộc",28:"Thổ",29:"Thổ",
    30:"Kim",31:"Kim",32:"Thủy",33:"Thủy",34:"Hỏa",35:"Hỏa",
    36:"Thổ",37:"Thổ",38:"Mộc",39:"Mộc",40:"Kim",41:"Kim",
    42:"Thủy",43:"Thủy",44:"Hỏa",45:"Hỏa",46:"Mộc",47:"Mộc",
    48:"Thổ",49:"Thổ",50:"Kim",51:"Kim",52:"Thủy",53:"Thủy",
    54:"Hỏa",55:"Hỏa",56:"Thổ",57:"Thổ",58:"Mộc",59:"Mộc",
}

# Khắc quan hệ: X bị khắc bởi Y
KHAC = {
    "Kim": "Hỏa",   # Hỏa khắc Kim
    "Mộc": "Kim",   # Kim khắc Mộc
    "Thủy": "Thổ",  # Thổ khắc Thủy
    "Hỏa": "Thủy",  # Thủy khắc Hỏa
    "Thổ": "Mộc",   # Mộc khắc Thổ
}

# Tứ hành xung (nhóm)
TU_HANH_XUNG = [
    {"Tý","Ngọ","Mão","Dậu"},
    {"Dần","Thân","Tị","Hợi"},
    {"Thìn","Tuất","Sửu","Mùi"},
]

# ─────────────────────────────────────────────
# LOGIC TÍNH TOÁN
# ─────────────────────────────────────────────

def year_to_can_chi(year: int) -> tuple[int, int]:
    """Trả về (can_idx, chi_idx) của năm dương lịch."""
    can = (year - 4) % 10
    chi = (year - 4) % 12
    return can, chi

def get_nap_am(year: int) -> str:
    """Mệnh nạp âm theo năm sinh."""
    can, chi = year_to_can_chi(year)
    idx = (can * 12 + chi) % 60
    return NAPAM_CORRECT[idx]

def date_to_can_chi(d: date) -> tuple[int, int]:
    """
    Tính Can Chi của ngày dương lịch.
    Giáp Tý = ngày 1/1/1924 (base chuẩn phổ biến).
    """
    base = date(1924, 1, 1)  # Giáp Tý
    delta = (d - base).days
    can = delta % 10
    chi = delta % 12
    return can, chi

def get_day_hanh(d: date) -> tuple[str, str, str, str]:
    """Trả về (can_name, chi_name, can_hanh, chi_hanh) của ngày."""
    can_idx, chi_idx = date_to_can_chi(d)
    return (
        CAN_NAMES[can_idx],
        CHI_NAMES[chi_idx],
        CAN_HANH[can_idx],
        CHI_HANH[chi_idx],
    )

def get_xung_group(chi_name: str) -> set:
    """Trả về nhóm tứ hành xung của chi."""
    for group in TU_HANH_XUNG:
        if chi_name in group:
            return group
    return set()

def score_day(birth_year: int, d: date) -> tuple[int, list[str]]:
    """
    Tính điểm kị của ngày d với người sinh năm birth_year.
    Trả về (score 0-3, list lý do).
    
    3 tầng:
      T1 — Mệnh nạp âm bị Can ngày khắc
      T2 — Địa chi năm sinh bị Chi ngày xung
      T3 — Thiên can năm sinh bị Can ngày khắc
    """
    score = 0
    reasons = []

    menh_napam = get_nap_am(birth_year)
    year_can_idx, year_chi_idx = year_to_can_chi(birth_year)
    year_can_hanh = CAN_HANH[year_can_idx]
    year_chi_name = CHI_NAMES[year_chi_idx]

    can_name, chi_name, can_hanh, chi_hanh = get_day_hanh(d)

    # Tầng 1: Can ngày khắc mệnh nạp âm
    if KHAC.get(menh_napam) == can_hanh:
        score += 1
        reasons.append(f"T1 — Can {can_name}({can_hanh}) khắc mệnh {menh_napam}")

    # Tầng 1b: Chi ngày khắc mệnh nạp âm (cộng thêm 0.5 → tính là 1 nếu chưa có T1)
    if KHAC.get(menh_napam) == chi_hanh and score == 0:
        score += 1
        reasons.append(f"T1b — Chi {chi_name}({chi_hanh}) khắc mệnh {menh_napam}")

    # Tầng 2: Chi ngày xung Chi năm sinh
    xung_group = get_xung_group(year_chi_name)
    if chi_name in xung_group and chi_name != year_chi_name:
        score += 1
        # Đối xung trực tiếp nặng hơn
        chi_idx = CHI_NAMES.index(chi_name)
        year_chi_idx2 = CHI_NAMES.index(year_chi_name)
        if abs(chi_idx - year_chi_idx2) == 6:
            reasons.append(f"T2 — Chi {chi_name} ĐỐI XUNG trực tiếp với {year_chi_name}")
        else:
            reasons.append(f"T2 — Chi {chi_name} xung nhóm với {year_chi_name}")

    # Tầng 3: Can ngày khắc Can năm sinh
    if KHAC.get(year_can_hanh) == can_hanh:
        score += 1
        reasons.append(f"T3 — Can {can_name}({can_hanh}) khắc Can năm({year_can_hanh})")

    return score, reasons

def get_severity(score: int) -> str:
    if score >= 3:
        return "🔴 ĐẠI KỊ TUYỆT ĐỐI"
    elif score == 2:
        return "🟠 ĐẠI KỊ NẶNG"
    elif score == 1:
        return "🟡 NGÀY KỊ NHẸ"
    return "✅ NGÀY BÌNH THƯỜNG"

def is_ki_day(birth_year: int, d: date, threshold: int = 2) -> bool:
    """Trả về True nếu ngày d là ngày kị (score >= threshold)."""
    score, _ = score_day(birth_year, d)
    return score >= threshold

def build_alert_message(birth_year: int, d: date) -> str | None:
    """Tạo message cảnh báo. Trả về None nếu không phải ngày kị."""
    score, reasons = score_day(birth_year, d)
    if score < 2:
        return None

    can_name, chi_name, _, _ = get_day_hanh(d)
    severity = get_severity(score)
    menh = get_nap_am(birth_year)
    _, year_chi_idx = year_to_can_chi(birth_year)
    year_chi = CHI_NAMES[year_chi_idx]

    lines = [
        f"📌 CẢNH BÁO NGÀY ĐẠI KỊ",
        f"━━━━━━━━━━━━━━━━━━",
        f"📅 {d.strftime('%d/%m/%Y')} — {can_name} {chi_name}",
        f"👤 Tuổi {year_chi} ({birth_year}) · Mệnh {menh}",
        f"",
        f"{severity}",
        f"",
        f"🔍 Lý do ({score}/3 tầng):",
    ]
    for r in reasons:
        lines.append(f"  • {r}")

    lines += [
        f"",
        f"⚠️ Vui lòng thận trọng trong giao dịch và quyết định quan trọng hôm nay.",
    ]
    return "\n".join(lines)

def get_monthly_ki_days(birth_year: int, year: int, month: int) -> list[tuple[date, int]]:
    """Lấy tất cả ngày kị trong tháng (score >= 2)."""
    import calendar
    result = []
    _, last_day = calendar.monthrange(year, month)
    for day in range(1, last_day + 1):
        d = date(year, month, day)
        score, _ = score_day(birth_year, d)
        if score >= 2:
            result.append((d, score))
    return result

# ─────────────────────────────────────────────
# DATABASE (JSON đơn giản)
# ─────────────────────────────────────────────

def load_users() -> dict:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def get_user(chat_id: int) -> dict | None:
    users = load_users()
    return users.get(str(chat_id))

def set_user(chat_id: int, data: dict):
    users = load_users()
    users[str(chat_id)] = data
    save_users(users)

# ─────────────────────────────────────────────
# CONVERSATION STATES
# ─────────────────────────────────────────────
ASK_YEAR = 0

# ─────────────────────────────────────────────
# HANDLERS
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)

    if user:
        await update.message.reply_text(
            f"👋 Chào lại! Mày đã đăng ký năm sinh *{user['birth_year']}*\.\n\n"
            f"Dùng /thongke để xem ngày kị tháng này.\n"
            f"Dùng /doi để đổi năm sinh.\n"
            f"Dùng /homnay để check ngày hôm nay.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🔮 *Bot Cảnh Báo Ngày Đại Kị*\n\n"
        "Logic: Đồng phase 3 tầng\n"
        "• T1 — Can/Chi ngày khắc mệnh nạp âm\n"
        "• T2 — Chi ngày xung Chi năm sinh\n"
        "• T3 — Can ngày khắc Can năm sinh\n\n"
        "👇 Nhập *năm sinh dương lịch* của mày (VD: 2009):",
        parse_mode="Markdown"
    )
    return ASK_YEAR

async def receive_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if not text.isdigit() or not (1920 <= int(text) <= 2010):
        await update.message.reply_text("❌ Năm sinh không hợp lệ. Nhập lại (VD: 2009):")
        return ASK_YEAR

    birth_year = int(text)
    menh = get_nap_am(birth_year)
    can_idx, chi_idx = year_to_can_chi(birth_year)
    can = CAN_NAMES[can_idx]
    chi = CHI_NAMES[chi_idx]

    set_user(chat_id, {
        "birth_year": birth_year,
        "can": can,
        "chi": chi,
        "menh": menh,
        "chat_id": chat_id,
    })

    await update.message.reply_text(
        f"✅ Đã đăng ký!\n\n"
        f"📋 Hồ sơ mệnh:\n"
        f"  • Năm sinh: {birth_year} ({can} {chi})\n"
        f"  • Mệnh nạp âm: {menh}\n"
        f"  • Can năm: {can} ({CAN_HANH[can_idx]})\n"
        f"  • Chi năm: {chi}\n\n"
        f"🔔 Bot sẽ gửi cảnh báo lúc *7:00 sáng* vào các ngày đại kị.\n\n"
        f"Dùng /thongke để xem ngày kị tháng này ngay.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cmd_doi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Nhập năm sinh mới:")
    return ASK_YEAR

async def cmd_homnay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if not user:
        await update.message.reply_text("Mày chưa đăng ký. Dùng /start nhé.")
        return

    today = datetime.now(TZ).date()
    score, reasons = score_day(user["birth_year"], today)
    can_name, chi_name, _, _ = get_day_hanh(today)
    severity = get_severity(score)

    lines = [
        f"📅 Hôm nay: {today.strftime('%d/%m/%Y')} — {can_name} {chi_name}",
        f"",
        f"{severity} (điểm: {score}/3)",
    ]
    if reasons:
        lines.append("\n🔍 Chi tiết:")
        for r in reasons:
            lines.append(f"  • {r}")

    await update.message.reply_text("\n".join(lines))

async def cmd_thongke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if not user:
        await update.message.reply_text("Mày chưa đăng ký. Dùng /start nhé.")
        return

    now = datetime.now(TZ)
    ki_days = get_monthly_ki_days(user["birth_year"], now.year, now.month)

    if not ki_days:
        await update.message.reply_text(f"✅ Tháng {now.month}/{now.year} không có ngày đại kị (≥2 tầng).")
        return

    lines = [f"📆 Ngày đại kị tháng {now.month}/{now.year}:", ""]
    for d, score in ki_days:
        can_name, chi_name, _, _ = get_day_hanh(d)
        icon = "🔴" if score >= 3 else "🟠"
        lines.append(f"{icon} *{d.strftime('%d/%m/%Y')}* ({can_name} {chi_name}) — {score}/3 tầng")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Các lệnh:*\n\n"
        "/start — Đăng ký năm sinh\n"
        "/homnay — Check ngày hôm nay\n"
        "/thongke — Xem ngày kị cả tháng\n"
        "/doi — Đổi năm sinh\n"
        "/help — Hướng dẫn\n\n"
        "🔔 Bot tự động cảnh báo lúc 7:00 sáng vào các ngày đại kị (score ≥ 2/3 tầng).",
        parse_mode="Markdown"
    )

# ─────────────────────────────────────────────
# SCHEDULED JOB — 7:00 sáng hằng ngày
# ─────────────────────────────────────────────

async def daily_alert_job(context: ContextTypes.DEFAULT_TYPE):
    """Chạy mỗi ngày lúc 7:00 — gửi cảnh báo cho user có ngày kị."""
    today = datetime.now(TZ).date()
    users = load_users()
    sent = 0

    for chat_id_str, user in users.items():
        try:
            msg = build_alert_message(user["birth_year"], today)
            if msg:
                await context.bot.send_message(
                    chat_id=int(chat_id_str),
                    text=msg,
                )
                sent += 1
        except Exception as e:
            logger.error(f"Lỗi gửi cho {chat_id_str}: {e}")

    logger.info(f"Daily alert job: {today} — đã gửi {sent}/{len(users)} users")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation: đăng ký năm sinh
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("doi", cmd_doi),
        ],
        states={
            ASK_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_year)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("homnay", cmd_homnay))
    app.add_handler(CommandHandler("thongke", cmd_thongke))
    app.add_handler(CommandHandler("help", cmd_help))

    # Job 7:00 sáng hằng ngày (Asia/Ho_Chi_Minh)
    job_queue: JobQueue = app.job_queue
    from datetime import time as dtime
    job_queue.run_daily(
        daily_alert_job,
        time=dtime(hour=ALERT_HOUR, minute=ALERT_MINUTE, tzinfo=TZ),
    )

    logger.info("Bot started. Polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
