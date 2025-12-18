from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class OSM3S(BaseModel):
    timestamp_osm_base: str
    copyright: str


class Position(BaseModel):
    lat: float
    lon: float


class Tag(BaseModel):

    addr_housenumber: Optional[str] = None
    addr_street: Optional[str] = None
    addr_city: Optional[str] = None
    addr_postcode: Optional[str] = None
    addr_country: Optional[str] = None
    
    amenity: Optional[str] = None
    building: Optional[str] = None
    name: Optional[str] = None
    name_ru: Optional[str] = None
    
    class Config:
        extra = 'allow'


class Node(BaseModel):
    type: str
    id: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    tags: Optional[Dict[str, Any]] = None


class Way(BaseModel):
    type: str
    id: int
    nodes: List[int]
    tags: Optional[Dict[str, Any]] = None


class Relation(BaseModel):
    type: str
    id: int
    members: List[Dict[str, Any]]
    tags: Optional[Dict[str, Any]] = None


class OSMElement(BaseModel):
    type: str
    id: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    nodes: Optional[List[int]] = None
    tags: Optional[Dict[str, Any]] = None
    members: Optional[List[Dict[str, Any]]] = None


class OverpassResponse(BaseModel):
    version: float
    generator: str
    osm3s: OSM3S
    elements: List[OSMElement]


class POICountResult(BaseModel):
    success: bool
    total: int
    counts: Dict[str, int]
    category: str
    elements_found: int
    error: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    radius: Optional[float] = None


class LocationContext(BaseModel):
    landuse_types: List[str] = []
    building_types: List[str] = []
    is_in_building: bool = False
    primary_landuse: Optional[str] = None
    primary_building: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class HighwayContext(BaseModel):
    highway_type: Optional[str] = None
    highway_name: Optional[str] = None
    distance_meters: Optional[float] = None
    nearest_highway_id: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


class ParkingContext(BaseModel):
    parking_count: int = 0
    parking_types: List[str] = []
    nearest_parking_distance: Optional[float] = None
    parking_capacity: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


class TransportationContext(BaseModel):
    metro_stations_count: int = 0
    metro_station_names: List[str] = []
    nearest_metro_distance: Optional[float] = None
    nearest_metro_name: Optional[str] = None
    
    bus_stops_count: int = 0
    tram_stops_count: int = 0
    nearest_bus_distance: Optional[float] = None
    
    total_public_transport: int = 0
    has_major_transport_hub: bool = False
    success: bool = True
    error: Optional[str] = None


class StreetLightingContext(BaseModel):
    street_lamps_count: int = 0
    nearest_street_lamp_distance: Optional[float] = None
    lighting_density: float = 0.0
    has_adequate_lighting: bool = False
    success: bool = True
    error: Optional[str] = None

class DensityContext(BaseModel):
    building_density: float = 0.0
    address_density: float = 0.0
    is_high_density: bool = False
    success: bool = True
    error: Optional[str] = None