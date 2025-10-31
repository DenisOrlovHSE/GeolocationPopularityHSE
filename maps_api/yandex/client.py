from typing import Optional
import requests

from .constants import GEOCODE_URL
from .models import GeoObjectCollection


TIMEOUT = 5


class YandexMapsClient:

    def __init__(
        self,
        api_key: str
    ) -> None:
        self.api_key = api_key
        self.session = requests.Session()
        self.geocode_url = GEOCODE_URL
        self.timeout = TIMEOUT
        self.session.headers.update({
            'User-Agent': 'YandexMapsClient/1.0'
        })

    def get_geodata(
        self,
        address: Optional[str] = None,
        coords: Optional[tuple[float, float]] = None    # long, lat
    ) -> GeoObjectCollection | None:
        try:
            assert address is not None or coords is not None
            params = {
                "apikey": self.api_key,
                "format": "json"
            }
            if coords is not None:
                long, lat = coords
                params["geocode"] = f"{long:.6f},{lat:.6f}"
            if address is not None:
                params["geocode"] = address.replace(" ", "+")
            response = self.session.get(
                url=self.geocode_url,
                params=params,
                timeout=self.timeout
            )
            resp_json = response.json()
            return GeoObjectCollection.model_validate(resp_json["response"]["GeoObjectCollection"])
        except Exception as e:
            print(f"Error in geodata fetching: {e}")
            return
        