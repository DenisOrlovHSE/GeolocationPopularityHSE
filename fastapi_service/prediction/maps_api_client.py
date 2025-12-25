from typing import Any
from maps_api.overpass import (
    OverpassClient,
    POICountResult
)
from maps_api.overpass.models import TransportationContext
from maps_api.nominatim import NominatimClient


QUERY_CATEGORIES = {
    'shop': [
        'convenience', 'kiosk', 'newsagent', 'tobacco',
        'lottery', 'pawnbroker', 'money_lender', 'charity',
        'mall', 'department_store', 'supermarket',
        'hairdresser', 'beauty', 'barber', 'massage',
        'tailor', 'laundry', 'dry_cleaning'
    ],
    
    'amenity': [
        'marketplace', 'vending_machine',
        'restaurant', 'cafe', 'fast_food', 'food_court',
        'ice_cream', 'bar', 'pub',
        'cinema', 'theatre', 'casino', 'nightclub',
        'bus_station', 'train_station', 'taxi',
        'ferry_terminal', 'bicycle_rental',
        'university', 'college', 'school', 'kindergarten',
        'library', 'community_centre', 'post_office',
        'police', 'courthouse', 'place_of_worship',
        'hospital', 'clinic', 'pharmacy', 'dentist',
        'bank', 'bureau_de_change', 'atm'
    ],
    
    'tourism': [
        'hotel', 'hostel', 'guest_house', 'motel'
    ],
    
    'building': [
        'church', 'cathedral', 'chapel', 'mosque', 
        'temple', 'synagogue', 'shrine', 'monastery'
    ]
}


class MapsApiClient:

    def __init__(
        self
    ) -> None:
        self.overpass_client = OverpassClient()
        self.nominatim_client = NominatimClient()

    async def __aenter__(self) -> "MapsApiClient":
        await self.overpass_client.start()
        await self.nominatim_client.start()
        return self
    
    async def __aexit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any
    ) -> None:
        await self.overpass_client.stop()
        await self.nominatim_client.stop()

    async def count_categories(
        self,
        long: float,
        lat: float,
        radius: int = 1000
    ) -> dict[str, POICountResult]:
        result = await self.overpass_client.count_categories(
            long=long,
            lat=lat,
            radius=radius,
            categories=QUERY_CATEGORIES
        )
        return result

    async def get_transport_context(
        self,
        long: float,
        lat: float,
        radius: int = 500
    ) -> dict[str, TransportationContext]:
        result = await self.overpass_client.get_transportation_context(
            long=long,
            lat=lat,
            radius=radius
            )
        return result
        
    async def get_region(
        self,
        long: float,
        lat: float
    ) -> str | None:
        response = await self.nominatim_client.get_administrative_context(
            long=long,
            lat=lat
        )
        return response.region