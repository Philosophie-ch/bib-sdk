# Rust Index Building Specification

## Overview

This document specifies the Rust implementation for the performance-critical `build_index()` function, which creates multi-index structures for fuzzy matching of bibliographic items.

## Performance Problem

The current Python implementation takes 40+ minutes to build an index for 209K bibliographic items due to:
- 9.8M trigram extraction and insertion operations (209K items × ~47 trigrams each)
- Python's slow string allocations and set operations at this scale
- Inefficient memory layout and poor cache locality

**Target**: Reduce index building time from 40+ minutes to 10-30 seconds using Rust.

## Architecture

### Integration Strategy

- **Core bottleneck only**: Only the `build_index()` function will be implemented in Rust
- **Rest stays Python**: All other code (parsing, comparison, scoring, IO) remains in Python
- **PyO3 bindings**: Expose Rust functions to Python via PyO3
- **Maturin build**: Use maturin for building and packaging
- **PyPI compatible**: Ensure wheel distribution works for PyPI

### Project Structure

```
bib-sdk/
├── pyproject.toml           # Add maturin build-backend
├── Cargo.toml                # New: Rust project config
├── src/                      # New: Rust source code
│   └── lib.rs                # PyO3 bindings
├── philoch_bib_sdk/
│   └── logic/
│       └── functions/
│           └── fuzzy_matcher.py  # Modified: use Rust when available
└── docs/
    └── rust-index-building-spec.md  # This file
```

## Python API (Current)

### Function Signature

```python
def build_index(bibitems: Sequence[BibItem]) -> BibItemBlockIndex:
    """Build multi-index structure for fast fuzzy matching."""
    ...
```

### Input: `BibItem` Structure

```python
@dataclass
class BibItem:
    bibkey: str
    title: BibStringAttr | str
    author: Tuple[Author, ...]
    date: str
    journal: Journal | None
    doi: str
    # ... other fields
```

### Output: `BibItemBlockIndex` Structure

```python
@dataclass
class BibItemBlockIndex:
    doi_index: Dict[str, BibItem]              # DOI -> BibItem
    title_trigrams: Dict[str, FrozenSet[BibItem]]  # trigram -> items
    author_surnames: Dict[str, FrozenSet[BibItem]] # surname -> items
    year_decades: Dict[int | None, FrozenSet[BibItem]]  # decade -> items
    journals: Dict[str, FrozenSet[BibItem]]    # journal -> items
    all_items: Tuple[BibItem, ...]             # all items
```

## Rust Implementation Strategy

### Data Serialization Approach

Since BibItem is a complex Python object, we'll use a lightweight serialization approach:

1. **Extract minimal data in Python** before calling Rust
2. **Pass simple data structures** to Rust (strings, integers)
3. **Return index mappings** from Rust as simple dictionaries
4. **Reconstruct BibItemBlockIndex** in Python using original BibItem objects

### Simplified Rust API

```rust
use pyo3::prelude::*;
use std::collections::{HashMap, HashSet};

#[pyfunction]
fn build_index_rust(
    items_data: Vec<ItemData>,
) -> PyResult<IndexData> {
    // Build indexes in Rust, return lightweight mappings
}

#[derive(FromPyObject)]
struct ItemData {
    item_index: usize,           // Index in original Python list
    doi: Option<String>,
    title: String,
    author_surnames: Vec<String>,
    year: Option<i32>,
    journal_name: Option<String>,
}

#[derive(IntoPyObject)]
struct IndexData {
    doi_to_index: HashMap<String, usize>,
    trigram_to_indices: HashMap<String, Vec<usize>>,
    surname_to_indices: HashMap<String, Vec<usize>>,
    decade_to_indices: HashMap<Option<i32>, Vec<usize>>,
    journal_to_indices: HashMap<String, Vec<usize>>,
}
```

### Python Wrapper

