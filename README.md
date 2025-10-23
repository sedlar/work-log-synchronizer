# Work Log Synchronizer

A command-line tool to synchronize work logs from Clockify to BambooHR timesheets.

## Features

- **Automatic Synchronization**: Sync your Clockify time entries to BambooHR timesheets
- **Smart Mapping**: Interactively map Clockify projects/tasks to BambooHR projects/tasks
- **Duplicate Detection**: Prevents duplicate entries when running multiple times
- **Dry-Run Mode**: Preview changes before applying them
- **Persistent Configuration**: YAML-based mapping configuration that persists across runs
- **Detailed Logging**: Comprehensive logging to file and console
- **Easy Setup**: Interactive configuration wizard

## Requirements

- Python 3.13+
- Clockify API key
- BambooHR API key and subdomain

## Installation

### From source

```bash
git clone <repository-url>
cd work-log-synchronizer
uv sync
```

### Install the CLI

```bash
uv pip install -e .
```

## Quick Start

### 1. Initial Configuration

Run the configuration wizard to set up your Clockify and BambooHR credentials:

```bash
uv run work-log-sync configure
```

This will:
- Prompt for your Clockify API key
- Prompt for your BambooHR API key and subdomain
- Test the connections
- Save credentials to `~/.work-log-sync/tokens.json`

### 2. Sync Work Logs

Synchronize work logs from Clockify to BambooHR:

```bash
uv run work-log-sync sync
```

**Options:**
- `--from-date YYYY-MM-DD`: Start date for sync (default: last sync date or 30 days ago)
- `--to-date YYYY-MM-DD`: End date for sync (default: today)
- `--dry-run`: Show what would be synced without creating entries
- `--no-interactive`: Don't prompt for unmapped entries
- `--verbose`: Enable debug logging

**Examples:**

```bash
# Sync from specific date range
uv run work-log-sync sync --from-date 2024-01-01 --to-date 2024-01-31

# Preview changes without applying them
uv run work-log-sync sync --dry-run

# Sync without interactive prompts
uv run work-log-sync sync --no-interactive
```

### 3. View Mappings

View your current project/task mappings:

```bash
uv run work-log-sync mapping
```

## Configuration

Configuration is stored in `~/.work-log-sync/`:

- **mapping.yaml**: Project/task mappings
- **state.json**: Sync state and history
- **tokens.json**: Cached API credentials (restricted permissions)
- **work-log-sync.log**: Log file with sync history

### Mapping Configuration

The `mapping.yaml` file stores the mapping between Clockify and BambooHR projects/tasks:

```yaml
projects:
  "My Project:Development":
    bamboo_project_id: "1"
    bamboo_task_id: "101"
  "My Project:Support":
    skip: true
```

**Fields:**
- `bamboo_project_id`: BambooHR project ID to sync to
- `bamboo_task_id`: BambooHR task ID within that project
- `skip`: Set to `true` to ignore this Clockify entry (not synced)

### Interactive Mapping

When you run sync with unmapped entries, you'll be prompted to:

1. Select a BambooHR project from the available list
2. Select a task within that project
3. Or choose to skip the entry entirely

Your selection is automatically saved to `mapping.yaml`.

## Development

### Running Tests

```bash
uv run pytest
```

Run with coverage report:

```bash
uv run pytest --cov=src/work_log_sync --cov-report=html
```

### Code Quality

Run linting and type checking:

```bash
# Lint code
uv run ruff check src/ tests/

# Format code
uv run ruff format src/ tests/

# Type check
uv run mypy src/
```

### Project Structure

```
work-log-synchronizer/
├── src/work_log_sync/
│   ├── cli.py              # CLI interface (Typer)
│   ├── config.py           # Configuration management
│   ├── clockify/           # Clockify API client
│   ├── bamboohr/           # BambooHR API client
│   ├── sync/               # Synchronization engine
│   └── utils/              # Utilities (storage, logging)
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
└── README.md
```

## Architecture

### Components

1. **CLI (cli.py)**: Typer-based command-line interface
2. **API Clients**:
   - `ClockifyClient`: Handles Clockify API communication
   - `BambooHRClient`: Handles BambooHR API communication
3. **Sync Engine**: Core synchronization logic
   - `SyncEngine`: Orchestrates the sync process
   - `TaskMapper`: Interactive mapping management
4. **Configuration**:
   - `Config`: Configuration management
   - `StorageManager`: Persistent storage for state and tokens

### Sync Flow

1. Load configuration and API credentials
2. Fetch Clockify time entries for date range
3. For each entry:
   - Check if project/task is mapped
   - If unmapped and interactive, prompt user for mapping
   - Check for duplicates in BambooHR
   - Create entry in BambooHR (or dry-run)
4. Update last sync date
5. Log results and summary

## API Credentials

### Clockify API Key

1. Go to [Clockify Settings](https://app.clockify.me/user/settings)
2. Click on "API" in the left sidebar
3. Copy your API key

### BambooHR API Key

1. Go to BambooHR Settings (as admin)
2. Navigate to "API Keys"
3. Create or copy your API key
4. Note your subdomain (from URL: `https://yourcompany.bamboohr.com`)

## Troubleshooting

### "API key not found"

Ensure you've run `work-log-sync configure` and your credentials are saved correctly.

### Duplicate entries

The tool detects duplicates by checking date, project, task, and hours. If you're still seeing duplicates, check that the mappings are consistent.

### No entries synced

- Verify your date range with `--from-date` and `--to-date`
- Check that your Clockify entries have projects assigned
- Use `--verbose` flag to see detailed logs

### Mapping not being saved

Ensure `~/.work-log-sync/` directory is writable and has sufficient permissions (755).

## Logs

Logs are stored in `~/.work-log-sync/work-log-sync.log`:

```bash
# View recent logs
tail -f ~/.work-log-sync/work-log-sync.log
```

## Contributing

When contributing, please:

1. Run the test suite: `uv run pytest`
2. Check code quality: `uv run ruff check` and `uv run mypy`
3. Format code: `uv run ruff format`

## License

MIT
