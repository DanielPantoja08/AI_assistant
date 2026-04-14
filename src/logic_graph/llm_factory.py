from __future__ import annotations

from langchain_core.language_models import BaseChatModel


def create_llm(provider: str, model: str, **kwargs) -> BaseChatModel:
    """Instantiate a chat model for the given provider and model name."""
    from logic_graph.config import settings as _settings

    match provider:
        case "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=model, google_api_key=_settings.google_api_key, **kwargs
            )
        case "groq":
            from langchain_groq import ChatGroq
            return ChatGroq(
                model=model, api_key=_settings.groq_api_key, **kwargs
            )
        case "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(model=model, base_url=_settings.ollama_base_url, **kwargs)
        case _:
            raise ValueError(f"Unsupported provider: {provider}")


def create_llm_for_node(
    node_name: str,
    settings: Settings | None = None,
    **kwargs,
) -> BaseChatModel:
    """Return a chat model configured for the given graph node.

    Loads provider and model from *settings* (or a fresh Settings instance
    when *settings* is None) and delegates to :func:`create_llm`.
    """
    from logic_graph.config import Settings as _Settings

    if settings is None:
        settings = _Settings()

    provider, model = settings.get_node_config(node_name)
    return create_llm(provider, model, **kwargs)
