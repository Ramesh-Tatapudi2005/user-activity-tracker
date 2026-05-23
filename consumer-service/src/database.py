import os
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base

logger = logging.getLogger(__name__)

def get_database_url():
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "root_password")
    db = os.getenv("MYSQL_DATABASE", "user_activity_db")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully.")
            return
        except Exception as e:
            logger.warning(f"Database connection failed. Retrying... {e}")
            retries -= 1
            time.sleep(5)
    raise ConnectionError("Failed to connect to the database after multiple attempts.")