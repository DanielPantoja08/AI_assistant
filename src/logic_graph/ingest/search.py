"""Vector similarity search and emergency resource lookup."""

import chromadb
from google import genai

from logic_graph.ingest.config import TOP_K
from logic_graph.ingest.clients import get_or_create_collection
from logic_graph.ingest.embeddings import embed_query, normalize_embedding


def search(
    collection: chromadb.Collection,
    gemini_client: genai.Client,
    query: str,
    top_k: int = TOP_K,
):
    """Busca los elementos mas similares (texto o imagen) a una consulta."""
    query_embedding = embed_query(gemini_client, query)
    query_embedding = normalize_embedding(query_embedding)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    return results


def lookup_emergencia(chroma_client: chromadb.PersistentClient, lookup_type: str | None = None) -> str:
    """Direct metadata lookup in emergencia collection (no vector search).

    Returns a formatted string with the matching emergency resources.
    """
    collection = get_or_create_collection(chroma_client, "emergencia")
    kwargs: dict = {"where": {"type": lookup_type}} if lookup_type else {}
    results = collection.get(**kwargs)

    if not results["ids"]:
        return "No se encontraron recursos de emergencia."

    parts: list[str] = []
    for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"]), 1):
        name = meta.get("name") or doc
        phone = meta.get("phone", "")
        entry_type = meta.get("type", "")
        description = meta.get("description", "")

        entry_parts = [f"[{i}] {name}"]
        if entry_type:
            entry_parts.append(f"    Tipo: {entry_type}")
        if phone:
            entry_parts.append(f"    Telefono/Contacto: {phone}")
        if description:
            entry_parts.append(f"    Descripcion: {description}")
        parts.append("\n".join(entry_parts))

    return "\n\n".join(parts)
