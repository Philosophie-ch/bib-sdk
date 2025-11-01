# TODO: Enhanced Fuzzy Matching Output

## Overview

Currently, fuzzy matching workflow requires a manual post-processing step to enrich the output CSV with human-readable citations and preserve metadata from the original staged CSV.

## Current Workflow

1. Run fuzzy matching (streaming or batch mode)
2. Get basic output: `out-match-streaming.csv` with match bibkeys and scores
3. **Manual step**: Run `merge_fuzzy_results.py` to:
   - Add `context` column from original staged CSV
   - Add full citation strings for each match (with author names, titles, etc.)
   - Reorder columns for better readability

## Problem

The manual post-processing step (`merge_fuzzy_results.py`) is cumbersome:
- Requires running a separate script with 4 arguments
- User must track multiple file paths
- Easy to forget or make mistakes with paths
- Not integrated into the main SDK workflow

## Proposed Solution

Integrate the enhanced output functionality directly into the SDK's fuzzy matching procedures.

### Option A: Extend Existing Procedures

Modify `fuzzy_match_procedure()` to:
1. Accept optional `include_full_citations: bool = True` parameter
2. Accept optional `preserve_metadata: bool = True` parameter
3. When enabled, automatically:
   - Load original staged CSV to extract metadata (context, etc.)
   - Generate full citation strings for all matches
   - Reorder output columns for readability
   - Output enhanced CSV directly

**Benefits:**
- No breaking changes (new parameters are optional)
- Single command execution
- No manual path tracking

**Implementation:**
```python
@try_except_wrapper(logger)
def fuzzy_match_procedure(
    bibliography_path: str,
    staged_path: str,
    output_path: str,
    load_bibliography: LoadBibliographyFn,
    load_staged: LoadStagedFn,
    write_report: WriteReportFn,
    top_n: int = 5,
    min_score: float = 0.0,
    include_full_citations: bool = True,  # NEW
    preserve_metadata: bool = True,        # NEW
) -> None:
    # ... existing logic ...

    if include_full_citations:
        # Generate citation formatter
        citation_formatter = create_citation_formatter(bibliography)

        # Enhance staged items with full citations
        for item in staged_with_matches:
            for match in item.top_matches:
                match.full_citation = citation_formatter(match.bibkey)

    if preserve_metadata:
        # Re-read original CSV to extract metadata
        original_metadata = load_csv_metadata(staged_path)

        # Merge metadata back into results
        for item in staged_with_matches:
            item.metadata = original_metadata.get(item.key)

    # Write enhanced output
    write_report(output_path, staged_with_matches)
```

### Option B: Create New Enhanced Procedure

Create `fuzzy_match_enhanced_procedure()` as a higher-level wrapper:

```python
@try_except_wrapper(logger)
def fuzzy_match_enhanced_procedure(
    bibliography_path: str,
    original_staged_csv_path: str,  # For metadata extraction
    fuzzy_output_path: str,
    enhanced_output_path: str,
    **fuzzy_match_kwargs
) -> None:
    """Run fuzzy matching + post-processing in one step."""

    # Step 1: Run standard fuzzy matching
    fuzzy_match_procedure(
        bibliography_path=bibliography_path,
        staged_path=original_staged_csv_path,
        output_path=fuzzy_output_path,
        **fuzzy_match_kwargs
    )

    # Step 2: Enhance output automatically
    enhance_fuzzy_output(
        bibliography_path=bibliography_path,
        original_csv_path=original_staged_csv_path,
        fuzzy_results_path=fuzzy_output_path,
        output_path=enhanced_output_path
    )
```

**Benefits:**
- Clear separation of concerns
- Backward compatible (existing procedure unchanged)
- Easy to maintain

## Citation Formatting Requirements

The enhanced output must include full citations formatted as:

**Format:**
```
Author1, FirstName1 and Author2, FirstName2 (Year). Title. Journal(Volume): Number, Pages. Publisher.
```

**Examples:**
- Single author: `Bagley, Benjamin (2019). (The Varieties of) Love in Contemporary Anglophone Philosophy. 453--464.`
- Multiple authors: `Aalders, H.~Wzn.~G.J.D. and De Blois, L. (1992). Plutarch und die politische Philosophie der Griechen.`

## Metadata Preservation

Must preserve all metadata columns from original staged CSV:
- `context` - Source document (e.g., "imaguire.docx", "blumson-joaquin.bib")
- Any other custom columns added by preprocessing tools

## Output Column Order

Enhanced CSV must have columns in this order:

1. Metadata columns (context, etc.)
2. Staged item fields: `bibkey, entry_type, author, title, date, journal, volume, number, pages, doi, url, publisher`
3. Match groups (repeated 5x): `match_N_bibkey, match_N_score, match_N_full_entry`
4. Summary stats: `candidates_searched, search_time_ms`

## Implementation Details

### Citation Formatter

Create `philoch_bib_sdk/converters/plaintext/bibitem/citation_formatter.py`:

```python
def format_citation(bibitem: BibItem) -> str:
    """Format BibItem as a human-readable citation string.

    Returns formatted string like:
        "Author, First (2020). Title. Journal(45): 2, 123-145. Publisher."
    """
    # Implementation from merge_fuzzy_results.py
    pass
```

### Metadata Extractor

Create `philoch_bib_sdk/adapters/io/csv/metadata.py`:

```python
def extract_csv_metadata(
    csv_path: str,
    key_fields: tuple[str, ...] = ("title", "author")
) -> dict[tuple[str, ...], dict[str, str]]:
    """Extract metadata from CSV, keyed by specified fields.

    Returns mapping from (title, author) -> {metadata columns}
    """
    pass
```

### Enhanced Write Report Function

Extend CSV writer to support:
- Custom column ordering
- Additional metadata columns
- Full citation strings in match results

## Testing Requirements

1. Unit tests for `format_citation()`
2. Integration test: fuzzy match → enhanced output
3. Verify column ordering
4. Verify metadata preservation
5. Verify multi-author citation formatting
6. Verify backward compatibility (existing code still works)

## Migration Path

1. Implement citation formatter and metadata extractor
2. Update `write_report` functions to support enhanced mode
3. Update CLI interface to expose new options
4. Update `run_fuzzy_matching_streaming.py` to use enhanced output
5. Deprecate standalone `merge_fuzzy_results.py` script
6. Update documentation

## Reference Implementation

See `docs/todo/merge_fuzzy_results.py` for current working implementation that should be integrated into the SDK.

## Priority

**Medium-High** - This significantly improves UX for fuzzy matching workflow, reducing manual steps and potential errors.

## Estimated Effort

- Citation formatter: 2 hours
- Metadata extractor: 2 hours
- Enhanced write functions: 3 hours
- CLI integration: 2 hours
- Testing: 3 hours
- Documentation: 2 hours

**Total: ~14 hours**
