from typing import TypedDict

import os
import json
import pandas as pd
from pathlib import Path

from maps_api.overpass import OverpassClient


ADDRESSES_PATH = "dataset/atm_train_extended.csv"
SAVE_PATH = "temp/data_collecting_save.json"

EXTENDED_DATASET_PATH = "temp/atm_train_extended.csv"


class SaveData(TypedDict):
    initialized: bool
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
    return SaveData(index=0, initialized=False)


def initialize_extended_df(initialized: bool) -> pd.DataFrame:
    if os.path.exists(EXTENDED_DATASET_PATH) and initialized:
        return pd.read_csv(EXTENDED_DATASET_PATH, encoding='utf-8')
    else:
        df = pd.read_csv(ADDRESSES_PATH, encoding='utf-8')
        df["highway_type"] = "unknown"
        df["highway_distance"] = 0.0
        return df
    

def save_extended_df(
    df: pd.DataFrame,
    last_processed_index: int
) -> None:
    df.to_csv(f"{EXTENDED_DATASET_PATH}", index=False, encoding='utf-8')
    save_data(
        SaveData(index=last_processed_index, initialized=True)
    )


client = OverpassClient()

loaded_data = load_data()
last_processed_index = loaded_data["index"]

df = pd.read_csv(ADDRESSES_PATH, encoding='utf-8')

extended_df = initialize_extended_df(loaded_data["initialized"])

current_index = 0

for index, row in df.iterrows():
    if current_index < last_processed_index:
        current_index += 1
        continue
    long = float(df.at[index, 'long'])
    lat = float(df.at[index, 'lat'])
    hw_context = client.get_nearest_highway_context(
        long=long,
        lat=lat
    )
    if hw_context.success:
        extended_df.at[index, "highway_type"] = hw_context.highway_type
        extended_df.at[index, "highway_distance"] = hw_context.distance_meters
    current_index += 1
    if current_index % 100 == 0:
        save_extended_df(extended_df, current_index)
        print(f"{current_index} addresses processed")

save_extended_df(extended_df, current_index)

print("Data is collected")