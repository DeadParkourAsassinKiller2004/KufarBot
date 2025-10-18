import logging
import requests
import time
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError # Импортируем класс для обработки ошибок

# --- НАСТРОЙКИ ---
# Вставьте сюда ваш токен, полученный от @BotFather
TELEGRAM_BOT_TOKEN = '8247116313:AAGVL3d_3SNPPYI7Wroo8nSE4HhAoEQkKlI'

# Вставьте сюда ваш Chat ID, полученный от @userinfobot
ALLOWED_CHAT_IDS = [575531308]

# URL для запроса к API Kufar (можете настроить фильтры здесь)
API_URL = 'https://api.kufar.by/search-api/v2/search/rendered-paginated?cat=1010&cmp=0&cur=USD&gtsy=country-belarus~province-minsk~locality-minsk&lang=ru&prc=r%3A0%2C360&rms=v.or%3A1&size=30&sort=lst.d&typ=let'

# Заголовки для запроса
HEADERS = {
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
}

# Интервал проверки для мониторинга в секундах
CHECK_INTERVAL = 60
# Файл для хранения ID уже отправленных объявлений
SENT_ADS_FILE = 'sent_ads.txt'

# Настройка логирования для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Вспомогательные функции (без изменений) ---

def load_sent_ads():
    """Загружает ID отправленных объявлений из файла."""
    if not os.path.exists(SENT_ADS_FILE):
        return set()
    with open(SENT_ADS_FILE, 'r') as f:
        return set(line.strip() for line in f)

def save_sent_ad(ad_id):
    """Сохраняет ID отправленного объявления в файл."""
    with open(SENT_ADS_FILE, 'a') as f:
        f.write(str(ad_id) + '\n')

async def fetch_ads():
    """Получает список объявлений с API Kufar."""
    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data.get('ads', [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return []

# --- НОВАЯ ФУНКЦИЯ ДЛЯ ОТПРАВКИ ОБЪЯВЛЕНИЙ С ФОТО ---
# Она заменяет старую функцию format_ad_message

async def send_ad_notification(context: ContextTypes.DEFAULT_TYPE, chat_id: int, ad: dict, notification_text: str = ""):
    """
    Форматирует и отправляет одно объявление с фото (если оно есть).
    Если фото нет или возникает ошибка, отправляет как текстовое сообщение.
    """
    # 1. Форматируем подпись (caption) для фото
    link = ad.get('ad_link', 'Нет ссылки')
    subject = ad.get('subject', 'Без заголовка')
    description = ad.get('body_short', 'Нет описания').strip()
    address = 'Не указан'
    size = 'N/A'
    floor = 'N/A'
    
    price_raw = ad.get('price_usd')
    if price_raw and price_raw.isdigit():
        try:
            price_usd = f"{int(price_raw) / 100.0:.2f}"
        except (ValueError, TypeError):
            price_usd = price_raw
    else:
        price_usd = 'N/A'

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
        f"📍 <b>Адрес:</b> {address}\n"
        f"📏 <b>Площадь:</b> {size} м²\n"
        f"🏢 <b>Этаж:</b> {floor}\n\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"<a href='{link}'><b>➡️ Посмотреть на Kufar</b></a>"
    )

    # 2. Пытаемся найти URL фото
    photo_url = None
    images = ad.get('images')
    if images:
        image_path = images[0].get('path')
        if image_path:
            # Собираем полный URL для картинки
            photo_url = f"https://rms.kufar.by/v1/gallery/{image_path}"

    # 3. Отправляем сообщение
    try:
        if photo_url:
            # Если нашли фото, используем send_photo
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo_url,
                caption=caption_text,
                parse_mode='HTML'
            )
        else:
            # Если фото нет, отправляем как обычное сообщение
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    except TelegramError as e:
        # Если Telegram не смог загрузить фото (например, ссылка битая), тоже отправляем текстом
        logger.warning(f"Не удалось отправить фото {photo_url}. Ошибка: {e}. Отправляю текстом.")
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )

# --- ОБНОВЛЕННЫЕ ФУНКЦИИ ---

async def monitoring_callback(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет новые объявления и отправляет уведомления."""
    chat_id = context.job.chat_id
    logger.info(f"Выполняю плановую проверку объявлений для чата {chat_id}...")
    
    ads = await fetch_ads()
    if not ads:
        return

    sent_ads = load_sent_ads()
    for ad in reversed(ads):
        ad_id = ad.get('ad_id')
        if ad_id and str(ad_id) not in sent_ads:
            logger.info(f"Найдено новое объявление: {ad_id}")
            # Вызываем новую функцию для отправки с фото
            await send_ad_notification(
                context, 
                chat_id, 
                ad, 
                notification_text="🔔 <b>Найдена новая квартира!</b>\n\n"
            )
            save_sent_ad(ad_id)
            await asyncio.sleep(2)

async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает все текущие объявления и полностью обновляет 
    список отслеживаемых ID.
    """
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    await update.message.reply_text("🔍 Запрашиваю актуальные объявления и синхронизирую список...")
    
    ads = await fetch_ads()
    if not ads:
        await update.message.reply_text("Не удалось найти объявления.")
        return

    all_current_ids = [str(ad.get('ad_id')) for ad in ads if ad.get('ad_id')]
    try:
        with open(SENT_ADS_FILE, 'w') as f:
            for ad_id in all_current_ids:
                f.write(ad_id + '\n')
        await update.message.reply_text(f"✅ **Список отслеживания сброшен.**\n\n👇 Найдено и запомнено объявлений: {len(ads)}. Отправляю их вам...")
    except IOError as e:
        logger.error(f"Не удалось записать в файл {SENT_ADS_FILE}: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при обновлении списка ID.")
        return
    
    for ad in ads:
        # Вызываем новую функцию для отправки с фото
        await send_ad_notification(context, chat_id, ad)
        await asyncio.sleep(1)

    await update.message.reply_text("✅ Все актуальные объявления показаны.")

# --- Команды /start, /stop и main() остаются без изменений ---

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
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
    await update.message.reply_text(f"✅ **Мониторинг запущен!**\n\nЯ буду проверять новые объявления каждые {CHECK_INTERVAL} секунд. Чтобы остановить, используйте команду /stop.")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return
        
    job_removed = remove_job_if_exists(str(chat_id), context)
    if job_removed:
        text = "❌ **Мониторинг остановлен.**"
    else:
        text = "ℹ️ Мониторинг и не был запущен."
    await update.message.reply_text(text)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("show", show_command))
    logger.info("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()