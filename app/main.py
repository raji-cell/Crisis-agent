from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uuid
import json
import os

from app.crisis_engine import (
    audit_input_with_enkrypt,
    retrieve_sops,
    run_crisis_triage_agent,
    audit_output_with_enkrypt
)
from app.dispatchers import dispatch_notifications
from app.database import record_incident_audit, SessionLocal, IncidentAuditLog

app = FastAPI(title="AI Crisis Operations Agent API")

class IncidentRequest(BaseModel):
    location: str
    message: str
    source: str = "sensor_alert"

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the live crisis operations console dashboard."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="dashboard.html template not found")
    return FileResponse(template_path)

@app.post("/api/v1/incidents/triage")
async def triage_incident(req: IncidentRequest):
    incident_id = str(uuid.uuid4())

    # Step 1: Input Guardrails via Enkrypt AI
    sanitized_text = await audit_input_with_enkrypt(req.message)

    # Step 2: Dynamic SOP Retrieval via Qdrant & FastEmbed
    sops = retrieve_sops(sanitized_text)

    # Step 3: Crisis Agent Reasoning
    action_plan = run_crisis_triage_agent(
        incident_id=incident_id,
        clean_text=sanitized_text,
        location=req.location,
        sops=sops
    )

    # Step 4: Output Guardrail Verification
    is_valid = await audit_output_with_enkrypt(action_plan)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Action plan suppressed by Enkrypt safety guardrails.")

    # Step 5: Live Dispatch & Notification Routing
    dispatch_results = await dispatch_notifications(action_plan, req.location)

    # Step 6: Immutable Audit Record Persistence (SQLite)
    record_incident_audit(
        incident_id=incident_id,
        location=req.location,
        raw_message=req.message,
        sanitized_message=sanitized_text,
        action_plan=action_plan.model_dump(),
        dispatch_status=dispatch_results
    )

    return {
        "status": "TRIAGED_AND_DISPATCHED",
        "incident_id": incident_id,
        "action_plan": action_plan,
        "dispatch_status": dispatch_results
    }

@app.get("/api/v1/incidents/history")
def get_incident_history(limit: int = 15):
    """Fetches recent incident audit records."""
    db = SessionLocal()
    try:
        logs = db.query(IncidentAuditLog).order_by(IncidentAuditLog.timestamp.desc()).limit(limit).all()
        return [
            {
                "incident_id": log.incident_id,
                "timestamp": log.timestamp.isoformat(),
                "location": log.location,
                "type": log.incident_type,
                "severity": log.severity_level,
                "evacuation_required": log.evacuation_required,
                "action_plan": json.loads(log.action_plan_json),
                "dispatch_status": json.loads(log.dispatch_status_json)
            }
            for log in logs
        ]
    finally:
        db.close()

@app.get("/healthz")
def health():
    return {"status": "healthy"}