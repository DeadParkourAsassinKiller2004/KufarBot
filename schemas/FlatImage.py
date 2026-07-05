from io import BytesIO
from pydantic import BaseModel, Field
import requests
from PIL import Image
from constants.constants import BASE_IMAGE_URL


class FlatImage(BaseModel):
    id: str = Field(alias="id")
    media_storage: str = Field(alias="media_storage")
    path: str = Field(alias="path")
    yams_storage: bool = Field(alias="yams_storage")
    _base_image_url: str = BASE_IMAGE_URL

    def getImageByPath(self) -> Image.Image:
        full_url = f"{self._base_image_url}{self.path}"
        response = requests.get(full_url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
