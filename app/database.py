import json
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./crisis_audit.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class IncidentAuditLog(Base):
    __tablename__ = "incident_audit_logs"

    incident_id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    location = Column(String, nullable=False)
    raw_message = Column(Text, nullable=False)
    sanitized_message = Column(Text, nullable=False)
    incident_type = Column(String, nullable=False)
    severity_level = Column(Integer, nullable=False)
    evacuation_required = Column(Boolean, default=False)
    action_plan_json = Column(Text, nullable=False)
    dispatch_status_json = Column(Text, nullable=False)

# Auto-create tables on import
Base.metadata.create_all(bind=engine)

def record_incident_audit(
    incident_id: str,
    location: str,
    raw_message: str,
    sanitized_message: str,
    action_plan: dict,
    dispatch_status: dict
):
    """Persists a complete incident audit entry into SQLite."""
    db = SessionLocal()
    try:
        log_entry = IncidentAuditLog(
            incident_id=incident_id,
            location=location,
            raw_message=raw_message,
            sanitized_message=sanitized_message,
            incident_type=action_plan.get("incident_type", "unknown"),
            severity_level=action_plan.get("severity_level", 1),
            evacuation_required=action_plan.get("evacuation_required", False),
            action_plan_json=json.dumps(action_plan),
            dispatch_status_json=json.dumps(dispatch_status)
        )
        db.add(log_entry)
        db.commit()
    finally:
        db.close()
