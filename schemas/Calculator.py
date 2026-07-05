from typing import Optional
from pydantic import BaseModel
from schemas.Currency import Currency


class Calculator(BaseModel):
    currency: Currency
    price: str
    price_per_meter: Optional[str] = None
