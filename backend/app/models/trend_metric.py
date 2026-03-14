from datetime import date

from sqlalchemy import Date, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TrendMetric(Base):
    __tablename__ = "trend_metrics"
    __table_args__ = (UniqueConstraint("topic_id", "date", name="uq_trend_metrics_topic_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    mentions_count: Mapped[int] = mapped_column(nullable=False, default=0)
    growth_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trend_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    topic = relationship("Topic", back_populates="trend_metrics")
