import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
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
