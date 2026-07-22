from __future__ import annotations

from sqlalchemy.orm import Session
from models.flat_info import FlatInfo


class FlatInfoRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_address(self, address: str) -> FlatInfo | None:
        return self.session.query(FlatInfo).filter(FlatInfo.address == address).first()

    def create(self, **kwargs) -> FlatInfo:
        flat = FlatInfo(**kwargs)
        self.session.add(flat)
        self.session.flush()  # чтобы получить id, но не коммитить
        return flat

    def get_or_create(self, address: str, defaults: dict) -> FlatInfo:
        existing = self.get_by_address(address)
        if existing:
            return existing
        return self.create(address=address, **defaults)
