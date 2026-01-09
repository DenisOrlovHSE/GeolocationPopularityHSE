from fastapi import APIRouter, HTTPException, Depends

from ..database.session import get_session
from ..prediction.predictors import PredictorV1
from ..services import PredictionService
from .schemas import (
    PredictionRequest,
    PredictionResponse,
    PredictionHistoryResponse,
    PredictionHistoryItem,
    PredictionStatsResponse
)
from ..application.dto import (
    PredictionRequestDTO
)

from ..core.config import settings


router = APIRouter()
predictor = PredictorV1(settings.model_path, settings.training_data_path)


@router.post("/forward", response_model=PredictionResponse, description="Forward ATM data to get popularity prediction")
async def forward(
    request: PredictionRequest,
    session=Depends(get_session)
) -> PredictionResponse:
    print(request)
    prediction_service = PredictionService(
        predictor=predictor,
        session=session
    )
    prediction_dto = PredictionRequestDTO(
        atm_group=request.atm_group,
        latitude=request.lat,
        longitude=request.long
    )
    result = await prediction_service.predict_atm_popularity(prediction_request=prediction_dto)
    if not result.success:
        raise HTTPException(status_code=403, detail="Model failed to process the request.")
    return PredictionResponse(
        atm_group=request.atm_group,
        popularity=result.predicted_popularity
    )


@router.get("/history", response_model=PredictionHistoryResponse, description="Get history of predictions. Limited to last 5000 entries.")
async def history(
    session=Depends(get_session)
) -> PredictionHistoryResponse:
    prediction_service = PredictionService(
        predictor=predictor,
        session=session
    )
    history = await prediction_service.get_predictions_history()
    history_response_items = [
        PredictionHistoryItem(
            atm_group=item.atm_group,
            popularity=item.predicted_popularity,
            created_at=item.created_at,
            processed_at=item.processed_at,
            success=item.success
        )
        for item in history
    ]
    return PredictionHistoryResponse(data=history_response_items)


@router.get("/stats", response_model=PredictionStatsResponse, description="Get basic statistics about the service")
async def stats(
    session=Depends(get_session)
) -> PredictionStatsResponse:
    prediction_service = PredictionService(
        predictor=predictor,
        session=session
    )
    stats_dto = await prediction_service.get_prediction_stats()
    return PredictionStatsResponse(
        average_prediction_time_ms=stats_dto.average_prediction_time_ms,
        prediction_time_ms_q_50=stats_dto.prediction_time_ms_q_50,
        prediction_time_ms_q_95=stats_dto.prediction_time_ms_q_95,
        prediction_time_ms_q_99=stats_dto.prediction_time_ms_q_99,
        average_popularity=stats_dto.average_popularity,
        most_popular_atm_group=stats_dto.most_popular_atm_group,
        success_rate=stats_dto.success_rate
    )