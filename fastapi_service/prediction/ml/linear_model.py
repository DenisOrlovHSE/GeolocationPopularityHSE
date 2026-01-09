import pickle
import pandas as pd

from .model_interface import ModelInterface


FEATURE_NAMES = [
    'long', 'lat', 'region', 'atm_group',
    'food_drink_500', 'bus_tram_count', 'food_drink_1000',
    'food_drink_250', 'metro_distance', 'personal_services_1000',
    'metro_count', 'financial_services_250', 'financial_services_500',
    'financial_services_1000', 'food_drink_100', 'personal_services_500',
    'cash_intensive_shops_1000', 'entertainment_1000',
    'markets_vendors_1000', 'healthcare_1000',
    'financial_services_100', 'personal_services_250',
    'cash_intensive_shops_500', 'entertainment_500', 'tourism_1000'
]


class LinearModel(ModelInterface):

    def __init__(
        self,
        model_path: str,
        training_data_path: str
    ) -> None:
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)
        self._fit_target_encoder(training_data_path)

    def predict(
        self,
        input_data: dict[str, float | int]
    ) -> float | None:
        super().predict(input_data)
        try:
            region = input_data['region']
            if region in self.region_target_mapping:
                input_data['region'] = self.region_target_mapping[region]
            else:
                input_data['region'] = self.region_target_mapping['overall_mean']
            features = pd.DataFrame([input_data])
            features = features.reindex(columns=FEATURE_NAMES)
            features = features.astype(float, errors='ignore')
            prediction = self.model.predict(features)[0]
            return prediction
        except Exception as e:
            print(f"Prediction error: {e}")
            return None

    def _fit_target_encoder(
        self,
        training_data_path: str
    ) -> None:
        with open(training_data_path, "rb") as f:
            training_data = pd.read_csv(f)
            self.region_target_mapping = training_data.groupby('region')['target'].mean().to_dict()
            self.region_target_mapping['overall_mean'] = training_data['target'].mean()