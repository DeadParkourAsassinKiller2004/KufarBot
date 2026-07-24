from pydantic import BaseModel, Field
from constants.constants import BASE_IMAGE_URL


class FlatImage(BaseModel):
    id: str = Field(alias="id")
    media_storage: str = Field(alias="media_storage")
    path: str = Field(alias="path")
    yams_storage: bool = Field(alias="yams_storage")
    _base_image_url: str = BASE_IMAGE_URL
