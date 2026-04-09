from langchain_core.messages import HumanMessage, SystemMessage

from logic_graph.llm_factory import create_llm_for_node
from logic_graph.models import HallucinationGrade
from logic_graph.prompts import HALLUCINATION_SYSTEM_PROMPT
from logic_graph.state import GraphState


def hallucination_evaluator(state: GraphState) -> dict:
    # Auto-pass when agent responded without RAG — no documents to evaluate against
    if not state.get("retrieved_documents"):
        return {
            "hallucination_grade": HallucinationGrade(
                is_faithful=True,
                unfaithful_claims=[],
                reasoning="No se recuperaron documentos; no aplica evaluación de fidelidad.",
            )
        }

    llm = create_llm_for_node("hallucination_evaluator")
    structured_llm = llm.with_structured_output(HallucinationGrade, method="json_mode")

    documents_text = "\n\n---\n\n".join(
        doc["content"] for doc in state["retrieved_documents"]
    )

    system_prompt = HALLUCINATION_SYSTEM_PROMPT.format(
        retrieved_documents=documents_text,
        generated_response=state["generated_response"],
    )

    grade: HallucinationGrade = structured_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="Evalúa la fidelidad de la respuesta generada respecto a los documentos fuente."),
    ])

    result: dict = {"hallucination_grade": grade}

    # Provide feedback message so the agent can regenerate with context
    if not grade.is_faithful:
        claims = ", ".join(grade.unfaithful_claims) or "algunas afirmaciones"
        result["messages"] = [SystemMessage(
            content=(
                f"[EVALUACIÓN DE FIDELIDAD] Afirmaciones no respaldadas: {claims}. "
                "Regenera ciñéndote a las fuentes."
            )
        )]

    return result
