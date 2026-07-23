from __future__ import annotations

from sqlalchemy.orm import Session

from mappers.kufar_mapper import map_kufar_flat_to_orm
from models.ad import Ad
from schemas.KufarFlat import KufarFlat


class AdsRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_kufar_flats_to_db(self, kufar_flats: list[KufarFlat]
    ) -> None:
        ads_to_save = []

        for flat_pydantic in kufar_flats:
            ad_orm = map_kufar_flat_to_orm(flat_pydantic)
            ads_to_save.append(ad_orm)

        self.session.add_all(ads_to_save)
        self.session.commit()

    def get_by_id(self, ad_id: int) -> list[Ad] | None:
        return self.session.query(Ad).filter(Ad.id == ad_id).all()

    def get_by_account_id(self, account_id: str) -> list[Ad] | None:
        return self.session.query(Ad).filter(Ad.account_id == account_id).all()
