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

## Functional Architecture (Hexagonal / Ports & Adapters)

This project follows hexagonal architecture principles using functional programming. The key insight: **hexagonal architecture doesn't require OOP** - function signatures serve as interfaces.

### Core Principles

1. **Business logic doesn't depend on I/O details**
2. **Dependencies point inward** - concrete implementations depend on abstract interfaces
3. **Ports define what you need** - type aliases for function signatures
4. **Adapters provide how** - concrete implementations matching those signatures

### Defining Ports (Abstract Interfaces)

Use type aliases to define the "shape" of functions your core logic needs:

```python
from typing import Callable, Generator

# Port: what the core logic needs (abstract)
type TContentReader[ReaderIn] = Callable[[ReaderIn], Generator[Content, None, None]]
type TContentWriter[WriterIn] = Callable[[Generator[Content, None, None], WriterIn], None]
type TTransform = Callable[[str], str]
```

The type signature **is** the contract. Any function matching that signature can be injected.

### Implementing Adapters (Concrete Implementations)

Create concrete functions that satisfy the port signatures:

```python
# Adapter: filesystem implementation
def filesystem_content_reader(input_dirname: str) -> Generator[Content, None, None]:
    for file_name in os.listdir(input_dirname):
        yield read_file(os.path.join(input_dirname, file_name))

# Adapter: database implementation (alternative)
def database_content_reader(connection_string: str) -> Generator[Content, None, None]:
    # ... database-specific logic
```

### Abstract Process Functions

Write core logic that accepts injected functions:

```python
def abstract_process[I, O](
    content_reader: TContentReader[I],
    reader_input: I,
    transform: TTransform,
    content_writer: TContentWriter[O],
    writer_input: O,
) -> None:
    """Core business logic - knows nothing about filesystems, databases, etc."""
    raw_content = content_reader(reader_input)
    processed = (transform(item) for item in raw_content)
    content_writer(processed, writer_input)
```

### Wiring: Injecting Dependencies

Create concrete entry points that wire everything together:

```python
def main_filesystem(input_dir: str, output_dir: str) -> None:
    """Concrete implementation using filesystem adapters."""
    abstract_process(
        content_reader=filesystem_content_reader,
        reader_input=input_dir,
        transform=my_transform_function,
        content_writer=filesystem_content_writer,
        writer_input=output_dir,
    )
```

### Benefits Over OOP-Style Dependency Injection

| Aspect | FP Style | OOP Style |
|--------|----------|-----------|
| Interface definition | Type alias | Abstract class/Protocol |
| Boilerplate | Minimal | Class definitions, `__init__`, etc. |
| Testing | Pass mock functions directly | Mock objects, DI frameworks |
| Composition | Natural function composition | Decorator pattern, etc. |
| State | Explicit (parameters) | Hidden in `self` |

### When to Use This Pattern

Use functional hexagonal architecture when:

- Processing pipelines (read → transform → write)
- Multiple I/O backends are possible (filesystem, database, API)
- Business logic should be testable in isolation
- You want to swap implementations without changing core logic

### Example: Complete Module Structure

```python
# types.py - Port definitions
type TFixFootnotes = Callable[[str], str]
type TRemoveReferences = Callable[[str], str]
type TContentReader[In] = Callable[[In], Generator[Content, None, None]]
type TContentWriter[Out] = Callable[[Generator[Content, None, None], Out], None]

# core.py - Abstract process (pure business logic)
def postprocess_html(
    content: str,
    fix_footnotes: TFixFootnotes,
    remove_references: TRemoveReferences,
) -> str:
    return remove_references(fix_footnotes(content))

def abstract_process[I, O](...) -> None:
    # Orchestration logic

# adapters/filesystem.py - Filesystem adapter
def filesystem_reader(dirname: str) -> Generator[Content, None, None]: ...
def filesystem_writer(contents: Generator[Content, None, None], dirname: str) -> None: ...

# adapters/transforms.py - Transform implementations
def bs4_fix_footnotes(content: str) -> str: ...
def bs4_remove_references(content: str) -> str: ...

# main.py - Wiring
def main_bs4_filesystem(input_dir: str, output_dir: str) -> None:
    abstract_process(
        content_reader=filesystem_reader,
        reader_input=input_dir,
        fix_footnotes=bs4_fix_footnotes,
        remove_references=bs4_remove_references,
        content_writer=filesystem_writer,
        writer_input=output_dir,
    )
```

## Code Organization

### Module Structure

- **Types/Ports**: Type aliases defining function signatures (interfaces)
- **Core**: Abstract process functions that accept injected dependencies
- **Adapters**: Concrete implementations for I/O and transformations
- **Main/Wiring**: Entry points that wire adapters into core logic
- **Models**: Define data structures using `attrs.define(frozen=True, slots=True)`
- **No classes** except for simple data containers and index structures

### Function Design

Functions should be:

- **Pure** when possible (no side effects)
- **Small and focused** (single responsibility)
- **Composable** (easy to combine with other functions)
- **Injectable** (accept dependencies as parameters rather than importing them)

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
