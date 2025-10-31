"""CLI interface for fuzzy matching bibliographic items.

This module provides a command-line interface for matching new bibliographic entries
against an existing bibliography using fuzzy matching.

Usage:
    poetry run python -m philoch_bib_sdk.interfaces.cli.fuzzy_matching \\
        --bibliography path/to/bibliography.csv \\
        --input path/to/new_items.csv \\
        --output path/to/report \\
        [--format csv] \\
        [--top-n 5] \\
        [--min-score 100.0]
"""

import argparse
import sys
from functools import partial

from aletk.ResultMonad import Err, main_try_except_wrapper
from aletk.utils import get_logger

from philoch_bib_sdk.adapters.io import load_bibliography, load_staged, write_report
from philoch_bib_sdk.procedures.fuzzy_matching import fuzzy_match_procedure

logger = get_logger(__name__)


@main_try_except_wrapper(logger)
def cli() -> None:
    """Command-line interface for fuzzy matching.

    Returns:
        None on success (raises exception on failure)
    """
    parser = argparse.ArgumentParser(
        description="Fuzzy match bibliographic items against an existing bibliography.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with CSV files
  %(prog)s --bibliography refs.csv --input new_refs.csv --output matches

  # With custom matching parameters
  %(prog)s --bibliography refs.csv --input new_refs.csv --output matches \\
           --top-n 10 --min-score 200.0

  # Specify output format explicitly
  %(prog)s --bibliography refs.csv --input new_refs.csv --output matches \\
           --format csv
        """,
    )

    parser.add_argument(
        "--bibliography",
        required=True,
        help="Path to bibliography file (format auto-detected from extension)",
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input file with new items to match",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path to output report file (without extension)",
    )

    parser.add_argument(
        "--format",
        default="csv",
        choices=["csv"],
        help="Output format (default: csv)",
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of top matches to return per item (default: 5)",
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum score threshold for matches (default: 0.0)",
    )

    args = parser.parse_args()

    # Validate parameters
    if args.top_n < 1:
        raise ValueError("--top-n must be at least 1")

    if args.min_score < 0:
        raise ValueError("--min-score must be non-negative")

    # Create write_report function with format bound
    write_report_with_format = partial(write_report, output_format=args.format)

    # Execute procedure
    logger.info("Starting fuzzy matching CLI")
    result = fuzzy_match_procedure(
        bibliography_path=args.bibliography,
        staged_path=args.input,
        output_path=args.output,
        load_bibliography=load_bibliography,
        load_staged=load_staged,
        write_report=write_report_with_format,
        top_n=args.top_n,
        min_score=args.min_score,
    )

    # Handle result - raise exception if procedure failed
    if isinstance(result, Err):
        raise RuntimeError(result.message)

    print(f"Success! Report written to {args.output}.{args.format}")
    logger.info("Fuzzy matching completed successfully")


def main() -> None:
    """Entry point for CLI when run as script."""
    result = cli()
    if isinstance(result, Err):
        sys.exit(result.code if result.code > 0 else 1)
    sys.exit(0)


if __name__ == "__main__":
    main()
