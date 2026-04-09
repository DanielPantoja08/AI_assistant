import asyncio
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore

from logic_graph.api import deps
from logic_graph.api.routers import auth, chat, ingest
from logic_graph.app import build_graph
from logic_graph.config import settings


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


def run() -> None:
    import selectors

    config = uvicorn.Config(
        "logic_graph.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
    server = uvicorn.Server(config)

    # psycopg async requires SelectorEventLoop; Windows defaults to ProactorEventLoop.
    # loop_factory forces SelectorEventLoop regardless of the platform policy.
    asyncio.run(
        server.serve(),
        loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
    )
