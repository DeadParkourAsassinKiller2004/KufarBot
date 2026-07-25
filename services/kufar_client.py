import requests

from schemas.Currency import Currency
from schemas.KufarFlat import KufarFlat
from constants.constants import BASE_URL


class KufarClient:
    def __init__(self):
        self._BASE_URL = BASE_URL

    def fetch_flats(self, currency: Currency, price_from_to: tuple, size: int = 100) -> list[KufarFlat]:
        url = f"{self._BASE_URL}search/rendered-paginated"

        params = {
            "cat": "1010",
            "cur": currency.value,
            "gtsy": "country-belarus~province-minsk~locality-minsk", # TODO: сделать изменяемым параметром
            "lang": "ru",
            "prc": f"r:{price_from_to[0]},{price_from_to[1]}",
            "size": str(size),
            "typ": "let"
        }

        headers = {
            "accept": "*/*",
            "content-type": "application/json"
        }

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()

        return [KufarFlat(**item) for item in data["ads"]]
