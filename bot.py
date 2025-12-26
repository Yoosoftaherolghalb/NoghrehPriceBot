import asyncio  # اضافه کن بالای فایل
import logging
import time
import re
import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    JobQueue
)
from datetime import datetime




# ============ تنظیمات ============
BOT_TOKEN = "8450031409:AAFDIcNP5MS3HGsfL1vM7roLVEyJVK1uofo"
SILVER_999_URL = "https://www.tgju.org/profile/silver_999"
SILVER_925_URL = "https://www.tgju.org/profile/silver_925"
LOGO_PATH = "logo.png"  # نام فایل عکس لوگو که فرستادی

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.6,en;q=0.4",
    "Connection": "keep-alive",
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============ ابزارهای HTML ============
def fetch_html_with_retry(url: str, retries: int = 5, delay: int = 4) -> str | None:
    for i in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=25)
            html = resp.text
            if "Just a moment" in html or "cf-browser-verification" in html:
                time.sleep(delay)
                continue
            return html
        except Exception as e:
            logger.error(f"Error fetching HTML (try {i+1}): {e}")
            time.sleep(delay)
    return None


def extract_price_from_html(html: str) -> str | None:
    pattern = r"نرخ فعلی[^0-9]*([\d,]+)"
    matches = re.findall(pattern, html)
    candidates = []
    for m in matches:
        num_str = m.replace(",", "").strip()
        if num_str.isdigit():
            value = int(num_str)
            if value > 100_000:
                candidates.append(value)
    if not candidates:
        return None
    best = max(candidates)
    return f"{best:,}"


def format_price_message(title: str, price: str) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M")

    return (
        f"💰 *{title}*\n"
        f"━━━━━━━━━━━━━━\n"
        f"📅 تاریخ: {date_str}\n"
        f"⏰ ساعت: {time_str}\n"
        f"💵 قیمت: `{price} ریال`\n"
        f"━━━━━━━━━━━━━━"
    )

# ============ توابع قیمت ============
def get_silver_price_999() -> str | None:
    html = fetch_html_with_retry(SILVER_999_URL)
    if not html:
        return None
    return extract_price_from_html(html)


def get_silver_price_925() -> str | None:
    html = fetch_html_with_retry(SILVER_925_URL)
    if not html:
        return None
    return extract_price_from_html(html)


# ============ پیام‌های قالب‌بندی‌شده ============
def format_price_message(title: str, price: str) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M")

    return (
        f"💰 *{title}*\n"
        f"━━━━━━━━━━━━━━\n"
        f"📅 تاریخ: {date_str}\n"
        f"⏰ ساعت: {time_str}\n"
        f"💵 قیمت: `{price} ریال`\n"
        f"━━━━━━━━━━━━━━"
    )



# ============ هندلرهای ربات ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # اگر از CallbackQuery آمده، باید از query.message استفاده کنیم
    message = update.message or update.callback_query.message

    # ارسال لوگو
    with open(LOGO_PATH, "rb") as photo:
        await message.reply_photo(photo)

    keyboard = [
        [InlineKeyboardButton("💰 قیمت نقره 999", callback_data="silver_999")],
        [InlineKeyboardButton("💰 قیمت نقره 925", callback_data="silver_925")],
        [InlineKeyboardButton("🏪 اطلاعات فروشگاه", callback_data="shop_info")]
    ]

    await message.reply_text(
        "سلام، به ربات فروشگاه پیکو خوش اومدی 👋\nاز منوی زیر یکی را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "silver_999":
        price = get_silver_price_999()
        if not price:
            await query.edit_message_text("❗ خطا در دریافت قیمت نقره ۹۹۹.")
            return

        text = format_price_message("قیمت نقره ۹۹۹", price)
        keyboard = [
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="silver_999")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "silver_925":
        price = get_silver_price_925()
        if not price:
            await query.edit_message_text("❗ خطا در دریافت قیمت نقره ۹۲۵.")
            return

        text = format_price_message("قیمت نقره ۹۲۵", price)
        keyboard = [
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="silver_925")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "shop_info":
        text = (
            "🏪 *اطلاعات فروشگاه*\n\n"
            "📍 آدرس: یزد خیابان فضیلت\n"
            "📞 تلفن: 0912xxxxxxx\n"
            "⏰ ساعات کاری: 10 تا 20\n"
            "📦 ارسال به سراسر کشور"
        )
        keyboard = [[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "back_to_menu":
        await start(update, context)


# ============ ارسال خودکار روزانه ============
async def send_daily_price(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    price = get_silver_price_999()
    if not price:
        await context.bot.send_message(chat_id=chat_id, text="❗ خطا در دریافت قیمت نقره ۹۹۹.")
        return

    text = format_price_message("قیمت نقره ۹۹۹ (ارسال روزانه)", price)
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    job_queue: JobQueue = context.job_queue

    # ثبت ارسال روزانه ساعت ۱۱ صبح
    job_queue.run_daily(
        send_daily_price,
        time=time.strptime("11:00", "%H:%M"),
        chat_id=chat_id,
        name=f"daily_price_{chat_id}"
    )

    await update.message.reply_text("✅ ارسال روزانه قیمت نقره ۹۹۹ فعال شد (ساعت ۱۱ صبح).")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(f"daily_price_{chat_id}")
    for job in jobs:
        job.schedule_removal()

    await update.message.reply_text("❌ ارسال روزانه قیمت نقره ۹۹۹ غیرفعال شد.")


# ============ راه‌اندازی ربات ============
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()



if __name__ == "__main__":
    main()