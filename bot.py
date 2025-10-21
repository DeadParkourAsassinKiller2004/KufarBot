# pip install "python-telegram-bot[job-queue]
# pip install python-telegram-bot
# pip install requests

import logging
import requests
import os
import asyncio
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from telegram.error import TelegramError

# --- НАСТРОЙКИ ---
TELEGRAM_BOT_TOKEN = '8247116313:AAGVL3d_3SNPPYI7Wroo8nSE4HhAoEQkKlI'

# Для получения chat id нужно перейти по ссылке https://api.telegram.org/bot<Токен вашего бота>/getUpdates и отправить сообщение в бот
ALLOWED_CHAT_IDS = [575531308, 753075180]

# URL для запроса к API Kufar
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


def sync_sent_ads_with_current(ads: list):
    """
    Синхронизирует sent_ads.txt с текущими объявлениями.
    Удаляет из файла ad_id, которых больше нет в API.
    """
    current_ad_ids = {str(ad.get('ad_id')) for ad in ads if ad.get('ad_id')}
    
    if not current_ad_ids:
        logger.info("Нет объявлений в API — файл sent_ads.txt будет очищен.")
        open(SENT_ADS_FILE, 'w').close()
        return

    # Загружаем текущие сохранённые ID
    saved_ads = load_sent_ads()
    
    # Оставляем только те, что есть в API
    synced_ads = saved_ads.intersection(current_ad_ids)
    
    removed_count = len(saved_ads) - len(synced_ads)
    if removed_count > 0:
        logger.info(f"Удалено {removed_count} устаревших ad_id из {SENT_ADS_FILE}")

    # Перезаписываем файл
    with open(SENT_ADS_FILE, 'w') as f:
        for ad_id in sorted(synced_ads):
            f.write(ad_id + '\n')


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


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


async def send_ad_notification(context: ContextTypes.DEFAULT_TYPE, chat_id: int, ad: dict, notification_text: str = ""):
    """
    Отправляет до 5 первых фото + текст в виде альб...
    """
    # === 1. Формируем подпись ===
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
        f"📍 <b>Адрес:</b> {address}\n"
        f"📏 <b>Площадь:</b> {size} м²\n"
        f"🏢 <b>Этаж:</b> {floor}\n\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"<a href='{link}'><b>➡️ Посмотреть на Kufar</b></a>"
    )

    # === 2. Собираем до 5 фото ===
    images = ad.get('images', [])
    media = []
    for i, img in enumerate(images[:5]):
        path = img.get('path')
        if path:
            url = f"https://rms.kufar.by/v1/gallery/{path}"
            if i == 0:
                # Первый — с подписью
                media.append(
                    InputMediaPhoto(
                        media=url,
                        caption=caption_text,
                        parse_mode='HTML'
                    )
                )
            else:
                media.append(InputMediaPhoto(media=url))

    # === 3. Отправляем ===
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
        logger.warning(f"Ошибка при отправке медиа: {e}. Отправляю текстом.")
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )


async def monitoring_callback(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет новые объявления и отправляет уведомления."""
    chat_id = context.job.chat_id
    logger.info(f"Выполняю плановую проверку объявлений для чата {chat_id}...")
    
    ads = await fetch_ads()
    if not ads:
        return

    # === ДОБАВЛЕНО: Синхронизация sent_ads.txt с API ===
    sync_sent_ads_with_current(ads)

    # === Остальной код без изменений ===
    sent_ads = load_sent_ads()
    for ad in reversed(ads):
        ad_id = ad.get('ad_id')
        if ad_id and str(ad_id) not in sent_ads:
            logger.info(f"Найдено новое объявление: {ad_id}")
            await send_ad_notification(
                context, 
                chat_id, 
                ad, 
                notification_text="🔔 <b>Найдена новая квартира!</b>\n\n"
            )
            save_sent_ad(ad_id)
            await asyncio.sleep(2)


async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("У вас нет доступа к этому боту.")
        return

    await update.message.reply_text("Запрашиваю актуальные объявления и синхронизирую список...")
    
    ads = await fetch_ads()
    if not ads:
        await update.message.reply_text("Не удалось найти объявления.")
        return

    # === Синхронизация ===
    sync_sent_ads_with_current(ads)

    all_current_ids = [str(ad.get('ad_id')) for ad in ads if ad.get('ad_id')]
    try:
        with open(SENT_ADS_FILE, 'w') as f:
            for ad_id in all_current_ids:
                f.write(ad_id + '\n')
        await update.message.reply_text(f"Список отслеживания сброшен.\n\nНайдено и запомнено объявлений: {len(ads)}. Отправляю их вам...")
    except IOError as e:
        logger.error(f"Не удалось записать в файл {SENT_ADS_FILE}: {e}")
        await update.message.reply_text("Произошла ошибка при обновлении списка ID.")
        return
    
    for ad in reversed(ads):
        await send_ad_notification(context, chat_id, ad)
        await asyncio.sleep(1)

    await update.message.reply_text("Все актуальные объявления показаны.")


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


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очищает файл с ID отправленных объявлений."""
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return
        
    try:
        # Открываем файл в режиме 'w' (write), что автоматически очищает его.
        # Если файла нет, он будет создан.
        with open(SENT_ADS_FILE, 'w') as f:
            pass  # Ничего не делаем, просто открываем и закрываем, чтобы очистить
        
        logger.info(f"Файл {SENT_ADS_FILE} был успешно очищен по команде от пользователя {chat_id}.")
        
        await update.message.reply_text(
            "✅ **Список отслеживания очищен.**\n\n"
            "При следующем запуске мониторинга (/start) все актуальные объявления будут отправлены как новые."
        )
        
    except IOError as e:
        logger.error(f"Ошибка при очистке файла {SENT_ADS_FILE}: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при очистке списка отслеживания.")


async def send_welcome_message(application: Application):
    """Отправляет информационное сообщение со списком команд во все разрешённые чаты."""
    welcome_text = (
        "🤖 Бот запущен!\n\n"
        "Доступные команды:\n"
        "📌 /start — Запустить мониторинг новых объявлений\n"
        "🛑 /stop — Остановить мониторинг\n"
        "🔍 /show — Показать все актуальные объявления и обновить список\n"
        "🗑️ /clear — Очистить список отслеживаемых объявлений\n\n"
        "Я буду уведомлять вас о новых объявлениях с Kufar!"
    )
    
    for chat_id in ALLOWED_CHAT_IDS:
        try:
            logger.info(f"Отправка приветственного сообщения в чат {chat_id}")
            await application.bot.send_message(
                chat_id=chat_id,
                text=welcome_text,
                parse_mode='HTML'
            )
            await asyncio.sleep(1)
        except TelegramError as e:
            logger.error(f"Ошибка при отправке сообщения в чат {chat_id}: {e}")


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("show", show_command))
    application.add_handler(CommandHandler("clear", clear_command))

    # Запускаем приветственное сообщение через job_queue (после инициализации)
    application.job_queue.run_once(
        callback=lambda context: send_welcome_message(application),
        when=2,  # через 2 секунды после старта
        name="welcome_message"
    )

    logger.info("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()