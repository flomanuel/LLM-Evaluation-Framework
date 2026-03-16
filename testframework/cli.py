#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from __future__ import annotations
import argparse
import os
import sys
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

from testframework.chatbots import VectorStore, DocumentLoader
from testframework.enums import CliArgs
from testframework.reporting import write_run_summary
from testframework.tests.default_test import DefaultTest


def configure_logging() -> None:
    """Configure loguru with file and console logging."""
    logger.remove()
    log_level = os.environ.get("CUSTOM_LOG_LEVEL", "ERROR").upper()
    log_dir = Path("_logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "testframework.log"
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        # backtrace=True,
    )
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        # backtrace=True,
    )
    logger.info(f"Logging configured (level={log_level}, file={log_file})")


def main() -> None:
    """Entry point for the CLI."""
    load_dotenv()
    configure_logging()
    parser = argparse.ArgumentParser(description="LLM guardrail test framework CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_arguments(subparsers)

    args = parser.parse_args()
    logger.info(f"CLI command received: {args.command}")

    if args.command == CliArgs.RUN_BASELINE.value:
        results_dir = Path(args.results_dir)
        logger.info(f"Starting default test suite (results_dir={results_dir})")
        test = DefaultTest(results_dir=results_dir)
        test.run()
        logger.info("Default test suite completed")

    elif args.command == CliArgs.POPULATE_DB.value:
        documents_dir = Path(args.documents_dir)
        collection_name = args.collection_name or VectorStore.COLLECTION_NAME
        logger.info(
            "Starting document ingestion "
            f"(documents_dir={documents_dir}, chunk_size={args.chunk_size}, "
            f"chunk_overlap={args.chunk_overlap}, collection={collection_name})"
        )

        loader = DocumentLoader(
            documents_dir=documents_dir,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        chunks = loader.load_and_split()

        if not chunks:
            logger.warning("No documents found to ingest. Exiting.")
            sys.exit(0)

        logger.info(f"Connecting to vector store collection '{collection_name}'")
        vector_store = VectorStore(collection_name=args.collection_name)
        logger.info(f"Persisting {len(chunks)} document chunk(s) to the vector store")
        ids = vector_store.add_documents(chunks)

        logger.info(f"Successfully ingested {len(ids)} document chunks into the vector store")

    elif args.command == CliArgs.SUMMARIZE_RUN.value:
        logger.info(
            f"Summarizing run folder '{args.run}'"
        )

        if args.output is not None:
            output_path = Path(args.output)
            write_run_summary(
                run_folder=args.run,
                output_path=output_path,
                exclude_scanners=args.exclude_scanners,
            )
            logger.info(f"Run summary written to {output_path}")


def add_arguments(subparsers: _SubParsersAction[ArgumentParser]):
    """Add command line arguments."""

    run_baseline_parser = subparsers.add_parser(
        CliArgs.RUN_BASELINE.value,
        help="Run the default test suite."
    )
    run_baseline_parser.add_argument(
        CliArgs.RESULTS_DIR.value,
        type=str,
        default="_runs",
        help="Directory to store test run results.",
    )

    populate_db_parser = subparsers.add_parser(
        CliArgs.POPULATE_DB.value,
        help="Populate the vector database with documents from a directory.",
    )
    populate_db_parser.add_argument(
        CliArgs.DOC_DIR.value,
        type=str,
        default="_rag_documents",
        help="Directory containing documents to ingest (default: _rag_documents).",
    )
    populate_db_parser.add_argument(
        CliArgs.CHUNK_SIZE.value,
        type=int,
        default=1000,
        help="Size of text chunks for splitting (default: 1000).",
    )
    populate_db_parser.add_argument(
        CliArgs.CHUNK_OVERLAP.value,
        type=int,
        default=200,
        help="Overlap between chunks (default: 200).",
    )
    populate_db_parser.add_argument(
        CliArgs.COLLECTION_NAME.value,
        type=str,
        default=None,
        help="Name of the vector store collection (default: rag_documents).",
    )

    summarize_run_parser = subparsers.add_parser(
        CliArgs.SUMMARIZE_RUN.value,
        help="Summarize a persisted run into per-model confusion matrices.",
    )
    summarize_run_parser.add_argument(
        CliArgs.RUN.value,
        required=True,
        help="Path to the run folder containing the testcase directory.",
    )
    summarize_run_parser.add_argument(
        CliArgs.OUTPUT.value,
        type=str,
        required=True,
        default=None,
        help="Optional output path for the generated summary JSON.",
    )
    summarize_run_parser.add_argument(
        CliArgs.EXCLUDE_SCANNERS.value,
        action="store_true",
        help="Exclude configured scanners from the summary and recompute guardrail success.",
    )


if __name__ == "__main__":
    main()
