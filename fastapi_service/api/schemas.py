from pydantic import BaseModel


class PredictionRequest(BaseModel):
    id: int
    atm_group: float
    lat: float
    long: float


class PredictionResponse(BaseModel):
    id: int
    atm_group: float
    popularity: float


class PredictionHistoryItem(BaseModel):
    id: int
    atm_group: float
    popularity: float
    created_at: str
    processed_at: str | None
    success: bool


class PredictionHistoryResponse(BaseModel):
    data: list[PredictionHistoryItem]


class PredictionStatsResponse(BaseModel):
    average_prediction_time_ms: float
    prediction_time_ms_q_50: float
    prediction_time_ms_q_95: float
    prediction_time_ms_q_99: float
    average_popularity: float
    most_popular_atm_group: float
    success_rate: float