"""Interactive mapping of Clockify projects/tasks to BambooHR."""

import logging
from typing import Any

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

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

    def prompt_for_mapping(self, clockify_key: str) -> dict[str, Any] | None:
        """Interactively prompt user to map a Clockify project/task.

        User can enter a new mapping, select from existing mappings, or skip.

        Args:
            clockify_key: Clockify project/task key.

        Returns:
            Mapping dictionary with bamboo_project_id, bamboo_task_id, and bamboo_name,
            or {"skip": True} if user wants to skip,
            or None if user cancels.
        """
        console.print(f"\n[yellow]Unmapped Clockify entry: {clockify_key}[/yellow]")

        # Show options
        options = ["Enter new mapping", "Select from existing", "Skip this entry"]
        for idx, option in enumerate(options, 1):
            console.print(f"  {idx}. {option}")

        while True:
            try:
                choice = Prompt.ask(
                    "Choose an option",
                    choices=["1", "2", "3"],
                )
                choice_idx = int(choice) - 1
                break
            except (ValueError, IndexError):
                console.print("[red]Invalid choice, please try again[/red]")
                continue

        if choice_idx == 2:  # Skip
            return {"skip": True}
        elif choice_idx == 1:  # Select from existing
            return self._select_existing_mapping()
        else:  # Enter new
            return self._prompt_for_new_mapping()

    def _select_existing_mapping(self) -> dict[str, Any] | None:
        """Show existing mappings and let user select one.

        Returns:
            Selected mapping dictionary or None if user cancels.
        """
        existing_mappings = self.config.get_all_mappings()

        if not existing_mappings:
            console.print("[yellow]No existing mappings found[/yellow]")
            return None

        # Display existing mappings
        table = Table(title="Existing Mappings")
        table.add_column("Index", style="cyan")
        table.add_column("Clockify Entry", style="magenta")
        table.add_column("BambooHR", style="green")

        for idx, (key, mapping) in enumerate(existing_mappings.items(), 1):
            if mapping.get("skip"):
                bamboo_info = "[red]SKIP[/red]"
            else:
                project_id = mapping.get("bamboo_project_id", "?")
                task_id = mapping.get("bamboo_task_id")
                task_info = f"/{task_id}" if task_id else ""
                name = mapping.get("bamboo_name", "?")
                bamboo_info = f"{name} ({project_id}{task_info})"

            table.add_row(str(idx), key, bamboo_info)

        console.print(table)

        # Get selection
        max_idx = len(existing_mappings)
        while True:
            try:
                choice = Prompt.ask(
                    f"Select mapping (1-{max_idx})",
                    choices=[str(i) for i in range(1, max_idx + 1)],
                )
                selected_idx = int(choice) - 1
                break
            except (ValueError, IndexError):
                console.print("[red]Invalid choice, please try again[/red]")
                continue

        # Get the selected mapping
        selected_key = list(existing_mappings.keys())[selected_idx]
        selected_mapping = existing_mappings[selected_key]
        logger.info(f"Selected existing mapping: {selected_key}")

        return selected_mapping

    def _prompt_for_new_mapping(self) -> dict[str, Any]:
        """Prompt user to enter new BambooHR project/task details.

        Returns:
            Mapping dictionary with bamboo_project_id, bamboo_task_id, and bamboo_name.
        """
        console.print("\n[cyan]Enter BambooHR project/task details:[/cyan]")

        # Get project ID
        while True:
            project_id = Prompt.ask("BambooHR Project ID (required)")
            if project_id.strip():
                break
            console.print("[red]Project ID is required[/red]")

        # Get task ID (optional)
        task_id_input = Prompt.ask("BambooHR Task ID (optional, press Enter to skip)")
        task_id = task_id_input.strip() if task_id_input.strip() else None

        # Get display name
        while True:
            name = Prompt.ask("Friendly name for this project/task (required)")
            if name.strip():
                break
            console.print("[red]Name is required[/red]")

        mapping = {
            "bamboo_project_id": project_id.strip(),
            "bamboo_task_id": task_id,
            "bamboo_name": name.strip(),
        }

        logger.info(f"Created new mapping: {mapping}")
        return mapping

    def save_mapping(self, clockify_key: str, mapping: dict[str, Any]) -> None:
        """Save a mapping to configuration.

        Args:
            clockify_key: Clockify project/task key.
            mapping: Mapping details.
        """
        self.config.update_mapping(clockify_key, mapping)
        logger.info(f"Saved mapping for {clockify_key}")
