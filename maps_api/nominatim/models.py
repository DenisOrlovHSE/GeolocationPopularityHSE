from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class NominatimAddress(BaseModel):
    house_number: Optional[str] = None
    road: Optional[str] = None
    suburb: Optional[str] = None
    city_district: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    ISO3166_2_lvl4: Optional[str] = None
    region: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    
    model_config = ConfigDict(extra='allow')
    
    @property
    def address_str(self) -> str:
        address_parts = []
        
        if self.house_number and self.road:
            address_parts.append(f"{self.road} {self.house_number}")
        elif self.road:
            address_parts.append(self.road)
        elif self.house_number:
            address_parts.append(self.house_number)
        
        if self.suburb:
            address_parts.append(self.suburb)
        
        if self.city:
            address_parts.append(self.city)
        elif self.city_district:
            address_parts.append(self.city_district)
        
        if self.state:
            address_parts.append(self.state)
        elif self.region:
            address_parts.append(self.region)
        
        if self.country:
            address_parts.append(self.country)
        
        if self.postcode and address_parts:
            address_parts.append(self.postcode)
        
        return ", ".join(address_parts) if address_parts else "Address not available"


class NominatimResponse(BaseModel):
    place_id: int
    licence: str
    osm_type: str
    osm_id: int
    lat: str
    lon: str
    class_: str = Field(alias='class')
    type: str
    place_rank: int
    importance: float
    addresstype: str
    name: Optional[str] = None
    display_name: str
    address: NominatimAddress
    boundingbox: list[str]
    
    model_config = ConfigDict(populate_by_name=True)


class AdministrativeContext(BaseModel):
    city: Optional[str] = None
    city_population: Optional[int] = None
    region: Optional[str] = None
    country: Optional[str] = None
    postcode: Optional[str] = None
    is_urban: bool = True
    success: bool = True
    error: Optional[str] = None