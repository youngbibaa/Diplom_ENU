from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    keywords: Mapped[str] = mapped_column(Text, nullable=False)

    document_links = relationship("DocumentTopic", back_populates="topic", cascade="all, delete-orphan")
    trend_metrics = relationship("TrendMetric", back_populates="topic", cascade="all, delete-orphan")
