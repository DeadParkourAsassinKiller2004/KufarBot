from core.database import SessionLocal
from repositories.ads_repository import AdsRepository


if __name__ == '__main__':
    # kufar_controller = Kufar()
    # flats = kufar_controller.fetch_kufar_flats(Currency.USD, (0, 350, 130))

    session = SessionLocal()
    repo = AdsRepository(session)

    ads = repo.get_by_account_id(account_id='OjK2oI7tlF0BqG6F2Ymh0UI')

    for ad in ads:
        print(ad)
