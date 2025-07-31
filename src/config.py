from collections.abc import Callable
from typing import Any

from pydantic import (
    AliasChoices,
    AmqpDsn,
    BaseModel,
    Field,
    ImportString,
    PostgresDsn,
    RedisDsn,
)

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    OPENAI_API_KEY=
QDRANT_URL=http://localhost:6333
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=1024
CHUNK_OVERLAP=20
GROQ_API_KEY=
ANTHROPIC_API_KEY=

    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    ANTHROPIC_API_KEY: str = Field(
        default="",
        description="Anthropic API key for accessing the Anthropic API.",
    )
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for accessing the OpenAI API.",
    )
    QDRANT_URL: str = Field(
        default="http://localhost:6333",
        description="Qdrant URL for vector database connection.",
    )
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="Model name for text embeddings.",
    )
    CHUNK_SIZE: int = Field(
        default=1024,
        description="Size of text chunks for processing.",
    )
    CHUNK_OVERLAP: int = Field(
        default=20,
        description="Overlap size between text chunks.",
    )
    GROQ_API_KEY: str = Field(
        default="",
        description="GROQ API key for accessing the GROQ API.",
    )
    
settings = Settings()