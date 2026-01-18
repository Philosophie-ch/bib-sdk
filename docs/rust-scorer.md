# Rust Scorer

## Quick Start

```bash
# Build
cd philoch_bib_sdk/rust_scorer
cargo lint                    # Verify code quality
maturin build --release -o ./dist

# Install
pip install ./dist/rust_scorer-*.whl --force-reinstall

# Verify
python -c "import rust_scorer; print(rust_scorer.token_sort_ratio('hello', 'hello'))"
```

## Usage

```python
from philoch_bib_sdk.logic.functions.fuzzy_matcher import stage_bibitems_batch

# Auto-uses Rust if available
staged = stage_bibitems_batch(subjects, index, top_n=5)

# Force Rust or Python
staged = stage_bibitems_batch(subjects, index, use_rust=True)   # Rust
staged = stage_bibitems_batch(subjects, index, use_rust=False)  # Python
```

---

## Performance

| Dataset | Python | Rust | Speedup |
|---------|--------|------|---------|
| 5 subjects vs 209K | 40s | 3s | 12x |
| 2,238 subjects (dialectica) | ~5 hours | ~24 min | 12x |

## What It Does

The Rust scorer replaces the Python scoring loop that was the bottleneck:

```
Python path (slow):
  stage_bibitems_batch → stage_bibitem → find_similar_bibitems
    → compare_bibitems_detailed (per candidate)
      → fuzzywuzzy.token_sort_ratio × 3 fields × thousands of candidates

Rust path (fast):
  stage_bibitems_batch → rust_scorer.score_batch()
    → parallel scoring via rayon
    → returns top-N matches directly
```

## Files

```
philoch_bib_sdk/rust_scorer/
├── Cargo.toml           # Dependencies: pyo3, rayon, strsim
├── .cargo/config.toml   # Lint aliases (cargo lint, cargo test-all)
└── src/lib.rs           # Implementation
    ├── token_sort_ratio()   # Jaro-Winkler string similarity
    ├── score_batch()        # Parallel batch scoring
    ├── score_title()        # Title scoring with bonuses
    ├── score_author()       # Author scoring
    ├── score_date()         # Date scoring
    └── score_bonus()        # DOI, journal, pages, publisher
```

## Scoring Logic

Same as Python implementation:

| Component | Weight | Bonus |
|-----------|--------|-------|
| Title | 0.5 | +100 if >85% match or containment |
| Author | 0.3 | +100 if >85% match |
| Date | 0.1 | 100 (exact) → 30 (same decade) → 0 |
| Bonus | 0.1 | DOI +100, Journal+Vol+Num +50, Pages +20, Publisher +10 |

## Development

```bash
cd philoch_bib_sdk/rust_scorer

# Run lints (clippy with strict type safety)
cargo lint

# Run tests
cargo test-all

# Build for development
maturin develop --release
```

## Tests

6 Rust-specific tests in `tests/logic/functions/test_fuzzy_matcher.py`:
- `test_rust_scorer_available`
- `test_rust_batch_scorer_basic`
- `test_stage_bibitems_batch_rust_integration`
- `test_stage_bibitems_batch_rust_vs_python_consistency`
- `test_rust_scorer_performance`
