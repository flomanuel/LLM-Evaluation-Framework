from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from .test.baseline_test import BaselineTest


def configure_logging() -> None:
    """Configure loguru with file and console logging."""
    # Remove default handler
    logger.remove()

    # Get log level from environment variable, default to INFO
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Add file handler with rotation
    log_dir = Path("logs")
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
    # Load environment variables from .env file
    load_dotenv()

    # Configure logging
    configure_logging()

    parser = argparse.ArgumentParser(description="LLM guardrail test framework CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_baseline_parser = subparsers.add_parser("run-baseline", help="Run the baseline test suite.")
    run_baseline_parser.add_argument(
        "--results-dir",
        type=str,
        default="runs",
        help="Directory to store test run results.",
    )

    args = parser.parse_args()

    if args.command == "run-baseline":
        logger.info("Starting baseline test suite")
        results_dir = Path(args.results_dir)
        test = BaselineTest(results_dir=results_dir)
        test.run()
        logger.info("Baseline test suite completed")


if __name__ == "__main__":
    main()

