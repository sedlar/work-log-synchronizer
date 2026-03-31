# Clockify Export

A two-part tool for getting Clockify time entries into BambooHR timesheets:

1. **Python CLI** (`clockify-export`) — fetches Clockify entries, maps projects/tasks to BambooHR IDs, and outputs BambooHR-ready JSON.
2. **Tampermonkey userscript** (`bamboo-import.user.js`) — runs on the BambooHR timesheet page to import the JSON, leveraging the user's existing browser session.

This split avoids all BambooHR authentication complexity — Python handles API logic and data mapping, the browser script handles the import.

## Features

- **Clockify API Integration**: Fetches time entries with pagination and retry logic
- **Interactive Mapping**: Map Clockify projects/tasks to BambooHR project/task IDs
- **Timezone Conversion**: Converts UTC Clockify entries to your workspace timezone
- **Adjacent Entry Merging**: Merges back-to-back entries for the same project/task
- **Overlap Detection**: Warns about overlapping time entries
- **BambooHR Import UI**: Browser-based floating panel with entry preview, conflict detection, and batch import
- **Persistent Configuration**: YAML-based config and mapping stored in `~/.config/clockify-export/`

## Requirements

- Python 3.13+
- Clockify API key
- [Tampermonkey](https://www.tampermonkey.net/) browser extension (for the import step)

## Installation

### CLI

```bash
git clone <repository-url>
cd work-log-synchronizer
uv sync
```

### Tampermonkey Userscript

1. Install the [Tampermonkey](https://www.tampermonkey.net/) browser extension
2. Open `bamboo-import.user.js` from this repository
3. Click "Install" when Tampermonkey prompts, or create a new script and paste the contents

## Quick Start

### 1. Setup Clockify API Access

```bash
clockify-export setup
```

This will:
- Prompt for your Clockify API key
- List your workspaces and let you select one
- Verify the connection
- Save config to `~/.config/clockify-export/config.yaml`

### 2. Build Project/Task Mapping

```bash
clockify-export init-mapping
```

This fetches your Clockify projects and tasks, then walks you through mapping each one to a BambooHR project/task ID.

To use BambooHR project/task names in the mapping menus (instead of raw IDs), first extract the timesheet data from BambooHR using the userscript's "Extract Page Data" button, save it as a JSON file, then:

```bash
clockify-export init-mapping --bamboo-data js-timesheet-data.json
```

### 3. Export Time Entries

```bash
clockify-export export --from 2026-03-01 --to 2026-03-31
```

This outputs BambooHR-ready JSON to stdout. To save to a file:

```bash
clockify-export export --from 2026-03-01 --to 2026-03-31 -o export.json
```

### 4. Import into BambooHR

1. Open your BambooHR timesheet page in the browser
2. The Tampermonkey userscript adds a floating "Clockify Import" panel
3. Paste the exported JSON into the text area
4. Preview entries — the panel shows validation status, conflicts, and total hours
5. Click "Import" to post entries to BambooHR

## CLI Reference

All commands accept `--config-dir PATH` to override the default config directory.

### `clockify-export setup`

Interactive first-time configuration for Clockify API access.

### `clockify-export init-mapping`

Build the project/task mapping interactively.

| Option | Description |
|--------|-------------|
| `--bamboo-data PATH` | Path to `js-timesheet-data.json` for BambooHR project/task menus |

### `clockify-export export`

Export Clockify entries to BambooHR-ready JSON.

| Option | Description |
|--------|-------------|
| `--from YYYY-MM-DD` | Start date (required) |
| `--to YYYY-MM-DD` | End date (required) |
| `-o, --output PATH` | Output file path (defaults to stdout) |

## Configuration

Configuration is stored in `~/.config/clockify-export/`:

| File | Contents |
|------|----------|
| `config.yaml` | Clockify API key and workspace ID |
| `mapping.yaml` | Project/task mappings |
| `clockify-export.log` | Log file |

### Mapping Format

`mapping.yaml` maps Clockify project/task pairs to BambooHR IDs:

```yaml
mappings:
  - clockify_project: "My Project"
    clockify_task: "Development"
    bamboo_project_id: 10
    bamboo_task_id: 42
  - clockify_project: "Internal"
    clockify_task: null
    bamboo_project_id: 5
    bamboo_task_id: null
```

## Project Structure

```
work-log-synchronizer/
├── src/clockify_export/
│   ├── __init__.py          # Package version
│   ├── cli.py               # Click-based CLI
│   ├── config.py            # MappingConfig (YAML persistence)
│   ├── bamboo_data.py       # Parser for BambooHR js-timesheet-data.json
│   ├── export.py            # Export engine (timezone, merging, overlap detection)
│   ├── mapper.py            # Interactive mapping prompts
│   ├── clockify/
│   │   ├── client.py        # ClockifyClient (pagination, retry)
│   │   └── models.py        # Pydantic models for Clockify API
│   └── utils/
│       ├── logging.py       # Logging setup
│       └── storage.py       # StorageManager for YAML config files
├── bamboo-import.user.js    # Tampermonkey userscript for BambooHR import
├── tests/                   # Test suite
├── pyproject.toml           # Project configuration
├── Makefile                 # Code quality commands
└── README.md
```

## Architecture

### Workflow

```
Clockify API  →  clockify-export CLI  →  JSON file  →  Tampermonkey userscript  →  BambooHR
```

1. `clockify-export export` fetches time entries from the Clockify API
2. Entries are converted to the user's workspace timezone
3. Adjacent entries for the same project/task are merged
4. Mapped entries are output as BambooHR-ready JSON
5. The Tampermonkey userscript imports the JSON into BambooHR via the browser

### Components

- **ClockifyClient**: HTTP client for the Clockify API (httpx, with pagination and retry)
- **MappingConfig**: Reads/writes project/task mappings to YAML
- **Export Engine**: Converts Clockify entries to BambooHR format (timezone conversion, merging, overlap detection)
- **Mapper**: Interactive CLI flow for mapping Clockify projects to BambooHR IDs
- **BambooHR Userscript**: Browser-side import with preview, validation, and conflict detection

## Clockify API Key

1. Go to [Clockify Settings](https://app.clockify.me/user/settings)
2. Scroll to "API" section
3. Generate or copy your API key

## Troubleshooting

### "Not configured" error

Run `clockify-export setup` to configure your API key and workspace.

### "No mappings configured" error

Run `clockify-export init-mapping` to set up project/task mappings.

### No time entries found

- Verify your date range with `--from` and `--to`
- Check that your Clockify entries have projects assigned
- Review the log file at `~/.config/clockify-export/clockify-export.log`

### Unmapped entries skipped during export

Run `clockify-export init-mapping` to add mappings for new projects/tasks.

### Userscript not appearing on BambooHR

- Ensure Tampermonkey is enabled
- Check that the script's `@match` pattern matches your BambooHR URL (`https://*.bamboohr.com/employees/timesheet*`)

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup, testing, and code quality instructions.

### Quick Reference

```bash
make check   # Run all checks (lint, format, mypy, tests)
make fix     # Auto-fix lint and formatting issues
make test    # Run tests with coverage
```

## License

MIT
