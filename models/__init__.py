from .ad import Ad
from .flat_info import FlatInfo
from sqlalchemy.orm import relationship

Ad.flat_info = relationship("FlatInfo", back_populates="ads")
FlatInfo.ads = relationship("Ad", back_populates="flat_info", cascade="all, delete-orphan")
