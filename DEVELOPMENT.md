# Development Guide

This guide explains how to set up a development environment, run tests, and contribute to the Work Log Synchronizer project.

## Development Setup

### Prerequisites

- Python 3.13+
- Git
- curl (for installing uv)

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd work-log-synchronizer
```

2. Install uv (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install dependencies:

```bash
uv sync --all-extras
```

This installs both regular and development dependencies.

## Running Tests

### Run All Tests

```bash
uv run pytest
```

### Run Tests with Coverage

```bash
uv run pytest --cov=src/work_log_sync --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Run Tests for Specific Module

```bash
# Test storage module
uv run pytest tests/test_storage.py

# Test configuration module
uv run pytest tests/test_config.py

# Test a specific test class
uv run pytest tests/test_storage.py::TestStorageManager

# Run a specific test
uv run pytest tests/test_storage.py::TestStorageManager::test_init_creates_directory
```

### Run Tests in Watch Mode

```bash
uv run pytest-watch  # If installed
```

Or use pytest with autoreload:

```bash
uv run pytest --looponfail
```

## Code Quality Checks

### Linting with Ruff

```bash
# Check for linting issues
uv run ruff check src/ tests/

# Fix auto-fixable issues
uv run ruff check --fix src/ tests/
```

### Code Formatting with Ruff

```bash
# Check formatting
uv run ruff format --check src/ tests/

# Format code
uv run ruff format src/ tests/
```

### Type Checking with mypy

```bash
# Type check the source code
uv run mypy src/
```

### All Checks at Once

Create a shell script or use a pre-commit hook:

```bash
#!/bin/bash
set -e

echo "Running ruff check..."
uv run ruff check src/ tests/

echo "Running ruff format check..."
uv run ruff format --check src/ tests/

echo "Running mypy..."
uv run mypy src/

echo "Running tests..."
uv run pytest

echo "All checks passed!"
```

## Project Structure Explanation

```
src/work_log_sync/
├── __init__.py              # Package initialization
├── cli.py                   # CLI interface (entry point)
├── config.py                # Configuration management
│
├── clockify/                # Clockify API integration
│   ├── __init__.py
│   ├── client.py            # ClockifyClient class
│   └── models.py            # Pydantic models for Clockify
│
├── bamboohr/                # BambooHR API integration
│   ├── __init__.py
│   ├── client.py            # BambooHRClient class
│   └── models.py            # Pydantic models for BambooHR
│
├── sync/                    # Synchronization logic
│   ├── __init__.py
│   ├── engine.py            # SyncEngine class
│   └── mapper.py            # TaskMapper for interactive mapping
│
└── utils/                   # Utility modules
    ├── __init__.py
    ├── logging.py           # Logging configuration
    └── storage.py           # StorageManager for persistence
```

## Key Classes and Their Responsibilities

### CLI Layer
- **cli.py**: Typer-based CLI, handles user commands

### API Clients
- **ClockifyClient**: Handles all Clockify API operations
- **BambooHRClient**: Handles all BambooHR API operations

### Data Models
- **Clockify models**: ClockifyProject, ClockifyTask, ClockifyTimeEntry
- **BambooHR models**: BambooProject, BambooTask, BambooTimeEntry, BambooEmployee

### Business Logic
- **SyncEngine**: Orchestrates the sync process, coordinates between clients
- **TaskMapper**: Handles interactive prompting and mapping persistence

### Infrastructure
- **StorageManager**: Manages file persistence (config, state, tokens)
- **Config**: Wrapper around StorageManager for mapping-specific operations
- **logging**: Sets up file and console logging

## Adding a New Feature

### Example: Add Support for Custom Date Formats

1. **Update the CLI** (cli.py):

```python
@app.command()
def sync(
    from_date: Optional[str] = typer.Option(
        None,
        "--from-date",
        help="Start date (supports YYYY-MM-DD or MM/DD/YYYY)",
    ),
    # ... rest of options
):
    """Parse date with multiple format support."""
    parsed_date = parse_flexible_date(from_date)
```

2. **Add utility function** (utils/):

```python
# In utils/dates.py
def parse_flexible_date(date_str: str) -> date:
    """Parse date from multiple formats."""
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")
```

3. **Add tests** (tests/test_dates.py):

