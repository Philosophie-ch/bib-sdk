#!/usr/bin/env python3
"""CLI script to import ODS/CSV bibliography data into the Rust API.

Usage:
    python scripts/import_ods_to_api.py \\
        --input /path/to/biblio.csv \\
        --api-url http://localhost:8080/api/v1 \\
        --api-key YOUR_ADMIN_KEY

Options:
    --input PATH        Path to the ODS or CSV file to import (required)
    --api-url URL       Base URL of the API (default: http://localhost:8080/api/v1)
    --api-key KEY       Admin API key for authentication (required)
    --bibstring-type    Type of bibstring to use: simplified, latex, unicode (default: simplified)
    --dry-run           Validate file without making API calls
    -v, --verbose       Enable verbose logging
"""

import argparse
import logging
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import ODS/CSV bibliography data into the Rust API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the ODS or CSV file to import",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8080/api/v1",
        help="Base URL of the API (default: http://localhost:8080/api/v1)",
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="Admin API key for authentication",
    )
    parser.add_argument(
        "--bibstring-type",
        default="simplified",
        choices=["simplified", "latex", "unicode"],
        help="Type of bibstring to use (default: simplified)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate file without making API calls",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Validate input file exists
    if not args.input.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        return 1

    # Import here to allow --help without loading all dependencies
    from philoch_bib_sdk.procedures.import_to_api import import_to_api

    print(f"Importing {args.input} to {args.api_url}")
    if args.dry_run:
        print("DRY RUN MODE - no API calls will be made")
    print()

    result = import_to_api(
        input_path=str(args.input),
        api_base_url=args.api_url,
        api_key=args.api_key,
        bibstring_type=args.bibstring_type,
        dry_run=args.dry_run,
    )

    # Print summary
    print()
    print("=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(
        f"  Authors:      {result.authors.created:5} created, {result.authors.skipped:5} skipped, {result.authors.failed:5} failed"
    )
    print(
        f"  Journals:     {result.journals.created:5} created, {result.journals.skipped:5} skipped, {result.journals.failed:5} failed"
    )
    print(
        f"  Publishers:   {result.publishers.created:5} created, {result.publishers.skipped:5} skipped, {result.publishers.failed:5} failed"
    )
    print(
        f"  Institutions: {result.institutions.created:5} created, {result.institutions.skipped:5} skipped, {result.institutions.failed:5} failed"
    )
    print(
        f"  Schools:      {result.schools.created:5} created, {result.schools.skipped:5} skipped, {result.schools.failed:5} failed"
    )
    print(
        f"  Series:       {result.series.created:5} created, {result.series.skipped:5} skipped, {result.series.failed:5} failed"
    )
    print(
        f"  BibItems:     {result.bibitems.created:5} created, {result.bibitems.skipped:5} skipped, {result.bibitems.failed:5} failed"
    )
    print(
        f"  Author Links: {result.author_links.created:5} created, {result.author_links.skipped:5} skipped, {result.author_links.failed:5} failed"
    )

    if result.errors:
        print()
        print(f"ERRORS ({len(result.errors)}):")
        for error in result.errors[:20]:
            print(f"  - {error}")
        if len(result.errors) > 20:
            print(f"  ... and {len(result.errors) - 20} more")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
