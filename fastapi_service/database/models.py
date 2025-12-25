from datetime import datetime, timezone
from sqlalchemy import Float, DateTime, JSON, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PredictionRequest(Base):
    __tablename__ = "prediction_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    popularity: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    processed_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
