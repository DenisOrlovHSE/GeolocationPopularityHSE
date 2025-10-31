import requests

import time

from .constant import NOMINATIM_URL
from .models import NominatimResponse, AdministrativeContext


TIMEOUT = 5
INTERVAL = 1


class NominatimClient:
    
    def __init__(self) -> None:
        self.session = requests.Session()
        self.url = NOMINATIM_URL
        self.timeout = TIMEOUT
        self.interval = INTERVAL
        self.last_request_time = 0
        self.session.headers.update({
            "User-Agent": "CustomOSMClient/1.0 (daorlov@edu.hse.ru)"
        })
    
    def get_geodata_by_coords(
        self,
        long: float,
        lat: float,
        language: str = 'ru'
    ) -> NominatimResponse | None:
        self._wait_for_rate_limit()
        params = {
            "lat": lat,
            "lon": long,
            "format": 'json',
            "addressdetails": 1,
            "accept-language": language
        }
        try:
            response = self.session.get(
                self.url,
                params=params,
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            response.raise_for_status()
            data = response.json()
            return NominatimResponse.model_validate(data)
        except Exception as e:
            print(f"Error getting address from Nominatim: {e}")
            return None
        
    def get_administrative_context(
        self,
        long: float,
        lat: float
    ) -> AdministrativeContext:
        self._wait_for_rate_limit()
        try:
            params = {
                'lat': lat,
                'lon': long,
                'format': 'json',
                'addressdetails': 1,
                'accept-language': 'ru'
            }
            
            response = self.session.get(
                self.url,
                params=params,
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            response.raise_for_status()
            data = response.json()
            address = data.get('address', {})
            city = (
                address.get('city') or
                address.get('town') or 
                address.get('municipality') or
                address.get('village') or
                address.get('hamlet') or
                address.get('county')
            )
            is_urban = bool(address.get('city') or address.get('town'))
            return AdministrativeContext(
                city=city,
                region=address.get('state'),
                country=address.get('country'),
                postcode=address.get('postcode'),
                is_urban=is_urban,
                success=True
            ) 
        except Exception as e:
            print(f"Error getting administrative context: {e}")
            return AdministrativeContext(
                success=False,
                error=str(e)
            )
        
    def _wait_for_rate_limit(self) -> None:
        delta = time.time() - self.last_request_time
        if delta < self.interval:
            time.sleep(delta)