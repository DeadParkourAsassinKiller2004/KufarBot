from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.flat_info import FlatInfo


class FlatInfoRepository:

    def __init__(self, session: Session):
        self.session = session

    def add(self, flat_info: FlatInfo) -> FlatInfo:
        """Сохраняет одну квартиру в БД и возвращает её с заполненой первичным ключом (id)."""
        self.session.add(flat_info)
        self.session.commit()
        self.session.refresh(flat_info)
        return flat_info

    def add_all(self, flat_infos: list[FlatInfo]) -> None:
        """Сохраняет список квартир в БД."""
        self.session.add_all(flat_infos)
        self.session.commit()

    def get_by_id(self, id: int) -> FlatInfo | None:
        """Поиск квартиры по первичному ключу таблицы (id)."""
        stmt = select(FlatInfo).where(FlatInfo.id == id)
        return self.session.scalar(stmt)

    def get_by_address(self, address: str) -> FlatInfo | None:
        """Поиск квартиры по адресу (для дедупликации объектов жилья)."""
        stmt = select(FlatInfo).where(FlatInfo.address == address)
        return self.session.scalar(stmt)

    def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[FlatInfo]:
        """Получить список квартир с поддержкой пагинации."""
        stmt = select(FlatInfo).limit(limit).offset(offset)
        return self.session.scalars(stmt).all()