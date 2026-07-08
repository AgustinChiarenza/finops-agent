"""Application settings for the FinOps Agent.

All values are environment-driven (``.env`` friendly) so the same image can be
reconfigured per tenant without rebuilds. The dashboard connection, MaaS
credentials, embedding provider, RAG store, and orchestrator defaults all live
here.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Cloud Ops Dashboard API (live FinOps data source) ---
    dashboard_api_base: str = "http://dashboard-backend:8000"
    dashboard_timeout_seconds: float = 30.0

    # --- MaaS (Huawei ModelArts Studio, OpenAI-compatible) ---
    maas_api_key: str = ""
    maas_base_url: str = "https://api-ap-southeast-1.modelarts-maas.com/openai/v1"

    # --- Embeddings (RAG) ---
    embed_provider: str = "ollama"  # "ollama" | "maas"
    ollama_host: str = "http://ollama:11434"
    embed_model: str = "nomic-embed-text"

    # --- RAG / vector store ---
    chroma_dir: str = "agent/data/chroma_db"
    chroma_collection: str = "finops_knowledge"
    knowledge_dir: str = "agent/knowledge"
    rag_top_k: int = 6

    # --- LiteLLM orchestrator ---
    default_tier: str = "standard"  # cheap | standard | powerful
    orchestrator_timeout_seconds: float = 180.0
    max_tokens: int = 4096
    temperature: float = 0.2

    # --- Application ---
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8082"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def maas_enabled(self) -> bool:
        return bool(self.maas_api_key.strip())


settings = Settings()
