"""Interactive mapping of Clockify projects/tasks to BambooHR."""

import logging
from typing import Any

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from work_log_sync.bamboohr.models import BambooProject, BambooTask
from work_log_sync.config import Config

logger = logging.getLogger(__name__)
console = Console()


class TaskMapper:
    """Handles interactive mapping of Clockify tasks to BambooHR tasks."""

    def __init__(self, config: Config) -> None:
        """Initialize task mapper.

        Args:
            config: Application configuration.
        """
        self.config = config

    def get_unmapped_key(
        self,
        clockify_project_name: str,
        clockify_task_name: str | None = None,
    ) -> str:
        """Generate a unique key for a Clockify project/task combination.

        Args:
            clockify_project_name: Clockify project name.
            clockify_task_name: Clockify task name (optional).

        Returns:
            Unique key for mapping.
        """
        if clockify_task_name:
            return f"{clockify_project_name}:{clockify_task_name}"
        return clockify_project_name

    def needs_mapping(self, clockify_key: str) -> bool:
        """Check if a Clockify project/task needs mapping.

        Args:
            clockify_key: Clockify project/task key.

        Returns:
            True if mapping is needed, False otherwise.
        """
        return not self.config.is_mapped(clockify_key)

    def prompt_for_mapping(
        self,
        clockify_key: str,
        bamboo_projects: list[BambooProject],
        all_tasks: dict[str, list[BambooTask]],
    ) -> dict[str, Any] | None:
        """Interactively prompt user to map a Clockify project/task.

        Args:
            clockify_key: Clockify project/task key.
            bamboo_projects: List of available BambooHR projects.
            all_tasks: Dictionary of project_id -> list of tasks.

        Returns:
            Mapping dictionary or None if user wants to skip.
        """
        console.print(f"\n[yellow]Unmapped Clockify entry: {clockify_key}[/yellow]")

        # Display available projects
        table = Table(title="Available BambooHR Projects")
        table.add_column("Index", style="cyan")
        table.add_column("Project", style="magenta")

        for idx, project in enumerate(bamboo_projects, 1):
            table.add_row(str(idx), project.name)

        # Add skip option
        table.add_row(str(len(bamboo_projects) + 1), "[bold red]Skip this entry[/bold red]")

        console.print(table)

        # Get project selection
        max_idx = len(bamboo_projects) + 1
        while True:
            try:
                choice = Prompt.ask(
                    f"Select project (1-{max_idx})",
                    choices=[str(i) for i in range(1, max_idx + 1)],
                )
                project_idx = int(choice) - 1
                break
            except (ValueError, IndexError):
                console.print("[red]Invalid choice, please try again[/red]")
                continue

        # Handle skip
        if project_idx >= len(bamboo_projects):
            return {"skip": True}

        selected_project = bamboo_projects[project_idx]
        logger.info(f"Selected BambooHR project: {selected_project.name}")

        # Get tasks for selected project
        project_tasks = all_tasks.get(str(selected_project.id), [])

        if not project_tasks:
            console.print(f"[yellow]No tasks found for project {selected_project.name}[/yellow]")
            return None

        # Display available tasks
        table = Table(title="Available Tasks")
        table.add_column("Index", style="cyan")
        table.add_column("Task", style="magenta")

        for idx, task in enumerate(project_tasks, 1):
            table.add_row(str(idx), task.name)

        console.print(table)

        # Get task selection
        while True:
            try:
                choice = Prompt.ask(
                    f"Select task (1-{len(project_tasks)})",
                    choices=[str(i) for i in range(1, len(project_tasks) + 1)],
                )
                task_idx = int(choice) - 1
                break
            except (ValueError, IndexError):
                console.print("[red]Invalid choice, please try again[/red]")
                continue

        selected_task = project_tasks[task_idx]
        logger.info(f"Selected BambooHR task: {selected_task.name}")

        mapping = {
            "bamboo_project_id": str(selected_project.id),
            "bamboo_task_id": str(selected_task.id),
        }

        return mapping

    def save_mapping(self, clockify_key: str, mapping: dict[str, Any]) -> None:
        """Save a mapping to configuration.

        Args:
            clockify_key: Clockify project/task key.
            mapping: Mapping details.
        """
        self.config.update_mapping(clockify_key, mapping)
        logger.info(f"Saved mapping for {clockify_key}")
