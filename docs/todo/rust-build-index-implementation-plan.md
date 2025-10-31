# Rust build_index Implementation Plan

## Objective

Replace the Python `build_index()` function with a Rust implementation to reduce index building time from 40+ minutes to 10-30 seconds for 209K bibliographic items.

## Background

Current bottleneck: Building fuzzy matching indexes for 209K items requires ~9.8M trigram operations, which is too slow in Python. Rust implementation will provide 100-300x speedup while maintaining identical API and fallback compatibility.

## Prerequisites

- Rust toolchain installed (rustc, cargo)
- maturin installed: `pip install maturin`
- Understanding of PyO3 bindings
- Reference: [docs/rust-index-building-spec.md](../rust-index-building-spec.md)

## Implementation Phases

### Phase 1: Project Setup and Infrastructure

**Goal**: Set up Rust project structure integrated with existing Python codebase.

**Tasks**:

1. **Initialize Rust project structure**
   - Create `Cargo.toml` with PyO3 dependencies
   - Create `src/lib.rs` for PyO3 module
   - Configure as cdylib crate type

2. **Update pyproject.toml**
   - Add maturin as build-backend
   - Configure maturin build settings
   - Ensure Python 3.11+ requirement maintained

3. **Verify basic integration**
   - Create minimal PyO3 function (e.g., `hello_rust()`)
   - Build with `maturin develop`
   - Import and test from Python

**Acceptance Criteria**:
- `maturin develop` builds successfully
- Can import `from philoch_bib_sdk._rust import hello_rust`
- No conflicts with existing Poetry setup

**Estimated Time**: 1-2 hours

---

### Phase 2: Data Structures and Serialization

**Goal**: Define Rust data structures for efficient index building and Python interop.

**Tasks**:

1. **Define Rust input structure**
   ```rust
   #[derive(FromPyObject)]
   struct ItemData {
       item_index: usize,
       doi: Option<String>,
       title: String,
       author_surnames: Vec<String>,
       year: Option<i32>,
       journal_name: Option<String>,
   }
   ```

2. **Define Rust output structure**
   ```rust
   #[pyclass]
   struct IndexData {
       doi_to_index: HashMap<String, usize>,
       trigram_to_indices: HashMap<String, Vec<usize>>,
       surname_to_indices: HashMap<String, Vec<usize>>,
       decade_to_indices: HashMap<Option<i32>, Vec<usize>>,
       journal_to_indices: HashMap<String, Vec<usize>>,
   }
   ```

3. **Implement helper functions**
   - Trigram extraction: `fn extract_trigrams(text: &str) -> HashSet<String>`
   - Decade calculation: `fn get_decade(year: Option<i32>) -> Option<i32>`
   - Text normalization helpers

**Acceptance Criteria**:
- Data structures compile without errors
- Can serialize/deserialize between Python and Rust
- Helper functions have unit tests in Rust

**Estimated Time**: 2-3 hours

---

### Phase 3: Core Index Building Logic

**Goal**: Implement the core index building algorithm in Rust.

**Tasks**:

1. **Implement single-pass index builder**
   ```rust
   #[pyfunction]
   fn build_index_rust(items_data: Vec<ItemData>) -> PyResult<IndexData> {
       // Pre-allocate HashMaps with capacity
       // Single pass over items building all indexes
       // Return IndexData
   }
   ```

2. **Optimize for performance**
   - Use `ahash::AHashMap` instead of `std::HashMap`
   - Pre-allocate collections with capacity hints
   - Use string slices (`&str`) where possible
   - Avoid unnecessary clones

3. **Add basic error handling**
   - Handle empty inputs gracefully
   - Return PyErr for exceptional cases
   - Log progress for debugging (optional)

**Acceptance Criteria**:
- `build_index_rust()` compiles and runs
- Produces correct index mappings for small test dataset (100 items)
- No panics or crashes on edge cases (empty strings, missing fields)

**Estimated Time**: 3-4 hours

---

### Phase 4: Python Integration Layer

**Goal**: Create Python wrapper that uses Rust when available, falls back to Python.

**Tasks**:

