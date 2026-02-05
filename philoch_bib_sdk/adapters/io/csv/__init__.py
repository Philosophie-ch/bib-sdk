"""CSV adapters for reading and writing bibliographic data.

This module provides CSV-specific implementations for loading bibliographies,
staged items, and writing fuzzy matching reports.
"""

import csv
import traceback
from pathlib import Path
from typing import Dict, Tuple

from aletk.ResultMonad import Err, Ok
from aletk.utils import get_logger

from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_formatter import format_bibkey
from philoch_bib_sdk.converters.plaintext.bibitem.parser import parse_bibitem
from philoch_bib_sdk.logic.models import BibItem

logger = get_logger(__name__)


def _csv_row_to_parsed_data(row: dict[str, str]) -> dict[str, str]:
    """Convert CSV row to ParsedBibItemData, filtering empty values.

    Args:
        row: Dictionary from csv.DictReader

    Returns:
        ParsedBibItemData with empty values removed
    """
    # Filter out empty values and create ParsedBibItemData
    # TypedDict with total=False allows any subset of fields
    return {k: v for k, v in row.items() if v}


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


