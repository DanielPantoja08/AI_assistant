from __future__ import annotations

from typing import Any

# Module-level singletons set during lifespan startup.
_checkpointer: Any = None
_store: Any = None
_graph: Any = None


def get_checkpointer():
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized — is the lifespan running?")
    return _checkpointer


def get_store():
    if _store is None:
        raise RuntimeError("Store not initialized — is the lifespan running?")
    return _store


def get_graph():
    if _graph is None:
        raise RuntimeError("Graph not initialized — is the lifespan running?")
    return _graph
