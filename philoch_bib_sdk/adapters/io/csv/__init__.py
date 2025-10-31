"""CSV adapters for reading and writing bibliographic data.

This module provides CSV-specific implementations for loading bibliographies,
staged items, and writing fuzzy matching reports.
"""

import csv
import traceback
from pathlib import Path
from typing import Any, Dict, Tuple

from aletk.ResultMonad import Err, Ok
from aletk.utils import get_logger

from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_formatter import format_bibkey
from philoch_bib_sdk.converters.plaintext.bibitem.parser import (
    ParsedBibItemData,
    parse_bibitem,
)
from philoch_bib_sdk.logic.models import BibItem
from philoch_bib_sdk.logic.models_staging import BibItemStaged

logger = get_logger(__name__)


def _csv_row_to_parsed_data(row: dict[str, Any]) -> ParsedBibItemData:
    """Convert CSV row to ParsedBibItemData, filtering empty values.

    Args:
        row: Dictionary from csv.DictReader

    Returns:
        ParsedBibItemData with empty values removed
    """
    # Filter out empty values and create ParsedBibItemData
    # TypedDict with total=False allows any subset of fields
    return {k: v for k, v in row.items() if v}  # type: ignore[return-value]


def load_bibliography_csv(filename: str) -> Ok[Dict[str, BibItem]] | Err:
    """Load bibliography from CSV file.

    Expected CSV format: Standard CSV with headers matching ParsedBibItemData fields.
    Required columns: entry_type, author, title, date
    Optional columns: journal, volume, number, pages, doi, etc.

    Args:
        filename: Path to CSV file

    Returns:
        Ok[Dict[str, BibItem]] with bibkey as key, or Err on failure
    """
    try:
        file_path = Path(filename)
        if not file_path.exists():
            return Err(
                message=f"File not found: {filename}",
                code=-1,
                error_type="FileNotFoundError",
            )

        bibliography: Dict[str, BibItem] = {}
        errors = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                return Err(
                    message=f"CSV file has no headers: {filename}",
                    code=-1,
                    error_type="CSVFormatError",
                )

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                # Convert CSV row to ParsedBibItemData
                parsed_data = _csv_row_to_parsed_data(row)

                # Parse the row into a BibItem
                parse_result = parse_bibitem(parsed_data, bibstring_type="simplified")

                if isinstance(parse_result, Err):
                    errors.append(f"Row {row_num}: {parse_result.message}")
                    continue

                bibitem = parse_result.out
                bibkey = format_bibkey(bibitem.bibkey)

                # Check for duplicate bibkeys
                if bibkey in bibliography:
                    errors.append(f"Row {row_num}: Duplicate bibkey '{bibkey}' (first seen in earlier row)")
                    continue

                bibliography[bibkey] = bibitem

        # Report results
        if errors:
            error_summary = f"Loaded {len(bibliography)} items with {len(errors)} errors:\n" + "\n".join(
                errors[:10]  # Show first 10 errors
            )
            if len(errors) > 10:
                error_summary += f"\n... and {len(errors) - 10} more errors"

            logger.warning(error_summary)

        if not bibliography:
            return Err(
                message=f"No valid items loaded from {filename}. Errors: {len(errors)}",
                code=-1,
                error_type="EmptyBibliographyError",
            )

        logger.info(f"Successfully loaded {len(bibliography)} items from {filename}")
        return Ok(bibliography)

    except Exception as e:
        return Err(
            message=f"Failed to load bibliography from {filename}: {e.__class__.__name__}: {e}",
            code=-1,
            error_type=e.__class__.__name__,
            error_trace=traceback.format_exc(),
        )


