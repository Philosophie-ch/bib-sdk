# Python Style Guide

This document describes the Python coding standards and practices for this project.

## Type Safety

This project enforces strict type safety using mypy with the `--strict` flag.

### Requirements

- All functions must have complete type annotations for parameters and return values
- No use of `Any` type
- No use of `cast()` calls
- No use of `# type: ignore` comments
- All type errors must be resolved properly through type narrowing or proper type design

### Type Narrowing

When dealing with union types, use explicit type checking:

```python
from philoch_bib_sdk.logic.models import BibStringAttr

title_attr = bibitem.title
if isinstance(title_attr, BibStringAttr):
    title = title_attr.simplified  # Type narrowed, safe to access
```

### Preserve Type Safety - Never Convert to Dicts

**CRITICAL**: Do not convert typed objects to dictionaries to access attributes. This loses all type safety.

```python
# NEVER DO THIS - loses type safety
data = bibitem.model_dump()  # or __dict__ or dict(bibitem)
title = data.get("title", "")  # Type checker cannot verify this

# ALWAYS DO THIS - preserves type safety
title_attr = bibitem.title
if isinstance(title_attr, BibStringAttr):
    title = title_attr.simplified
else:
    title = ""
```

Reasons:
- Dictionary access bypasses type checking completely
- Typos in keys are not caught by mypy
- Attribute renames do not update dictionary keys automatically
- Type narrowing is lost, leading to runtime errors

Always access attributes directly and use isinstance() for type narrowing.

### Forward References

Use `TYPE_CHECKING` for imports that are only needed for type annotations to avoid circular imports:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from philoch_bib_sdk.logic.models import Author
```

## Data Structures and Performance

### Immutability

Prefer immutable data structures:

- Use `Tuple` over `List` for sequences that do not need mutation
- Use `FrozenSet` over `Set` for immutable unique collections
- All attrs classes use `frozen=True` for immutability and `slots=True` for memory efficiency

### Performance Optimization

The following patterns are preferred for performance:

1. **Prefer tuples over lists** for immutable sequences
   ```python
   items = tuple(process(x) for x in source)  # Preferred
   items = [process(x) for x in source]       # Avoid
   ```

2. **Prefer comprehensions over explicit loops**
   ```python
   # Preferred
   results = {key: frozenset(items) for key, items in mapping.items()}

   # Avoid
   results = {}
   for key, items in mapping.items():
       results[key] = frozenset(items)
   ```

3. **Prefer generators over lists** when iteration is one-time
   ```python
   # Preferred - memory efficient
   scored = (score(item) for item in candidates)

   # Avoid - loads everything into memory
   scored = [score(item) for item in candidates]
   ```

4. **Use set operations** for collection operations
   ```python
   # Preferred
   candidates.update(index[key])

   # Avoid
   for item in index[key]:
       candidates.add(item)
   ```

5. **Avoid nested loops** - use comprehensions or functional operations
   ```python
   # Preferred - flat comprehension
   trigrams = frozenset(
       text[i:i+3]
       for i in range(len(text) - 2)
   )

   # Avoid - nested loop
   trigrams = set()
   for i in range(len(text) - 2):
       trigrams.add(text[i:i+3])
   ```

### Leveraging cytoolz

The project includes `cytoolz` as a dependency for high-performance functional operations:

```python
from cytoolz import topk

# Efficient heap-based top-N selection
top_results = topk(n, items, key=lambda x: x.score)
```

## Code Organization

### Module Structure

- **Models**: Define data structures using `attrs.define(frozen=True, slots=True)`
- **Functions**: Pure functions that transform data
- **No classes** except for simple data containers and index structures

### Function Design

Functions should be:

- **Pure** when possible (no side effects)
- **Small and focused** (single responsibility)
- **Composable** (easy to combine with other functions)

### Imports

Group imports in the following order:

1. Standard library imports
2. Third-party library imports
3. Local application imports

Within each group, sort alphabetically.

## Testing

### Test Requirements

- All new functionality must have corresponding tests
- Tests must pass with `pytest`
- Test coverage should be comprehensive
- Tests should be deterministic and fast

### Test Structure

```python
def test_feature_description() -> None:
    """Brief description of what is being tested."""
    # Arrange
    input_data = create_test_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_value
```

### Parametrized Tests

Use `pytest.mark.parametrize` for testing multiple cases:

```python
@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (case1_input, case1_output),
        (case2_input, case2_output),
    ],
)
def test_multiple_cases(input_value: str, expected_output: str) -> None:
    assert transform(input_value) == expected_output
```

## Documentation

### Docstrings

All public functions and classes must have docstrings following this format:

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Brief one-line description.

    Longer description if needed, explaining the purpose and behavior.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Description of return value
    """
```

### Comments

- Use comments sparingly - prefer self-documenting code
- Explain **why**, not **what** (the code shows what)
- Update comments when code changes

## Formatting

### General Style

- Follow PEP 8 conventions
- Line length: 88 characters (Black default)
- Use double quotes for strings
- Use trailing commas in multi-line structures

### Function Signatures

For functions with many parameters, format each parameter on its own line:

```python
def complex_function(
    parameter1: Type1,
    parameter2: Type2,
    parameter3: Type3 = default_value,
) -> ReturnType:
    pass
```

## Error Handling

### Type-Safe Error Handling

Handle expected errors explicitly:

```python
# Check conditions and return early
if not valid_input(data):
    return default_value

# Use isinstance for type narrowing
if isinstance(value, ExpectedType):
    process(value)
```

### Avoid Bare Except

Always catch specific exceptions:

```python
# Preferred
try:
    risky_operation()
except ValueError as e:
    handle_value_error(e)

# Avoid
try:
    risky_operation()
except:
    pass
```

## Version Control

### Commit Messages

Follow conventional commits format:

```
type(scope): brief description

Longer explanation if needed.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

## Tools

### Required Tools

- `mypy` - Type checking with `--strict` mode
- `pytest` - Testing framework
- `poetry` - Dependency management and packaging

### Running Checks

```bash
# Type checking
poetry run mypy .

# Run tests
poetry run pytest

# Run specific test file
poetry run pytest tests/path/to/test_file.py -v
```

## Summary

This project prioritizes:

1. **Type safety** - Strict mypy compliance without escape hatches
2. **Performance** - Immutable data structures, comprehensions, generators
3. **Readability** - Clear, functional code without nested loops
4. **Testability** - Comprehensive test coverage with fast, deterministic tests

When in doubt, consult existing code in the project for examples of these patterns in practice.
