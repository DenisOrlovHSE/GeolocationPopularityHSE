import aiohttp
import asyncio

from .constant import NOMINATIM_URL
from .models import NominatimResponse, AdministrativeContext


TIMEOUT = 5
INTERVAL = 1


class NominatimClient:
    
    def __init__(self) -> None:
        self.session: aiohttp.ClientSession | None = None
        self.url = NOMINATIM_URL
        self.timeout = TIMEOUT
        self.interval = INTERVAL
        self.last_request_time = 0
        self.headers = {
            "User-Agent": "CustomOSMClient/1.0 (daorlov@edu.hse.ru)"
        }

    async def start(self) -> None:
        self.session = aiohttp.ClientSession(headers=self.headers)
    
    async def stop(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_geodata_by_coords(
        self,
        long: float,
        lat: float,
        language: str = 'ru'
    ) -> NominatimResponse | None:
        await self._wait_for_rate_limit()
        params = {
            "lat": lat,
            "lon": long,
            "format": 'json',
            "addressdetails": 1,
            "accept-language": language
        }
        try:
            async with self.session.get(
                self.url,
                params=params,
                timeout=self.timeout
            ) as response:
                self.last_request_time = asyncio.get_event_loop().time()
                response.raise_for_status()
                data = await response.json()
                return NominatimResponse.model_validate(data)
        except Exception as e:
            print(f"Error getting address from Nominatim: {e}")
            return None
        
    async def get_administrative_context(
        self,
        long: float,
        lat: float
    ) -> AdministrativeContext:
        await self._wait_for_rate_limit()
        try:
            params = {
                'lat': lat,
                'lon': long,
                'format': 'json',
                'addressdetails': 1,
                'accept-language': 'ru'
            }
            
            async with self.session.get(
                self.url,
                params=params,
                timeout=self.timeout
            ) as response:
                self.last_request_time = asyncio.get_event_loop().time()
                response.raise_for_status()
                data = await response.json()
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
        
    async def _wait_for_rate_limit(self) -> None:
        delta = asyncio.get_event_loop().time() - self.last_request_time
        if delta < self.interval:
            await asyncio.sleep(self.interval - delta)