# Clockify Export - Usage Examples

Practical examples for the `clockify-export` CLI and the BambooHR import userscript.

## Initial Setup

### 1. Configure Clockify API Access

```bash
clockify-export setup
```

Output:
```
Clockify Export Setup

Enter your Clockify API key: ••••••••••••••••

Available workspaces:
  1. My Company

Auto-selected: My Company

Connected as John Doe
Workspace: My Company
Config saved.

Next: run clockify-export init-mapping to set up project/task mapping.
```

### 2. Build Project/Task Mapping

Without BambooHR data (enter raw IDs):

```bash
clockify-export init-mapping
```

With BambooHR project/task names (recommended):

```bash
clockify-export init-mapping --bamboo-data js-timesheet-data.json
```

To get `js-timesheet-data.json`: open your BambooHR timesheet in the browser, click the "Extract Page Data" button in the userscript panel, and save the copied JSON to a file.

## Exporting Time Entries

### Export a Date Range to stdout

```bash
clockify-export export --from 2026-03-01 --to 2026-03-31
```

JSON is printed to stdout; warnings and summary go to stderr.

### Export to a File

```bash
clockify-export export --from 2026-03-01 --to 2026-03-31 -o march.json
```

Output:
```
Exported 42 entries to march.json
```

### Export Last Week

```bash
clockify-export export \
  --from $(date -d 'last monday' +%Y-%m-%d) \
  --to $(date -d 'last friday' +%Y-%m-%d) \
  -o last-week.json
```

### Handling Unmapped Entries

If entries are unmapped, the export warns you:

```
Warning: Overlap detected: 09:00-10:00 and 09:30-11:00 on 2026-03-15

Unmapped entries (skipped):
  - Research:Spike
  - Internal:Onboarding

Exported 38 entries.
```

Run `clockify-export init-mapping` to add mappings for the skipped entries.

## Importing into BambooHR

1. Open your BambooHR timesheet page (`https://yourcompany.bamboohr.com/employees/timesheet/...`)
2. The Tampermonkey userscript shows a floating "Clockify Import" panel
3. Paste the exported JSON into the text area
4. Review the preview:
   - Each entry shows date, time, project, task, and validation status
   - Conflicts with existing entries are flagged
   - Total hours are displayed
5. Click "Import" to post all valid entries

## Custom Config Directory

All commands support `--config-dir` for non-default locations:

```bash
clockify-export setup --config-dir ~/my-config
clockify-export init-mapping --config-dir ~/my-config
clockify-export export --from 2026-03-01 --to 2026-03-31 --config-dir ~/my-config
```

## Checking Logs

```bash
# View recent log entries
tail -50 ~/.config/clockify-export/clockify-export.log

# Follow logs in real-time
tail -f ~/.config/clockify-export/clockify-export.log
```

## Working with Mappings

### View Current Mappings

```bash
cat ~/.config/clockify-export/mapping.yaml
```

### Edit Mappings Manually

Edit `~/.config/clockify-export/mapping.yaml` directly:

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

Set `clockify_task: null` to match all tasks under a project.

## Tips

1. **Extract BambooHR data first**: Use the userscript's "Extract Page Data" button before running `init-mapping` — it gives you project/task names instead of having to look up raw IDs
2. **Review unmapped entries**: After export, check for unmapped entries and add mappings before re-exporting
3. **Check the preview**: The userscript preview shows conflicts with existing BambooHR entries before you import
4. **Pipe to clipboard**: `clockify-export export --from ... --to ... | xclip -selection clipboard` to paste directly into the userscript
