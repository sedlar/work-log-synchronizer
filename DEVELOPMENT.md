# Development Guide

This guide explains how to set up a development environment, run tests, and contribute to the Clockify Export project.

## Development Setup

### Prerequisites

- Python 3.13+
- Git
- [uv](https://docs.astral.sh/uv/) package manager

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
uv run pytest --cov=src/clockify_export --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Run Tests for Specific Module

```bash
# Test export engine
uv run pytest tests/test_export.py

# Test configuration module
uv run pytest tests/test_config.py

# Run a specific test class
uv run pytest tests/test_storage.py::TestStorageManager

# Run a specific test
uv run pytest tests/test_export.py::test_merge_adjacent_entries
```

## Code Quality

The project uses a Makefile for all code quality commands.

### Individual Checks

```bash
make lint     # Ruff lint check
make format   # Ruff format check
make mypy     # Type checking
make test     # Tests with coverage
```

### All Checks at Once

```bash
make check    # Runs lint, format, mypy, and test
```

### Auto-fix

```bash
make fix      # Auto-fix lint issues and reformat code
```

## Project Structure

```
src/clockify_export/
├── __init__.py              # Package version
├── cli.py                   # Click-based CLI (setup, init-mapping, export)
├── config.py                # MappingConfig for project/task mappings
├── bamboo_data.py           # Parser for BambooHR js-timesheet-data.json
├── export.py                # Export engine (timezone, merging, overlaps)
├── mapper.py                # Interactive mapping prompts
│
├── clockify/                # Clockify API integration
│   ├── __init__.py
│   ├── client.py            # ClockifyClient (httpx, pagination, retry)
│   └── models.py            # Pydantic models for API responses
│
└── utils/                   # Utility modules
    ├── __init__.py
    ├── logging.py           # Logging configuration
    └── storage.py           # StorageManager for YAML persistence
```

Additionally, `bamboo-import.user.js` in the project root is the Tampermonkey userscript for importing into BambooHR.

## Key Classes

### CLI Layer
- **cli.py**: Click-based CLI with three commands: `setup`, `init-mapping`, `export`

### API Client
- **ClockifyClient**: HTTP client for the Clockify API using httpx, with pagination and retry

### Data Models
- **Clockify models**: `ClockifyProject`, `ClockifyTask`, `ClockifyTimeEntry` (Pydantic)

### Export Logic
- **ExportEntry**: Dataclass representing a single BambooHR-ready time entry
- **build_export()**: Converts Clockify entries to export entries (timezone conversion, merging, overlap detection)
- **generate_json()**: Produces the final JSON payload for the userscript

### Mapping
- **MappingConfig**: Reads/writes YAML mapping between Clockify and BambooHR project/task IDs
- **run_mapping_flow()**: Interactive CLI flow for building mappings

### Infrastructure
- **StorageManager**: Manages YAML config files in `~/.config/clockify-export/`

## Test Suite

| File | Covers |
|------|--------|
| `test_export.py` | Export engine: timezone conversion, merging, overlap detection |
| `test_bamboo_data.py` | BambooHR timesheet data parser |
| `test_config.py` | MappingConfig read/write/find |
| `test_models.py` | Pydantic model validation |
| `test_storage.py` | StorageManager YAML persistence |
| `test_mapper.py` | Interactive mapping flow |
| `conftest.py` | Shared fixtures (temp dirs, sample Clockify objects) |

## Common Development Tasks

### Adding Configuration Options

1. Update `MappingConfig` in `config.py`
2. Update `StorageManager` in `utils/storage.py` if needed
3. Add tests
4. Update README with the new option

### Modifying Export Logic

1. Update `build_export()` or `ExportEntry` in `export.py`
2. Update `generate_json()` if the output format changes
3. Add tests in `tests/test_export.py`
4. Test with a real export: `clockify-export export --from ... --to ...`

### Adding CLI Commands

1. Add the command in `cli.py` using `@cli.command()`
2. Follow the existing Click patterns for options and error handling
3. Update README CLI Reference section

## Debugging

### Check Stored Config

```bash
# View current config
cat ~/.config/clockify-export/config.yaml

# View mappings
cat ~/.config/clockify-export/mapping.yaml

# View logs
tail -f ~/.config/clockify-export/clockify-export.log
```

### Use Python Debugger

```bash
# Run with pytest debugger on failure
uv run pytest --pdb
```

## Resources

- [Click Documentation](https://click.palletsprojects.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [httpx Documentation](https://www.python-httpx.org/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
