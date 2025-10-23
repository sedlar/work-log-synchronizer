"""Configuration management for work log synchronizer."""

from pathlib import Path
from typing import Any

from work_log_sync.utils.storage import StorageManager


class Config:
    """Manages application configuration and mappings."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize configuration.

        Args:
            config_dir: Directory for storing configuration.
        """
        self.storage = StorageManager(config_dir)
        self._mapping = self.storage.load_mapping()

    def get_mapping(self) -> dict[str, Any]:
        """Get current project/task mappings.

        Returns:
            Mapping configuration.
        """
        return self._mapping

    def update_mapping(self, clockify_key: str, mapping: dict[str, Any]) -> None:
        """Update mapping for a Clockify project/task.

        Args:
            clockify_key: Clockify project/task key.
            mapping: Mapping details (bamboo_project_id, bamboo_task_id, or skip=True).
        """
        if "projects" not in self._mapping:
            self._mapping["projects"] = {}

        self._mapping["projects"][clockify_key] = mapping
        self.storage.save_mapping(self._mapping)

    def get_mapping_for(self, clockify_key: str) -> dict[str, Any] | None:
        """Get mapping for a specific Clockify project/task.

        Args:
            clockify_key: Clockify project/task key.

        Returns:
            Mapping details or None if not mapped.
        """
        projects = self._mapping.get("projects", {})
        return projects.get(clockify_key)

    def should_skip(self, clockify_key: str) -> bool:
        """Check if a Clockify project/task should be skipped.

        Args:
            clockify_key: Clockify project/task key.

        Returns:
            True if should be skipped, False otherwise.
        """
        mapping = self.get_mapping_for(clockify_key)
        return mapping and mapping.get("skip", False) if mapping else False

    def is_mapped(self, clockify_key: str) -> bool:
        """Check if a Clockify project/task is mapped.

        Args:
            clockify_key: Clockify project/task key.

        Returns:
            True if mapped, False otherwise.
        """
        mapping = self.get_mapping_for(clockify_key)
        if not mapping:
            return False
        # Mapped if it has bamboo_project_id or skip flag
        return "bamboo_project_id" in mapping or mapping.get("skip", False)
