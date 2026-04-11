from __future__ import annotations

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.postgres import AsyncPostgresStore

# Module-level singletons set during lifespan startup.
_checkpointer: AsyncPostgresSaver | None = None
_store: AsyncPostgresStore | None = None
_graph: CompiledStateGraph | None = None


def get_checkpointer() -> AsyncPostgresSaver:
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized — is the lifespan running?")
    return _checkpointer


def get_store() -> AsyncPostgresStore:
    if _store is None:
        raise RuntimeError("Store not initialized — is the lifespan running?")
    return _store


def get_graph() -> CompiledStateGraph:
    if _graph is None:
        raise RuntimeError("Graph not initialized — is the lifespan running?")
    return _graph
