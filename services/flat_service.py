from repositories.ads_repository import AdsRepository
from mappers.kufar_mapper import map_kufar_flat_to_orm
from schemas.KufarFlat import KufarFlat

class FlatService:
    def __init__(self, ads_repo: AdsRepository):
        self.ads_repo = ads_repo

    def process_and_save_flats(self, fetched_flats: list[KufarFlat]) -> int:
        if not fetched_flats:
            return 0

        incoming_ids = [f.ad_id for f in fetched_flats if f.ad_id is not None]

        existing_ids = self.ads_repo.get_existing_kufar_ids(incoming_ids)

        new_flats = [f for f in fetched_flats if f.ad_id not in existing_ids]
        if not new_flats:
            return 0

        new_ads_orm = [map_kufar_flat_to_orm(f) for f in new_flats]

        self.ads_repo.add_all(new_ads_orm)
        return len(new_ads_orm)
