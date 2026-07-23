from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.ad import Ad


class AdsRepository:

    def __init__(self, session: Session):
        self.session = session

    def add_all(self, ads: list[Ad]) -> None:
        """Принимает список готовых ORM-объектов и сохраняет их в БД."""
        self.session.add_all(ads)
        self.session.commit()

    def get_by_id(self, id: int) -> Ad | None:
        """Поиск по первичному ключу таблицы (PK)."""
        stmt = select(Ad).where(Ad.id == id)
        return self.session.scalar(stmt)

    def get_by_kufar_id(self, ad_id: int) -> Ad | None:
        """Поиск по ID объявления Kufar."""
        stmt = select(Ad).where(Ad.ad_id == ad_id)
        return self.session.scalar(stmt)

    def get_existing_kufar_ids(self, ad_ids: list[int]) -> set[int]:
        """Возвращает set из ad_id, которые УЖЕ есть в БД (для фильтрации)."""
        if not ad_ids:
            return set()

        stmt = select(Ad.ad_id).where(Ad.ad_id.in_(ad_ids))
        return set(self.session.scalars(stmt).all())

    def get_by_account_id(self, account_id: str) -> Sequence[Ad]:
        """Получить все объявления одного аккаунта."""
        stmt = select(Ad).where(Ad.account_id == account_id)
        return self.session.scalars(stmt).all()
