from __future__ import annotations

from sqlalchemy.orm import Session
from models.ad import Ad


class AdsRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> Ad:
        ad = Ad(**kwargs)
        self.session.add(ad)
        self.session.flush()
        return ad

    def get_by_id(self, ad_id: int) -> list[Ad] | None:
        return self.session.query(Ad).filter(Ad.id == ad_id).all()

    def get_by_account_id(self, account_id: str) -> list[Ad] | None:
        return self.session.query(Ad).filter(Ad.account_id == account_id).all()
