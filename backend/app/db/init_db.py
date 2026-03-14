from app.core.database import Base, engine
import app.models  # noqa: F401


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
