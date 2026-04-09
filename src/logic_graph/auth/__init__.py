from __future__ import annotations

# PEP 562 lazy imports — defers backend/settings initialization until first access.
# This allows `import logic_graph.auth.models` (e.g. from alembic/env.py) without
# triggering Settings() validation, which requires LG_DATABASE_URL + LG_JWT_SECRET.

__all__ = ["fastapi_users", "auth_backend", "current_active_user", "User"]


def __getattr__(name: str):
    if name in ("fastapi_users", "auth_backend", "current_active_user"):
        from logic_graph.auth.backend import (
            auth_backend,
            current_active_user,
            fastapi_users,
        )
        return locals()[name]
    if name == "User":
        from logic_graph.auth.models import User
        return User
    raise AttributeError(f"module 'logic_graph.auth' has no attribute {name!r}")
