#!/usr/bin/env python
"""Run fuzzy matching with streaming CSV output for real-time progress monitoring."""

from __future__ import annotations

import csv
import time
from typing import TYPE_CHECKING

from aletk.ResultMonad import Err
from philoch_bib_sdk.adapters.io.csv import load_staged_csv_allow_empty_bibkeys
from philoch_bib_sdk.adapters.io.ods import load_bibliography_ods
from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_formatter import format_bibkey
from philoch_bib_sdk.logic.functions.fuzzy_matcher import (
    build_index,
    stage_bibitems_streaming,
)
from philoch_bib_sdk.logic.models import BibStringAttr

if TYPE_CHECKING:
    from philoch_bib_sdk.logic.models import BibItem

print("=" * 80)
print("FUZZY MATCHING (STREAMING): STAGING ITEMS AGAINST FULL BIBLIOGRAPHY")
print("=" * 80)

# Paths
bibliography_path = "/home/alebg/philosophie-ch/Dropbox/philosophie-ch/biblio/biblio-v8-table.ods"
staging_path = "/home/alebg/philosophie-ch/Dropbox/philosophie-ch/biblio/biblio-training/out.csv"
output_path = "/home/alebg/philosophie-ch/Dropbox/philosophie-ch/biblio/biblio-training/out-match-streaming.csv"

# 1. Load bibliography
print(f"\n[1/4] Loading bibliography from ODS...")
print(f"      {bibliography_path}")
start_total = time.time()
start = time.time()

result = load_bibliography_ods(bibliography_path)
if isinstance(result, Err):
    print(f"ERROR: {result.message}")
    exit(1)

bibliography = result.out
elapsed = time.time() - start
print(f"      ✓ Loaded {len(bibliography):,} items in {elapsed:.2f}s")

# 2. Load staging items
print(f"\n[2/4] Loading staging items from CSV...")
print(f"      {staging_path}")
start = time.time()

staging_result = load_staged_csv_allow_empty_bibkeys(staging_path)
if isinstance(staging_result, Err):
    print(f"ERROR: {staging_result.message}")
    exit(1)

staging_items = staging_result.out
elapsed = time.time() - start
print(f"      ✓ Loaded {len(staging_items):,} staging items in {elapsed:.2f}s")

# 3. Build index
print(f"\n[3/4] Building fuzzy matching index...")
print(f"      (This is the Rust-accelerated step)")
start = time.time()

index = build_index(list(bibliography.values()))
elapsed = time.time() - start
print(f"      ✓ Built index in {elapsed:.2f}s")
print(f"        - DOI index: {len(index.doi_index):,} entries")
print(f"        - Title trigrams: {len(index.title_trigrams):,} unique")
print(f"        - Author surnames: {len(index.author_surnames):,} unique")
print(f"        - Year decades: {len(index.year_decades):,} unique")
print(f"        - Journals: {len(index.journals):,} unique")


def extract_bibitem_fields(bibitem: BibItem) -> dict[str, str]:
    """Extract all fields from BibItem for CSV output.

    Args:
        bibitem: BibItem to extract fields from

    Returns:
        Dictionary mapping column names to string values
    """

    def get_string_attr(attr: BibStringAttr | str | None) -> str:
        """Get string from BibStringAttr or plain string.

        Args:
            attr: BibStringAttr, plain string, or None

        Returns:
            Simplified string if BibStringAttr, string representation otherwise
        """
        if isinstance(attr, BibStringAttr):
            return attr.simplified
        return str(attr) if attr else ""

    # Format authors
    authors: list[str] = []
    for author in bibitem.author:
        given = get_string_attr(author.given_name)
        family = get_string_attr(author.family_name)
        mononym = get_string_attr(author.mononym)

        if mononym:
            authors.append(mononym)
        elif given and family:
            authors.append(f"{family}, {given}")
        elif family:
            authors.append(family)
        elif given:
            authors.append(given)

    author_str = " and ".join(authors)

    # Format journal - check if journal exists first
    journal_name = ""
    if bibitem.journal:
        journal_name = get_string_attr(bibitem.journal.name)

    # Volume and number are attributes of BibItem, not Journal
    journal_volume = bibitem.volume or ""
    journal_number = bibitem.number or ""

    # Format date - check type first
    date_str = ""
    if bibitem.date != "no date":
        # bibitem.date is BibItemDateAttr, has year attribute
        date_str = str(bibitem.date.year)

    # Format pages - PageAttr only has start and end attributes, not page
    pages_str = ""
    if bibitem.pages:
        page_parts: list[str] = []
        for page in bibitem.pages:
            # PageAttr only has start and end, no page attribute
            if page.start and page.end:
                page_parts.append(f"{page.start}--{page.end}")
            elif page.start:
                # Only start page, no end
                page_parts.append(page.start)
        pages_str = ", ".join(page_parts)

    # Format bibkey
    bibkey_str = ""
    if bibitem.bibkey:
        bibkey_str = format_bibkey(bibitem.bibkey)

    # Format publisher
    publisher_str = ""
    publisher_attr = bibitem.publisher
    if isinstance(publisher_attr, BibStringAttr):
        publisher_str = publisher_attr.simplified

    return {
        "bibkey": bibkey_str,
        "entry_type": bibitem.entry_type,
        "author": author_str,
        "title": get_string_attr(bibitem.title),
        "date": date_str,
        "journal": journal_name,
        "volume": journal_volume,
        "number": journal_number,
        "pages": pages_str,
        "doi": bibitem.doi or "",
        "url": bibitem.url or "",
        "publisher": publisher_str,
    }


