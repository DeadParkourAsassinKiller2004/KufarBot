from models.ad import Ad
from schemas.TelegramAdMessage import TelegramAdMessage


def map_ad_to_telegram_message(ad: Ad) -> TelegramAdMessage:
    """Преобразует ORM модель Ad в чистый объект TelegramAdMessage."""
    flat = ad.flat_info
    address = getattr(flat, 'address', 'Не указан')
    square = getattr(flat, 'square', 'Не указана')
    floor = getattr(flat, 'floor', 'Не указан')

    price_usd = getattr(ad, 'usd_price', 'Не указана')
    price_byn = getattr(ad, 'byn_price', 'Не указана')
    description = getattr(ad, 'description', 'Описание отсутствует')
    ad_link = getattr(ad, 'ad_link', 'https://re.kufar.by/')
    created_at = getattr(ad, 'create_date')

    image_urls = getattr(ad, 'image_links', None)

    return TelegramAdMessage(
        price_usd=price_usd,
        price_byn=price_byn,
        address=address,
        square=square,
        floor=floor,
        description=description,
        image_urls=image_urls,
        created_at=created_at,
        ad_link=ad_link
    )
