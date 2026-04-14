import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from logic_graph.api.deps import get_graph, get_store
from logic_graph.auth import User, current_active_user
from logic_graph.nodes.memory import session_finalizer

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class EndSessionRequest(BaseModel):
    session_id: str


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(current_active_user),
    graph=Depends(get_graph),
) -> ChatResponse:
    user_id = str(user.id)
    session_id = request.session_id or str(uuid.uuid4())
    thread_id = f"{user_id}_{session_id}"

    initial_state = {
        "user_input": request.message,
        "messages": [HumanMessage(content=request.message)],
        "user_id": user_id,
    }
    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(initial_state, config)
    response_text = result.get("generated_response", "")

    return ChatResponse(response=response_text, session_id=session_id)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user: User = Depends(current_active_user),
    graph=Depends(get_graph),
):
    user_id = str(user.id)
    session_id = request.session_id or str(uuid.uuid4())
    thread_id = f"{user_id}_{session_id}"

    initial_state = {
        "user_input": request.message,
        "messages": [HumanMessage(content=request.message)],
        "user_id": user_id,
    }
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator():
        emergency_text: str | None = None
        gen = graph.astream_events(initial_state, config, version="v2")
        pending: asyncio.Task | None = None

        try:
            while True:
                if pending is None:
                    pending = asyncio.ensure_future(gen.__anext__())

                done, _ = await asyncio.wait({pending}, timeout=20.0)

                if not done:
                    # No token yet — send keepalive comment to prevent nginx/browser timeout
                    yield ": keepalive\n\n"
                    continue

                pending = None
                try:
                    event = done.pop().result()
                except StopAsyncIteration:
                    break
                except Exception:
                    break

                if event["event"] == "on_chat_model_stream":
                    chunk_content = event["data"]["chunk"].content
                    if chunk_content:
                        yield f"data: {chunk_content}\n\n"
                elif event["event"] == "on_chain_end" and event.get("name") == "emergency_responder":
                    output = event["data"].get("output", {})
                    emergency_text = output.get("emergency_text", "")
        finally:
            if pending and not pending.done():
                pending.cancel()

        if emergency_text:
            yield "data: \n\n"
            yield "data: \n\n"
            for line in emergency_text.split("\n"):
                yield f"data: {line}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "X-Session-Id": session_id,
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history")
async def chat_history(
    session_id: str,
    user: User = Depends(current_active_user),
    graph=Depends(get_graph),
) -> dict:
    user_id = str(user.id)
    thread_id = f"{user_id}_{session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    state = await graph.aget_state(config)
    if not state or not state.values:
        return {"messages": []}

    messages = []
    for msg in state.values.get("messages", []):
        if isinstance(msg, HumanMessage):
            messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages.append({"role": "assistant", "content": msg.content})

    return {"messages": messages}


@router.post("/end-session")
async def end_session(
    request: EndSessionRequest,
    user: User = Depends(current_active_user),
    graph=Depends(get_graph),
    store=Depends(get_store),
) -> dict:
    user_id = str(user.id)
    thread_id = f"{user_id}_{request.session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    state = await graph.aget_state(config)
    if state and state.values:
        await session_finalizer(state.values, store=store)

    return {"status": "ok", "session_id": request.session_id}
