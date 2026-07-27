# PaperMind AI — Core Configuration
# =============================================================================
# This module loads, validates, and exposes all application settings.
# Uses Pydantic BaseSettings for type-safe, environment-driven configuration.
# =============================================================================

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root
BASE_DIR = Path(__file__).resolve().parents[3]


class AppSettings(BaseSettings):
    """Core application settings."""

    name: str = Field(default="PaperMind AI", alias="APP_NAME")
    version: str = Field(default="0.1.0", alias="APP_VERSION")
    env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    host: str = Field(default="0.0.0.0", alias="APP_HOST")
    port: int = Field(default=8000, alias="APP_PORT")
    workers: int = Field(default=4, alias="APP_WORKERS")
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    provider: Literal["groq", "openai", "anthropic", "google", "together", "azure", "ollama"] = Field(
        default="groq", alias="LLM_PROVIDER"
    )

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434/v1", alias="OLLAMA_BASE_URL")
    ollama_default_model: str = Field(default="qwen2.5:3b", alias="OLLAMA_DEFAULT_MODEL")

    # Groq
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_default_model: str = Field(
        default="llama-3.3-70b-versatile", alias="GROQ_DEFAULT_MODEL"
    )
    groq_vision_model: str = Field(
        default="llama-3.2-90b-vision-preview", alias="GROQ_VISION_MODEL"
    )

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_default_model: str = Field(default="gpt-4o", alias="OPENAI_DEFAULT_MODEL")

    # Anthropic
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_default_model: str = Field(
        default="claude-3-5-sonnet-20241022", alias="ANTHROPIC_DEFAULT_MODEL"
    )

    # Google
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    google_default_model: str = Field(
        default="gemini-2.0-flash-exp", alias="GOOGLE_DEFAULT_MODEL"
    )

    # Together AI
    together_api_key: str = Field(default="", alias="TOGETHER_API_KEY")
    together_default_model: str = Field(
        default="meta-llama/Llama-3-70b-chat-hf", alias="TOGETHER_DEFAULT_MODEL"
    )

    # Azure OpenAI
    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: str = Field(default="gpt-4o", alias="AZURE_OPENAI_DEPLOYMENT")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class EmbeddingSettings(BaseSettings):
    """Embedding model configuration."""

    provider: Literal["sentence_transformers", "fastembed", "openai", "cohere"] = Field(
        default="fastembed", alias="EMBEDDING_PROVIDER"
    )
    model: str = Field(default="BAAI/bge-small-en-v1.5", alias="EMBEDDING_MODEL")
    dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")
    batch_size: int = Field(default=32, alias="EMBEDDING_BATCH_SIZE")
    device: Literal["cpu", "cuda", "mps"] = Field(default="cpu", alias="EMBEDDING_DEVICE")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class VectorStoreSettings(BaseSettings):
    """Qdrant vector database configuration."""

    host: str = Field(default="localhost", alias="QDRANT_HOST")
    port: int = Field(default=6333, alias="QDRANT_PORT")
    grpc_port: int = Field(default=6334, alias="QDRANT_GRPC_PORT")
    api_key: str = Field(default="", alias="QDRANT_API_KEY")
    collection_name: str = Field(default="papermind_docs", alias="QDRANT_COLLECTION_NAME")
    use_grpc: bool = Field(default=False, alias="QDRANT_USE_GRPC")

    hybrid_alpha: float = Field(default=0.5, alias="HYBRID_ALPHA")
    top_k_retrieval: int = Field(default=10, alias="TOP_K_RETRIEVAL")
    top_k_rerank: int = Field(default=5, alias="TOP_K_RERANK")
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2", alias="RERANKER_MODEL"
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class OCRSettings(BaseSettings):
    """OCR engine configuration."""

    engine: Literal["paddleocr", "tesseract", "auto"] = Field(
        default="paddleocr", alias="OCR_ENGINE"
    )
    lang: str = Field(default="en", alias="OCR_LANG")
    use_gpu: bool = Field(default=False, alias="OCR_USE_GPU")
    tesseract_cmd: str = Field(default="tesseract", alias="TESSERACT_CMD")
    confidence_threshold: float = Field(default=0.7, alias="OCR_CONFIDENCE_THRESHOLD")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class StorageSettings(BaseSettings):
    """File storage configuration."""

    max_file_size_mb: int = Field(default=100, alias="MAX_FILE_SIZE_MB")
    upload_dir: Path = Field(default=BASE_DIR / "data" / "uploads", alias="UPLOAD_DIR")
    processed_dir: Path = Field(default=BASE_DIR / "data" / "processed", alias="PROCESSED_DIR")
    cache_dir: Path = Field(default=BASE_DIR / "data" / "cache", alias="CACHE_DIR")
    exports_dir: Path = Field(default=BASE_DIR / "data" / "exports", alias="EXPORTS_DIR")

    @field_validator("upload_dir", "processed_dir", "cache_dir", "exports_dir", mode="before")
    @classmethod
    def ensure_dirs_exist(cls, v: str | Path) -> Path:
        p = Path(v)
        p.mkdir(parents=True, exist_ok=True)
        return p

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class PipelineSettings(BaseSettings):
    """Document processing pipeline configuration."""

    workers: int = Field(default=2, alias="PIPELINE_WORKERS")
    timeout: int = Field(default=300, alias="PIPELINE_TIMEOUT")
    chunk_overlap: int = Field(default=50, alias="CHUNK_OVERLAP")
    min_chunk_size: int = Field(default=100, alias="MIN_CHUNK_SIZE")
    max_chunk_size: int = Field(default=2000, alias="MAX_CHUNK_SIZE")
    layout_model: str = Field(default="auto", alias="LAYOUT_MODEL")
    layout_confidence_threshold: float = Field(
        default=0.7, alias="LAYOUT_CONFIDENCE_THRESHOLD"
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )
    format: Literal["json", "text"] = Field(default="json", alias="LOG_FORMAT")
    file: str = Field(default="logs/papermind.log", alias="LOG_FILE")
    rotation: str = Field(default="10 MB", alias="LOG_ROTATION")
    retention: str = Field(default="30 days", alias="LOG_RETENTION")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class CacheSettings(BaseSettings):
    """Cache configuration."""

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_ttl: int = Field(default=3600, alias="REDIS_TTL")
    use_redis: bool = Field(default=False, alias="USE_REDIS")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class SecuritySettings(BaseSettings):
    """API security configuration."""

    api_key_header: str = Field(default="X-API-Key", alias="API_KEY_HEADER")
    allowed_origins: list[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        alias="ALLOWED_ORIGINS",
    )
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class GraphSettings(BaseSettings):
    """Knowledge graph configuration."""

    use_neo4j: bool = Field(default=False, alias="USE_NEO4J")
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="papermind", alias="NEO4J_DATABASE")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


class Settings:
    """
    Aggregate settings container.
    Access via: get_settings().llm.groq_api_key
    """

    def __init__(self) -> None:
        self.app = AppSettings()
        self.llm = LLMSettings()
        self.embedding = EmbeddingSettings()
        self.vector_store = VectorStoreSettings()
        self.ocr = OCRSettings()
        self.storage = StorageSettings()
        self.pipeline = PipelineSettings()
        self.logging = LoggingSettings()
        self.cache = CacheSettings()
        self.security = SecuritySettings()
        self.graph = GraphSettings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached singleton Settings instance.
    Use this everywhere via FastAPI dependency injection:

        settings: Settings = Depends(get_settings)
    """
    return Settings()
