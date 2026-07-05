from pydantic import BaseModel


class ShowParameters(BaseModel):
    show_call: bool
    show_chat: bool
    show_import_link: bool
    show_web_shop_link: bool
