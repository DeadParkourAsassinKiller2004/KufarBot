from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from schemas.FlatImage import FlatImage
from schemas.Parameter import Parameter


class KufarFlat(BaseModel):
    ad_id: Optional[int] = None
    ad_link: str
    account_id: Optional[str] = None
    type: Optional[str] = None
    price_byn: Optional[str] = None
    price_usd: Optional[str] = None
    company_ad: bool = False
    list_time: Optional[datetime] = None
    body_short: Optional[str] = None
    body: Optional[str] = None
    images: list[FlatImage] = []
    account_parameters: list[Parameter] = []
    ad_parameters: list[Parameter] = []
