from sqlalchemy import Column, Integer, String, Text, DateTime, Float
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

    # Optional message or request body (may be Fernet-encrypted if DB_ENCRYPTION_ENABLED=true)
    message = Column(Text, nullable=True)

    # Timestamp when the log was created (UTC)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Structured event classification (e.g. "ai_query", "ai_query_blocked", "dlp_alert")
    event_type = Column(String(50), nullable=True, index=True)

    frameworks = Column(String, nullable=True)  # or Column(ARRAY(String))

    decision = Column(String, nullable=True)

    # Coarse severity level derived from risk_score: "low", "medium", "high"
    severity = Column(String(20), nullable=True, index=True)

    # Continuous risk score in [0.0, 1.0] produced by the DLP engine
    risk_score = Column(Float, nullable=True)

    # Component that generated the log entry (e.g. "ai_route", "dlp_middleware")
    source = Column(String(100), nullable=True)

    # DLP policy outcome: "allow", "redact", or "block"
    policy_decision = Column(String(20), nullable=True, index=True)
