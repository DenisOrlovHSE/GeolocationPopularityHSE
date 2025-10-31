from typing import TypedDict

import os
import json
import pandas as pd
from pathlib import Path

from maps_api.overpass import OverpassClient, POICountResult


ADDRESSES_PATH = "dataset/atm_train.csv"
SAVE_PATH = "temp/data_collecting_save.json"

EXTENDED_DATASET_PATH = "temp/atm_train_extended.csv"


RADII = [100, 250, 500, 1000]


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


class SaveData(TypedDict):
    index: int


def save_data(
    data: SaveData,
    save_path: str = SAVE_PATH
) -> None:
    file_path = Path(save_path)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_data(
    save_path: str = SAVE_PATH
) -> SaveData:
    file_path = Path(save_path)
    if file_path.exists():
        try:
            with file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise FileNotFoundError("Save file is corrupted")
    return SaveData(index=0)


def get_surroundings_types() -> list[str]:
    surs = set()
    for sur_type in SURROUNDINGS_MAPPING.values():
        surs.add(sur_type)
    return list(surs)


def initialize_extended_df() -> pd.DataFrame:
    if os.path.exists(EXTENDED_DATASET_PATH):
        return pd.read_csv(EXTENDED_DATASET_PATH, encoding='utf-8')
    else:
        df = pd.read_csv(ADDRESSES_PATH, encoding='utf-8')
        surrounding_types = get_surroundings_types()
        for radius in RADII:
            for sur in surrounding_types:
                df[f"{sur}_{radius}"] = 0
        return df
    

def save_extended_df(
    df: pd.DataFrame,
    last_processed_index: int
) -> None:
    df.to_csv(f"{EXTENDED_DATASET_PATH}", index=False, encoding='utf-8')
    save_data(
        SaveData(index=last_processed_index)
    )


def count_surroundings(
    data: dict[str, POICountResult],
    radius: int
) -> dict[str, int]:
    result = {}
    for sur in get_surroundings_types():
        result[f"{sur}_{radius}"] = 0
    for pois_count in data.values():
        for poi, count in pois_count.counts.items():
            surrounding = SURROUNDINGS_MAPPING[poi]
            result[f"{surrounding}_{radius}"] += count
    return result


client = OverpassClient()

df = pd.read_csv(ADDRESSES_PATH, encoding='utf-8')

extended_df = initialize_extended_df()

last_processed_index = load_data()["index"]
current_index = 0

for radius in RADII:
    for index, row in df.iterrows():
        if current_index < last_processed_index:
            current_index += 1
            continue
        long = float(df.at[index, 'long'])
        lat = float(df.at[index, 'lat'])
        counted_pois = client.count_categories(
            long=long,
            lat=lat,
            radius=radius,
            categories=QUERY_CATEGORIES
        )
        for sur, count in count_surroundings(counted_pois, radius).items():
            extended_df.at[index, sur] = count
        current_index += 1
        if current_index % 100 == 0:
            save_extended_df(extended_df, current_index)
            print(f"{current_index} addresses processed")

save_extended_df(extended_df, current_index)

print("Data is collected")
