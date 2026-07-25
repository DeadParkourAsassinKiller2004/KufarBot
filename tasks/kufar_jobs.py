from logger import logger

from mappers.telegram_mapper import map_ad_to_telegram_message
from repositories.ads_repository import AdsRepository
from schemas.TelegramAdMessage import TelegramAdMessage
from services.flat_service import FlatService
from services.kufar_client import KufarClient
from core.database import SessionLocal
from constants.constants import CURRENCY, FROM_TO, SIZE


def kufar_fetch_job() -> list[TelegramAdMessage]:
    """Задача, которая выполняется раз в минуту."""
    logger.info("Запуск получения новых объявлений Kufar...")
    kufar_client = KufarClient()

    try:
        flats = kufar_client.fetch_flats(
            #TODO: получать сеттинги из БД (отказаться от файла)
            currency=CURRENCY, price_from_to=FROM_TO, size=SIZE
        )
        logger.info(f"Загружено {len(flats)} объявлений с Kufar API.")

        if not flats:
            return []

        with SessionLocal() as session:
            ads_repo = AdsRepository(session)
            flat_service = FlatService(ads_repo)

            saved = flat_service.process_and_save_flats(flats)
            saved_count = len(saved)

            logger.info(
                f"Обработка завершена. Добавлено новых объявлений: {saved_count}"
            )

            return [map_ad_to_telegram_message(ad) for ad in saved]

    except Exception as e:
        logger.error(
            f"Ошибка во время выполнения kufar_fetch_job: {e}", exc_info=True
        )
        return []
