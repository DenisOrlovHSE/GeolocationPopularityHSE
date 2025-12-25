from datetime import datetime, timezone

from ..database.repository import Repository, AsyncSession
from ..database.models import PredictionRequest
from ..prediction.predictors import PredictorInterface
from ..application.dto import (
    PredictionRequestDTO,
    PredictionResponseDTO,
    PredictionHistoryItemDTO,
    PredictionStatsDTO
)


class PredictionService:

    def __init__(
        self,
        predictor: PredictorInterface,
        session: AsyncSession
    ) -> None:
        self.predictor = predictor
        self.repository = Repository(session)

    async def predict_atm_popularity(
        self,
        prediction_request: PredictionRequestDTO
    ) -> PredictionResponseDTO:
        prediction_request_entry = await self.repository.create_prediction_request(
            input_data=prediction_request.model_dump()
        )
        popularity = await self.predictor.predict(
            id=prediction_request.atm_id,
            atm_group=prediction_request.atm_group,
            long=prediction_request.longitude,
            lat=prediction_request.latitude
        )
        await self.repository.modify_prediction_request(
            request=prediction_request_entry,
            popularity=popularity,
            processed_at=datetime.now(timezone.utc),
            success=popularity is not None
        )
        response = PredictionResponseDTO(
            success=popularity is not None,
            atm_id=prediction_request.atm_id,
            atm_group=prediction_request.atm_group,
            predicted_popularity=popularity
        )
        return response
    
    async def get_predictions_history(self) -> list[PredictionHistoryItemDTO]:
        requests = await self.repository.get_prediction_history()
        history_dto = [
            PredictionHistoryItemDTO(
                atm_id=int(req.input_data.get("atm_id", -1)),
                atm_group=float(req.input_data.get("atm_group", -1)),
                predicted_popularity=req.popularity,
                created_at=req.created_at.isoformat(),
                processed_at=req.processed_at.isoformat() if req.processed_at else None,
                success=req.success
            )
            for req in requests
        ]
        return history_dto
    
    async def get_prediction_stats(self) -> PredictionStatsDTO:
        all_requests = await self.repository.get_prediction_history()
        avg_time, q_50, q_95, q_99 = self._calculate_prediction_time_stats(all_requests)
        average_popularity, most_popular_atm_group, success_rate = self._calculate_prediction_data_stats(all_requests)
        stats_dto = PredictionStatsDTO(
            average_prediction_time_ms=avg_time,
            prediction_time_ms_q_50=q_50,
            prediction_time_ms_q_95=q_95,
            prediction_time_ms_q_99=q_99,
            average_popularity=average_popularity,
            most_popular_atm_group=most_popular_atm_group,
            success_rate=success_rate
        )
        return stats_dto
    
    def _calculate_prediction_time_stats(
        self,
        requests: list[PredictionRequest]
    ) -> tuple[float, float, float, float]:
        pred_times = [
            int((req.processed_at.timestamp() - req.created_at.timestamp()) * 1000.0)
            for req in requests
            if req.processed_at is not None
        ]
        pred_times.sort()
        
        if not pred_times:
            return 0.0, 0.0, 0.0, 0.0
        
        avg_time = sum(pred_times) / len(pred_times)
        q_50 = pred_times[int(len(pred_times) * 0.50)]
        q_95 = pred_times[int(len(pred_times) * 0.95)]
        q_99 = pred_times[int(len(pred_times) * 0.99)]
        return avg_time, q_50, q_95, q_99
    
    def _calculate_prediction_data_stats(
        self,
        requests: list[PredictionRequest]
    ) -> tuple[float, float, float]:
        popularities = [
            req.popularity
            for req in requests
            if req.popularity is not None
        ]
        atm_grops = [
            req.input_data.get("atm_group")
            for req in requests
            if req.input_data.get("atm_group") is not None
        ]

        if not popularities:
            return 0.0, 0.0, 0.0
        
        average_popularity = sum(popularities) / len(popularities)
        most_popular_atm_group = max(set(atm_grops), key=atm_grops.count)
        success_rate = len(popularities) / len(requests) if requests else 0.0
        return average_popularity, most_popular_atm_group, success_rate