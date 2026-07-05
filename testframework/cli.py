#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


import argparse
import os
import sys
from argparse import _SubParsersAction
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

from testframework.chatbots import VectorStore, DocumentLoader
from testframework.enums import CliArgs
from testframework.persistence.importer import import_runs
from testframework.persistence.service.analysis_service import AnalysisService
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
    logger.info("Logging configured (level={}, file={})", log_level, log_file)


def main() -> None:
    """Entry point for the CLI."""
    load_dotenv()
    configure_logging()
    # https://docs.python.org/3/howto/argparse.html
    # https://dev.to/taikedz/ive-parked-my-side-projects-3o62
    parser = argparse.ArgumentParser(description="LLM guardrail test framework CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_arguments(subparsers)

    args = parser.parse_args()
    logger.info("CLI command received: {}", args.command)

    if args.command == CliArgs.RUN_BASELINE.value:
        results_dir = Path(args.results_dir)
        logger.info("Starting default test suite (results_dir={})", results_dir)
        test = DefaultTest(results_dir=results_dir)
        test.run()
        logger.info("Default test suite completed")

    elif args.command == CliArgs.POPULATE_DB.value:
        documents_dir = Path(args.documents_dir)
        collection_name = args.collection_name or VectorStore.COLLECTION_NAME
        logger.info(
            "Starting document ingestion (documents_dir={}, chunk_size={}, chunk_overlap={}, collection={})",
            documents_dir,
            args.chunk_size,
            args.chunk_overlap,
            collection_name,
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

        logger.info("Connecting to vector store collection '{}'", collection_name)
        vector_store = VectorStore(collection_name=args.collection_name)
        logger.info("Persisting {} document chunk(s) to the vector store", len(chunks))
        ids = vector_store.add_documents(chunks)

        logger.info("Successfully ingested {} document chunks into the vector store", len(ids))

    elif args.command == CliArgs.MIGRATE.value:
        from alembic import command as alembic_command
        from alembic.config import Config as AlembicConfig
        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_command.upgrade(alembic_cfg, "head")
        logger.info("Database migration completed successfully")

    elif args.command == CliArgs.IMPORT_RUNS.value:
        runs_dir = Path(args.runs_dir)
        stats = import_runs(
            runs_dir=runs_dir,
            force=args.force,
            reanalyze=not args.no_reanalyze,
        )
        logger.info(
            "Import complete: imported={}, skipped={}, failed={}",
            stats.imported,
            stats.skipped,
            stats.failed,
        )

    elif args.command == CliArgs.SERVE.value:
        from testframework.api.asgi_server import run as run_api
        logger.info("Starting REST API server")
        run_api()

    elif args.command == CliArgs.SUMMARIZE_RUN.value:
        run_id = getattr(args, "run_id", None)
        run_folder = getattr(args, "run", None)

        if run_id:
            logger.info("Summarizing run '{}' from DB", run_id)
            AnalysisService().summarize_and_store(
                run_id,
                exclude_scanners=args.exclude_scanners,
                consider_chatbot_success=args.consider_chatbot_success,
            )
            logger.info("Analysis persisted for run_id={}", run_id)
        elif run_folder and args.output:
            logger.info("Summarizing run folder '{}' (legacy JSON path)", run_folder)
            output_path = Path(args.output)
            write_run_summary(
                run_folder=run_folder,
                output_path=output_path,
                exclude_scanners=args.exclude_scanners,
                consider_chatbot_success=args.consider_chatbot_success,
            )
            logger.info("Run summary written to {}", output_path)
        else:
            logger.error("Provide either --run-id or both --run and --output")
            sys.exit(1)


def add_arguments(subparsers: _SubParsersAction):
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

    subparsers.add_parser(
        CliArgs.MIGRATE.value,
        help="Apply pending Alembic migrations (alembic upgrade head).",
    )

    import_runs_parser = subparsers.add_parser(
        CliArgs.IMPORT_RUNS.value,
        help="Import historical _runs/*/result.json files into the DB.",
    )
    import_runs_parser.add_argument(
        CliArgs.RUNS_DIR.value,
        type=str,
        default="_runs",
        help="Directory containing run subdirectories (default: _runs).",
    )
    import_runs_parser.add_argument(
        CliArgs.FORCE.value,
        action="store_true",
        help="Re-import runs that already exist in the DB (deletes existing record first).",
    )
    import_runs_parser.add_argument(
        CliArgs.NO_REANALYZE.value,
        action="store_true",
        help="Skip creating analysis_run rows after import.",
    )

    subparsers.add_parser(
        CliArgs.SERVE.value,
        help="Start the REST API server (uvicorn).",
    )

    summarize_run_parser = subparsers.add_parser(
        CliArgs.SUMMARIZE_RUN.value,
        help="Summarize a persisted run into per-model confusion matrices.",
    )
    summarize_run_parser.add_argument(
        CliArgs.RUN_ID.value,
        type=str,
        default=None,
        help="UUID of the run to summarize (reads from and writes to the DB).",
    )
    summarize_run_parser.add_argument(
        CliArgs.RUN.value,
        type=str,
        default=None,
        help="[Legacy] Path to the run folder containing the testcase directory.",
    )
    summarize_run_parser.add_argument(
        CliArgs.OUTPUT.value,
        type=str,
        default=None,
        help="[Legacy] Output path for the generated summary JSON (used with --run).",
    )
    summarize_run_parser.add_argument(
        CliArgs.EXCLUDE_SCANNERS.value,
        action="store_true",
        help="Exclude configured scanners from the summary and recompute guardrail success.",
    )
    summarize_run_parser.add_argument(
        CliArgs.CONSIDER_CHATBOT_SUCCESS.value,
        action="store_true",
        help=(
            "Count an attack as detected if either the guardrail detects the unsafe prompt "
            "or the chatbot itself returns a safe response. For safe prompts, chatbot over-blocking "
            "counts as incorrect."
        ),
    )


if __name__ == "__main__":
    main()
