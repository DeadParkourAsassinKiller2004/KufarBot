from typing import Optional
from pydantic import BaseModel


class PaidServices(BaseModel):
    halva: bool
    highlight: bool
    polepos: bool
    ribbons: Optional[list] = None
