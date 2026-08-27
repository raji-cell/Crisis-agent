import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding

# Initialize local Qdrant storage & FastEmbed model
from pathlib import Path

STORAGE_PATH = str(Path.home() / ".crisis_agent" / "qdrant_storage")
client = QdrantClient(path=STORAGE_PATH)
embed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
COLLECTION_NAME = "crisis_protocols"

# Recreate collection with 384 dimensions (Cosine similarity)
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
)

SAMPLE_SOPS = [
    {
        "title": "Severe Fire & Structural Evacuation Protocol",
        "incident_type": "fire",
        "severity": 4,
        "directive": "1. Sound regional fire alarms. 2. Dispatch municipal fire units. 3. Cut HVAC & electrical mains. 4. Evacuate through designated exterior stairwells.",
        "search_text": "Fire outbreak, smoke detected, structural flames, building evacuation, fire alarm activation, burn hazards."
    },
    {
        "title": "Hazardous Material & Chemical Spill Protocol",
        "incident_type": "hazmat",
        "severity": 5,
        "directive": "1. Seal negative-pressure doors. 2. Deploy Hazmat Unit with Level-A PPE. 3. Enforce 100m perimeter. 4. Prohibit water contact with reactive chemicals.",
        "search_text": "Chemical spill, toxic vapor leak, acid drum rupture, hazardous materials, solvent gas, reactive chemical contamination."
    },
    {
        "title": "Active Threat & Armed Hostility Protocol",
        "incident_type": "active_threat",
        "severity": 5,
        "directive": "1. Initiate full facility lockdown. 2. Dispatch tactical law enforcement. 3. Broadcast Run-Hide-Fight directive to all personnel.",
        "search_text": "Active shooter, armed intruder, hostile threat, facility breach, physical violence, lockdown emergency."
    },
    {
        "title": "Medical Mass Casualty Protocol",
        "incident_type": "medical",
        "severity": 4,
        "directive": "1. Deploy on-site trauma response team. 2. Stage triage zone at building lobby. 3. Request multi-ambulance dispatch.",
        "search_text": "Mass casualty, severe medical emergency, multiple injuries, cardiac arrest, trauma response, unconscious personnel."
    }
]

# Generate true semantic embeddings for each protocol
texts_to_embed = [sop["search_text"] + " " + sop["directive"] for sop in SAMPLE_SOPS]
embeddings = list(embed_model.embed(texts_to_embed))

points = [
    models.PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding.tolist(),
        payload=sop
    )
    for sop, embedding in zip(SAMPLE_SOPS, embeddings)
]

client.upsert(collection_name=COLLECTION_NAME, points=points)
print(f"✅ FastEmbed complete: {len(points)} dynamic vector SOPs seeded into Qdrant.")