def load_staged_csv_allow_empty_bibkeys(filename: str) -> Ok[Tuple[BibItem, ...]] | Err:
    """Load staged items from CSV file, allowing empty bibkeys.

    This is useful for staging files where bibkeys haven't been assigned yet.
    Items without bibkeys will be assigned temporary sequential keys.

    Args:
        filename: Path to CSV file

    Returns:
        Ok[Tuple[BibItem, ...]] or Err on failure
    """
    try:
        file_path = Path(filename)

        if not file_path.exists():
            return Err(
                message=f"File not found: {filename}",
                code=-1,
                error_type="FileNotFoundError",
            )

        staged_items: list[BibItem] = []
        errors = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                return Err(
                    message=f"CSV file has no headers: {filename}",
                    code=-1,
                    error_type="CSVFormatError",
                )

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                # Convert CSV row to ParsedBibItemData
                parsed_data = _csv_row_to_parsed_data(row)

                # If bibkey is empty, assign a temporary one
                if not parsed_data.get("bibkey"):
                    parsed_data["bibkey"] = f"temp:{row_num}"

                # Parse the row into a BibItem
                parse_result = parse_bibitem(parsed_data, bibstring_type="simplified")

                if isinstance(parse_result, Err):
                    errors.append(f"Row {row_num}: {parse_result.message}")
                    continue

                bibitem = parse_result.out
                staged_items.append(bibitem)

        # Report results
        if errors:
            error_summary = f"Loaded {len(staged_items)} items with {len(errors)} errors:\n" + "\n".join(
                errors[:10]  # Show first 10 errors
            )
            if len(errors) > 10:
                error_summary += f"\n... and {len(errors) - 10} more errors"

            logger.warning(error_summary)

        if not staged_items:
            return Err(
                message=f"No valid items loaded from {filename}. Errors: {len(errors)}",
                code=-1,
                error_type="EmptyFileError",
            )

        logger.info(f"Successfully loaded {len(staged_items)} staged items from {filename}")

        return Ok(tuple(staged_items))

    except Exception as e:
        return Err(
            message=f"Failed to load staged items from {filename}: {e.__class__.__name__}: {e}",
            code=-1,
            error_type=e.__class__.__name__,
            error_trace=traceback.format_exc(),
        )


def load_staged_csv(filename: str) -> Ok[Tuple[BibItem, ...]] | Err:
    """Load staged items from CSV file.

    Uses the same format as load_bibliography_csv - standard CSV with ParsedBibItemData fields.
    Additional score-related columns (if present) are ignored during loading.

    Args:
        filename: Path to CSV file

    Returns:
        Ok[Tuple[BibItem, ...]] or Err on failure
    """
    try:
        # Load as bibliography first
        result = load_bibliography_csv(filename)

        if isinstance(result, Err):
            return result

        bibliography = result.out

        # Convert dict values to tuple
        staged_items = tuple(bibliography.values())

        logger.info(f"Successfully loaded {len(staged_items)} staged items from {filename}")
        return Ok(staged_items)

    except Exception as e:
        return Err(
            message=f"Failed to load staged items from {filename}: {e.__class__.__name__}: {e}",
            code=-1,
            error_type=e.__class__.__name__,
            error_trace=traceback.format_exc(),
        )


def write_report_csv(filename: str, staged: Tuple[BibItemStaged, ...]) -> Ok[None] | Err:
    """Write fuzzy matching report to CSV file.

    Output format: Uses BibItemStaged.to_csv_row() with columns:
    - staged_bibkey, staged_title, staged_author, staged_year
    - num_matches, best_match_score, best_match_bibkey
    - top_matches_json (JSON-encoded match details)
    - search_time_ms, candidates_searched

    Args:
        filename: Path to output CSV file (without extension)
        staged: Tuple of staged items with matches

    Returns:
        Ok[None] on success, Err on failure
    """
    try:
        # Add .csv extension if not present
        output_path = Path(filename)
        if output_path.suffix != ".csv":
            output_path = output_path.with_suffix(".csv")

        if not staged:
            logger.warning("No staged items to write")
            # Create empty file with headers
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                simple_writer = csv.writer(f)
                simple_writer.writerow(
                    [
                        "staged_bibkey",
                        "staged_title",
                        "staged_author",
                        "staged_year",
                        "num_matches",
                        "best_match_score",
                        "best_match_bibkey",
                        "top_matches_json",
                        "search_time_ms",
                        "candidates_searched",
                    ]
                )
            logger.info(f"Created empty report at {output_path}")
            return Ok(None)

        # Convert to CSV rows
        rows = tuple(item.to_csv_row() for item in staged)

        # Write to CSV
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            if rows:
                fieldnames = list(rows[0].keys())
                dict_writer = csv.DictWriter(f, fieldnames=fieldnames)
                dict_writer.writeheader()
                dict_writer.writerows(rows)

        logger.info(f"Successfully wrote {len(staged)} items to {output_path}")
        return Ok(None)

    except Exception as e:
        return Err(
            message=f"Failed to write report to {filename}: {e.__class__.__name__}: {e}",
            code=-1,
            error_type=e.__class__.__name__,
            error_trace=traceback.format_exc(),
        )
