from __future__ import annotations

import chromadb
from google import genai

from logic_graph.config import settings
from logic_graph.ingest.config import COLLECTIONS

_chroma_client: chromadb.PersistentClient | None = None
_gemini_client: genai.Client | None = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
    return _chroma_client


def get_gemini_client() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.google_api_key)
    return _gemini_client


def get_or_create_collection(
    chroma_client: chromadb.PersistentClient, name: str
) -> chromadb.Collection:
    if name not in COLLECTIONS:
        raise ValueError(f"Colección desconocida '{name}'. Válidas: {list(COLLECTIONS)}")
    config = COLLECTIONS[name]
    if config.get("vectorial"):
        return chroma_client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )
    return chroma_client.get_or_create_collection(name=name)
