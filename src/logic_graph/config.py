from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LG_", env_file=".env", extra="ignore")

    # API keys
    google_api_key: str = ""
    groq_api_key: str = ""

    # agent (reasoning agent with tool calling — uses Ollama gemma4:e4b)
    agent_provider: str = "ollama"
    agent_model: str = "gemma4:e4b"

    # crisis_detector
    crisis_detector_provider: str = "groq"
    crisis_detector_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # hallucination_evaluator
    hallucination_evaluator_provider: str = "groq"
    hallucination_evaluator_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # memory_summarizer
    memory_summarizer_provider: str = "groq"
    memory_summarizer_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # crisis_agent
    crisis_agent_provider: str = "groq"
    crisis_agent_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # database
    database_url: str

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if "+asyncpg" not in v:
            raise ValueError(
                "database_url must use the asyncpg driver (e.g., postgresql+asyncpg://...)"
            )
        return v

    @computed_field
    @property
    def database_url_psycopg(self) -> str:
        # AsyncPostgresSaver/AsyncPostgresStore need a native psycopg3 URI:
        # postgresql://... (not the SQLAlchemy postgresql+psycopg:// form)
        return self.database_url.replace("+asyncpg", "", 1)

    @computed_field
    @property
    def database_url_alembic(self) -> str:
        # Alembic async migrations need the psycopg v3 SQLAlchemy driver:
        # postgresql+psycopg://... (NOT psycopg2 which is the default for plain postgresql://)
        return self.database_url.replace("+asyncpg", "+psycopg", 1)

    # JWT
    jwt_secret: str
    jwt_lifetime_seconds: int = 3600

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ChromaDB
    chroma_db_path: str = "./chroma_db"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    def get_node_config(self, node_name: str) -> tuple[str, str]:
        """Return (provider, model) for the given node name."""
        provider = getattr(self, f"{node_name}_provider")
        model = getattr(self, f"{node_name}_model")
        return provider, model


settings = Settings()
