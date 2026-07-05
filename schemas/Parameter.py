from pydantic import BaseModel
from typing import Optional, Union


class ParameterGroup(BaseModel):
    gi: int
    gl: Optional[str] = None
    go: int
    po: int


class Parameter(BaseModel):
    pl: str
    vl: Union[str, list, bool, None]
    p: str
    v: Union[str, int, float, bool, list, None]
    pu: str
    g: Optional[list[ParameterGroup]] = None
