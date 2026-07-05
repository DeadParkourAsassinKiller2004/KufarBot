from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from schemas.Parameter import Parameter
from schemas.FlatImage import FlatImage
from schemas.Calculator import Calculator
from schemas.PaidServices import PaidServices
from schemas.ShowParameters import ShowParameters


class KufarFlat(BaseModel):
    account_id: str
    account_parameters: list[Parameter]
    ad_id: int
    ad_link: str
    ad_parameters: list[Parameter]
    body: Optional[str] = None
    body_short: Optional[str] = None
    calculator: list[Calculator]
    category: str
    company_ad: bool
    currency: str
    feedback_info: Optional[str] = None
    images: list[FlatImage]
    is_mine: bool
    list_id: int
    list_time: datetime
    message_id: str
    paid_services: PaidServices
    phone_hidden: bool
    price_byn: str
    price_usd: str
    remuneration_type: str
    show_parameters: ShowParameters
    subject: str
    type: str
