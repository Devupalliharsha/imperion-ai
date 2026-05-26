# database.py
# SQLAlchemy connects Python to SQLite.
# SessionLocal is what every route uses to talk to the DB.
# get_db() is a FastAPI "dependency" — FastAPI automatically injects it into routes that need it.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# This creates a file called imperion.db in the project root.
# No setup needed — SQLite creates it automatically on first run.
DATABASE_URL = "sqlite:///./imperion.db"

engine = create_engine(
    DATABASE_URL,
    # SQLite needs this flag for multi-threaded use (FastAPI runs async)
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All our models (tables) inherit from this Base
Base = declarative_base()


def get_db():
    """
    FastAPI dependency. Opens a DB session, yields it to the route,
    then closes it when the route finishes — even if there's an error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