1. **Create data extraction helpers in Python**
   ```python
   def _prepare_items_for_rust(bibitems: Sequence[BibItem]) -> list[dict]:
       """Extract minimal data needed by Rust."""
       return [
           {
               "item_index": i,
               "doi": item.doi if item.doi else None,
               "title": _get_title_str(item.title),
               "author_surnames": _extract_author_surnames(item.author),
               "year": _parse_year(item.date),
               "journal_name": _get_journal_name(item.journal),
           }
           for i, item in enumerate(bibitems)
       ]
   ```

2. **Implement index reconstruction**
   ```python
   def _reconstruct_index(
       index_data: Any,  # Rust IndexData
       items: Tuple[BibItem, ...]
   ) -> BibItemBlockIndex:
       """Reconstruct BibItemBlockIndex from Rust output."""
       # Convert index -> BibItem using items tuple
       # Build doi_index, title_trigrams, etc.
       # Return BibItemBlockIndex
   ```

3. **Update main build_index() function**
   ```python
   def build_index(bibitems: Sequence[BibItem]) -> BibItemBlockIndex:
       try:
           from philoch_bib_sdk._rust import build_index_rust
           use_rust = True
       except ImportError:
           use_rust = False

       items_tuple = tuple(bibitems)

       if use_rust:
           items_data = _prepare_items_for_rust(items_tuple)
           index_data = build_index_rust(items_data)
           return _reconstruct_index(index_data, items_tuple)
       else:
           return _build_index_python(items_tuple)
   ```

4. **Rename existing implementation**
   - Rename current `build_index()` → `_build_index_python()`
   - Ensure it remains available as fallback

**Acceptance Criteria**:
- Can call `build_index()` with Rust available
- Can call `build_index()` with Rust unavailable (import error)
- Both paths produce identical results for same input
- All existing tests pass without modification

**Estimated Time**: 2-3 hours

---

### Phase 5: Testing and Validation

**Goal**: Ensure correctness and performance of Rust implementation.

**Tasks**:

1. **Correctness testing**
   - Test with 100-item dataset: compare Rust vs Python output
   - Verify all indexes have same number of entries
   - Verify lookups return identical items
   - Test edge cases: empty fields, special characters, Unicode

2. **Performance benchmarking**
   - Benchmark with 1K items
   - Benchmark with 10K items
   - Benchmark with 100K items
   - Benchmark with 209K items (full dataset)
   - Record times for Python vs Rust

3. **Integration testing**
   - Run full fuzzy matching workflow with Rust index
   - Verify staging CSV processing works end-to-end
   - Test fallback path by temporarily hiding Rust module

4. **Add Rust unit tests**
   ```rust
   #[cfg(test)]
   mod tests {
       #[test]
       fn test_extract_trigrams() { ... }

       #[test]
       fn test_build_index_small_dataset() { ... }
   }
   ```

**Acceptance Criteria**:
- All Python tests pass: `poetry run pytest tests/logic/functions/test_fuzzy_matcher.py -v`
- Rust unit tests pass: `cargo test`
- Performance improvement: 209K items in under 30 seconds
- Correctness: Rust and Python produce identical indexes

**Estimated Time**: 3-4 hours

---

### Phase 6: Optimization (Optional)

**Goal**: Further optimize if initial performance targets not met.

**Tasks**:

1. **Profile Rust code**
   - Use `cargo flamegraph` or `perf` to identify bottlenecks
   - Check for unnecessary allocations
   - Verify hash function performance

2. **Parallel processing with rayon**
   ```rust
   use rayon::prelude::*;

   items_data.par_iter().for_each(|item| {
       // Extract trigrams in parallel
   });
   ```

3. **String interning**
   - Reuse common trigrams to reduce allocations
   - Use `Rc<str>` or string interning crate

4. **Memory layout optimization**
   - Consider struct packing
   - Use references instead of clones where possible

**Acceptance Criteria**:
- Performance meets target: <30 seconds for 209K items
- Memory usage reasonable (not exceeding Python version significantly)

**Estimated Time**: 2-4 hours (only if needed)

---

### Phase 7: CI/CD and Distribution

**Goal**: Enable building and distributing platform-specific wheels.

**Tasks**:

