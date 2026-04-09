"""MCP RAG server — exposes the 3 ChromaDB collections via FastMCP."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from logic_graph.ingest.clients import (
    get_chroma_client,
    get_gemini_client,
    get_or_create_collection,
)
from logic_graph.ingest.search import search

mcp = FastMCP(
    name="logic-graph-rag",
    instructions=(
        "Servidor RAG para el asistente de bienestar psicológico. "
        "Proporciona acceso a guías clínicas, información sobre pseudociencia "
        "y técnicas de TCC para el contexto colombiano."
    ),
)


def _format_results(results: dict) -> str:
    """Format ChromaDB query results as numbered readable text."""
    documents = results.get("documents", [[]])[0]
    if not documents:
        return "No se encontraron documentos relevantes."
    parts = []
    for i, doc in enumerate(documents, 1):
        parts.append(f"[{i}] {doc}")
    return "\n\n".join(parts)


@mcp.tool()
def buscar_guias_clinicas(query: str, top_k: int = 5) -> str:
    """Busca información en guías clínicas y psicoeducación sobre depresión.

    Usa esta herramienta cuando se pregunte sobre síntomas, causas,
    tratamientos, medicamentos, diagnóstico o información clínica sobre depresión
    y otras condiciones de salud mental.
    """
    collection = get_or_create_collection(get_chroma_client(), "clinico")
    results = search(collection, get_gemini_client(), query, top_k)
    return _format_results(results)


@mcp.tool()
def buscar_ciencia_vs_pseudociencia(query: str, top_k: int = 5) -> str:
    """Busca información para contrastar mitos y pseudociencia sobre salud mental.

    Usa esta herramienta cuando se mencionen remedios no comprobados,
    creencias incorrectas, mitos populares o afirmaciones sin evidencia científica
    sobre depresión y salud mental.
    """
    collection = get_or_create_collection(get_chroma_client(), "pseudociencia")
    results = search(collection, get_gemini_client(), query, top_k)
    return _format_results(results)


@mcp.tool()
def buscar_tecnicas_tcc(query: str, top_k: int = 5) -> str:
    """Busca técnicas de Terapia Cognitivo-Conductual (TCC) y ejercicios prácticos.

    Usa esta herramienta cuando se pidan ejercicios, estrategias de
    afrontamiento, técnicas de manejo emocional o herramientas prácticas de TCC.
    """
    collection = get_or_create_collection(get_chroma_client(), "tecnicas_tcc")
    results = search(collection, get_gemini_client(), query, top_k)
    return _format_results(results)


def main() -> None:
    """Entry point for the MCP RAG server."""
    mcp.run()


if __name__ == "__main__":
    main()