# 4. Run fuzzy matching with streaming output
print(f"\n[4/4] Running fuzzy matching with streaming CSV output...")
print(f"      Output: {output_path}")
print(f"      Processing {len(staging_items)} items...")
print(f"      (Results written in real-time as they're generated)")
print()

start_matching = time.time()

# Define columns
base_columns = [
    "bibkey",
    "entry_type",
    "author",
    "title",
    "date",
    "journal",
    "volume",
    "number",
    "pages",
    "doi",
    "url",
    "publisher",
]

match_columns = [
    "match_1_bibkey",
    "match_1_score",
    "match_2_bibkey",
    "match_2_score",
    "match_3_bibkey",
    "match_3_score",
    "match_4_bibkey",
    "match_4_score",
    "match_5_bibkey",
    "match_5_score",
    "candidates_searched",
    "search_time_ms",
]

all_columns = base_columns + match_columns

# Open CSV and write results as they stream in
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=all_columns)
    writer.writeheader()
    f.flush()  # Flush header immediately

    # Track timing
    item_times: list[float] = []
    processed = 0
    total = len(staging_items)

    # Stream results
    for staged_item in stage_bibitems_streaming(staging_items, index, top_n=5, min_score=50):
        # Record timing
        item_start = time.time()

        # Get base fields from original bibitem
        row = extract_bibitem_fields(staged_item.bibitem)

        # Add match scores
        for i in range(1, 6):
            if i <= len(staged_item.top_matches):
                match = staged_item.top_matches[i - 1]
                row[f"match_{i}_bibkey"] = match.bibkey
                row[f"match_{i}_score"] = f"{match.total_score:.1f}"
            else:
                row[f"match_{i}_bibkey"] = ""
                row[f"match_{i}_score"] = ""

        # Add search metadata
        row["candidates_searched"] = str(staged_item.search_metadata.get("candidates_searched", ""))
        row["search_time_ms"] = str(staged_item.search_metadata.get("search_time_ms", ""))

        # Write row and flush immediately for real-time visibility
        writer.writerow(row)
        f.flush()

        # Update timing
        item_times.append(time.time() - item_start)
        processed += 1

        # Calculate ETA
        avg = sum(item_times) / len(item_times)
        remaining = total - processed
        eta = (remaining * avg) / 60  # in minutes

        # Progress indicator (overwrites previous line)
        print(f"[{processed}/{total}] Avg: {avg:.1f}s/item | ETA: {eta:.1f}min", end="\r")

    print()  # New line after progress indicator

elapsed = time.time() - start_matching
print(f"\n      ✓ Matched and wrote {processed} items in {elapsed:.2f}s")
print(f"        Average: {elapsed/processed:.1f}s per item")

# Summary
total_elapsed = time.time() - start_total
print("\n" + "=" * 80)
print("SUCCESS!")
print("=" * 80)
print(f"\nTotal time: {total_elapsed:.2f}s ({total_elapsed/60:.2f} minutes)")
print(f"\nOutput file: {output_path}")
print(f"  - {processed} staged items matched")
print(f"  - Results streamed to CSV in real-time")
print(f"  - Up to 5 matches per item (score >= 50)")

print("\n" + "=" * 80)
