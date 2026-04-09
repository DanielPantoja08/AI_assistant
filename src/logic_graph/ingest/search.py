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


def lookup_emergencia(chroma_client: chromadb.PersistentClient, lookup_type: str | None = None) -> None:
    """Direct metadata lookup in emergencia collection (no vector search)."""
    collection = get_or_create_collection(chroma_client, "emergencia")
    kwargs: dict = {"where": {"type": lookup_type}} if lookup_type else {}
    results = collection.get(**kwargs)

    if not results["ids"]:
        print("No se encontraron recursos de emergencia.")
        return

    print(f"\n{'=' * 70}")
    print("Recursos de emergencia")
    if lookup_type:
        print(f"   Filtro: tipo = '{lookup_type}'")
    print(f"{'=' * 70}")

    for i, (entry_id, doc, meta) in enumerate(zip(
        results["ids"], results["documents"], results["metadatas"]
    )):
        name = meta.get("name") or doc
        phone = meta.get("phone", "")
        entry_type = meta.get("type", "")
        print(f"\n  [{i + 1}] {name}")
        if entry_type:
            print(f"      Tipo: {entry_type}")
        if phone:
            print(f"      Telefono/Contacto: {phone}")
        if meta.get("description"):
            print(f"      Descripcion: {meta['description']}")
