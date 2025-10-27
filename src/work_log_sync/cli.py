"""Command-line interface for work log synchronizer."""

import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from work_log_sync import __version__
from work_log_sync.bamboohr import BambooHRClient
from work_log_sync.bamboohr.oauth import BambooHROAuthConfig, BambooHROAuthClient
from work_log_sync.clockify import ClockifyClient
from work_log_sync.config import Config
from work_log_sync.sync import SyncEngine
from work_log_sync.utils import get_logger, setup_logging, StorageManager

app = typer.Typer(help="Synchronize work logs from Clockify to BambooHR")
console = Console()
logger = get_logger(__name__)


@app.command()
def sync(
    from_date: Optional[str] = typer.Option(
        None,
        "--from-date",
        help="Start date for sync (YYYY-MM-DD). Defaults to last sync date or 30 days ago.",
    ),
    to_date: Optional[str] = typer.Option(
        None,
        "--to-date",
        help="End date for sync (YYYY-MM-DD). Defaults to today.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be synced without actually creating entries.",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Prompt for unmapped projects/tasks.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging.",
    ),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Print each API call and prompt for confirmation before sending.",
    ),
    config_dir: Optional[Path] = typer.Option(
        None,
        "--config-dir",
        help="Configuration directory. Defaults to ~/.work-log-sync/",
    ),
) -> None:
    """Synchronize work logs from Clockify to BambooHR."""
    setup_logging(
        log_level=logging.DEBUG if verbose else logging.INFO,
        config_dir=config_dir,
    )

    logger.info(f"Work Log Synchronizer v{__version__}")

    # Parse dates
    from_dt: Optional[date] = None
    to_dt: Optional[date] = None

    if from_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD[/red]")
            raise typer.Exit(code=1)

    if to_date:
        try:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD[/red]")
            raise typer.Exit(code=1)

    try:
        # Initialize clients
        config = Config(config_dir)
        storage = StorageManager(config_dir)

        clockify_key = storage.get_token("clockify")
        if not clockify_key:
            console.print("[yellow]Clockify API key not found. Please configure it first.[/yellow]")
            console.print("Run: work-log-sync configure")
            raise typer.Exit(code=1)

        bamboohr_domain = storage.load_state().get("bamboohr_domain")
        if not bamboohr_domain:
            console.print("[yellow]BambooHR not configured. Please configure it first.[/yellow]")
            console.print("Run: work-log-sync configure")
            raise typer.Exit(code=1)

        # Initialize BambooHR OAuth client
        oauth_config = BambooHROAuthConfig(
            client_id=storage.load_state().get("bamboohr_client_id", ""),
            client_secret=storage.load_state().get("bamboohr_client_secret", ""),
            domain=bamboohr_domain,
        )

        if not oauth_config.client_id or not oauth_config.client_secret:
            console.print("[yellow]BambooHR OAuth credentials not configured.[/yellow]")
            console.print("Run: work-log-sync configure")
            raise typer.Exit(code=1)

        oauth_client = BambooHROAuthClient(oauth_config, storage=storage)
        bamboohr_client = BambooHRClient(
            domain=bamboohr_domain,
            oauth_client=oauth_client,
            storage=storage,
            confirm=confirm,
        )

        with ClockifyClient(api_key=clockify_key, storage=storage, confirm=confirm) as clockify_client, bamboohr_client:
            engine = SyncEngine(
                config=config,
                clockify_client=clockify_client,
                bamboohr_client=bamboohr_client,
            )

            mode_str = "[bold cyan]DRY RUN[/bold cyan]" if dry_run else "[bold green]SYNC[/bold green]"
            console.print(f"Starting {mode_str} mode...")

            result = engine.sync(
                from_date=from_dt,
                to_date=to_dt,
                dry_run=dry_run,
                interactive=interactive,
            )

            # Display results
            table = Table(title="Sync Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="magenta")
            table.add_row("Synced", str(result.entries_synced))
            table.add_row("Skipped", str(result.entries_skipped))
            table.add_row("Failed", str(result.entries_failed))
            table.add_row("Unmapped", str(len(result.unmapped_entries)))

            console.print(table)

            if result.unmapped_entries:
                console.print("\n[yellow]Unmapped entries:[/yellow]")
                for entry in result.unmapped_entries:
                    console.print(f"  - {entry}")

            if result.errors:
                console.print("\n[red]Errors:[/red]")
                for error in result.errors:
                    console.print(f"  - {error}")

            exit_code = 0 if result.entries_failed == 0 else 1
            raise typer.Exit(code=exit_code)

    except httpx.RequestError as e:
        if "cancelled by user" in str(e).lower():
            console.print("[yellow]Sync cancelled by user[/yellow]")
            raise typer.Exit(code=0)
        else:
            logger.error(f"API request failed: {e}", exc_info=True)
            console.print(f"[red]Error: API request failed: {e}[/red]")
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


def _check_configuration_status(storage: StorageManager) -> dict:
    """Check and display current configuration status."""
    state = storage.load_state()
    clockify_key = storage.get_token("clockify")
    bamboohr_domain = state.get("bamboohr_domain")
    bamboohr_client_id = state.get("bamboohr_client_id")
    bamboohr_client_secret = state.get("bamboohr_client_secret")

    clockify_configured = bool(clockify_key)
    bamboohr_configured = bool(bamboohr_domain and bamboohr_client_id and bamboohr_client_secret)

    console.print("[bold cyan]Current Configuration Status[/bold cyan]")
    clockify_status = "[green]✓ Configured[/green]" if clockify_configured else "[yellow]✗ Not configured[/yellow]"
    bamboohr_status = "[green]✓ Configured[/green]" if bamboohr_configured else "[yellow]✗ Not configured[/yellow]"
    console.print(f"  Clockify:  {clockify_status}")
    console.print(f"  BambooHR:  {bamboohr_status}")
    console.print()

    return {
        "clockify_configured": clockify_configured,
        "bamboohr_configured": bamboohr_configured,
    }


def _configure_clockify(storage: StorageManager) -> str:
    """Configure Clockify API credentials."""
    console.print("[yellow]Clockify Configuration[/yellow]")
    clockify_key = Prompt.ask(
        "Enter your Clockify API key",
        password=True,
    )
    storage.set_token("clockify", clockify_key)
    console.print("[green]✓ Clockify API key saved[/green]")
    return clockify_key


def _configure_bamboohr(storage: StorageManager) -> tuple[str, str, str]:
    """Configure BambooHR OAuth credentials."""
    console.print("[yellow]BambooHR Configuration (OAuth 2.0)[/yellow]")
    bamboohr_domain = Prompt.ask("Enter your BambooHR subdomain (e.g., 'mycompany')")
    bamboohr_client_id = Prompt.ask(
        "Enter your BambooHR OAuth Client ID",
        password=False,
    )
    bamboohr_client_secret = Prompt.ask(
        "Enter your BambooHR OAuth Client Secret",
        password=True,
    )

    # Save OAuth credentials
    state = storage.load_state()
    state["bamboohr_domain"] = bamboohr_domain
    state["bamboohr_client_id"] = bamboohr_client_id
    state["bamboohr_client_secret"] = bamboohr_client_secret
    storage.save_state(state)

    console.print("[cyan]Initializing OAuth authentication...[/cyan]")

    # Create OAuth config and initiate authentication
    oauth_config = BambooHROAuthConfig(
        client_id=bamboohr_client_id,
        client_secret=bamboohr_client_secret,
        domain=bamboohr_domain,
    )

    try:
        oauth_client = BambooHROAuthClient(oauth_config, storage=storage)
        console.print("[cyan]Opening browser for BambooHR authorization...[/cyan]")
        token = oauth_client.handle_callback()
        console.print("[green]✓ BambooHR OAuth authentication successful[/green]")
    except Exception as e:
        console.print(f"[red]✗ BambooHR authentication failed: {e}[/red]")
        raise typer.Exit(code=1)

    return bamboohr_domain, bamboohr_client_id, bamboohr_client_secret


@app.command()
def configure(
    config_dir: Optional[Path] = typer.Option(
        None,
        "--config-dir",
        help="Configuration directory. Defaults to ~/.work-log-sync/",
    ),
) -> None:
    """Configure Clockify and BambooHR credentials selectively."""
    setup_logging(config_dir=config_dir)

    storage = StorageManager(config_dir)
    config = Config(config_dir)

    console.print("[bold cyan]Work Log Synchronizer Configuration[/bold cyan]")
    console.print()

    # Check current configuration
    status = _check_configuration_status(storage)

    # Ask which service(s) to configure
    console.print("[cyan]Which service would you like to configure?[/cyan]")
    choice = Prompt.ask(
        "Select",
        choices=["clockify", "bamboohr", "both"],
        default="both",
    )
    console.print()

    configured_services = []
    clockify_key = None
    bamboohr_domain = None
    oauth_client = None

    # Configure Clockify if selected
    if choice in ["clockify", "both"]:
        clockify_key = _configure_clockify(storage)
        configured_services.append("Clockify")
        console.print()

    # Configure BambooHR if selected
    if choice in ["bamboohr", "both"]:
        bamboohr_domain, _, _ = _configure_bamboohr(storage)
        configured_services.append("BambooHR")
        console.print()

    # Test connections for newly configured services
    console.print("[cyan]Testing connections...[/cyan]")

    if choice in ["clockify", "both"]:
        try:
            with ClockifyClient(api_key=clockify_key, storage=storage) as clockify_client:
                user = clockify_client.get_current_user()
                console.print(f"[green]✓ Connected to Clockify as {user.get('name', 'user')}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to connect to Clockify: {e}[/red]")

    if choice in ["bamboohr", "both"]:
        try:
            state = storage.load_state()
            oauth_config = BambooHROAuthConfig(
                client_id=state.get("bamboohr_client_id", ""),
                client_secret=state.get("bamboohr_client_secret", ""),
                domain=state.get("bamboohr_domain", ""),
            )
            oauth_client = BambooHROAuthClient(oauth_config, storage=storage)
            bamboohr_client = BambooHRClient(
                domain=bamboohr_domain or state.get("bamboohr_domain", ""),
                oauth_client=oauth_client,
                storage=storage,
            )
            projects = bamboohr_client.list_projects()
            console.print(f"[green]✓ Connected to BambooHR (found {len(projects)} projects)[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to connect to BambooHR: {e}[/red]")

    console.print("\n[green]Configuration complete![/green]")
    console.print("Run 'work-log-sync sync' to start syncing work logs.")


@app.command()
def mapping(
    config_dir: Optional[Path] = typer.Option(
        None,
        "--config-dir",
        help="Configuration directory. Defaults to ~/.work-log-sync/",
    ),
) -> None:
    """View and manage project/task mappings."""
    setup_logging(config_dir=config_dir)

    config = Config(config_dir)
    mapping = config.get_mapping()

    if not mapping or not mapping.get("projects"):
        console.print("[yellow]No mappings configured yet.[/yellow]")
        return

    projects = mapping["projects"]

    table = Table(title="Project/Task Mappings")
    table.add_column("Clockify", style="cyan")
    table.add_column("BambooHR Project", style="magenta")
    table.add_column("BambooHR Task", style="magenta")
    table.add_column("Action", style="yellow")

    for clockify_key, mapping_data in projects.items():
        if mapping_data.get("skip"):
            table.add_row(clockify_key, "-", "-", "SKIP")
        else:
            table.add_row(
                clockify_key,
                mapping_data.get("bamboo_project_id", "-"),
                mapping_data.get("bamboo_task_id", "-"),
                "SYNC",
            )

    console.print(table)


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"Work Log Synchronizer v{__version__}")


def main() -> None:
    """Main entry point."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
