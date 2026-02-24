from __future__ import annotations

import argparse
import os
import sys
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from .tests.default_test import DefaultTest
from testframework.chatbots.rag.document_loader import DocumentLoader
from testframework.chatbots.rag.vector_store import VectorStore


def configure_logging() -> None:
    """Configure loguru with file and console logging."""
    logger.remove()
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    log_dir = Path("_logs")
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "testframework.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
    )
    logger.info(f"Logging configured with level: {log_level}")


def main() -> None:
    """Entry point for the CLI."""
    load_dotenv()
    configure_logging()
    parser = argparse.ArgumentParser(description="LLM guardrail test framework CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_arguments(subparsers)

    args = parser.parse_args()

    if args.command == "run-baseline":
        logger.info("Starting default test suite")
        results_dir = Path(args.results_dir)
        test = DefaultTest(results_dir=results_dir)
        test.run()
        logger.info("Default test suite completed")

    elif args.command == "populate-db":
        documents_dir = Path(args.documents_dir)
        logger.info(f"Starting document ingestion from: {documents_dir}")

        loader = DocumentLoader(
            documents_dir=documents_dir,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        chunks = loader.load_and_split()

        if not chunks:
            logger.warning("No documents found to ingest. Exiting.")
            sys.exit(0)

        vector_store = VectorStore(collection_name=args.collection_name)
        ids = vector_store.add_documents(chunks)

        logger.info(f"Successfully ingested {len(ids)} document chunks into the vector store")


def add_arguments(subparsers: _SubParsersAction[ArgumentParser]):
    """Add command line arguments."""

    run_baseline_parser = subparsers.add_parser("run-baseline", help="Run the default test suite.")
    run_baseline_parser.add_argument(
        "--results-dir",
        type=str,
        default="runs",
        help="Directory to store test run results.",
    )

    populate_db_parser = subparsers.add_parser(
        "populate-db",
        help="Populate the vector database with documents from a directory.",
    )
    populate_db_parser.add_argument(
        "--documents-dir",
        type=str,
        default="_documents",
        help="Directory containing documents to ingest (default: _documents).",
    )
    populate_db_parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Size of text chunks for splitting (default: 1000).",
    )
    populate_db_parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Overlap between chunks (default: 200).",
    )
    populate_db_parser.add_argument(
        "--collection-name",
        type=str,
        default=None,
        help="Name of the vector store collection (default: rag_documents).",
    )


if __name__ == "__main__":
    main()
