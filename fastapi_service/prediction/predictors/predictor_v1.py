import asyncio

from .predictor_interface import PredictorInterface
from ..ml.linear_model import LinearModel
from ..maps_api_client import (
    MapsApiClient,
    TransportationContext,
    POICountResult
)


SURROUNDINGS_MAPPING = {
    'convenience': 'cash_intensive_shops',
    'kiosk': 'cash_intensive_shops',
    'newsagent': 'cash_intensive_shops',
    'tobacco': 'cash_intensive_shops',
    'lottery': 'cash_intensive_shops',
    'pawnbroker': 'cash_intensive_shops',
    'money_lender': 'cash_intensive_shops',
    'charity': 'cash_intensive_shops',

    'church': 'religious_buildings',
    'cathedral': 'religious_buildings',
    'chapel': 'religious_buildings',
    'mosque': 'religious_buildings',
    'temple': 'religious_buildings',
    'synagogue': 'religious_buildings',
    'shrine': 'religious_buildings',
    'monastery': 'religious_buildings',
    'place_of_worship': 'religious_buildings',

    'marketplace': 'markets_vendors',
    'vending_machine': 'markets_vendors',

    'restaurant': 'food_drink',
    'cafe': 'food_drink',
    'fast_food': 'food_drink',
    'food_court': 'food_drink',
    'ice_cream': 'food_drink',
    'bar': 'food_drink',
    'pub': 'food_drink',

    'bus_station': 'transportation',
    'train_station': 'transportation',
    'taxi': 'transportation',
    'ferry_terminal': 'transportation',
    'bicycle_rental': 'transportation',

    'hotel': 'tourism',
    'hostel': 'tourism',
    'guest_house': 'tourism',
    'motel': 'tourism',

    'hairdresser': 'personal_services',
    'beauty': 'personal_services',
    'barber': 'personal_services',
    'massage': 'personal_services',
    'tailor': 'personal_services',
    'laundry': 'personal_services',
    'dry_cleaning': 'personal_services',
    
    'university': 'education',
    'college': 'education',
    'school': 'education',
    'kindergarten': 'education',
    
    'bank': 'financial_services',
    'bureau_de_change': 'financial_services',
    'atm': 'financial_services',
    
    'mall': 'large_retail',
    'department_store': 'large_retail',
    'supermarket': 'large_retail',
    
    'cinema': 'entertainment',
    'theatre': 'entertainment',
    'casino': 'entertainment',
    'nightclub': 'entertainment',
    
    'library': 'public_amenities',
    'community_centre': 'public_amenities',
    'post_office': 'public_amenities',
    'police': 'public_amenities',
    'courthouse': 'public_amenities',
    
    'hospital': 'healthcare',
    'clinic': 'healthcare',
    'pharmacy': 'healthcare',
    'dentist': 'healthcare'
}


class PredictorV1(PredictorInterface):

    RADII = [100, 250, 500, 1000]

    def __init__(
        self,
        model_path: str,
        traning_data_path: str
    ) -> None:
        self.model = LinearModel(model_path, traning_data_path)
        self.maps_api_client = MapsApiClient()

    async def predict(
        self,
        id: float,
        atm_group: float,
        long: float,
        lat: float
    ) -> float | None:
        await super().predict(id, atm_group, long, lat)
        features = {
            'id': id,
            'atm_group': atm_group,
            'long': long,
            'lat': lat
        }
        features.update(await self._gather_additional_features(long, lat))
        prediction = self.model.predict(features)
        return prediction
    
    async def _gather_additional_features(
        self,
        long: float,
        lat: float
    ) -> dict[str, float | int]:
        features = {}
        tasks = []
        tasks.append(
            self.maps_api_client.get_region(
                long=long,
                lat=lat
            )
        )
        tasks.append(
            self.maps_api_client.get_transport_context(
                long=long,
                lat=lat
            )
        )
        for radius in self.RADII:
            tasks.append(
                self.maps_api_client.count_categories(
                    long=long,
                    lat=lat,
                    radius=radius
                )
            )
        async with self.maps_api_client:
            region, transport_context, *category_counts = await asyncio.gather(*tasks)
        features['region'] = region or 'unknown'
        features.update(self._extract_features_from_transport_context(transport_context))
        for radius, counts in zip(self.RADII, category_counts):
            features.update(self._extract_features_from_category_counts(counts, radius))
        return features
    
    def _extract_features_from_transport_context(
        self,
        transport_context: TransportationContext
    ) -> float:
        features = {}
        features['metro_distance'] = transport_context.nearest_metro_distance or 0.0
        features['metro_count'] = transport_context.metro_stations_count
        features['bus_tram_count'] = transport_context.total_public_transport
        return features
    
    def _extract_features_from_category_counts(
        self,
        category_counts: dict[str, POICountResult],
        radius: int
    ) -> dict[str, float]:
        features = {}
        for sur in self._get_surroundings_types():
            features[f"{sur}_{radius}"] = 0
        for pois_count in category_counts.values():
            for poi, count in pois_count.counts.items():
                surrounding = SURROUNDINGS_MAPPING[poi]
                features[f"{surrounding}_{radius}"] += count
        return features
    
    def _get_surroundings_types(self) -> list[str]:
        surs = set()
        for sur_type in SURROUNDINGS_MAPPING.values():
            surs.add(sur_type)
        return list(surs)