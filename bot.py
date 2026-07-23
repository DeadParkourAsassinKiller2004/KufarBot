from Kufar import Kufar
from core.database import SessionLocal
from mappers.kufar_mapper import map_kufar_flat_to_orm
from repositories import ads_repository
from repositories.ads_repository import AdsRepository
from schemas.Currency import Currency

if __name__ == '__main__':
    session = SessionLocal()
    repo = AdsRepository(session)

    kufar_controller = Kufar()
    flats = kufar_controller.fetch_kufar_flats(Currency.USD, (0, 350, 130))
    repo.save_kufar_flats_to_db(flats)
    print("hello")

    # session = SessionLocal()
    # repo = AdsRepository(session)
    #
    # ads = repo.get_by_account_id(account_id='user_usr_112')
    #
    # for ad in ads:
    #     print(ad)
