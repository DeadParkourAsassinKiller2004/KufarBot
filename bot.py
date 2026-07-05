from schemas.Currency import Currency
from Kufar import Kufar
from sqlalchemy import create_engine, text


if __name__ == '__main__':
    # kufar_controller = Kufar()
    # flats = kufar_controller.fetch_kufar_flats(Currency.USD, (0, 350, 130))

    engine = create_engine('postgresql+psycopg2://localhost:5432/postgres')

    with engine.connect() as conn:
        result = conn.execute(text("select * from users"))
        for row in result:
            print(row)
