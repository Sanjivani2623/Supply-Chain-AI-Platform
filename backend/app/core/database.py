"""
SQLAlchemy engine / session management.

Defaults to a local SQLite file (zero server setup - just a .db file on
disk). SQLite needs `check_same_thread=False` because FastAPI serves sync
route handlers from a thread pool; every request still gets its own Session
via get_db(), so this is safe. If DATABASE_URL points at Postgres/MySQL/etc.
instead, the extra connect_arg is simply ignored.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Ensure the directory for the SQLite file exists (e.g. ./data/scai.db)
    db_path = settings.DATABASE_URL.replace("sqlite:///", "", 1)
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
