from decimal import Decimal

from constants.constants import BASE_IMAGE_URL
from models import Ad, FlatInfo
from schemas.KufarFlat import KufarFlat


def map_kufar_flat_to_orm(flat: KufarFlat) -> Ad:
    """Преобразует Pydantic модель KufarFlat в связанные объекты ORM (FlatInfo + Ad)."""

    ad_params = {param.p: param for param in flat.ad_parameters} if flat.ad_parameters else {}
    account_params = (
        {param.p: param for param in flat.account_parameters}
        if flat.account_parameters
        else {}
    )

    def get_param_val(params_dict, key: str, attr: str = "vl"):
        param = params_dict.get(key)
        if not param:
            return None
        return getattr(param, attr, None)


    raw_floor = get_param_val(ad_params, "floor", attr="v")
    floor_val = (
        raw_floor[0]
        if isinstance(raw_floor, list) and raw_floor
        else raw_floor
    )

    raw_coords = get_param_val(ad_params, "coordinates", attr="v")
    coords_str = (
        f"{raw_coords[0]}, {raw_coords[1]}"
        if isinstance(raw_coords, list) and len(raw_coords) == 2
        else "0, 0"
    )

    address_str = (
        get_param_val(account_params, "address", attr="v") or "Адрес не указан"
    )

    raw_people_cat = get_param_val(ad_params, "flat_rent_for_whom", attr="vl")
    people_cat_str = (
        ", ".join(raw_people_cat)
        if isinstance(raw_people_cat, list)
        else raw_people_cat
    )

    flat_info = FlatInfo(
        address=address_str,
        building_type=get_param_val(ad_params, "house_type", attr="vl"),
        region=get_param_val(ad_params, "region", attr="vl"),
        city_region=get_param_val(
            ad_params, "area", attr="vl"
        ),
        num_of_rooms=(
            int(get_param_val(ad_params, "rooms", attr="v"))
            if get_param_val(ad_params, "rooms", attr="v")
            else None
        ),
        square=(
            Decimal(str(get_param_val(ad_params, "size", attr="v")))
            if get_param_val(ad_params, "size", attr="v")
            else None
        ),
        floor=int(floor_val) if floor_val is not None else None,
        coordinates=coords_str,
    )

    byn_price = (
        Decimal(flat.price_byn) / Decimal("100") if flat.price_byn else None
    )
    usd_price = (
        Decimal(flat.price_usd) / Decimal("100") if flat.price_usd else None
    )

    create_date = flat.list_time

    images = [f"{BASE_IMAGE_URL}{image.path}" for image in flat.images]

    ad = Ad(
        flat_info=flat_info,
        ad_link=flat.ad_link,
        account_id=flat.account_id,
        ad_id=flat.ad_id,
        deal_type=flat.type,
        byn_price=byn_price,
        usd_price=usd_price,
        people_category=people_cat_str,
        company_ad=flat.company_ad,
        create_date=create_date,
        description=flat.body_short or flat.body,
        image_links=images,
    )

    return ad
