"""Document loader module for RAG ingestion."""

#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger


class DocumentLoader:
    """
    Load and process documents from a directory for RAG ingestion.
    See https://docs.langchain.com/oss/python/langchain/rag
    See https://docs.langchain.com/oss/python/langchain/knowledge-base
    """
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200

    def __init__(
            self,
            documents_dir: Path | str,
            chunk_size: int = DEFAULT_CHUNK_SIZE,
            chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        """Initialize the document loader."""
        self._documents_dir = Path(documents_dir)
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

        # recommended text splitter for generic text use cases: https://docs.langchain.com/oss/python/langchain/rag
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

    def _load_pdf_files(self) -> tuple[List[Document], int]:
        """
        Load all PDF files from the documents directory.
        See https://docs.langchain.com/oss/python/integrations/document_loaders/pypdfloader
        See https://github.com/langchain-ai/langchain-community
        """
        documents: List[Document] = []
        pdf_files = list(self._documents_dir.glob("**/*.pdf"))
        logger.info(
            f"Discovered {len(pdf_files)} PDF file(s) in '{self._documents_dir}'"
        )

        for pdf_path in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs = loader.load()
                documents.extend(docs)
                logger.debug(f"Loaded {len(docs)} pages from '{pdf_path.name}'")
            except Exception as e:
                logger.error(f"Failed to load PDF '{pdf_path}': {e}")

        return documents, len(pdf_files)

    def load_documents(self) -> List[Document]:
        """Load all documents from the configured directory."""
        if not self._documents_dir.exists():
            raise FileNotFoundError(f"Documents directory not found: {self._documents_dir}")

        documents: List[Document] = []

        pdf_docs, pdf_file_count = self._load_pdf_files()
        logger.info(
            f"Loaded {len(pdf_docs)} page document(s) from {pdf_file_count} PDF file(s)"
        )
        documents.extend(pdf_docs)

        logger.info(f"Total documents loaded: {len(documents)}")
        return documents

    def load_and_split(self) -> List[Document]:
        """Load documents and split them into chunks."""
        documents = self.load_documents()

        if not documents:
            logger.warning("No documents found to split")
            return []

        logger.info(f"Splitting {len(documents)} document(s) into chunks")
        chunks = self._text_splitter.split_documents(documents)
        logger.info(
            f"Split {len(documents)} documents into {len(chunks)} chunks "
            f"(chunk_size={self._chunk_size}, overlap={self._chunk_overlap})"
        )
        return chunks

    @property
    def documents_dir(self) -> Path:
        """Get the documents-directory path."""
        return self._documents_dir
