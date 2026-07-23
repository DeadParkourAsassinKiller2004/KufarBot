from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY

from core.database import Base


class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flat_id = Column(Integer, ForeignKey("flat_info.id", ondelete="CASCADE"), nullable=False)
    ad_link = Column(Text, nullable=False)
    account_id = Column(String(50), nullable=True)
    ad_id = Column(Integer, unique=True, index=True, nullable=True)
    deal_type = Column(String(20), nullable=True)
    byn_price = Column(Numeric(12, 2), nullable=True)
    usd_price = Column(Numeric(12, 2), nullable=True)
    people_category = Column(ARRAY(Text), nullable=True)
    company_ad = Column(Boolean, nullable=True, default=False)
    create_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    image_links = Column(ARRAY(Text), nullable=True)

    def __repr__(self):
        return f"<Ad(id={self.id}, ad_id={self.ad_id}, deal_type='{self.deal_type}')>"
