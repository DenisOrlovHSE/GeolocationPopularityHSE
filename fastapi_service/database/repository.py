from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import PredictionRequest


LIMIT_HISTORY_ITEMS = 5000


class Repository:

    def __init__(
        self,
        session: AsyncSession
    ) -> None:
        self.session = session

    async def create_prediction_request(
        self,
        input_data: dict,
        created_at: datetime | None = None
    ) -> None:
        new_request = PredictionRequest(input_data=input_data, created_at=created_at or datetime.now(timezone.utc))
        self.session.add(new_request)
        return new_request
    
    async def modify_prediction_request(
        self,
        request: PredictionRequest,
        popularity: float | None = None,
        processed_at: datetime | None = None,
        success: bool | None = None
    ) -> PredictionRequest:
        if popularity is not None:
            request.popularity = popularity
        if processed_at is not None:
            request.processed_at = processed_at
        if success is not None:
            request.success = success
        self.session.add(request)
        return request
    
    async def get_prediction_history(
        self
    ) -> list[PredictionRequest]:
        stmt = select(PredictionRequest).order_by(PredictionRequest.created_at.desc()).limit(LIMIT_HISTORY_ITEMS)
        result = await self.session.execute(stmt)
        return result.scalars().all()