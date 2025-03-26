from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional, cast

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.types import Documents, EmbeddingFunction
from chromadb.api.types import Metadata as ChromaMetadata
from chromadb.api.types import QueryResult
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from chromadb.utils.embedding_functions.openai_embedding_function import (
    OpenAIEmbeddingFunction,
)
from loguru import logger

from cp_agent.config import settings


@dataclass
class Document:
    """Represents a document with its content and metadata."""

    content: str
    metadata: dict[str, Any]


class VectorStore(ABC):
    """Abstract base class for vector database operations."""

    @abstractmethod
    def add_documents(
        self, documents: list[Document], ids: Optional[list[str]] = None
    ) -> None:
        """Add documents to the vector store.

        Args:
            documents: List of Document objects to add
            ids: Optional list of IDs for the documents
        """
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[tuple[Document, float]]:
        """Search for similar documents.

        Args:
            query: Query string
            top_k: Number of results to return

        Returns:
            List of tuples containing Documents and their similarity scores
        """
        pass

    @abstractmethod
    def update_document(self, doc_id: str, document: Document) -> None:
        """Update a document in the store.

        Args:
            doc_id: ID of document to update
            document: New document content and metadata
        """
        pass

    @abstractmethod
    def delete_documents(self, ids: list[str]) -> None:
        """Delete documents from the store.

        Args:
            ids: List of document IDs to delete
        """
        pass

    @abstractmethod
    def get_documents(self, ids: Optional[list[str]] = None) -> list[Document]:
        """Get documents from the store.

        Args:
            ids: Optional list of document IDs to retrieve. If None, gets all documents.

        Returns:
            List of retrieved documents
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """Get the number of documents in the store.

        Returns:
            Number of documents
        """
        pass

    @abstractmethod
    def list_collections(self) -> list[str]:
        """List all available collections.

        Returns:
            List of collection names
        """
        pass

    @abstractmethod
    def nuke(self) -> None:
        """Delete the entire collection and its contents.

        This is a destructive operation that removes all documents and the collection itself.
        """
        pass


class ChromaStore(VectorStore):
    """ChromaDB implementation of VectorStore."""

    def __init__(self, collection_name: str):
        """Initialize ChromaDB store.

        Args:
            collection_name: Name of the collection to use
        """
        self.collection_name = collection_name
        self.client = self._initialize_client()

        ef: EmbeddingFunction[Documents] | None = None

        if (
            settings.EMBEDDING_VENDER
            and settings.EMBEDDING_MODEL
            and settings.EMBEDDING_API_KEY
            and settings.EMBEDDING_VENDER == "openai"
        ):
            ef = OpenAIEmbeddingFunction(
                api_key=settings.EMBEDDING_API_KEY, model_name=settings.EMBEDDING_MODEL
            )
            logger.info("Using OpenAI embedding function")
        else:
            ef = embedding_functions.DefaultEmbeddingFunction()
            logger.info("Using default embedding function")

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=ef,  # type: ignore
        )

    def _initialize_client(self) -> ClientAPI:
        """Initialize ChromaDB client based on configuration.

        Returns:
            ChromaDB client instance
        """

        if settings.KB_CHROMA_CLIENT_TYPE == "http":
            chroma_settings = Settings(
                anonymized_telemetry=False,
            )
            return chromadb.HttpClient(
                host=settings.KB_CHROMA_HTTP_HOST,
                port=settings.KB_CHROMA_HTTP_PORT,
                ssl=settings.KB_CHROMA_HTTP_SSL,
                settings=chroma_settings,
            )
        else:  # "persistent"
            chroma_settings = Settings(
                anonymized_telemetry=False,
            )
            persist_dir = Path(settings.KB_CHROMA_DIRECTORY)
            persist_dir.mkdir(parents=True, exist_ok=True)
            return chromadb.PersistentClient(
                path=str(persist_dir),
                settings=chroma_settings,
            )

    def add_documents(
        self, documents: list[Document], ids: Optional[list[str]] = None
    ) -> None:
        """Add documents to ChromaDB collection."""
        if not documents:
            return

        if ids is None:
            ids = [str(i) for i in range(len(documents))]

        # Prepare data for ChromaDB
        docs = [doc.content for doc in documents]
        # Convert metadata to compatible format
        metadatas: list[ChromaMetadata] = [
            {str(k): str(v) for k, v in doc.metadata.items()} for doc in documents
        ]

        # Add to collection
        self.collection.add(documents=docs, metadatas=metadatas, ids=ids)

    def search(self, query: str, top_k: int = 5) -> list[tuple[Document, float]]:
        """Search ChromaDB collection."""
        results: QueryResult = self.collection.query(
            query_texts=[query], n_results=top_k
        )

        documents_with_scores: list[tuple[Document, float]] = []
        if not results or "ids" not in results or not results["ids"]:
            return documents_with_scores

        for i in range(len(results["ids"][0])):
            doc = Document(
                content=str(results["documents"][0][i]) if results["documents"] else "",
                metadata=cast(
                    dict[str, Any],
                    results["metadatas"][0][i] if results["metadatas"] else {},
                ),
            )
            # Convert distance to similarity score (1 - distance for cosine)
            score = 1.0 - float(
                results["distances"][0][i] if results["distances"] else 1.0
            )
            documents_with_scores.append((doc, score))

        return documents_with_scores

    def update_document(self, doc_id: str, document: Document) -> None:
        """Update a document in ChromaDB collection."""
        metadata = {str(k): str(v) for k, v in document.metadata.items()}
        self.collection.update(
            ids=[doc_id], documents=[document.content], metadatas=[metadata]
        )

    def delete_documents(self, ids: list[str]) -> None:
        """Delete documents from ChromaDB collection."""
        self.collection.delete(ids=ids)

    def get_documents(self, ids: Optional[list[str]] = None) -> list[Document]:
        """Get documents from ChromaDB collection."""
        results = self.collection.get(ids=ids) if ids else self.collection.get()

        documents = []
        if not results or "ids" not in results:
            return documents

        for i, _ in enumerate(results["ids"]):
            doc = Document(
                content=str(results["documents"][i] if results["documents"] else ""),
                metadata=cast(
                    dict[str, Any],
                    results["metadatas"][i] if results["metadatas"] else {},
                ),
            )
            documents.append(doc)

        return documents

    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()

    def list_collections(self) -> list[str]:
        """List all available collections."""
        collections = self.client.list_collections()
        return list(map(str, collections))

    def nuke(self) -> None:
        """Delete the entire collection and its contents."""
        self.client.delete_collection(self.collection_name)


def create_vector_store(
    store_type: Literal["chroma"], collection_name: str
) -> VectorStore:
    """Factory function to create vector stores.

    Args:
        store_type: Type of vector store ("chroma" currently supported)
        collection_name: Name for the vector store collection

    Returns:
        VectorStore instance

    Raises:
        ValueError: If unsupported store type is provided
    """
    if store_type == "chroma":
        return ChromaStore(collection_name=collection_name)

    raise ValueError(f"Unsupported vector store type: {store_type}")
