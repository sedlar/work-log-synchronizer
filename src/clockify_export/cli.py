# ABOUTME: Click-based CLI for clockify-export tool.
# ABOUTME: Provides setup, init-mapping, and export commands.

import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import click
from rich.console import Console
from rich.table import Table

from clockify_export import __version__
from clockify_export.bamboo_data import parse_timesheet_data
from clockify_export.clockify import ClockifyClient
from clockify_export.config import MappingConfig
from clockify_export.export import build_export, generate_json
from clockify_export.mapper import run_mapping_flow
from clockify_export.utils import setup_logging
from clockify_export.utils.storage import StorageManager

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="clockify-export")
def cli() -> None:
    """Export Clockify time entries to BambooHR-ready JSON."""


@cli.command()
@click.option("--config-dir", type=click.Path(path_type=Path), default=None)
def setup(config_dir: Path | None) -> None:
    """Interactive first-time setup for Clockify API access."""
    setup_logging(config_dir=config_dir)
    storage = StorageManager(config_dir)

    console.print("[bold]Clockify Export Setup[/bold]\n")

    api_key = click.prompt("Enter your Clockify API key", hide_input=True)

    try:
        with ClockifyClient(api_key=api_key) as client:
            workspaces = client.list_workspaces()
    except Exception as e:
        console.print(f"[red]Failed to connect to Clockify: {e}[/red]")
        sys.exit(1)

    if not workspaces:
        console.print("[red]No workspaces found for this API key.[/red]")
        sys.exit(1)

    console.print("\n[cyan]Available workspaces:[/cyan]")
    for i, ws in enumerate(workspaces, 1):
        console.print(f"  {i}. {ws['name']}")

    if len(workspaces) == 1:
        choice = 1
        console.print(f"\nAuto-selected: {workspaces[0]['name']}")
    else:
        choice = click.prompt("\nSelect workspace #", type=int)
        if choice < 1 or choice > len(workspaces):
            console.print("[red]Invalid selection.[/red]")
            sys.exit(1)

    selected = workspaces[choice - 1]
    config = {
        "clockify": {
            "api_key": api_key,
            "workspace_id": selected["id"],
        }
    }
    storage.save_config(config)

    user = None
    try:
        with ClockifyClient(api_key=api_key) as client:
            user = client.get_current_user()
    except Exception:
        pass

    if user:
        console.print(f"\n[green]Connected as {user.get('name', 'user')}[/green]")
    console.print(f"[green]Workspace: {selected['name']}[/green]")
    console.print("[green]Config saved.[/green]")
    console.print("\nNext: run [bold]clockify-export init-mapping[/bold] to set up project/task mapping.")


@cli.command("init-mapping")
@click.option("--bamboo-data", type=click.Path(exists=True, path_type=Path), default=None,
              help="Path to js-timesheet-data.json for BambooHR project/task menus.")
@click.option("--config-dir", type=click.Path(path_type=Path), default=None)
def init_mapping(bamboo_data: Path | None, config_dir: Path | None) -> None:
    """Build the project/task mapping interactively."""
    setup_logging(config_dir=config_dir)
    storage = StorageManager(config_dir)

    api_key = storage.get_api_key()
    workspace_id = storage.get_workspace_id()
    if not api_key or not workspace_id:
        console.print("[red]Not configured. Run 'clockify-export setup' first.[/red]")
        sys.exit(1)

    console.print("[bold]Building project/task mapping...[/bold]\n")

    # Fetch Clockify projects and tasks
    try:
        with ClockifyClient(api_key=api_key) as client:
            projects = client.list_projects(workspace_id)
            clockify_pairs: list[tuple[str, str | None]] = []
            for project in projects:
                tasks = client.list_tasks(workspace_id, project.id)
                if tasks:
                    for task in tasks:
                        clockify_pairs.append((project.name, task.name))
                else:
                    clockify_pairs.append((project.name, None))
    except Exception as e:
        console.print(f"[red]Failed to fetch Clockify data: {e}[/red]")
        sys.exit(1)

    console.print(f"Found {len(clockify_pairs)} Clockify project/task pairs.\n")

    # Parse BambooHR data if provided
    bamboo_projects = None
    if bamboo_data:
        try:
            bamboo_projects = parse_timesheet_data(bamboo_data)
            console.print(f"Loaded {len(bamboo_projects)} BambooHR projects.\n")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not parse BambooHR data: {e}[/yellow]")

    mapping = MappingConfig(config_dir)
    run_mapping_flow(clockify_pairs, mapping, bamboo_projects)

    console.print(f"\n[green]Mapping saved ({len(mapping.all_entries())} entries).[/green]")
    console.print("Run [bold]clockify-export export --from YYYY-MM-DD --to YYYY-MM-DD[/bold] to export.")


