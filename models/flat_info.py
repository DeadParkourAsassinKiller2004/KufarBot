from sqlalchemy import Column, Integer, String, Float, Text, Numeric

from core.database import Base


class FlatInfo(Base):
    __tablename__ = "flat_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(Text, nullable=False)
    building_type = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)
    city_region = Column(String(100), nullable=True)
    num_of_rooms = Column(Integer, nullable=True)
    square = Column(Numeric(12, 2), nullable=True)
    floor = Column(Integer, nullable=True)
    coordinates = Column(Text, nullable=False)
