from dataclasses import dataclass

@dataclass
class TelegramAdMessage:
    price_usd: str
    price_byn: str
    address: str
    square: str
    floor: str
    description: str
    image_urls: list[str]
    created_at: str
    ad_link: str

    def to_html(self) -> str:
        """Рендерит данные в HTML-шаблон для Telegram."""
        return (
            f"🔔 <b>Новое объявление!</b>\n\n"
            f"💵 <b>Цена USD:</b> {self.price_usd} $\n"
            f"💵 <b>Цена BYN:</b> {self.price_byn} руб.\n"
            f"📍 <b>Адрес:</b> {self.address}\n"
            f"📏 <b>Площадь:</b> {self.square} м²\n"
            f"🏢 <b>Этаж:</b> {self.floor}\n\n"
            f"📝 <b>Описание:</b>\n{self.description}\n"
            f"🕔 <b>Дата публикации:</b>\n{self.created_at}\n\n"
            f"<a href='{self.ad_link}'><b>➡️ Посмотреть на Kufar</b></a>"
        )
