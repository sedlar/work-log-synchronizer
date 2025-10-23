# Work Log Synchronizer - Usage Examples

This document provides practical examples of how to use the work-log-sync tool.

## Initial Setup

### 1. First-time Configuration

```bash
work-log-sync configure
```

Output:
```
Work Log Synchronizer Configuration

Clockify Configuration
Enter your Clockify API key: ••••••••••••••••
✓ Clockify API key saved

BambooHR Configuration
Enter your BambooHR subdomain (e.g., 'mycompany'): mycompany
Enter your BambooHR API key: ••••••••••••••••
✓ BambooHR configuration saved

Testing connections...
✓ Connected to Clockify as John Doe
✓ Connected to BambooHR (found 45 employees)

Configuration complete!
Run 'work-log-sync sync' to start syncing work logs.
```

## Common Workflows

### Scenario 1: Sync Last 7 Days of Work

```bash
work-log-sync sync --from-date $(date -d '7 days ago' +%Y-%m-%d) --to-date $(date +%Y-%m-%d)
```

This syncs all work entries from the last 7 days.

### Scenario 2: Preview Changes Before Syncing

```bash
work-log-sync sync --dry-run
```

Output:
```
Starting [DRY RUN] mode...

[DRY RUN] Would create entry: Development:Backend -> 6.5h on 2024-01-15
[DRY RUN] Would create entry: Support:Bug Fixes -> 1.5h on 2024-01-15

╭─ Sync Results ─╮
│ Metric     │ Count  │
├────────────┼────────┤
│ Synced     │ 2      │
│ Skipped    │ 0      │
│ Failed     │ 0      │
│ Unmapped   │ 0      │
╰────────────┴────────╯
```

### Scenario 3: Handle Unmapped Entries Interactively

```bash
work-log-sync sync --from-date 2024-01-01 --to-date 2024-01-10
```

Output (when unmapped entries are found):
```
[yellow]Unmapped Clockify entry: Client Project:Design[/yellow]

╭─ Available BambooHR Projects ─╮
│ Index │ Project            │
├───────┼────────────────────┤
│ 1     │ Internal            │
│ 2     │ Client Project      │
│ 3     │ Support             │
│ 4     │ Research            │
│ 5     │ Skip this entry     │
╰───────┴────────────────────╯

Select project (1-5): 2

╭─ Available Tasks ─╮
│ Index │ Task               │
├───────┼────────────────────┤
│ 1     │ Design - UX        │
│ 2     │ Design - Graphics  │
│ 3     │ Design - Web       │
╰───────┴────────────────────╯

Select task (1-3): 1

Saved mapping for Client Project:Design

╭─ Sync Results ─╮
│ Metric     │ Count  │
├────────────┼────────┤
│ Synced     │ 3      │
│ Skipped    │ 1      │
│ Failed     │ 0      │
│ Unmapped   │ 0      │
╰────────────┴────────╯
```

### Scenario 4: Sync Without Interactive Prompts

```bash
work-log-sync sync --no-interactive
```

Only syncs entries that are already mapped. Unmapped entries are skipped and reported:

```
╭─ Sync Results ─╮
│ Metric     │ Count  │
├────────────┼────────┤
│ Synced     │ 10     │
│ Skipped    │ 2      │
│ Failed     │ 0      │
│ Unmapped   │ 3      │
╰────────────┴────────╯

[yellow]Unmapped entries:[/yellow]
  - Research:New Feature
  - Training:Python Course
  - Client XYZ:Consultation
```

### Scenario 5: Sync Specific Date Range

```bash
work-log-sync sync --from-date 2024-01-15 --to-date 2024-01-31
```

This syncs entries between January 15-31, 2024.

### Scenario 6: Enable Verbose Logging

```bash
work-log-sync sync --verbose
```

Detailed debug output:
```
work_log_sync.cli - DEBUG - Work Log Synchronizer v0.1.0
work_log_sync.sync.engine - INFO - Syncing work logs from 2024-01-15 to 2024-01-31
work_log_sync.clockify.client - DEBUG - Fetching time entries for user_123
work_log_sync.clockify.client - DEBUG - Found 15 time entries
work_log_sync.sync.engine - DEBUG - Skipping entry entry_789 with no project
work_log_sync.sync.engine - INFO - Created BambooHR entry: Development:Backend -> 6.5h on 2024-01-15
...
```

## Viewing Mappings

### List Current Mappings

```bash
work-log-sync mapping
```

Output:
```
╭─ Project/Task Mappings ─╮
│ Clockify           │ BambooHR Project │ BambooHR Task │ Action │
├────────────────────┼──────────────────┼───────────────┼────────┤
│ Development:Backend│ 1                │ 101           │ SYNC   │
│ Development:Frontend
                    │ 1                │ 102           │ SYNC   │
│ Support:Bug Fixes  │ 2                │ 201           │ SYNC   │
│ Internal:Meetings  │ -                │ -             │ SKIP   │
│ Break              │ -                │ -             │ SKIP   │
╰────────────────────┴──────────────────┴───────────────┴────────╯
```

## Scheduling Regular Syncs

### Linux/macOS - Crontab

Sync daily at 9 AM:

```bash
# Add to crontab
crontab -e

# Add this line:
0 9 * * * /path/to/uv run work-log-sync sync >> ~/.work-log-sync/cron.log 2>&1
```

Or sync every 2 hours:

```bash
0 */2 * * * /path/to/uv run work-log-sync sync
```

### Windows - Task Scheduler

1. Create a batch file `sync.bat`:
```batch
@echo off
cd C:\path\to\work-log-synchronizer
uv run work-log-sync sync
```

2. Create a scheduled task running this batch file at desired intervals

## Troubleshooting Examples

### Check Logs

```bash
# View last 50 lines of log
tail -50 ~/.work-log-sync/work-log-sync.log

# Follow logs in real-time
tail -f ~/.work-log-sync/work-log-sync.log

# Search for errors
grep ERROR ~/.work-log-sync/work-log-sync.log
```

### Dry-run to Diagnose Issues

```bash
work-log-sync sync --dry-run --verbose
```

### Re-configure Credentials

```bash
work-log-sync configure
```

This will update your stored credentials.

## Working with Mappings

### Manual Mapping Edits

Edit `~/.work-log-sync/mapping.yaml` directly:

```yaml
projects:
  "My Project:Development":
    bamboo_project_id: "1"
    bamboo_task_id: "101"
  "Internal:Admin":
    skip: true
```

### Skip New Projects

Add to `mapping.yaml`:

```yaml
projects:
  "Time Off":
    skip: true
```

Then sync won't try to sync time entries from "Time Off".

## Advanced Usage

### Sync Month-by-Month

For large date ranges, sync month by month to prevent overwhelming the system:

```bash
# January
work-log-sync sync --from-date 2024-01-01 --to-date 2024-01-31

# February
work-log-sync sync --from-date 2024-02-01 --to-date 2024-02-29

# And so on...
```

### Export Results

Capture sync results to a file:

```bash
work-log-sync sync --verbose > sync_results_2024-01-15.log 2>&1
```

## Tips & Best Practices

1. **Start with dry-run**: Always preview changes with `--dry-run` before the actual sync
2. **Regular syncs**: Schedule daily syncs to keep entries fresh
3. **Review mappings**: Periodically review `mapping.yaml` to ensure correct mappings
4. **Check logs**: Review `work-log-sync.log` for any warnings or errors
5. **Test credentials**: Run `configure` after credential changes to verify they work
6. **Non-interactive mode**: Use `--no-interactive` in scheduled tasks to avoid hanging
7. **Monitor duration**: Very large date ranges might take time; start with recent dates
