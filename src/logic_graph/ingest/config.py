"""Configuration constants and collection registry."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Models ──
EMBEDDING_MODEL = "gemini-embedding-2-preview"
CAPTIONING_MODEL = "gemini-2.5-flash"

# ── Search ──
TOP_K = 5

# ── Embeddings ──
OUTPUT_DIMENSIONALITY = 768

# ── Document processing ──
IMAGE_RESOLUTION_SCALE = 2.0
OUTPUT_DIR = Path("extracted_images")
TABLES_DIR = Path("extracted_tables")

# ── Collection registry ──
COLLECTIONS = {
    "clinico": {
        "description": "Psicoeducacion + diagnostico (vectorial)",
        "vectorial": True,
        "metadata_schema": ["source", "category", "chapter"],
    },
    "pseudociencia": {
        "description": "Desmitificacion (vectorial)",
        "vectorial": True,
        "metadata_schema": ["source", "category", "debunk_type"],
    },
    "tecnicas_tcc": {
        "description": "Intervenciones practicas (vectorial)",
        "vectorial": True,
        "metadata_schema": ["source", "category", "technique"],
    },
    "emergencia": {
        "description": "Lookup directo, NO vectorial",
        "vectorial": False,
        "metadata_schema": ["type", "name", "phone"],
    },
}

# ── Caption prompt ──
CAPTION_PROMPT = (
    "You are analyzing a figure extracted from a scientific/technical PDF document. "
    "Describe this image in detail: what it shows, any labels, axes, relationships, "
    "or architecture depicted. Be specific and concise (2-4 sentences). "
    "Focus on the technical content that would help someone find this image "
    "through a text search."
    "Write the caption in Spanish."
)
