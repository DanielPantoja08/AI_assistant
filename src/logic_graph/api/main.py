import asyncio
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore

from logic_graph.api import deps
from logic_graph.api.routers import assessments, auth, chat, ingest
from logic_graph.app import build_graph
from logic_graph.config import settings


async def _warmup_ollama() -> None:
    """Send a minimal request to Ollama so the model is loaded before the first user message."""
    try:
        from logic_graph.llm_factory import create_llm_for_node
        llm = create_llm_for_node("agent")
        await llm.ainvoke("hola")
    except Exception:
        pass  # warmup failure is non-fatal


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(
        settings.database_url_psycopg
    ) as checkpointer:
        await checkpointer.setup()
        async with AsyncPostgresStore.from_conn_string(
            settings.database_url_psycopg
        ) as store:
            await store.setup()
            deps._checkpointer = checkpointer
            deps._store = store
            deps._graph = build_graph(checkpointer=checkpointer, store=store)
            asyncio.create_task(_warmup_ollama())  # fire-and-forget, non-blocking
            yield


app = FastAPI(title="Logic Graph API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(assessments.router)


def run() -> None:
    import selectors

    config = uvicorn.Config(
        "logic_graph.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
    server = uvicorn.Server(config)

    # psycopg async requires SelectorEventLoop; Windows defaults to ProactorEventLoop.
    # loop_factory forces SelectorEventLoop regardless of the platform policy.
    asyncio.run(
        server.serve(),
        loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
    )
