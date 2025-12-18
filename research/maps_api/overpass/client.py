from typing import Any

import time
import math
import requests

from .constants import OVERPASS_URL
from .models import (
    OverpassResponse,
    POICountResult,
    LocationContext,
    HighwayContext,
    ParkingContext,
    TransportationContext,
    StreetLightingContext,
    DensityContext
)


TIMEOUT = 5
INTERVAL = 1
R = 6371000


class OverpassClient:

    def __init__(self) -> None:
        self.session = requests.Session()
        self.url = OVERPASS_URL
        self.timeout = TIMEOUT
        self.interval = INTERVAL
        self.last_request_time = 0
        self.session.headers.update({
            'User-Agent': 'OSMClient/1.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        })

    def get_geodata_by_coords(
        self,
        long: float,
        lat: float,
        radius: float = 50
    ) -> OverpassResponse | None:
        self._wait_for_rate_limit()
        query = f"""
        [out:json][timeout:25];
        (
        way(around:{radius},{lat},{long})["building"];
        way(around:{radius},{lat},{long})["addr:street"];
        node(around:{radius},{lat},{long})["addr:street"];
        );
        out body;
        >;
        out skel qt;
        """
    
        try:
            response = self.session.post(
                self.url,
                data={'data': query},
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            response.raise_for_status()
            data = response.json()
            return OverpassResponse.model_validate(data)
        except Exception as e:
            print(f"Error getting address: {e}")
            return None
        
    def count_categories(
        self,
        long: float,
        lat: float,
        radius: float = 1000,
        categories: dict[str, list[str]] = None
    ) -> dict[str, POICountResult]:
        self._wait_for_rate_limit()
        if categories is None:
            categories = {
                'amenity': ['restaurant', 'cafe', 'bank'],
                'shop': ['supermarket', 'convenience']
            }

        query_parts = []
        for category_type, values in categories.items():
            values_pattern = "|".join(values)
            query_parts.append(f'node(around:{radius},{lat},{long})["{category_type}"~"{values_pattern}"];')
            query_parts.append(f'way(around:{radius},{lat},{long})["{category_type}"~"{values_pattern}"];')
        
        query_conditions = "\n  ".join(query_parts)
        
        query = f"""[out:json][timeout:30];
            (
            {query_conditions}
            );
            out body;
            >;
            out skel qt;
        """
        
        coordinates = {"lat": lat, "lon": long}
        
        try:
            response = self.session.post(
                self.url,
                data={'data': query},
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            response.raise_for_status()
            data = response.json()
            results = {}
            for category_type, values in categories.items():
                results[category_type] = POICountResult(
                    success=True,
                    total=0,
                    counts={value: 0 for value in values},
                    category=category_type,
                    elements_found=0,
                    coordinates=coordinates,
                    radius=radius
                )
            
            total_elements = len(data.get('elements', []))
            for element in data.get('elements', []):
                if 'tags' in element:
                    for category_type, values in categories.items():
                        if category_type in element['tags']:
                            tag_value = element['tags'][category_type]
                            if tag_value in values:
                                results[category_type].counts[tag_value] += 1
                                results[category_type].total += 1
            for result in results.values():
                result.elements_found = total_elements
            return results
        except Exception as e:
            error_results = {}
            for category_type in categories.keys():
                error_results[category_type] = POICountResult(
                    success=False,
                    total=0,
                    counts={},
                    category=category_type,
                    elements_found=0,
                    error=str(e),
                    coordinates=coordinates,
                    radius=radius
                )
            return error_results
        
    def get_location_context(
        self,
        long: float,
        lat: float
    ) -> LocationContext:
        self._wait_for_rate_limit()
        query = f"""
            [out:json][timeout:15];
            (
            way(around:1, {lat}, {long})["landuse"];
            way(around:1, {lat}, {long})["building"];
            relation(around:1, {lat}, {long})["landuse"];
            relation(around:1, {lat}, {long})["building"];
            );
            out body;
            >;
            out skel qt;
        """
        try:
            response = self.session.post(
                self.url,
                data={'data': query},
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            response.raise_for_status()
            data = response.json()
            landuse_types = []
            building_types = []
            primary_landuse = None
            primary_building = None
            is_in_building = False
            for element in data.get('elements', []):
                if 'tags' in element:
                    tags = element['tags']
                    if 'landuse' in tags:
                        landuse_type = tags['landuse']
                        if landuse_type not in landuse_types:
                            landuse_types.append(landuse_type)
                        if primary_landuse is None:
                            primary_landuse = landuse_type
                    if 'building' in tags:
                        building_type = tags['building']
                        if building_type not in building_types:
                            building_types.append(building_type)
                        is_in_building = True
                        if primary_building is None:
                            primary_building = building_type
            return LocationContext(
                landuse_types=landuse_types,
                building_types=building_types,
                is_in_building=is_in_building,
                primary_landuse=primary_landuse,
                primary_building=primary_building,
                success=True
            )
        except Exception as e:
            print(f"Error getting location context: {e}")
            return LocationContext(
                success=False,
                error=str(e)
            )
        
    def get_nearest_highway_context(
        self,
        long: float,
        lat: float,
        radius: float = 100
    ) -> HighwayContext:
        self._wait_for_rate_limit()
        query = f"""
        [out:json][timeout:15];
        (
          way(around:{radius},{lat},{long})["highway"];
        );
        out body;
        >;
        out skel qt;
        """
        try:
            response = self.session.post(
                self.url,
                data={'data': query},
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            response.raise_for_status()
            data = response.json()
            nearest_highway = None
            min_distance = float('inf')
            for element in data.get('elements', []):
                if element['type'] == 'way' and 'tags' in element and 'highway' in element['tags']:
                    if 'nodes' in element and element['nodes']:
                        for node_element in data.get('elements', []):
                            if (node_element['type'] == 'node' and 
                                node_element['id'] == element['nodes'][0] and
                                'lat' in node_element and 'lon' in node_element):
                                distance = self._calculate_distance(
                                    lat, long, 
                                    node_element['lat'], node_element['lon']
                                )
                                if distance < min_distance:
                                    min_distance = distance
                                    nearest_highway = {
                                        'type': element['tags']['highway'],
                                        'name': element['tags'].get('name'),
                                        'id': element['id'],
                                        'distance': distance
                                    }
                                break
            if nearest_highway:
                return HighwayContext(
                    highway_type=nearest_highway['type'],
                    highway_name=nearest_highway['name'],
                    distance_meters=nearest_highway['distance'],
                    nearest_highway_id=nearest_highway['id'],
                    success=True
                )
            else:
                return HighwayContext(
                    success=False,
                    error="No highways found in the specified radius"
                )
                
        except Exception as e:
            print(f"Error getting nearest highway context: {e}")
            return HighwayContext(
                success=False,
                error=str(e)
            )
        
    def get_parking_context(
        self,
        long: float,
        lat: float,
        radius: float = 100
    ) -> ParkingContext:
        self._wait_for_rate_limit()
        
        query = f"""
        [out:json][timeout:15];
        (
        node(around:{radius},{lat},{long})["amenity"="parking"];
        way(around:{radius},{lat},{long})["amenity"="parking"];
        node(around:{radius},{lat},{long})["parking"];
        way(around:{radius},{lat},{long})["parking"];
        );
        out body;
        >;
        out skel qt;
        """
        try:
            response = self.session.post(
                self.url,
                data={'data': query},
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            response.raise_for_status()
            data = response.json()
            parking_count = 0
            parking_types = []
            nearest_parking_distance = float('inf')
            parking_capacity = None
            node_coordinates = {}
            for element in data.get('elements', []):
                if element['type'] == 'node' and 'lat' in element and 'lon' in element:
                    node_coordinates[element['id']] = (element['lat'], element['lon'])
            for element in data.get('elements', []):
                if 'tags' in element:
                    tags = element['tags']
                    is_parking = ('amenity' in tags and tags['amenity'] == 'parking') or ('parking' in tags)
                    if is_parking:
                        parking_count += 1
                        parking_type = tags.get('parking') or tags.get('amenity')
                        if parking_type and parking_type not in parking_types:
                            parking_types.append(parking_type)
                        capacity = tags.get('capacity')
                        if capacity and capacity.isdigit():
                            current_capacity = int(capacity)
                            if parking_capacity is None or current_capacity > parking_capacity:
                                parking_capacity = current_capacity
                        distance = None
                        if element['type'] == 'node' and 'lat' in element and 'lon' in element:
                            distance = self._calculate_distance(lat, long, element['lat'], element['lon'])
                        elif element['type'] == 'way':
                            if 'nodes' in element:
                                for node_id in element['nodes']:
                                    if node_id in node_coordinates:
                                        node_lat, node_lon = node_coordinates[node_id]
                                        node_distance = self._calculate_distance(lat, long, node_lat, node_lon)
                                        if distance is None or node_distance < distance:
                                            distance = node_distance
                            if ('center' in element and 
                                'lat' in element['center'] and 
                                'lon' in element['center']):
                                center_distance = self._calculate_distance(
                                    lat, long, 
                                    element['center']['lat'], 
                                    element['center']['lon']
                                )
                                if distance is None or center_distance < distance:
                                    distance = center_distance
                        if distance is not None and distance < nearest_parking_distance:
                            nearest_parking_distance = distance
            if nearest_parking_distance == float('inf'):
                nearest_parking_distance = None
            return ParkingContext(
                parking_count=parking_count,
                parking_types=parking_types,
                nearest_parking_distance=nearest_parking_distance,
                parking_capacity=parking_capacity,
                success=True
            )
        except Exception as e:
            print(f"Error getting parking context: {e}")
            return ParkingContext(
                success=False,
                error=str(e)
            )
        
    def get_transportation_context(
        self,
        long: float,
        lat: float,
        radius: float = 500
    ) -> TransportationContext:
        self._wait_for_rate_limit()
        
        query = f"""
        [out:json][timeout:20];
        (
        // Metro stations and entrances
        node(around:{radius},{lat},{long})["railway"="station"]["station"="subway"];
        node(around:{radius},{lat},{long})["railway"="subway_entrance"];
        
        // Bus stops
        node(around:{radius},{lat},{long})["highway"="bus_stop"];
        
        // Tram stops
        node(around:{radius},{lat},{long})["railway"="tram_stop"];
        node(around:{radius},{lat},{long})["public_transport"="stop_position"]["tram"="yes"];
        );
        out body;
        """
        try:
            response = self.session.post(
                self.url,
                data={'data': query},
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            response.raise_for_status()
            data = response.json()
            context = TransportationContext()
            for element in data.get('elements', []):
                if element['type'] == 'node' and 'tags' in element and 'lat' in element and 'lon' in element:
                    tags = element['tags']
                    distance = self._calculate_distance(lat, long, element['lat'], element['lon'])
                    is_metro = (
                        (tags.get('railway') == 'station' and tags.get('station') == 'subway') or
                        tags.get('railway') == 'subway_entrance'
                    )
                    if is_metro:
                        context.metro_stations_count += 1
                        context.total_public_transport += 1
                        station_name = tags.get('name')
                        if station_name and station_name not in context.metro_station_names:
                            context.metro_station_names.append(station_name)
                        if context.nearest_metro_distance is None or distance < context.nearest_metro_distance:
                            context.nearest_metro_distance = distance
                            context.nearest_metro_name = station_name
                    elif tags.get('highway') == 'bus_stop':
                        context.bus_stops_count += 1
                        context.total_public_transport += 1
                        
                        if context.nearest_bus_distance is None or distance < context.nearest_bus_distance:
                            context.nearest_bus_distance = distance
                    elif (tags.get('railway') == 'tram_stop' or 
                        (tags.get('public_transport') == 'stop_position' and tags.get('tram') == 'yes')):
                        context.tram_stops_count += 1
                        context.total_public_transport += 1
            context.has_major_transport_hub = (
                context.metro_stations_count > 0 or 
                context.bus_stops_count >= 3 or
                context.tram_stops_count >= 2
            )
            return context
        except Exception as e:
            print(f"Error getting transportation context: {e}")
            return TransportationContext(
                success=False,
                error=str(e)
            )
        
    def get_street_lighting_context(
        self,
        long: float,
        lat: float,
        radius: float = 1000
    ) -> StreetLightingContext:
        self._wait_for_rate_limit()
        query = f"""
        [out:json][timeout:15];
        (
        node(around:{radius},{lat},{long})["highway"="street_lamp"];
        node(around:{radius},{lat},{long})["man_made"="street_lamp"];
        );
        out body;
        """
        try:
            response = self.session.post(
                self.url,
                data={'data': query},
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            response.raise_for_status()
            data = response.json()
            street_lamps_count = 0
            nearest_street_lamp_distance = float('inf')
            for element in data.get('elements', []):
                if element['type'] == 'node' and 'tags' in element and 'lat' in element and 'lon' in element:
                    tags = element['tags']
                    is_street_lamp = (
                        tags.get('highway') == 'street_lamp' or
                        tags.get('man_made') == 'street_lamp'
                    )
                    if is_street_lamp:
                        street_lamps_count += 1
                        distance = self._calculate_distance(lat, long, element['lat'], element['lon'])
                        if distance < nearest_street_lamp_distance:
                            nearest_street_lamp_distance = distance
            area_hectares = (3.14159 * (radius ** 2)) / 10000
            lighting_density = street_lamps_count / area_hectares if area_hectares > 0 else 0
            has_adequate_lighting = (
                (nearest_street_lamp_distance is not None and nearest_street_lamp_distance <= 30) or
                lighting_density >= 2.0
            )
            if nearest_street_lamp_distance == float('inf'):
                nearest_street_lamp_distance = None
            return StreetLightingContext(
                street_lamps_count=street_lamps_count,
                nearest_street_lamp_distance=nearest_street_lamp_distance,
                lighting_density=lighting_density,
                has_adequate_lighting=has_adequate_lighting,
                success=True
            )
        except Exception as e:
            print(f"Error getting street lighting context: {e}")
            return StreetLightingContext(
                success=False,
                error=str(e)
            )
        
    def get_density_context(
        self,
        long: float,
        lat: float,
        radius: float = 1000
    ) -> DensityContext:
        self._wait_for_rate_limit()

        query = f"""
        [out:json][timeout:15];
        (
        node(around:{radius},{lat},{long})["building"];
        way(around:{radius},{lat},{long})["building"];
        node(around:{radius},{lat},{long})["addr:housenumber"];
        );
        out body;
        """
        try:
            response = self.session.post(
                self.url,
                data={'data': query},
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            response.raise_for_status()
            data = response.json()
            building_count = 0
            address_count = 0
            for element in data.get('elements', []):
                if 'tags' in element:
                    tags = element['tags']
                    if 'building' in tags:
                        building_count += 1
                    if 'addr:housenumber' in tags:
                        address_count += 1
            area_hectares = (3.14159 * (radius ** 2)) / 10000
            building_density = building_count / area_hectares if area_hectares > 0 else 0
            address_density = address_count / area_hectares if area_hectares > 0 else 0
            is_high_density = building_density > 20
            print(f"DEBUG: Found {building_count} buildings, {address_count} addresses in {radius}m radius")
            print(f"DEBUG: Density: {building_density:.1f} buildings/hectare")
            return DensityContext(
                building_density=building_density,
                address_density=address_density,
                is_high_density=is_high_density,
                success=True
            )
        except Exception as e:
            print(f"Error getting density context: {e}")
            return DensityContext(
                success=False,
                error=str(e)
            )
        
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
        
    def _wait_for_rate_limit(self) -> None:
        delta = time.time() - self.last_request_time
        if delta < self.interval:
            time.sleep(delta)