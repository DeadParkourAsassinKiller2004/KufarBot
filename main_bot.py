import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InputMediaPhoto, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from constants.constants import PLACEHOLDER_IMAGE_URL, BOT_TOKEN, CHAT_ID, KUFAR_MONITORING_JOB_ID

from tasks.kufar_jobs import kufar_fetch_job

# Global bot settings
TOKEN = BOT_TOKEN
ADMIN_CHAT_ID = CHAT_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

scheduler = AsyncIOScheduler()

class SettingsForm(StatesGroup):
    waiting_for_currency = State()
    waiting_for_price = State()
    waiting_for_region = State()


async def set_bot_commands(bot: Bot):
    """Настраивает список команд в синей кнопке 'Меню'."""
    commands = [
        BotCommand(command="start", description="Показать главное меню"),
        BotCommand(command="start_monitoring", description="Запустить мониторинг"),
        BotCommand(command="stop", description="Остановить мониторинг"),
        BotCommand(command="settings", description="Настроить параметры поиска"),
        BotCommand(command="mods", description="Выбрать мод поиска")
    ]
    await bot.set_my_commands(commands)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру с кнопками 'Запустить' и 'Остановить'."""
    builder = ReplyKeyboardBuilder()

    builder.add(KeyboardButton(text="🚀 Запустить мониторинг"))
    builder.add(KeyboardButton(text="🛑 Остановить мониторинг"))
    builder.add(KeyboardButton(text="⚙️ Настроить параметры поиска"))
    builder.add(KeyboardButton(text="🤖 Настроить параметры поиска"))

    builder.adjust(2)

    return builder.as_markup(resize_keyboard=True, is_persistent=True)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Ответ на команду /start"""
    await message.answer(
        "👋 Привет! Я бот для мониторинга аренды.\n\n"
        "Воспользуйтесь кнопками ниже, чтобы управлять запуском и остановкой мониторинга.",
        reply_markup=get_main_menu_keyboard()
    )


@dp.message(Command("start_monitoring"))
@dp.message(F.text == "🚀 Запустить мониторинг")
async def start_monitoring(message: Message):
    """Ответ на команду /start"""
    existing_job = scheduler.get_job(KUFAR_MONITORING_JOB_ID)

    if existing_job:
        await message.answer("ℹ️ Мониторинг уже запущен и активно проверяет новые объявления.")
        return

    scheduler.add_job(
        check_new_flats_job,
        trigger='interval',
        minutes=1,
        kwargs={'bot': bot, 'chat_id': ADMIN_CHAT_ID},
        id=KUFAR_MONITORING_JOB_ID
    )

    await message.answer(
        "🚀 <b>Мониторинг успешно запущен!</b>\n\n"
        "Я буду проверять новые объявления на Kufar каждую минуту и сразу присылать их в этот чат."
    )


@dp.message(Command("stop"))
@dp.message(F.text == "🛑 Остановить мониторинг")
async def stop_monitoring(message: Message):
    """Ответ на команду /stop"""
    existing_job = scheduler.get_job(KUFAR_MONITORING_JOB_ID)

    if not existing_job:
        await message.answer("ℹ️ Мониторинг не запущен, останавливать нечего.")
        return

    scheduler.remove_job(
        job_id=KUFAR_MONITORING_JOB_ID
    )
    await message.answer(
        "🛑 <b>Мониторинг остановлен!</b>\n\n"
        "Я больше не проверяю объявления. Чтобы возобновить работу, отправьте команду /start."
    )


@dp.message(Command("settings"))
@dp.message(F.text == "⚙️ Настроить параметры поиска")
async def set_search_params(message: Message, state: FSMContext):
    """Начало настройки: переключаем пользователя в первое состояние и просим валюту"""

    await state.set_state(SettingsForm.waiting_for_currency)

    await message.answer(
        "⚙️ <b>Панели настройки параметров поиска</b>\n\n"
        "Шаг 1/3: Введите валюту поиска (например: <code>USD</code> или <code>BYN</code>):\n\n"
        "<i>Для отмены настройки в любой момент введите команду /cancel</i>"
    )


@dp.message(SettingsForm.waiting_for_currency)
async def process_currency(message: Message, state: FSMContext):
    currency = message.text.upper().strip()

    if currency not in ["USD", "BYN"]:
        await message.answer("❌ Неверная валюта. Пожалуйста, введите либо <code>USD</code>, либо <code>BYN</code>:")
        return

    await state.update_data(currency=currency)

    await state.set_state(SettingsForm.waiting_for_price)
    await message.answer("Шаг 2/3: Введите минимальную и максимальную цену через пробел (например: <code>150 400</code>):")


@dp.message(SettingsForm.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    text = message.text.strip()
    parts = text.split()

    if len(parts) != 2:
        await message.answer("❌ Ошибка формата. Введите ровно два числа через один пробел (например: <code>100 350</code>):")
        return

    try:
        price_from = int(parts[0])
        price_to = int(parts[1])
        if price_from >= price_to or price_from < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Цены должны быть целыми положительными числами, и цена 'ОТ' должна быть меньше цены 'ДО'. Попробуйте еще раз:")
        return

    await state.update_data(price_from=price_from, price_to=price_to)

    await state.set_state(SettingsForm.waiting_for_region)
    await message.answer("Шаг 3/3: Введите регион поиска жилья (например: <code>Минск</code>):")


@dp.message(SettingsForm.waiting_for_region)
async def process_region(message: Message, state: FSMContext):
    region = message.text.strip()

    user_data = await state.get_data()
    currency = user_data.get("currency")
    price_from = user_data.get("price_from")
    price_to = user_data.get("price_to")

    await state.clear()

    #TODO: Создать в БД табличку с сеттингами и сетать в нее настройки

    await message.answer(
        f"✅ <b>Параметры поиска успешно обновлены!</b>\n\n"
        f"💵 Валюта: <b>{currency}</b>\n"
        f"💰 Диапазон цен: <b>{price_from} — {price_to}</b>\n"
        f"📍 Регион: <b>{region}</b>\n\n"
        "Теперь вы можете запустить или перезапустить мониторинг."
    )


# --- ЛОГИКА ФОНОВОЙ ЗАДАЧИ ---
async def check_new_flats_job(bot: Bot, chat_id: int):
    """Асинхронная обертка для вашей синхронной задачи."""

    saved_flats = await asyncio.to_thread(kufar_fetch_job)

    if saved_flats:
        logger.info(f"Отправляем {len(saved_flats)} сообщений в Telegram...")
        for msg in saved_flats:
            urls = msg.image_urls if msg.image_urls else []
            urls = urls[:5]

            if not urls:
                urls = [PLACEHOLDER_IMAGE_URL]

            try:
                if len(urls) == 1:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=urls[0],
                        caption=msg.to_html(),
                        parse_mode="HTML"
                    )

                else:
                    media_group = []
                    for index, url in enumerate(urls):
                        if index == 0:
                            media_group.append(
                                InputMediaPhoto(
                                    media=url,
                                    caption=msg.to_html(),
                                    parse_mode="HTML"
                                )
                            )
                        else:
                            media_group.append(InputMediaPhoto(media=url))

                    await bot.send_media_group(
                        chat_id=chat_id,
                        media=media_group
                    )

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")


# --- ЗАПУСК ВСЕГО ПРИЛОЖЕНИЯ ---
async def main():
    logger.info("Запуск Telegram-бота и планировщика задач...")

    await set_bot_commands(bot)

    scheduler.start()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