1. **Update GitHub Actions workflow**
   ```yaml
   - name: Build wheels
     uses: PyO3/maturin-action@v1
     with:
       command: build
       args: --release --out dist
       manylinux: auto
   ```

2. **Test wheel building locally**
   ```bash
   maturin build --release
   pip install target/wheels/philoch_bib_sdk-*.whl
   ```

3. **Configure platform matrix**
   - Linux (x86_64, aarch64)
   - macOS (x86_64, arm64)
   - Windows (x86_64)

4. **Test source distribution**
   ```bash
   maturin sdist
   pip install target/dist/philoch_bib_sdk-*.tar.gz
   ```

5. **Update documentation**
   - Add section to README about Rust acceleration
   - Note that Rust is optional (pure Python fallback)
   - Document development setup with maturin

**Acceptance Criteria**:
- CI/CD builds wheels for all target platforms
- Wheels install and work on target platforms
- Source distribution builds successfully with Rust toolchain
- Pure Python fallback works when Rust not available

**Estimated Time**: 2-3 hours

---

### Phase 8: Documentation and Release

**Goal**: Document implementation and prepare for release.

**Tasks**:

1. **Update technical documentation**
   - Document Rust module API in `docs/fuzzy-matching.md`
   - Add performance benchmarks to docs
   - Document fallback behavior

2. **Update README**
   - Add note about optional Rust acceleration
   - Installation instructions remain same (`pip install philoch-bib-sdk`)
   - Development setup with maturin

3. **Update CHANGELOG**
   - Add entry for Rust performance improvements
   - Note compatibility (no breaking changes)

4. **Version bump**
   - Increment version (e.g., 0.1.6 → 0.2.0)
   - Update version in pyproject.toml and Cargo.toml

5. **Test release process**
   - Build wheels: `maturin build --release`
   - Test PyPI upload (test.pypi.org first)
   - Verify installation from TestPyPI

**Acceptance Criteria**:
- Documentation updated and accurate
- Version bumped appropriately
- Test release successful on TestPyPI
- Ready for production PyPI release

**Estimated Time**: 2-3 hours

---

## Risk Mitigation

### Risk: Performance targets not met

**Mitigation**:
- Start with benchmarking at Phase 5
- If <30s not achieved, proceed to Phase 6 optimizations
- Worst case: Pure Python fallback ensures functionality

### Risk: Platform compatibility issues

**Mitigation**:
- Test on all target platforms early (Phase 7)
- Maintain pure Python fallback for unsupported platforms
- Use manylinux for maximum Linux compatibility

### Risk: Breaking existing functionality

**Mitigation**:
- All existing tests must pass without modification
- Side-by-side testing of Rust vs Python output (Phase 5)
- Gradual rollout: can disable Rust in production if issues arise

### Risk: Build complexity for contributors

**Mitigation**:
- Pure Python development still works (fallback)
- Document maturin setup clearly
- Provide pre-built wheels so most users don't need Rust

---

## Success Metrics

- **Performance**: Index building for 209K items in <30 seconds (vs 40+ minutes)
- **Correctness**: 100% test pass rate, identical output to Python
- **Compatibility**: Works on Linux, macOS, Windows (x86_64 minimum)
- **Developer Experience**: No changes required to calling code
- **User Experience**: `pip install` works seamlessly

---

## Timeline Estimate

**Minimum (straight path)**: 15-20 hours
**Realistic (with debugging)**: 20-25 hours
**With optimizations**: 25-30 hours

**Suggested schedule**:
- Day 1: Phases 1-3 (setup, data structures, core logic)
- Day 2: Phases 4-5 (integration, testing)
- Day 3: Phases 6-8 (optimization, CI/CD, docs)

---

## References

- [Rust Index Building Specification](../rust-index-building-spec.md)
- [Fuzzy Matching Documentation](../fuzzy-matching.md)
- PyO3 Documentation: https://pyo3.rs/
- Maturin Documentation: https://www.maturin.rs/
- Project: `/home/alebg/philosophie-ch/bibliography/bib-sdk`

---

## Notes

- Keep pure Python implementation as `_build_index_python()` for fallback and testing
- No changes to public API - transparent acceleration
- Can be rolled back by removing Rust import if issues arise
- Consider this a performance optimization, not a rewrite
