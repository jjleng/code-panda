import uuid
from pathlib import Path
from typing import Literal, Optional, Sequence

from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from cp_agent.kb.vector_store import Document, create_vector_store


class KnowledgeBaseManager:
    """Manages knowledge base operations including file processing and vector storage."""

    def __init__(
        self,
        store_type: Literal["chroma"] = "chroma",
        collection_name: str = "default",
        chunk_size: int = 15000,  # Large enough. basically, means no chunking
        chunk_overlap: int = 50,
    ):
        """Initialize KnowledgeBaseManager.

        Args:
            store_type: Type of vector store to use
            collection_name: Name of the collection in vector store
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.vector_store = create_vector_store(
            store_type=store_type,
            collection_name=collection_name,
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def add_texts(
        self, texts: Sequence[str], metadatas: Optional[list[dict]] = None
    ) -> None:
        """Add texts to the knowledge base.

        Args:
            texts: Sequence of text strings to add
            metadatas: Optional metadata for each text
        """
        # Split texts into chunks
        all_splits = []
        for i, text in enumerate(texts):
            splits = self.text_splitter.split_text(text)
            metadata = metadatas[i] if metadatas else {}
            for split in splits:
                all_splits.append(Document(content=split, metadata=metadata))

        # Generate UUIDs for each document
        doc_ids = [str(uuid.uuid4()) for _ in all_splits]

        # Add to vector store with generated UUIDs
        self.vector_store.add_documents(all_splits, ids=doc_ids)

    def process_text_files(self, data_dir: str | Path) -> None:
        """Process all text files in the given directory.

        Args:
            data_dir: Directory containing text files to process
        """
        data_dir = Path(data_dir)
        if not data_dir.exists():
            raise FileNotFoundError(f"Directory not found: {data_dir}")

        # Walk through all text files
        for file_path in data_dir.rglob("*.txt"):
            logger.info(f"Processing file: {file_path}")
            # Read file content
            content = file_path.read_text(encoding="utf-8")

            # Add to knowledge base with file metadata
            self.add_texts(texts=[content], metadatas=[{"source": str(file_path)}])

    def search_similar(
        self,
        query: str,
        top_k: int = 4,
    ) -> list[tuple[Document, float]]:
        """Search for similar documents and return with similarity scores.

        Args:
            query: Query string
            top_k: Number of documents to return

        Returns:
            List of tuples containing documents and their similarity scores
        """
        return self.vector_store.search(query=query, top_k=top_k)

    def list_collections(self) -> list[str]:
        """List all available collections.

        Returns:
            List of collection names
        """
        return self.vector_store.list_collections()

    def nuke(self) -> None:
        """Delete the entire collection and its contents.

        This is a destructive operation that removes all documents and the collection itself.
        The collection will be recreated empty after this operation.
        """
        self.vector_store.nuke()
