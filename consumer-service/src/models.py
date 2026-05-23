from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserActivity(Base):
    __tablename__ = 'user_activities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    metadata_payload = Column('metadata', JSON)