from logger import logger

from repositories.ads_repository import AdsRepository
from services.flat_service import FlatService
from services.kufar_client import KufarClient
from core.database import SessionLocal
from schemas.Currency import Currency


def kufar_fetch_job():
    """Задача, которая выполняется раз в минуту."""
    logger.info("Запуск получения новых объявлений Kufar...")
    kufar_client = KufarClient()

    try:
        flats = kufar_client.fetch_flats(
            currency=Currency.USD, price_from_to=(0, 350), size=130
        )
        logger.info(f"Загружено {len(flats)} объявлений с Kufar API.")

        if not flats:
            return

        with SessionLocal() as session:
            ads_repo = AdsRepository(session)
            flat_service = FlatService(ads_repo)

            saved_count = flat_service.process_and_save_flats(flats)
            logger.info(
                f"Обработка завершена. Добавлено новых объявлений: {saved_count}"
            )

    except Exception as e:
        logger.error(
            f"Ошибка во время выполнения kufar_fetch_job: {e}", exc_info=True
        )
