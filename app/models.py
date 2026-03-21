from sqlalchemy import Column, Integer, String, Text, DateTime, func
from datetime import datetime
from app.db.db import Base


# Represents a single log entry in the database
class LogEntry(Base):
    __tablename__ = "logs"  # Table name in PostgreSQL

    # Unique ID for each log entry
    id = Column(Integer, primary_key=True, index=True)

    # Endpoint that generated the log (e.g., /logs/ingest)
    endpoint = Column(String(100), nullable=False)

    # HTTP method used (e.g., GET, POST)
    method = Column(String(10), nullable=False)

    # Response status code (e.g., 200, 404)
    status_code = Column(Integer, nullable=False)

    # Optional message or request body
    message = Column(Text, nullable=True)

    # Timestamp when the log was created (UTC)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)