```python
def test_parse_flexible_date_iso():
    result = parse_flexible_date("2024-01-15")
    assert result == date(2024, 1, 15)

def test_parse_flexible_date_us():
    result = parse_flexible_date("01/15/2024")
    assert result == date(2024, 1, 15)
```

## Testing Strategy

### Unit Tests
- Test individual functions and classes in isolation
- Use mocks for external dependencies (APIs)
- Located in `tests/` directory

### Integration Tests
- Test interactions between components
- Can use real or mocked APIs
- Currently focused on core sync logic

### Fixtures (conftest.py)
- Provide common test data
- Include sample models for Clockify and BambooHR
- Provide temporary storage for testing

### Coverage Goals
- Aim for 80%+ code coverage
- Focus on critical paths (sync logic, error handling)
- Less critical: CLI formatting, basic utilities

## Common Development Tasks

### Adding API Support

1. Create new client in `src/work_log_sync/new_service/`:
   - `client.py`: API client implementation
   - `models.py`: Pydantic models for responses

2. Create tests in `tests/test_new_service_client.py`

3. Integrate with sync engine if needed

### Adding Configuration Options

1. Update `Config` class in `config.py`
2. Add to `mapping.yaml` example in `examples/`
3. Update README with new option
4. Add tests in `tests/test_config.py`

### Modifying Sync Logic

1. Update `SyncEngine` in `sync/engine.py`
2. Update `SyncResult` if needed for new metrics
3. Add tests in `tests/test_sync_engine.py`
4. Test with `--dry-run` before committing

## Debugging

### Enable Debug Logging

```bash
uv run work-log-sync sync --verbose
```

This outputs detailed logs to console and file.

### Check Stored State

```bash
# View current mappings
cat ~/.work-log-sync/mapping.yaml

# View sync state
cat ~/.work-log-sync/state.json

# View logs
tail -f ~/.work-log-sync/work-log-sync.log
```

### Use Python Debugger

```python
# Add to code
import pdb; pdb.set_trace()

# Or use breakpoint()
breakpoint()

# Run with pytest
uv run pytest --pdb
```

### Mock API Responses

In tests, use `unittest.mock`:

```python
from unittest.mock import MagicMock

mock_client = MagicMock()
mock_client.get_time_entries.return_value = [sample_entry]
```

## Performance Optimization

### Profiling

```bash
# Install profiler
uv pip install py-spy

# Profile sync command
py-spy record -o profile.svg -- uv run work-log-sync sync
```

### Caching

The tool already implements:
- Token caching to avoid repeated logins
- Last sync date to avoid re-syncing old entries
- Duplicate detection to prevent redundant API calls

## Documentation

### Update README for new features

When adding features, update:
- README.md: Add to Features and Usage sections
- examples/USAGE_EXAMPLES.md: Add usage example
- examples/mapping.yaml: Add mapping example if applicable
- DEVELOPMENT.md: Update if affecting development

### Code Documentation

Use docstrings for classes and functions:

```python
def sync(self, from_date: Optional[date] = None) -> SyncResult:
    """Synchronize work logs from Clockify to BambooHR.

    Args:
        from_date: Start date for sync (uses last sync date if not provided).

    Returns:
        Sync results with counts and errors.

    Raises:
        ValueError: If credentials are missing.
    """
```

## Pre-commit Hooks (Optional)

Set up pre-commit to run checks automatically:

1. Install pre-commit:

```bash
uv pip install pre-commit
```

2. Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML, types-python-dateutil]
```

3. Install hooks:

```bash
pre-commit install
```

## Releasing

When ready to release a new version:

1. Update version in `src/work_log_sync/__init__.py`
2. Update version in `pyproject.toml`
3. Commit changes
4. Create git tag: `git tag v0.2.0`
5. Push: `git push origin main --tags`
6. GitHub Actions builds and tests automatically

## Troubleshooting Development Issues

### Import errors

```bash
# Reinstall package in development mode
uv sync --all-extras

# Or
uv pip install -e .
```

### Test failures

1. Check the error message carefully
2. Run with `--verbose` flag: `uv run pytest -v`
3. Check test fixtures are correctly set up
4. Verify mocks return expected values

### Type checking errors

```bash
# Show detailed type errors
uv run mypy src/ --show-error-codes

# Ignore specific errors if justified
# Add type: ignore comments sparingly
```

## Resources

- [Python 3.13 Documentation](https://docs.python.org/3.13/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