```python
def build_index(bibitems: Sequence[BibItem]) -> BibItemBlockIndex:
    """Build multi-index structure for fast fuzzy matching.

    Uses Rust implementation when available, falls back to Python.
    """
    try:
        from philoch_bib_sdk._rust import build_index_rust
        use_rust = True
    except ImportError:
        use_rust = False

    items_tuple = tuple(bibitems)

    if use_rust:
        # Extract minimal data for Rust
        items_data = [
            {
                "item_index": i,
                "doi": item.doi if item.doi else None,
                "title": _get_title_str(item.title),
                "author_surnames": _extract_author_surnames(item.author),
                "year": _parse_year(item.date),
                "journal_name": _get_journal_name(item.journal),
            }
            for i, item in enumerate(items_tuple)
        ]

        # Call Rust
        index_data = build_index_rust(items_data)

        # Reconstruct Python objects
        return _reconstruct_index(index_data, items_tuple)
    else:
        # Fallback to pure Python implementation
        return _build_index_python(items_tuple)
```

## Performance Optimizations

### Rust-Specific Optimizations

1. **Efficient string handling**: Use `&str` slices where possible
2. **Pre-allocated collections**: Reserve capacity for HashMaps/HashSets
3. **Parallel processing**: Use rayon for parallel trigram extraction
4. **String interning**: Reuse common trigrams to reduce allocations

### Expected Improvements

- **String allocations**: Rust's zero-copy string slices vs Python's string objects
- **Set operations**: Rust's HashSet with efficient hashing vs Python's set
- **Memory layout**: Contiguous memory with better cache locality
- **Parallelization**: Optional rayon-based parallel processing

## Build Configuration

### pyproject.toml

```toml
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "philoch-bib-sdk"
requires-python = ">=3.11"
# ... existing config ...

[tool.maturin]
features = ["pyo3/extension-module"]
```

### Cargo.toml

```toml
[package]
name = "philoch_bib_sdk"
version = "0.1.6"
edition = "2021"

[lib]
name = "philoch_bib_sdk._rust"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
rayon = "1.8"  # Optional: for parallel processing
ahash = "0.8"   # Faster hashing than std

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
```

## Development Workflow

### Initial Setup

```bash
# Install maturin
pip install maturin

# Initialize Rust in existing project
maturin init --bindings pyo3

# Build and install in development mode
maturin develop --release
```

### Testing

```bash
# Test with Rust implementation
maturin develop --release
poetry run pytest tests/logic/functions/test_fuzzy_matcher.py -v

# Test fallback to Python (rename Rust module temporarily)
poetry run pytest tests/logic/functions/test_fuzzy_matcher.py -v
```

### Benchmarking

```python
import time
from philoch_bib_sdk.adapters.io.ods import load_bibliography_ods

result = load_bibliography_ods("data/biblio/biblio-v8-table.ods")
bibliography = result.out

start = time.time()
index = build_index(list(bibliography.values()))
elapsed = time.time() - start

print(f"Built index for {len(bibliography)} items in {elapsed:.2f}s")
print(f"Title trigrams: {len(index.title_trigrams)}")
```

## Migration Path

### Phase 1: Implement Core

1. Create basic Rust implementation of trigram extraction
2. Create PyO3 bindings for data passing
3. Implement Python wrapper with fallback

### Phase 2: Optimize

1. Add parallel processing with rayon
2. Optimize string handling and memory allocations
3. Benchmark and profile

### Phase 3: Production

1. Test with full 209K dataset
2. Verify correctness matches Python implementation
3. Update documentation
4. Release to PyPI with platform-specific wheels

## Testing Strategy

### Correctness Tests

- Verify Rust output matches Python output exactly for small datasets (100 items)
- Compare index sizes (number of trigrams, surnames, etc.)
- Verify all lookups return same results

### Performance Tests

- Benchmark with 1K, 10K, 100K, 209K items
- Measure memory usage
- Profile Rust code to identify any remaining bottlenecks

### Fallback Tests

- Verify pure Python fallback works when Rust not available
- Test on systems without Rust toolchain

## Deployment

### Building Wheels

```bash
# Build for current platform
maturin build --release

# Build for multiple platforms (requires CI/CD)
maturin build --release --target x86_64-unknown-linux-gnu
maturin build --release --target x86_64-apple-darwin
maturin build --release --target aarch64-apple-darwin
```

### PyPI Distribution

- Publish platform-specific wheels (Linux, macOS, Windows)
- Include source distribution for systems with Rust toolchain
- Pure Python fallback ensures compatibility everywhere

## References

- PyO3 documentation: https://pyo3.rs/
- Maturin documentation: https://www.maturin.rs/
- rayon (parallel processing): https://docs.rs/rayon/
- ahash (fast hashing): https://docs.rs/ahash/
