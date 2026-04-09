"""Embedding generation and normalization using Gemini."""

import numpy as np
from google import genai
from google.genai import types

from logic_graph.ingest.config import EMBEDDING_MODEL, OUTPUT_DIMENSIONALITY


def embed_texts(client: genai.Client, texts: list[str]) -> list[list[float]]:
    """Genera embeddings para una lista de textos (documentos)."""
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=OUTPUT_DIMENSIONALITY,
        ),
    )
    return [e.values for e in result.embeddings]


def embed_query(client: genai.Client, query: str) -> list[float]:
    """Genera embedding para una consulta de texto."""
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query],
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=OUTPUT_DIMENSIONALITY,
        ),
    )
    return result.embeddings[0].values


def normalize_embedding(embedding: list[float]) -> list[float]:
    """Normaliza un embedding (recomendado para dimensiones < 3072)."""
    arr = np.array(embedding, dtype=np.float64)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr.tolist()
