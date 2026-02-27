# ABOUTME: Interactive mapping prompts for Clockify-to-BambooHR configuration.
# ABOUTME: Supports both BambooHR project menus and raw ID entry.

from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from clockify_export.bamboo_data import BambooProject
from clockify_export.config import MappingConfig, MappingEntry

console = Console()


def run_mapping_flow(
    clockify_projects: list[tuple[str, str | None]],
    mapping: MappingConfig,
    bamboo_projects: list[BambooProject] | None = None,
) -> None:
    """Run interactive mapping for each Clockify project/task pair.

    Args:
        clockify_projects: List of (project_name, task_name) tuples from Clockify.
        mapping: MappingConfig to store results.
        bamboo_projects: Optional BambooHR project list for numbered menus.
    """
    for project_name, task_name in clockify_projects:
        existing = mapping.find(project_name, task_name)
        if existing is not None:
            continue

        label = f"{project_name}: {task_name}" if task_name else project_name
        console.print(f"\n[bold cyan]Mapping: {label}[/bold cyan]")

        action = Prompt.ask(
            "  [bright_cyan]s[/bright_cyan]kip / [bright_cyan]m[/bright_cyan]ap",
            choices=["s", "m"],
            default="m",
        )
        if action == "s":
            continue

        if bamboo_projects:
            entry = _prompt_with_menu(project_name, task_name, bamboo_projects)
        else:
            entry = _prompt_raw_ids(project_name, task_name)

        if entry:
            mapping.add(entry)
            console.print("  [green]Saved.[/green]")


def _prompt_with_menu(
    project_name: str,
    task_name: str | None,
    bamboo_projects: list[BambooProject],
) -> MappingEntry | None:
    """Prompt user to select from numbered BambooHR project/task list."""
    # Show project menu
    table = Table(title="BambooHR Projects")
    table.add_column("#", style="bright_cyan")
    table.add_column("Project")
    for i, proj in enumerate(bamboo_projects, 1):
        table.add_row(str(i), proj.name)
    console.print(table)

    idx = IntPrompt.ask("  Select project #", default=0)
    if idx < 1 or idx > len(bamboo_projects):
        console.print("  [yellow]Skipped (invalid selection).[/yellow]")
        return None

    selected_project = bamboo_projects[idx - 1]
    bamboo_task_id: int | None = None

    if selected_project.tasks:
        task_table = Table(title=f"Tasks for {selected_project.name}")
        task_table.add_column("#", style="bright_cyan")
        task_table.add_column("Task")
        for i, task in enumerate(selected_project.tasks, 1):
            task_table.add_row(str(i), task.name)
        console.print(task_table)

        task_idx = IntPrompt.ask("  Select task # (0 for none)", default=0)
        if 1 <= task_idx <= len(selected_project.tasks):
            bamboo_task_id = selected_project.tasks[task_idx - 1].id

    return MappingEntry(
        clockify_project=project_name,
        clockify_task=task_name,
        bamboo_project_id=selected_project.id,
        bamboo_task_id=bamboo_task_id,
    )


def _prompt_raw_ids(project_name: str, task_name: str | None) -> MappingEntry | None:
    """Prompt user to enter BambooHR project/task IDs manually."""
    project_id_str = Prompt.ask("  BambooHR project ID")
    try:
        bamboo_project_id = int(project_id_str)
    except ValueError:
        console.print("  [yellow]Skipped (invalid ID).[/yellow]")
        return None

    task_id_str = Prompt.ask("  BambooHR task ID (empty for none)", default="")
    bamboo_task_id: int | None = None
    if task_id_str:
        try:
            bamboo_task_id = int(task_id_str)
        except ValueError:
            console.print("  [yellow]Invalid task ID, setting to none.[/yellow]")

    return MappingEntry(
        clockify_project=project_name,
        clockify_task=task_name,
        bamboo_project_id=bamboo_project_id,
        bamboo_task_id=bamboo_task_id,
    )
