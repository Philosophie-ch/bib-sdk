#!/usr/bin/env python
"""Quick throwaway script to merge fuzzy match results with full bibliography data.

Usage:
    python merge_fuzzy_results.py <bibliography_path> <original_staged_csv> <fuzzy_results_path> <output_path>
"""

import sys
import csv
from pathlib import Path

# Add parent directories to path so we can import from philoch_bib_sdk
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aletk.ResultMonad import Err
from philoch_bib_sdk.adapters.io.ods import load_bibliography_ods
from philoch_bib_sdk.logic.models import BibStringAttr

if len(sys.argv) != 5:
    print(
        "Usage: python merge_fuzzy_results.py <bibliography_path> <original_staged_csv> <fuzzy_results_path> <output_path>"
    )
    sys.exit(1)

bibliography_path = sys.argv[1]
original_staged_path = sys.argv[2]
fuzzy_results_path = sys.argv[3]
output_path = sys.argv[4]

print(f"Loading bibliography from: {bibliography_path}")
print(f"Loading original staged CSV from: {original_staged_path}")
print(f"Loading fuzzy results from: {fuzzy_results_path}")
print(f"Will write output to: {output_path}")

# Step 1: Load bibliography into a dict keyed by bibkey
print("\n[1/3] Loading bibliography...")
result = load_bibliography_ods(bibliography_path)
if isinstance(result, Err):
    print(f"ERROR: {result.message}")
    sys.exit(1)

bibliography_dict = result.out
print(f"      Loaded {len(bibliography_dict)} bibliography entries")

# Convert BibItems to simple citation format
bibliography_plaintext = {}
for bibkey, bibitem in bibliography_dict.items():
    # Build simple citation: Author (Date). Title. Journal(Volume): Number, Pages. Publisher.
    parts = []

    # Helper to get string from BibStringAttr
    def get_str(attr: BibStringAttr | str | None) -> str:
        if isinstance(attr, BibStringAttr):
            return attr.simplified
        return str(attr) if attr else ""

    # Author (Date) - include both family and given names
    author_str = ""
    if bibitem.author:
        author_names = []
        for auth in bibitem.author:
            family = get_str(auth.family_name)
            given = get_str(auth.given_name)
            if family and given:
                author_names.append(f"{family}, {given}")
            elif family:
                author_names.append(family)
        author_str = " and ".join(author_names) if author_names else ""

    date_str = ""
    if bibitem.date != "no date" and hasattr(bibitem.date, "year"):
        date_str = str(bibitem.date.year)

    if author_str and date_str:
        parts.append(f"{author_str} ({date_str})")
    elif author_str:
        parts.append(author_str)
    elif date_str:
        parts.append(f"({date_str})")

    # Title
    title_str = get_str(bibitem.title)
    if title_str:
        parts.append(title_str)

    # Journal(Volume): Number, Pages
    journal_part = []
    if bibitem.journal:
        journal_str = get_str(bibitem.journal.name)
        if bibitem.volume:
            journal_str += f"({bibitem.volume})"
        if bibitem.number:
            journal_str += f": {bibitem.number}"
        if journal_str:
            journal_part.append(journal_str)

    if bibitem.pages:
        page_parts = []
        for page in bibitem.pages:
            if page.start and page.end:
                page_parts.append(f"{page.start}--{page.end}")
            elif page.start:
                page_parts.append(page.start)
        if page_parts:
            journal_part.append(", ".join(page_parts))

    if journal_part:
        parts.append(", ".join(journal_part))

    # Publisher
    publisher_str = get_str(bibitem.publisher)
    if publisher_str:
        parts.append(publisher_str)

    bibliography_plaintext[bibkey] = ". ".join(parts) + "." if parts else ""

# Step 2: Load original staged CSV to get context column
print("\n[2/4] Loading original staged CSV for context...")
original_context_map = {}  # Map (title, author) -> context
with open(original_staged_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        title = row.get('title', '').strip()
        author = row.get('author', '').strip()
        context = row.get('context', '').strip()
        # Use title+author as key (first occurrence wins if duplicates)
        key = (title, author)
        if key not in original_context_map:
            original_context_map[key] = context

print(f"      Loaded {len(original_context_map)} context mappings")

# Step 3: Load fuzzy results
print("\n[3/4] Processing fuzzy match results...")
fuzzy_rows = []
with open(fuzzy_results_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames) if reader.fieldnames else []
    for row in reader:
        fuzzy_rows.append(row)

print(f"      Loaded {len(fuzzy_rows)} fuzzy match results")

# Step 4: Merge - add context + reorder columns with matches grouped
print("\n[4/4] Merging and writing output...")

# Reorder: context, bibkey, entry_type, author, title, date, journal, volume, number, pages, doi, url, publisher,
# then match_1_bibkey, match_1_score, match_1_full_entry, match_2_bibkey, match_2_score, match_2_full_entry, etc.
# then candidates_searched, search_time_ms
base_fields = [
    "context",
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

match_fields = []
for i in range(1, 6):
    match_fields.extend([f"match_{i}_bibkey", f"match_{i}_score", f"match_{i}_full_entry"])

end_fields = ["candidates_searched", "search_time_ms"]

output_fieldnames = base_fields + match_fields + end_fields

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=output_fieldnames)
    writer.writeheader()

    for row in fuzzy_rows:
        # Look up context from original CSV by title+author
        title = row.get('title', '').strip()
        author = row.get('author', '').strip()
        key = (title, author)
        context = original_context_map.get(key, "")
        row['context'] = context

        # Look up each match bibkey in bibliography and add full entry
        for i in range(1, 6):
            match_bibkey = row.get(f"match_{i}_bibkey", "").strip()
            if match_bibkey and match_bibkey in bibliography_plaintext:
                row[f"match_{i}_full_entry"] = bibliography_plaintext[match_bibkey]
            else:
                row[f"match_{i}_full_entry"] = ""

        writer.writerow(row)

print(f"      ✓ Written {len(fuzzy_rows)} rows to {output_path}")
print("\nDone! You can now open the CSV and visually inspect the matches.")
