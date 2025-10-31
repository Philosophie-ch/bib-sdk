"""IO adapters with automatic format detection.

This module provides format-agnostic wrappers that detect file formats
and delegate to appropriate format-specific adapters.
"""

from pathlib import Path
from typing import Dict, Tuple

from aletk.ResultMonad import Err, Ok

from philoch_bib_sdk.adapters.io.csv import (
    load_bibliography_csv,
    load_staged_csv,
    write_report_csv,
)
from philoch_bib_sdk.adapters.io.ods import (
    load_bibliography_ods,
    load_staged_ods,
)
from philoch_bib_sdk.logic.models import BibItem
from philoch_bib_sdk.logic.models_staging import BibItemStaged


def load_bibliography(filename: str, max_rows: int | None = None) -> Ok[Dict[str, BibItem]] | Err:
    """Load bibliography with automatic format detection.

    Detects format based on file extension and delegates to appropriate adapter.

    Supported formats:
    - .csv: CSV format
    - .ods: OpenDocument Spreadsheet format

    Args:
        filename: Path to bibliography file
        max_rows: Optional limit on number of rows (for testing large files)

    Returns:
        Ok[Dict[str, BibItem]] with bibkey as key, or Err on failure
    """
    file_path = Path(filename)
    suffix = file_path.suffix.lower()

    match suffix:
        case ".csv":
            return load_bibliography_csv(filename)
        case ".ods":
            return load_bibliography_ods(filename, max_rows=max_rows)
        case _:
            return Err(
                message=f"Unsupported bibliography format: {suffix}. Supported: .csv, .ods",
                code=-1,
                error_type="UnsupportedFormatError",
            )


def load_staged(filename: str, max_rows: int | None = None) -> Ok[Tuple[BibItem, ...]] | Err:
    """Load staged items with automatic format detection.

    Detects format based on file extension and delegates to appropriate adapter.

    Supported formats:
    - .csv: CSV format
    - .ods: OpenDocument Spreadsheet format

    Args:
        filename: Path to staged items file
        max_rows: Optional limit on number of rows (for testing large files)

    Returns:
        Ok[Tuple[BibItem, ...]] or Err on failure
    """
    file_path = Path(filename)
    suffix = file_path.suffix.lower()

    match suffix:
        case ".csv":
            return load_staged_csv(filename)
        case ".ods":
            return load_staged_ods(filename, max_rows=max_rows)
        case _:
            return Err(
                message=f"Unsupported staged items format: {suffix}. Supported: .csv, .ods",
                code=-1,
                error_type="UnsupportedFormatError",
            )


def write_report(filename: str, staged: Tuple[BibItemStaged, ...], output_format: str = "csv") -> Ok[None] | Err:
    """Write fuzzy matching report with format selection.

    Args:
        filename: Path to output file (extension will be added based on format)
        staged: Tuple of staged items with matches
        output_format: Output format ("csv", etc.)

    Returns:
        Ok[None] on success, Err on failure
    """
    match output_format.lower():
        case "csv":
            return write_report_csv(filename, staged)
        case _:
            return Err(
                message=f"Unsupported output format: {output_format}. Supported: csv",
                code=-1,
                error_type="UnsupportedFormatError",
            )


__all__ = [
    "load_bibliography",
    "load_staged",
    "write_report",
]
