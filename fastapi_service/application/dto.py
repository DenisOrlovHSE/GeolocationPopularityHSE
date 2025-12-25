from typing import Optional
from pydantic import BaseModel


class PredictionRequestDTO(BaseModel):
    atm_id: int
    atm_group: float
    latitude: float
    longitude: float


class PredictionResponseDTO(BaseModel):
    success: bool
    atm_id: int
    atm_group: float
    predicted_popularity: Optional[float] = None


class PredictionHistoryItemDTO(BaseModel):
    atm_id: int
    atm_group: float
    predicted_popularity: float | None
    created_at: str
    processed_at: str | None
    success: bool


class PredictionStatsDTO(BaseModel):
    average_prediction_time_ms: float
    prediction_time_ms_q_50: float
    prediction_time_ms_q_95: float
    prediction_time_ms_q_99: float
    average_popularity: float
    most_popular_atm_group: float
    success_rate: float
