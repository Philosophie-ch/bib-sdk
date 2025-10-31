"""ODS (OpenDocument Spreadsheet) adapters for bibliography I/O operations."""

import traceback
from typing import Dict, Tuple, Any
from pathlib import Path

from aletk.ResultMonad import Ok, Err
from aletk.utils import get_logger

from philoch_bib_sdk.logic.models import BibItem
from philoch_bib_sdk.converters.plaintext.bibitem.parser import parse_bibitem, ParsedBibItemData
from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_formatter import format_bibkey

lgr = get_logger(__name__)

__all__: list[str] = [
    "load_bibliography_ods",
    "load_staged_ods",
]


def _normalize_column_name(name: str) -> str:
    """
    Normalize column names from ODS to match ParsedBibItemData keys.

    ODS columns use hyphens (e.g., 'journal-id') while ParsedBibItemData uses underscores.
    """
    return name.replace("-", "_")


def _ods_row_to_parsed_data(row: dict[str, Any]) -> ParsedBibItemData:
    """
    Convert an ODS row (dict) to ParsedBibItemData.

    This helper exists to isolate the type: ignore directive.
    Polars returns dict[str, Any] while ParsedBibItemData is a TypedDict.
    We filter out None/empty values and normalize column names.
    """
    normalized = {_normalize_column_name(k): str(v) if v is not None else "" for k, v in row.items()}
    return {k: v for k, v in normalized.items() if v}  # type: ignore[return-value]


def load_bibliography_ods(
    filename: str, max_rows: int | None = None, bibstring_type: str = "simplified"
) -> Ok[Dict[str, BibItem]] | Err:
    """
    Load a bibliography from an ODS file.

    Args:
        filename: Path to the ODS file
        max_rows: Optional limit on number of rows to read (for testing)
        bibstring_type: Type of bibstring to use ('simplified', 'latex', 'unicode')

    Returns:
        Ok with dict mapping bibkey -> BibItem, or Err with details
    """
    try:
        import polars as pl

        if not Path(filename).exists():
            return Err(message=f"File not found: {filename}", code=1)

        # Read ODS file
        df = pl.read_ods(source=filename, has_header=True)

        if df.is_empty():
            return Err(message=f"ODS file is empty: {filename}", code=1)

        # Limit rows if requested
        if max_rows is not None:
            df = df.head(max_rows)

        # Convert to list of dicts
        rows = df.to_dicts()

        bibliography: dict[str, BibItem] = {}
        errors: list[str] = []
        seen_bibkeys: dict[str, int] = {}

        for i, row in enumerate(rows, start=2):  # Start at 2 because row 1 is header
            try:
                parsed_data = _ods_row_to_parsed_data(row)
                result = parse_bibitem(parsed_data, bibstring_type=bibstring_type)  # type: ignore[arg-type]

                if isinstance(result, Err):
                    errors.append(f"Row {i}: {result.message}")
                    continue

                bibitem = result.out
                bibkey_str = format_bibkey(bibitem.bibkey)

                # Check for duplicates
                if bibkey_str in seen_bibkeys:
                    first_row = seen_bibkeys[bibkey_str]
                    errors.append(f"Row {i}: Duplicate bibkey '{bibkey_str}' (first seen in row {first_row})")
                    continue

                bibliography[bibkey_str] = bibitem
                seen_bibkeys[bibkey_str] = i

            except Exception as e:
                errors.append(f"Row {i}: Unexpected error: {e}")
                continue

        if errors:
            lgr.warning(f"Loaded {len(bibliography)} items with {len(errors)} errors:\n" + "\n".join(errors[:10]))

        if not bibliography:
            error_summary = "\n".join(errors[:5])
            return Err(message=f"No valid items loaded from {filename}. Errors: {len(errors)}\n{error_summary}", code=1)

        lgr.info(f"Successfully loaded {len(bibliography)} items from {filename}")
        return Ok(bibliography)

    except Exception as e:
        return Err(
            message=f"Failed to load bibliography from {filename}: {e.__class__.__name__}: {e}",
            code=-1,
            error_type=e.__class__.__name__,
            error_trace=traceback.format_exc(),
        )


def load_staged_ods(filename: str, max_rows: int | None = None) -> Ok[Tuple[BibItem, ...]] | Err:
    """
    Load staged BibItems from an ODS file.

    Args:
        filename: Path to the ODS file
        max_rows: Optional limit on number of rows to read (for testing)

    Returns:
        Ok with tuple of BibItems, or Err with details
    """
    result = load_bibliography_ods(filename, max_rows=max_rows)

    if isinstance(result, Err):
        return result

    bibliography = result.out
    staged_items = tuple(bibliography.values())

    lgr.info(f"Successfully loaded {len(staged_items)} staged items from {filename}")

    return Ok(staged_items)
