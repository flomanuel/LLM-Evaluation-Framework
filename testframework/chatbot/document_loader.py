"""Document loader module for RAG ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger


class DocumentLoader:
    """Load and process documents from a directory for RAG ingestion."""

    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200

    def __init__(
            self,
            documents_dir: Path | str,
            chunk_size: int = DEFAULT_CHUNK_SIZE,
            chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        """Initialize the document loader.

        Args:
            documents_dir: Path to the directory containing documents.
            chunk_size: Size of text chunks for splitting.
            chunk_overlap: Overlap between chunks.
        """
        self._documents_dir = Path(documents_dir)
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

        logger.debug(
            f"DocumentLoader initialized with dir='{self._documents_dir}', "
            f"chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
        )

    def _load_pdf_files(self) -> List[Document]:
        """Load all .txt files from the documents directory."""
        loader = DirectoryLoader(
            str(self._documents_dir),
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=True,
            use_multithreading=True,
        )
        return loader.load()

    def load_documents(self) -> List[Document]:
        """Load all documents from the configured directory.

        Returns:
            List of loaded Document objects (not yet chunked).

        Raises:
            FileNotFoundError: If the documents directory does not exist.
        """
        if not self._documents_dir.exists():
            raise FileNotFoundError(f"Documents directory not found: {self._documents_dir}")

        documents: List[Document] = []

        # Load text files
        txt_docs = self._load_pdf_files()
        logger.info(f"Loaded {len(txt_docs)} .pdf files")
        documents.extend(txt_docs)

        logger.info(f"Total documents loaded: {len(documents)}")
        return documents

    def load_and_split(self) -> List[Document]:
        """Load documents and split them into chunks.

        Returns:
            List of chunked Document objects ready for embedding.
        """
        documents = self.load_documents()

        if not documents:
            logger.warning("No documents found to split")
            return []

        chunks = self._text_splitter.split_documents(documents)
        logger.info(
            f"Split {len(documents)} documents into {len(chunks)} chunks "
            f"(chunk_size={self._chunk_size}, overlap={self._chunk_overlap})"
        )
        return chunks

    @property
    def documents_dir(self) -> Path:
        """Get the documents directory path."""
        return self._documents_dir

