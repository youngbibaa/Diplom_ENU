from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(32), nullable=False, default="running")
    model_version = Column(String(255), nullable=True)
    documents_processed = Column(Integer, nullable=False, default=0)
    topics_created = Column(Integer, nullable=False, default=0)
    trend_rows_created = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)