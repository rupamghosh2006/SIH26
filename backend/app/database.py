"""
Database connection and session factory using SQLite and SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Initializes tables and performs lightweight SQLite migrations for new columns."""
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    
    # Ensure SQLite columns exist if upgrading existing databases
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        if "detections" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("detections")]
            expected_columns = {
                "detector_score": "FLOAT",
                "shadow_score": "FLOAT",
                "shape_score": "FLOAT",
                "shadow_detected": "BOOLEAN DEFAULT 0",
                "filter_details_json": "TEXT",
                "verification_json": "TEXT"
            }
            with engine.connect() as conn:
                for col_name, col_type in expected_columns.items():
                    if col_name not in columns:
                        conn.execute(text(f"ALTER TABLE detections ADD COLUMN {col_name} {col_type}"))
                conn.commit()
    except Exception as e:
        print(f"[Database] Migration check notice: {e}")


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
