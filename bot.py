# pip install "python-telegram-bot[job-queue]" requests

import logging
import requests
import os
import asyncio
from datetime import datetime, time, timezone, timedelta
from typing import Dict
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

# --- НАСТРОЙКИ ---
TELEGRAM_BOT_TOKEN = '8247116313:AAGVL3d_3SNPPYI7Wroo8nSE4HhAoEQkKlI'
ALLOWED_CHAT_IDS = [575531308, 753075180]

API_URL = 'https://api.kufar.by/search-api/v2/search/rendered-paginated?cat=1010&cmp=0&cur=USD&gtsy=country-belarus~province-minsk~locality-minsk&lang=ru&prc=r:0,360&rms=v.or:1&size=30&sort=lst.d&typ=let'
HEADERS = {
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
}

CHECK_INTERVAL = 60
SENT_ADS_FILE = 'sent_ads.txt'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


# === РАБОТА С ФАЙЛОМ sent_ads.txt ===
def load_sent_ads() -> Dict[str, datetime]:
    """Загружает {ad_id: datetime} из файла."""
    if not os.path.exists(SENT_ADS_FILE):
        return {}
    result = {}
    with open(SENT_ADS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ad_id, date_str = line.split(' ', 1)
                result[ad_id] = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Ошибка парсинга строки: {line} — {e}")
    return result


async def clean_old_ads(context: ContextTypes.DEFAULT_TYPE):
    """Очищает sent_ads.txt, оставляя последние 30 записей по дате."""
    logger.info("Запуск очистки sent_ads.txt...")
    ads = load_sent_ads()
    if len(ads) <= 30:
        logger.info(f"Записей {len(ads)} <= 30, очистка не требуется")
        return

    # Сортируем по дате (от новых к старым)
    sorted_ads = sorted(ads.items(), key=lambda x: x[1], reverse=True)
    # Оставляем только 30 последних
    latest_ads = sorted_ads[:30]

    # Перезаписываем файл
    with open(SENT_ADS_FILE, 'w', encoding='utf-8') as f:
        for ad_id, dt in latest_ads:
            iso = dt.isoformat().replace('+00:00', 'Z')
            f.write(f"{ad_id} {iso}\n")

    logger.info(f"Очищено {len(ads) - 30} записей, оставлено 30")


def save_sent_ad(ad_id: str, pub_date: datetime):
    """Добавляет ad_id и дату в файл, только если ad_id ещё нет."""
    ads = load_sent_ads()
    if ad_id in ads:
        logger.debug(f"ad_id {ad_id} уже существует — пропускаем сохранение")
        return

    iso_date = pub_date.isoformat().replace('+00:00', 'Z')
    with open(SENT_ADS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{ad_id} {iso_date}\n")
    logger.debug(f"Сохранено новое: {ad_id} {iso_date}")


def get_latest_pub_date() -> datetime:
    """Возвращает самую свежую дату из sent_ads.txt."""
    ads = load_sent_ads()
    if not ads:
        return datetime.now(timezone.utc) - timedelta(hours=3)
    return max(ads.values())


# === УТИЛИТЫ ===
def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if context.job_queue is None:
        return False
    jobs = context.job_queue.get_jobs_by_name(name)
    if not jobs:
        return False
    for job in jobs:
        job.schedule_removal()
    return True


# === API ===
async def fetch_ads():
    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data.get('ads', [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return []


# === ОТПРАВКА СООБЩЕНИЙ ===
async def send_ad_notification(context: ContextTypes.DEFAULT_TYPE, chat_id: int, ad: dict, notification_text: str = ""):
    link = ad.get('ad_link', 'Нет ссылки')
    subject = ad.get('subject', 'Без заголовка')
    description = ad.get('body_short', 'Нет описания').strip()
    address = 'Не указан'
    size = 'N/A'
    floor = 'N/A'
    
    price_raw = ad.get('price_usd')
    price_usd = f"{int(price_raw) / 100.0:.2f}" if price_raw and price_raw.isdigit() else 'N/A'

    for param in ad.get('account_parameters', []):
        if param.get('p') == 'address':
            address = param.get('v', 'Не указан')
            break
    for param in ad.get('ad_parameters', []):
        if param.get('p') == 'size':
            size = param.get('v', 'N/A')
        if param.get('p') == 'floor' and param.get('v'):
            floor = param['v'][0] if isinstance(param['v'], list) else 'N/A'

    caption_text = (
        f"{notification_text}"
        f"<b>{subject}</b>\n\n"
        f"💵 <b>Цена:</b> {price_usd}$\n"
        f"🕓 <b>Время публикации:</b> {datetime.fromisoformat(ad.get('list_time')) + timedelta(hours=3)}\n"
        f"📍 <b>Адрес:</b> {address}\n"
        f"📏 <b>Площадь:</b> {size} м²\n"
        f"🏢 <b>Этаж:</b> {floor}\n\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"<a href='{link}'><b>➡️ Посмотреть на Kufar</b></a>"
    )

    images = ad.get('images', [])
    media = []
    for i, img in enumerate(images[:5]):
        path = img.get('path')
        if path:
            url = f"https://rms.kufar.by/v1/gallery/{path}"
            if i == 0:
                media.append(InputMediaPhoto(media=url, caption=caption_text, parse_mode='HTML'))
            else:
                media.append(InputMediaPhoto(media=url))

    try:
        if media:
            await context.bot.send_media_group(chat_id=chat_id, media=media)
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    except TelegramError as e:
        logger.warning(f"Ошибка медиа: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )


# === КОМАНДЫ ===
async def monitoring_callback(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    logger.info(f"Проверка новых объявлений для чата {chat_id}...")

    ads = await fetch_ads()
    if not ads:
        return

    latest_date = get_latest_pub_date()
    sent_ads = load_sent_ads()
    new_ads = []

    for ad in ads:
        ad_id = str(ad.get('ad_id'))
        list_time_str = ad.get('list_time') or ad.get('list_date')
        if not ad_id or not list_time_str:
            continue
        try:
            pub_date = datetime.fromisoformat(list_time_str.replace('Z', '+00:00'))
        except:
            continue

        if ad_id not in sent_ads and pub_date > latest_date:
            new_ads.append((pub_date, ad))

    if not new_ads:
        logger.info("Новых объявлений не найдено")
        return

    # От новых к старым
    new_ads.sort(reverse=True, key=lambda x: x[0])

    for pub_date, ad in new_ads:
        ad_id = str(ad['ad_id'])
        logger.info(f"Новое: {ad_id} ({pub_date})")
        await send_ad_notification(
            context, chat_id, ad,
            "🔔 <b>Найдена новая квартира!</b>\n\n"
        )
        save_sent_ad(ad_id, pub_date)
        await asyncio.sleep(2)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("Нет доступа.")
        return

    job_name = str(chat_id)
    remove_job_if_exists(job_name, context)
    context.job_queue.run_repeating(
        monitoring_callback,
        interval=CHECK_INTERVAL,
        first=1,
        chat_id=chat_id,
        name=job_name
    )
    await update.message.reply_text(f"✅Мониторинг запущен! Проверка каждые {CHECK_INTERVAL} сек.")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("Нет доступа.")
        return
    if remove_job_if_exists(str(chat_id), context):
        await update.message.reply_text("Мониторинг остановлен.")
    else:
        await update.message.reply_text("Мониторинг не запущен.")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("Нет доступа.")
        return
    open(SENT_ADS_FILE, 'w').close()
    await update.message.reply_text("Список очищен. При /start — все объявления будут новыми.")


async def send_welcome_message(application: Application):
    text = (
        "🤖 Бот запущен! Но пока ничего не мониторит ☹️\n\n"
        "Доступные команды:\n"
        "📌 /start — Запустить мониторинг новых объявлений\n"
        "🛑 /stop — Остановить мониторинг\n"
        "🗑️ /clear — Очистить список отслеживаемых объявлений\n\n"
        "Я буду уведомлять вас о новых объявлениях с Kufar!"
    )
    for chat_id in ALLOWED_CHAT_IDS:
        try:
            await application.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
            await asyncio.sleep(1)
        except TelegramError as e:
            logger.error(f"Ошибка отправки в {chat_id}: {e}")


# === ЗАПУСК ===
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("clear", clear_command))

    # Приветствие через 2 сек после старта
    app.job_queue.run_once(
        lambda ctx: send_welcome_message(app),
        when=2,
        name="welcome"
    )

    # Ежедневная очистка в 00:00
    app.job_queue.run_daily(
        callback=clean_old_ads,
        time=time(hour=21, minute=0),
        days=(0, 1, 2, 3, 4, 5, 6)
    )

    # Проверка содержимого файла
    async def debug_sent_ads():
        await asyncio.sleep(5)
        if os.path.exists(SENT_ADS_FILE):
            with open(SENT_ADS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            logger.info(f"Содержимое sent_ads.txt:\n{content}")
        else:
            logger.warning("sent_ads.txt не существует!")

    app.job_queue.run_once(lambda ctx: asyncio.create_task(debug_sent_ads()), when=6)

    logger.info("Бот запущен...")
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()