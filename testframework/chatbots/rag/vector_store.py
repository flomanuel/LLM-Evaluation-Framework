"""Vector store module using PostgreSQL with pgvector for RAG."""

from __future__ import annotations

import os
from typing import List
from urllib.parse import urlsplit

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from loguru import logger


class VectorStore:
    """Wrapper around PGVector for document storage and retrieval."""

    # small: save costs, and since we only have a small dataset, this should be enough.
    EMBEDDING_MODEL = "text-embedding-3-small"
    COLLECTION_NAME = "rag_documents"

    def __init__(
            self,
            connection_string: str | None = None,
            collection_name: str | None = None,
    ) -> None:
        """Initialize the vector store.

        Args:
            connection_string: PostgreSQL connection string. If None, builds from env vars.
            collection_name: Name of the collection to use. Defaults to COLLECTION_NAME.
        """
        self._connection_string = connection_string or self._build_connection_string()
        self._collection_name = collection_name or self.COLLECTION_NAME

        self._embeddings = OpenAIEmbeddings(
            model=self.EMBEDDING_MODEL,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        self._vector_store = PGVector(
            embeddings=self._embeddings,
            collection_name=self._collection_name,
            connection=self._connection_string,
            use_jsonb=True,
        )

        logger.info(
            f"Initialized vector store (collection={self._collection_name}, "
            f"target={self._connection_target()})"
        )
        logger.debug(
            f"VectorStore initialized with collection '{self._collection_name}' "
            f"using embedding model '{self.EMBEDDING_MODEL}'"
        )

    @staticmethod
    def _build_connection_string() -> str:
        """Build PostgreSQL connection string from environment variables."""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        db = os.getenv("POSTGRES_DB", "vectordb")
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store.

        Args:
            documents: List of LangChain Document objects to add.

        Returns:
            List of document IDs.
        """
        logger.info(
            f"Adding {len(documents)} document chunk(s) to collection '{self._collection_name}'"
        )
        ids = self._vector_store.add_documents(documents)
        logger.info(
            f"Added {len(documents)} document chunk(s) to collection '{self._collection_name}'"
        )
        return ids

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Search for similar documents.

        Args:
            query: The query text to search for.
            k: Number of documents to return.

        Returns:
            List of similar Document objects.
        """
        results = self._vector_store.similarity_search(query, k=k)
        logger.debug(f"Found {len(results)} similar documents for query")
        return results

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """Get the embeddings model."""
        return self._embeddings

    @property
    def embedding_model_name(self) -> str:
        """Get the name of the embedding model."""
        return self.EMBEDDING_MODEL

    def _connection_target(self) -> str:
        """Return a sanitized host/port/database summary for logging."""
        parsed = urlsplit(self._connection_string)
        host = parsed.hostname or "unknown-host"
        port = parsed.port or 5432
        database = parsed.path.lstrip("/") or "unknown-db"
        return f"{host}:{port}/{database}"
