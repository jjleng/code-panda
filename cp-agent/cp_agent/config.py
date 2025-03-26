"""Configuration settings module."""

import os
from typing import List, Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine environment
ENV = os.getenv("ENV", "development")


class Settings(BaseSettings):
    """Application settings.

    Pydantic Settings will load values from environment-specific .env files:
    - .env.development for development environment
    - .env.production for production environment

    Environment variables will take precedence over values in .env files.
    """

    # Project config
    PROJECT_NAME: str = "CodePanda Agent"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Runner config
    RUNNER_BASE_URL: str = "http://localhost:8088"

    # CORS config
    CORS_ORIGINS: List[str] = ["*"]

    # Project workspace config
    STARTER_PROJECT_REPO: str = ""
    WORKSPACE_PATH: str = "/workspace" if ENV == "production" else "workspace"

    # OpenRouter config
    DEFAULT_MODEL_API_KEY: str = ""

    # Fireworks config
    CODER_API_KEY: str = ""

    # Coder LLM config
    CODER_MODEL: str = ""
    CODER_LLM_URL: Optional[str] = None

    # Default LLM config
    DEFAULT_MODEL: str = ""
    DEFAULT_LLM_URL: Optional[str] = None

    # Knowledge Base config
    KB_MIN_RELEVANCE_SCORE: float = 0.1

    # ChromaDB config
    KB_CHROMA_CLIENT_TYPE: Literal["persistent", "http"] = "persistent"
    KB_CHROMA_DIRECTORY: str = "kb_db"  # Used for persistent client
    KB_CHROMA_HTTP_HOST: str = "localhost"
    KB_CHROMA_HTTP_PORT: int = 8000
    KB_CHROMA_HTTP_SSL: bool = False

    # Embeddings config
    EMBEDDING_VENDER: Optional[str] = None  # Only openai is supported so far
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: Optional[str] = None

    # Memory management config
    COMPACT_THRESHOLD_TOKENS: int = 30000  # Compact at 30k tokens
    COMPACT_TARGET_RATIO: float = 0.3  # Target amount of tokens to keep
    ENABLE_PROMPT_CACHE: bool = False  # Control whether to optimize for prompt caching

    # Logging config
    LOG_LEVEL: str = "debug"
    RELOAD: bool = True

    # Supabase Integration config (only needed when REQUIRE_AUTH is False)
    USER_SUPABASE_PAT: str = ""  # Personal Access Token
    LINKED_SUPABASE_PROJECT_ID: str = ""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=f".env.{ENV}",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        validate_default=True,
    )


# Create settings instance
settings = Settings()
