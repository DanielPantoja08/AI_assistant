"""
logic_graph.ingest — Multi-collection multimodal RAG pipeline.

Public API for use as a library:
    from logic_graph.ingest import search, get_gemini_client, embed_query
"""

from logic_graph.ingest.config import COLLECTIONS
from logic_graph.ingest.clients import get_gemini_client, get_chroma_client, get_or_create_collection
from logic_graph.ingest.embeddings import embed_texts, embed_query, normalize_embedding
from logic_graph.ingest.document import process_document
from logic_graph.ingest.indexing import index_to_collection, index_emergencia
from logic_graph.ingest.search import search, lookup_emergencia

__all__ = [
    "COLLECTIONS",
    "get_gemini_client",
    "get_chroma_client",
    "get_or_create_collection",
    "embed_texts",
    "embed_query",
    "normalize_embedding",
    "process_document",
    "index_to_collection",
    "index_emergencia",
    "search",
    "lookup_emergencia",
]
