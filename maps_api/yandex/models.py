from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Component(BaseModel):
    kind: str
    name: str


class Address(BaseModel):
    country_code: Optional[str] = None
    formatted: str
    components: List[Component] = Field(..., alias="Components")


class Premise(BaseModel):
    premise_number: str = Field(..., alias="PremiseNumber")


class Thoroughfare(BaseModel):
    thoroughfare_name: str = Field(..., alias="ThoroughfareName")
    premise: Optional[Premise] = None


class Locality(BaseModel):
    locality_name: str = Field(..., alias="LocalityName")
    thoroughfare: Optional[Thoroughfare] = None


class SubAdministrativeArea(BaseModel):
    sub_administrative_area_name: str = Field(..., alias="SubAdministrativeAreaName")
    locality: Optional[Locality] = None


class AdministrativeArea(BaseModel):
    administrative_area_name: str = Field(..., alias="AdministrativeAreaName")
    sub_administrative_area: Optional[SubAdministrativeArea] = Field(None, alias="SubAdministrativeArea")


class Country(BaseModel):
    address_line: str = Field(..., alias="AddressLine")
    country_name_code: str = Field(..., alias="CountryNameCode")
    country_name: str = Field(..., alias="CountryName")
    administrative_area: Optional[AdministrativeArea] = Field(None, alias="AdministrativeArea")


class AddressDetails(BaseModel):
    country: Optional[Country] = Field(None, alias="Country")
    address: Optional[str] = Field(None, alias="Address")


class GeocoderMetaData(BaseModel):
    precision: str
    text: str
    kind: str
    address: Address = Field(..., alias="Address")
    address_details: AddressDetails = Field(..., alias="AddressDetails")


class GeoObjectMetaDataProperty(BaseModel):
    geocoder_meta_data: GeocoderMetaData = Field(..., alias="GeocoderMetaData")


class Envelope(BaseModel):
    lower_corner: str = Field(..., alias="lowerCorner")
    upper_corner: str = Field(..., alias="upperCorner")


class BoundedBy(BaseModel):
    envelope: Envelope = Field(..., alias="Envelope")


class Point(BaseModel):
    pos: str


class GeoObject(BaseModel):
    meta_data_property: GeoObjectMetaDataProperty = Field(..., alias="metaDataProperty")
    name: str
    description: Optional[str] = None
    bounded_by: BoundedBy = Field(..., alias="boundedBy")
    uri: str
    point: Point = Field(..., alias="Point")


class FeatureMember(BaseModel):
    geo_object: GeoObject = Field(..., alias="GeoObject")


class RequestPoint(BaseModel):
    pos: str


class GeocoderResponseMetaData(BaseModel):
    point: Optional[RequestPoint] = Field(None, alias="Point")
    request: str
    results: str
    suggest: Optional[str] = None
    found: str


class GeoObjectCollectionMetaDataProperty(BaseModel):
    geocoder_response_meta_data: GeocoderResponseMetaData = Field(..., alias="GeocoderResponseMetaData")


class GeoObjectCollection(BaseModel):
    meta_data_property: GeoObjectCollectionMetaDataProperty = Field(..., alias="metaDataProperty")
    feature_member: List[FeatureMember] = Field(..., alias="featureMember")