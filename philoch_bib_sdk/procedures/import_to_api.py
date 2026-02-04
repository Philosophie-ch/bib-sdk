"""Import procedure for loading ODS bibliography data into the Rust API.

This module orchestrates the full import process:
1. Load ODS file using existing bib-sdk parsers
2. Extract unique entities (authors, journals, publishers, etc.)
3. Create entities via API (get-or-create pattern)
4. Create bibitems with resolved entity IDs
5. Link authors to bibitems
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass, field

import attrs
from aletk.ResultMonad import Err, Ok
from aletk.utils import get_logger

from philoch_bib_sdk.adapters.api import ApiClient
from philoch_bib_sdk.adapters.io.csv import load_bibliography_csv
from philoch_bib_sdk.adapters.io.ods import load_bibliography_ods
from philoch_bib_sdk.converters.api import (
    author_to_api,
    bibitem_to_api,
    institution_to_api,
    journal_to_api,
    publisher_to_api,
    school_to_api,
    series_to_api,
)
from philoch_bib_sdk.logic.models import Author, BibItem, BibStringAttr, BaseNamedRenderable, Journal, TBibString

lgr = get_logger(__name__)

__all__: list[str] = [
    "import_to_api",
    "import_ods_to_api",  # Alias for backwards compatibility
    "ImportResult",
    "ImportStats",
]


@dataclass
class ImportStats:
    """Statistics for a single entity type."""

    created: int = 0
    skipped: int = 0  # Already existed (409)
    failed: int = 0


@dataclass
class ImportResult:
    """Result of the import operation."""

    authors: ImportStats = field(default_factory=ImportStats)
    journals: ImportStats = field(default_factory=ImportStats)
    publishers: ImportStats = field(default_factory=ImportStats)
    institutions: ImportStats = field(default_factory=ImportStats)
    schools: ImportStats = field(default_factory=ImportStats)
    series: ImportStats = field(default_factory=ImportStats)
    bibitems: ImportStats = field(default_factory=ImportStats)
    author_links: ImportStats = field(default_factory=ImportStats)

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@attrs.define
class OdsRowData:
    """Parsed data from an ODS row including explicit keys."""

    bibitem: BibItem
    bibkey_str: str

    # Explicit keys from ODS columns
    author_keys: Tuple[str, ...]  # Comma-separated, same order as bibitem.author
    editor_keys: Tuple[str, ...]  # Comma-separated, same order as bibitem.editor
    guesteditor_keys: Tuple[str, ...]  # Comma-separated, same order as bibitem._guesteditor
    journal_key: str
    publisher_key: str
    institution_key: str
    school_key: str
    series_key: str
    person_key: str


def _parse_key_list(key_string: str) -> Tuple[str, ...]:
    """Parse a comma-separated key string into a tuple of keys."""
    if not key_string or not key_string.strip():
        return ()
    return tuple(k.strip() for k in key_string.split(",") if k.strip())


def _validate_key_count(
    keys: Tuple[str, ...],
    entities: Tuple[object, ...],
    field_name: str,
    bibkey: str,
) -> List[str]:
    """Validate that the number of keys matches the number of entities.

    Returns a list of error messages (empty if valid).
    """
    errors: List[str] = []
    if len(keys) != len(entities):
        if len(entities) > 0 and len(keys) == 0:
            errors.append(
                f"[{bibkey}] {field_name}: has {len(entities)} entities but no keys provided. "
                f"Add '{field_name}_key' column with comma-separated keys."
            )
        elif len(keys) != len(entities):
            errors.append(
                f"[{bibkey}] {field_name}: key count mismatch. " f"Expected {len(entities)} keys but got {len(keys)}."
            )
    return errors


def _load_and_parse_file(
    file_path: str,
    bibstring_type: TBibString = "simplified",
) -> Ok[Tuple[OdsRowData, ...]] | Err:
    """Load ODS or CSV file and parse rows with explicit keys.

    This function loads the file using the appropriate loader, then extracts
    the explicit key columns that are needed for the API import.

    Args:
        file_path: Path to the ODS or CSV file
        bibstring_type: Type of bibstring to use

    Returns:
        Ok with tuple of OdsRowData, or Err
    """
    import csv
    import polars as pl
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        return Err(message=f"File not found: {file_path}", code=1)

    file_ext = path.suffix.lower()

    try:
        # Load raw data and parsed BibItems based on file type
        if file_ext == ".csv":
            # Read CSV to get raw rows with key columns
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                return Err(message=f"CSV file is empty: {file_path}", code=1)

            # Load via standard loader to get parsed BibItems
            bib_result = load_bibliography_csv(file_path)

        elif file_ext == ".ods":
            # Read ODS file directly to get raw data with key columns
            df = pl.read_ods(source=file_path, has_header=True)

            if df.is_empty():
                return Err(message=f"ODS file is empty: {file_path}", code=1)

            rows = df.to_dicts()

            # Load via standard loader to get parsed BibItems
            bib_result = load_bibliography_ods(file_path, bibstring_type=bibstring_type)

        else:
            return Err(message=f"Unsupported file format: {file_ext}. Use .csv or .ods", code=1)

        if isinstance(bib_result, Err):
            return bib_result

        bibliography = bib_result.out

        parsed_rows: List[OdsRowData] = []
        errors: List[str] = []

        for i, row in enumerate(rows, start=2):
            # Get bibkey from row
            bibkey_raw = str(row.get("bibkey", "")).strip()
            if not bibkey_raw:
                continue

            # Find corresponding BibItem
            if bibkey_raw not in bibliography:
                lgr.warning(f"Row {i}: bibkey '{bibkey_raw}' not found in parsed bibliography, skipping")
                continue

            bibitem = bibliography[bibkey_raw]

            # Extract explicit keys from ODS columns
            author_keys = _parse_key_list(str(row.get("author_key", "") or ""))
            editor_keys = _parse_key_list(str(row.get("editor_key", "") or ""))
            guesteditor_keys = _parse_key_list(
                str(row.get("guesteditor_key", "") or row.get("_guesteditor_key", "") or "")
            )
            journal_key = str(row.get("journal_key", "") or "").strip()
            publisher_key = str(row.get("publisher_key", "") or "").strip()
            institution_key = str(row.get("institution_key", "") or "").strip()
            school_key = str(row.get("school_key", "") or "").strip()
            series_key = str(row.get("series_key", "") or "").strip()
            person_key = str(row.get("person_key", "") or row.get("_person_key", "") or "").strip()

            # Validate key counts match entity counts
            row_errors: List[str] = []
            row_errors.extend(_validate_key_count(author_keys, bibitem.author, "author", bibkey_raw))
            row_errors.extend(_validate_key_count(editor_keys, bibitem.editor, "editor", bibkey_raw))
            row_errors.extend(_validate_key_count(guesteditor_keys, bibitem._guesteditor, "guesteditor", bibkey_raw))

            # Validate entity keys exist when entities exist
            if bibitem.journal and not journal_key:
                row_errors.append(f"[{bibkey_raw}] journal: has journal but no journal_key provided")
            if isinstance(bibitem.publisher, BibStringAttr) and bibitem.publisher.simplified and not publisher_key:
                row_errors.append(f"[{bibkey_raw}] publisher: has publisher but no publisher_key provided")
            if (
                isinstance(bibitem.institution, BibStringAttr)
                and bibitem.institution.simplified
                and not institution_key
            ):
                row_errors.append(f"[{bibkey_raw}] institution: has institution but no institution_key provided")
            if isinstance(bibitem.school, BibStringAttr) and bibitem.school.simplified and not school_key:
                row_errors.append(f"[{bibkey_raw}] school: has school but no school_key provided")
            if isinstance(bibitem.series, BaseNamedRenderable) and bibitem.series.name.simplified and not series_key:
                row_errors.append(f"[{bibkey_raw}] series: has series but no series_key provided")

            if row_errors:
                errors.extend(row_errors)
                continue

            parsed_rows.append(
                OdsRowData(
                    bibitem=bibitem,
                    bibkey_str=bibkey_raw,
                    author_keys=author_keys,
                    editor_keys=editor_keys,
                    guesteditor_keys=guesteditor_keys,
                    journal_key=journal_key,
                    publisher_key=publisher_key,
                    institution_key=institution_key,
                    school_key=school_key,
                    series_key=series_key,
                    person_key=person_key,
                )
            )

        if errors:
            error_summary = "\n".join(errors[:20])
            if len(errors) > 20:
                error_summary += f"\n... and {len(errors) - 20} more errors"
            return Err(
                message=f"Validation errors in ODS file:\n{error_summary}",
                code=1,
            )

        lgr.info(f"Parsed {len(parsed_rows)} rows from ODS file")
        return Ok(tuple(parsed_rows))

    except Exception as e:
        import traceback

        return Err(
            message=f"Failed to load ODS file: {e}",
            code=-1,
            error_type=e.__class__.__name__,
            error_trace=traceback.format_exc(),
        )


def _extract_unique_authors(
    rows: Tuple[OdsRowData, ...],
) -> Dict[str, Tuple[Author, str]]:
    """Extract unique authors with their keys.

    Returns:
        Dict mapping author_key -> (Author, role) where role is for reference
    """
    authors: Dict[str, Tuple[Author, str]] = {}

    for row in rows:
        # Authors
        for author, key in zip(row.bibitem.author, row.author_keys):
            if key and key not in authors:
                authors[key] = (author, "author")

        # Editors
        for editor, key in zip(row.bibitem.editor, row.editor_keys):
            if key and key not in authors:
                authors[key] = (editor, "editor")

        # Guest editors
        for guesteditor, key in zip(row.bibitem._guesteditor, row.guesteditor_keys):
            if key and key not in authors:
                authors[key] = (guesteditor, "guesteditor")

        # Person (treated as author entity)
        if row.person_key and isinstance(row.bibitem._person, Author):
            if row.person_key not in authors:
                authors[row.person_key] = (row.bibitem._person, "person")

    return authors


def _extract_unique_journals(rows: Tuple[OdsRowData, ...]) -> Dict[str, "Journal"]:
    """Extract unique journals with their keys."""
    journals: Dict[str, "Journal"] = {}

    for row in rows:
        if row.journal_key and row.bibitem.journal:
            if row.journal_key not in journals:
                journals[row.journal_key] = row.bibitem.journal

    return journals


def _extract_unique_publishers(rows: Tuple[OdsRowData, ...]) -> Dict[str, BibStringAttr]:
    """Extract unique publishers with their keys."""
    publishers: Dict[str, BibStringAttr] = {}

    for row in rows:
        if row.publisher_key and isinstance(row.bibitem.publisher, BibStringAttr):
            if row.publisher_key not in publishers:
                publishers[row.publisher_key] = row.bibitem.publisher

    return publishers


def _extract_unique_institutions(rows: Tuple[OdsRowData, ...]) -> Dict[str, BibStringAttr]:
    """Extract unique institutions with their keys."""
    institutions: Dict[str, BibStringAttr] = {}

    for row in rows:
        if row.institution_key and isinstance(row.bibitem.institution, BibStringAttr):
            if row.institution_key not in institutions:
                institutions[row.institution_key] = row.bibitem.institution

    return institutions


def _extract_unique_schools(rows: Tuple[OdsRowData, ...]) -> Dict[str, BibStringAttr]:
    """Extract unique schools with their keys."""
    schools: Dict[str, BibStringAttr] = {}

    for row in rows:
        if row.school_key and isinstance(row.bibitem.school, BibStringAttr):
            if row.school_key not in schools:
                schools[row.school_key] = row.bibitem.school

    return schools


def _extract_unique_series(rows: Tuple[OdsRowData, ...]) -> Dict[str, BibStringAttr]:
    """Extract unique series with their keys."""
    series_dict: Dict[str, BibStringAttr] = {}

    for row in rows:
        if row.series_key and isinstance(row.bibitem.series, BaseNamedRenderable):
            if row.series_key not in series_dict:
                series_dict[row.series_key] = row.bibitem.series.name

    return series_dict


def import_to_api(
    input_path: str,
    api_base_url: str,
    api_key: str,
    bibstring_type: TBibString = "simplified",
    dry_run: bool = False,
) -> ImportResult:
    """Import ODS or CSV bibliography data into the Rust API.

    Args:
        input_path: Path to the ODS or CSV file
        api_base_url: Base URL of the Rust API (e.g., "http://localhost:8080/api/v1")
        api_key: Admin API key for authentication
        bibstring_type: Type of bibstring to use ("simplified", "latex", "unicode")
        dry_run: If True, only validate without making API calls

    Returns:
        ImportResult with statistics and any errors
    """
    result = ImportResult()

    # Step 1: Load and parse file (auto-detects CSV or ODS)
    lgr.info(f"Loading file: {input_path}")
    parse_result = _load_and_parse_file(input_path, bibstring_type)
    if isinstance(parse_result, Err):
        result.errors.append(parse_result.message)
        return result

    rows = parse_result.out
    lgr.info(f"Loaded {len(rows)} valid rows")

    if dry_run:
        lgr.info("Dry run mode - skipping API calls")
        return result

    # Step 2: Create API client
    with ApiClient(base_url=api_base_url, api_key=api_key) as client:
        # Key -> ID mappings
        author_key_to_id: Dict[str, int] = {}
        journal_key_to_id: Dict[str, int] = {}
        publisher_key_to_id: Dict[str, int] = {}
        institution_key_to_id: Dict[str, int] = {}
        school_key_to_id: Dict[str, int] = {}
        series_key_to_id: Dict[str, int] = {}
        bibkey_to_id: Dict[str, int] = {}

        # Step 3: Create authors
        lgr.info("Creating authors...")
        unique_authors = _extract_unique_authors(rows)
        for author_key, (author, _role) in unique_authors.items():
            api_author = author_to_api(author, author_key)
            create_result = client.get_or_create_author(api_author)
            if isinstance(create_result, Ok):
                author_key_to_id[author_key] = create_result.out
                result.authors.created += 1
            else:
                if create_result.code == 409:
                    result.authors.skipped += 1
                else:
                    result.authors.failed += 1
                    result.errors.append(f"Author '{author_key}': {create_result.message}")

        lgr.info(
            f"Authors: {result.authors.created} created, {result.authors.skipped} skipped, {result.authors.failed} failed"
        )

        # Step 4: Create journals
        lgr.info("Creating journals...")
        unique_journals = _extract_unique_journals(rows)
        for journal_key, journal in unique_journals.items():
            api_journal = journal_to_api(journal, journal_key)
            create_result = client.get_or_create_journal(api_journal)
            if isinstance(create_result, Ok):
                journal_key_to_id[journal_key] = create_result.out
                result.journals.created += 1
            else:
                if create_result.code == 409:
                    result.journals.skipped += 1
                else:
                    result.journals.failed += 1
                    result.errors.append(f"Journal '{journal_key}': {create_result.message}")

        lgr.info(f"Journals: {result.journals.created} created, {result.journals.skipped} skipped")

        # Step 5: Create publishers
        lgr.info("Creating publishers...")
        unique_publishers = _extract_unique_publishers(rows)
        for publisher_key, publisher in unique_publishers.items():
            api_publisher = publisher_to_api(publisher, publisher_key)
            create_result = client.get_or_create_publisher(api_publisher)
            if isinstance(create_result, Ok):
                publisher_key_to_id[publisher_key] = create_result.out
                result.publishers.created += 1
            else:
                if create_result.code == 409:
                    result.publishers.skipped += 1
                else:
                    result.publishers.failed += 1
                    result.errors.append(f"Publisher '{publisher_key}': {create_result.message}")

        lgr.info(f"Publishers: {result.publishers.created} created, {result.publishers.skipped} skipped")

        # Step 6: Create institutions
        lgr.info("Creating institutions...")
        unique_institutions = _extract_unique_institutions(rows)
        for institution_key, institution in unique_institutions.items():
            api_institution = institution_to_api(institution, institution_key)
            create_result = client.get_or_create_institution(api_institution)
            if isinstance(create_result, Ok):
                institution_key_to_id[institution_key] = create_result.out
                result.institutions.created += 1
            else:
                if create_result.code == 409:
                    result.institutions.skipped += 1
                else:
                    result.institutions.failed += 1
                    result.errors.append(f"Institution '{institution_key}': {create_result.message}")

        # Step 7: Create schools
        lgr.info("Creating schools...")
        unique_schools = _extract_unique_schools(rows)
        for school_key, school in unique_schools.items():
            api_school = school_to_api(school, school_key)
            create_result = client.get_or_create_school(api_school)
            if isinstance(create_result, Ok):
                school_key_to_id[school_key] = create_result.out
                result.schools.created += 1
            else:
                if create_result.code == 409:
                    result.schools.skipped += 1
                else:
                    result.schools.failed += 1
                    result.errors.append(f"School '{school_key}': {create_result.message}")

        # Step 8: Create series
        lgr.info("Creating series...")
        unique_series = _extract_unique_series(rows)
        for series_key, series_name in unique_series.items():
            api_series = series_to_api(series_name, series_key)
            create_result = client.get_or_create_series(api_series)
            if isinstance(create_result, Ok):
                series_key_to_id[series_key] = create_result.out
                result.series.created += 1
            else:
                if create_result.code == 409:
                    result.series.skipped += 1
                else:
                    result.series.failed += 1
                    result.errors.append(f"Series '{series_key}': {create_result.message}")

        # Step 9: Create bibitems
        lgr.info("Creating bibitems...")
        for row in rows:
            # Convert bibitem with resolved IDs
            api_bibitem = bibitem_to_api(
                row.bibitem,
                journal_key=row.journal_key,
                publisher_key=row.publisher_key,
                institution_key=row.institution_key,
                school_key=row.school_key,
                series_key=row.series_key,
                person_key=row.person_key,
            )

            # Replace keys with IDs
            api_bibitem = attrs.evolve(
                api_bibitem,
                journal_id=journal_key_to_id.get(row.journal_key),
                publisher_id=publisher_key_to_id.get(row.publisher_key),
                institution_id=institution_key_to_id.get(row.institution_key),
                school_id=school_key_to_id.get(row.school_key),
                series_id=series_key_to_id.get(row.series_key),
                person_id=author_key_to_id.get(row.person_key),
            )

            create_result = client.get_or_create_bibitem(api_bibitem)
            if isinstance(create_result, Ok):
                bibkey_to_id[row.bibkey_str] = create_result.out
                result.bibitems.created += 1
            else:
                if create_result.code == 409:
                    result.bibitems.skipped += 1
                    # Still need to get the ID for linking authors
                    existing = client.get_bibitem_by_bibkey(row.bibkey_str)
                    if isinstance(existing, Ok):
                        id_value = existing.out.get("id")
                        if isinstance(id_value, int):
                            bibkey_to_id[row.bibkey_str] = id_value
                else:
                    result.bibitems.failed += 1
                    result.errors.append(f"BibItem '{row.bibkey_str}': {create_result.message}")

        lgr.info(
            f"BibItems: {result.bibitems.created} created, {result.bibitems.skipped} skipped, {result.bibitems.failed} failed"
        )

        # Step 10: Link authors to bibitems
        lgr.info("Linking authors to bibitems...")
        for row in rows:
            bibitem_id = bibkey_to_id.get(row.bibkey_str)
            if not bibitem_id:
                continue

            # Link authors
            for position, author_key in enumerate(row.author_keys, start=1):
                author_id = author_key_to_id.get(author_key)
                if author_id:
                    link_result = client.add_bibitem_author(bibitem_id, author_id, "author", position)
                    if isinstance(link_result, Ok):
                        result.author_links.created += 1
                    else:
                        if link_result.code == 409:
                            result.author_links.skipped += 1
                        else:
                            result.author_links.failed += 1
                            result.errors.append(
                                f"Author link [{row.bibkey_str}]->[{author_key}]: {link_result.message}"
                            )

            # Link editors
            for position, editor_key in enumerate(row.editor_keys, start=1):
                author_id = author_key_to_id.get(editor_key)
                if author_id:
                    link_result = client.add_bibitem_author(bibitem_id, author_id, "editor", position)
                    if isinstance(link_result, Ok):
                        result.author_links.created += 1
                    else:
                        if link_result.code == 409:
                            result.author_links.skipped += 1
                        else:
                            result.author_links.failed += 1

            # Link guest editors
            for position, guesteditor_key in enumerate(row.guesteditor_keys, start=1):
                author_id = author_key_to_id.get(guesteditor_key)
                if author_id:
                    link_result = client.add_bibitem_author(bibitem_id, author_id, "guesteditor", position)
                    if isinstance(link_result, Ok):
                        result.author_links.created += 1
                    else:
                        if link_result.code == 409:
                            result.author_links.skipped += 1
                        else:
                            result.author_links.failed += 1

        lgr.info(
            f"Author links: {result.author_links.created} created, {result.author_links.skipped} skipped, {result.author_links.failed} failed"
        )

    # Summary
    lgr.info("=" * 60)
    lgr.info("Import complete!")
    lgr.info(
        f"  Authors:      {result.authors.created} created, {result.authors.skipped} skipped, {result.authors.failed} failed"
    )
    lgr.info(
        f"  Journals:     {result.journals.created} created, {result.journals.skipped} skipped, {result.journals.failed} failed"
    )
    lgr.info(
        f"  Publishers:   {result.publishers.created} created, {result.publishers.skipped} skipped, {result.publishers.failed} failed"
    )
    lgr.info(
        f"  Institutions: {result.institutions.created} created, {result.institutions.skipped} skipped, {result.institutions.failed} failed"
    )
    lgr.info(
        f"  Schools:      {result.schools.created} created, {result.schools.skipped} skipped, {result.schools.failed} failed"
    )
    lgr.info(
        f"  Series:       {result.series.created} created, {result.series.skipped} skipped, {result.series.failed} failed"
    )
    lgr.info(
        f"  BibItems:     {result.bibitems.created} created, {result.bibitems.skipped} skipped, {result.bibitems.failed} failed"
    )
    lgr.info(
        f"  Author Links: {result.author_links.created} created, {result.author_links.skipped} skipped, {result.author_links.failed} failed"
    )

    if result.errors:
        lgr.warning(f"  Errors: {len(result.errors)}")
        for error in result.errors[:10]:
            lgr.warning(f"    - {error}")
        if len(result.errors) > 10:
            lgr.warning(f"    ... and {len(result.errors) - 10} more")

    return result


# Backwards compatibility alias
def import_ods_to_api(
    ods_path: str,
    api_base_url: str,
    api_key: str,
    bibstring_type: TBibString = "simplified",
    dry_run: bool = False,
) -> ImportResult:
    """Backwards compatibility alias for import_to_api."""
    return import_to_api(ods_path, api_base_url, api_key, bibstring_type, dry_run)