@cli.command()
@click.option("--from", "from_date", required=True, type=click.DateTime(formats=["%Y-%m-%d"]),
              help="Start date (YYYY-MM-DD).")
@click.option("--to", "to_date", required=True, type=click.DateTime(formats=["%Y-%m-%d"]),
              help="End date (YYYY-MM-DD).")
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None,
              help="Output file path. Defaults to stdout.")
@click.option("--config-dir", type=click.Path(path_type=Path), default=None)
def export(from_date: datetime, to_date: datetime, output: Path | None, config_dir: Path | None) -> None:
    """Export Clockify entries to BambooHR-ready JSON."""
    setup_logging(config_dir=config_dir)
    storage = StorageManager(config_dir)

    api_key = storage.get_api_key()
    workspace_id = storage.get_workspace_id()
    if not api_key or not workspace_id:
        console.print("[red]Not configured. Run 'clockify-export setup' first.[/red]")
        sys.exit(1)

    mapping = MappingConfig(config_dir)
    if not mapping.all_entries():
        console.print("[red]No mappings configured. Run 'clockify-export init-mapping' first.[/red]")
        sys.exit(1)

    from_dt = from_date.date() if isinstance(from_date, datetime) else from_date
    to_dt = to_date.date() if isinstance(to_date, datetime) else to_date

    try:
        with ClockifyClient(api_key=api_key) as client:
            user_info = client.get_current_user()
            user_id = user_info["id"]

            # Get workspace timezone from user settings
            tz_name = user_info.get("settings", {}).get("timeZone", "UTC")
            timezone = ZoneInfo(tz_name)

            entries = client.get_time_entries(
                workspace_id=workspace_id,
                user_id=user_id,
                start_date=datetime.combine(from_dt, datetime.min.time()),
                end_date=datetime.combine(to_dt, datetime.max.time()),
            )

            # Build project/task name lookup
            project_names: dict[str, str] = {}
            task_names: dict[str, str] = {}
            projects = client.list_projects(workspace_id)
            for proj in projects:
                project_names[proj.id] = proj.name
                for task in client.list_tasks(workspace_id, proj.id):
                    task_names[task.id] = task.name

    except Exception as e:
        console.print(f"[red]Clockify API error: {e}[/red]")
        sys.exit(1)

    if not entries:
        console.print("[yellow]No time entries found for the given date range.[/yellow]")
        sys.exit(0)

    result = build_export(entries, project_names, task_names, mapping, timezone)

    # Show warnings
    for warning in result.warnings:
        console.print(f"[yellow]Warning: {warning}[/yellow]")

    if result.unmapped:
        console.print("\n[yellow]Unmapped entries (skipped):[/yellow]")
        for item in sorted(set(result.unmapped)):
            console.print(f"  - {item}")

    # Generate and output JSON
    output_data = generate_json(result, from_dt, to_dt)

    json_str = json.dumps(output_data, indent=2)
    if output:
        output.write_text(json_str)
        console.print(f"\n[green]Exported {len(result.entries)} entries to {output}[/green]")
    else:
        click.echo(json_str)

    # Summary to stderr so it doesn't pollute JSON stdout
    if not output:
        Console(stderr=True).print(f"\n[green]Exported {len(result.entries)} entries.[/green]")


def main() -> None:
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
