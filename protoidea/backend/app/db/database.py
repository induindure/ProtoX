from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Supabase pooler (port 6543) requires these specific settings
engine = create_engine(
    settings.database_url,
    pool_pre_ping=False,       # don't ping — pooler doesn't support it
    pool_size=5,
    max_overflow=0,
    pool_timeout=10,           # give up after 10s instead of hanging forever
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()