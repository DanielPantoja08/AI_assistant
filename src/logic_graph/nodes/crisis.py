from langchain_core.messages import HumanMessage, SystemMessage

from logic_graph.llm_factory import create_llm_for_node
from logic_graph.models import CrisisAssessment
from logic_graph.prompts import CRISIS_SYSTEM_PROMPT
from logic_graph.state import GraphState


def _format_recent_messages(messages: list, n: int = 5) -> str:
    recent = messages[-n:] if messages else []
    lines = []
    for msg in recent:
        role = getattr(msg, "type", "unknown")
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


def _format_assessment_block(last_assessment: dict | None) -> str:
    if not last_assessment:
        return ""
    score = last_assessment.get("phq9_score")
    severity = last_assessment.get("phq9_severity", "")
    asq = last_assessment.get("asq_result", "")
    return (
        f"Evaluación clínica completada hoy (antes de la conversación):\n"
        f"- PHQ-9: {score} puntos — severidad: {severity}\n"
        f"- ASQ: {asq}\n\n"
    )


def crisis_detector(state: GraphState) -> dict:
    llm = create_llm_for_node("crisis_detector")
    structured_llm = llm.with_structured_output(CrisisAssessment, method="json_mode")

    conversation_context = _format_recent_messages(state.get("messages", []))
    user_input = state["user_input"]
    assessment_block = _format_assessment_block(state.get("last_assessment"))

    human_content = (
        f"{assessment_block}"
        f"Historial reciente:\n{conversation_context}\n\n"
        f"Mensaje actual del usuario:\n{user_input}"
    )

    result = structured_llm.invoke([
        SystemMessage(content=CRISIS_SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ])

    return {"crisis_assessment": result}


