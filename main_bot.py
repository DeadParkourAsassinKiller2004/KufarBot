import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InputMediaPhoto
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from constants.constants import PLACEHOLDER_IMAGE_URL, BOT_TOKEN, CHAT_ID
from tasks.kufar_jobs import kufar_fetch_job

# Settings
TOKEN = BOT_TOKEN
ADMIN_CHAT_ID = CHAT_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Ответ на команду /start"""
    await message.answer(
        "👋 Привет! Я бот для мониторинга аренды.\n"
        "Я работаю в фоне и буду присылать сюда новые объявления, как только они появятся на Kufar."
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

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_new_flats_job,
        trigger='interval',
        minutes=1,
        kwargs={'bot': bot, 'chat_id': ADMIN_CHAT_ID}
    )

    scheduler.start()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
