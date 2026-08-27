import os
from typing import List
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from fastembed import TextEmbedding
from openai import OpenAI
import httpx
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

# Initialize Local Vector Store & Embedding Engine


STORAGE_PATH = str(Path.home() / ".crisis_agent" / "qdrant_storage")
qdrant = QdrantClient(path=STORAGE_PATH)
embed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "mock-key"))
ENKRYPT_API_KEY = os.getenv("ENKRYPT_API_KEY", "")
ENKRYPT_API_URL = os.getenv("ENKRYPT_API_URL", "https://api.enkryptai.com")


# ==========================================
# 1. Structured Data Schemas
# ==========================================

class DispatchAction(BaseModel):
    order: int
    action: str
    assigned_unit: str = Field(description="fire_dept | hazmat_team | security | medical | facilities")
    urgency: str = Field(description="immediate | high | moderate")


class CrisisActionPlan(BaseModel):
    incident_id: str
    incident_type: str
    severity_level: int = Field(ge=1, le=5)
    summary: str
    affected_zones: List[str]
    immediate_actions: List[DispatchAction]
    evacuation_required: bool


# ==========================================
# 2. Enkrypt AI Guardrails Layer
# ==========================================

async def audit_input_with_enkrypt(raw_text: str) -> str:
    if not ENKRYPT_API_KEY or ENKRYPT_API_KEY == "your_enkrypt_key_here":
        return raw_text
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{ENKRYPT_API_URL}/v1/guardrails/input",
                headers={"Authorization": f"Bearer {ENKRYPT_API_KEY}", "Content-Type": "application/json"},
                json={"prompt": raw_text, "policy": "crisis-ops-strict"},
                timeout=5.0
            )
            data = res.json()
            if data.get("flagged", False):
                raise ValueError("Payload flagged by Enkrypt AI guardrails.")
            return data.get("sanitized_text", raw_text)
    except Exception:
        return raw_text


async def audit_output_with_enkrypt(plan: CrisisActionPlan) -> bool:
    if not ENKRYPT_API_KEY or ENKRYPT_API_KEY == "your_enkrypt_key_here":
        return True
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{ENKRYPT_API_URL}/v1/guardrails/output",
                headers={"Authorization": f"Bearer {ENKRYPT_API_KEY}", "Content-Type": "application/json"},
                json={"output": plan.model_dump_json(), "policy": "crisis-dispatch-verification"},
                timeout=5.0
            )
            return res.json().get("is_valid", True)
    except Exception:
        return True


# ==========================================
# 3. Dynamic Vector Retrieval Layer
# ==========================================

def retrieve_sops(incident_text: str) -> List[str]:
    """Dynamically embeds the incoming incident text and queries Qdrant for matching SOPs."""
    try:
        # Generate query vector on the fly using FastEmbed
        query_vector = list(embed_model.embed([incident_text]))[0].tolist()

        search_results = qdrant.search(
            collection_name="crisis_protocols",
            query_vector=query_vector,
            limit=2
        )
        return [f"{hit.payload['title']} (Score: {hit.score:.2f}): {hit.payload['directive']}" for hit in
                search_results]
    except Exception as e:
        return ["Default Safety Protocol: Secure perimeter and notify the on-duty crisis coordinator."]


# ==========================================
# 4. Agentic Crisis Triage Engine
# ==========================================

def run_crisis_triage_agent(incident_id: str, clean_text: str, location: str, sops: List[str]) -> CrisisActionPlan:
    sop_context = "\n".join([f"- {s}" for s in sops])

    system_prompt = f"""
    You are the Autonomous Crisis Operations Triage Agent.
    Evaluate the incident using these retrieved Standard Operating Procedures:
    {sop_context}
    """

    user_prompt = f"LOCATION: {location}\nINCIDENT: {clean_text}\nID: {incident_id}"

    try:
        response = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=CrisisActionPlan,
        )
        return response.choices[0].message.parsed
    except Exception:
        # Fallback triage logic
        incident_lower = clean_text.lower()
        if any(w in incident_lower for w in ["chem", "leak", "acid", "toxic", "vapor"]):
            inc_type, unit = "hazmat", "hazmat_team"
        elif any(w in incident_lower for w in ["fire", "smoke", "flame"]):
            inc_type, unit = "fire", "fire_dept"
        elif any(w in incident_lower for w in ["gun", "shooter", "intruder", "lockdown"]):
            inc_type, unit = "active_threat", "security"
        else:
            inc_type, unit = "medical", "medical"

        return CrisisActionPlan(
            incident_id=incident_id,
            incident_type=inc_type,
            severity_level=4,
            summary=f"Automated Plan: {clean_text}",
            affected_zones=[location],
            immediate_actions=[
                DispatchAction(order=1, action="Isolate zone and alert building occupants", assigned_unit="security",
                               urgency="immediate"),
                DispatchAction(order=2, action=f"Dispatch {unit} per retrieved SOP: {sops[0] if sops else 'General'}",
                               assigned_unit=unit, urgency="high")
            ],
            evacuation_required=True
        )
