import time
import numpy as np
import pandas as pd

from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor

from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor


RANDOM_SEED = 42


np.random.seed(RANDOM_SEED)


def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        final_time = end_time - start_time
        return final_time
    return wrapper


def fit_decision_tree(X, y):
    dt = DecisionTreeRegressor(random_state=RANDOM_SEED)
    dt.fit(X, y)
    return dt


def fit_random_forest(X, y):
    rf = RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1)
    rf.fit(X, y)
    return rf


def fit_catboost(X, y, cat_features):
    catboost = CatBoostRegressor(random_state=RANDOM_SEED, verbose=0)
    catboost.fit(X, y, cat_features=cat_features)
    return catboost


def fit_lightgbm(X, y):
    lightgbm = LGBMRegressor(random_state=RANDOM_SEED, n_jobs=-1)
    lightgbm.fit(X, y)
    return lightgbm


class TargetEncoder:

    def __init__(
        self,
        smoothing: float = 0.0
    ) -> None:
        assert 0.0 <= smoothing <= 1.0, "smoothing must be in [0, 1]"
        self.smoothing = smoothing
        self.global_mean_: float = None
        self.encoding_maps_: dict[str, dict] = {}

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        columns: list[str]
    ) -> "TargetEncoder":
        self.columns = columns
        self.global_mean_ = y.mean()
        for col in columns:
            cat_means = (
                pd.concat([X[col], y], axis=1)
                .groupby(col)[y.name]
                .mean()
            )
            encoded = (1 - self.smoothing) * cat_means + self.smoothing * self.global_mean_
            self.encoding_maps_[col] = encoded.to_dict()
        return self

    def transform(
        self,
        X: pd.DataFrame
    ) -> pd.DataFrame:
        X = X.copy()
        for col in self.columns:
            X[col] = X[col].map(self.encoding_maps_[col]).fillna(self.global_mean_)
        return X

    def fit_transform(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        columns: list[str]
    ) -> pd.DataFrame:
        return self.fit(X, y, columns).transform(X)
    

df_train = pd.read_csv("./dataset/atm_train_split.csv", encoding='utf-8')
df_test = pd.read_csv("./dataset/atm_test_split.csv", encoding='utf-8')

cat_cols = ["region", "atm_group"]

encoder = TargetEncoder(smoothing=0.1)
df_train_encoded = encoder.fit_transform(df_train, df_train["target"], columns=cat_cols)

df_test_encoded = encoder.transform(df_test)

feature_cols = [c for c in df_train.columns if c != "target"]

X_train = df_train[feature_cols].copy()
y_train = df_train["target"]

X_test = df_test[feature_cols].copy()
y_test = df_test["target"]

X_train_encoded = df_train_encoded[feature_cols]
X_test_encoded = df_test_encoded[feature_cols]

X_train["atm_group"] = X_train["atm_group"].astype(str)
X_test["atm_group"] = X_test["atm_group"].astype(str)

for col in cat_cols:
    X_train[col] = X_train[col].astype("category")
    X_test[col] = X_test[col].astype("category")


dt_time = measure_time(fit_decision_tree)(X_train_encoded, y_train)
rf_time = measure_time(fit_random_forest)(X_train_encoded, y_train)
catboost_time = measure_time(fit_catboost)(X_train, y_train, cat_cols)
lightgbm_time = measure_time(fit_lightgbm)(X_train, y_train)

print(f"Decision Tree: {dt_time:.2f} секунд")
print(f"Random Forest: {rf_time:.2f} секунд")
print(f"CatBoost: {catboost_time:.2f} секунд")
print(f"LightGBM: {lightgbm_time:.2f} секунд")