from sqlalchemy import Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DocumentTopic(Base):
    __tablename__ = "document_topics"
    __table_args__ = (UniqueConstraint("document_id", name="uq_document_topics_document_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    document = relationship("Document", back_populates="topic_links")
    topic = relationship("Topic", back_populates="document_links")
