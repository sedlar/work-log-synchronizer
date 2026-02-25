# ABOUTME: Mapping configuration for clockify-export.
# ABOUTME: Maps Clockify project/task pairs to BambooHR project/task IDs.

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from clockify_export.utils.storage import StorageManager


@dataclass
class MappingEntry:
    """A single Clockify-to-BambooHR project/task mapping."""

    clockify_project: str
    clockify_task: str | None
    bamboo_project_id: int
    bamboo_task_id: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "clockify_project": self.clockify_project,
            "clockify_task": self.clockify_task,
            "bamboo_project_id": self.bamboo_project_id,
            "bamboo_task_id": self.bamboo_task_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MappingEntry":
        return cls(
            clockify_project=data["clockify_project"],
            clockify_task=data.get("clockify_task"),
            bamboo_project_id=data["bamboo_project_id"],
            bamboo_task_id=data.get("bamboo_task_id"),
        )


class MappingConfig:
    """Manages the list of Clockify-to-BambooHR mappings."""

    def __init__(self, config_dir: Path | None = None) -> None:
        self.storage = StorageManager(config_dir)
        self._entries: list[MappingEntry] = []
        self._load()

    def _load(self) -> None:
        data = self.storage.load_mapping()
        self._entries = [
            MappingEntry.from_dict(item) for item in data.get("mappings", [])
        ]

    def _save(self) -> None:
        data = {"mappings": [entry.to_dict() for entry in self._entries]}
        self.storage.save_mapping(data)

    def find(self, clockify_project: str, clockify_task: str | None) -> MappingEntry | None:
        """Find a mapping for the given Clockify project and task."""
        for entry in self._entries:
            if entry.clockify_project == clockify_project and entry.clockify_task == clockify_task:
                return entry
        # Fall back to project-only mapping (task=None) if no exact match
        if clockify_task is not None:
            for entry in self._entries:
                if entry.clockify_project == clockify_project and entry.clockify_task is None:
                    return entry
        return None

    def add(self, entry: MappingEntry) -> None:
        """Add or update a mapping entry."""
        # Remove existing mapping for the same Clockify project/task pair
        self._entries = [
            e for e in self._entries
            if not (e.clockify_project == entry.clockify_project
                    and e.clockify_task == entry.clockify_task)
        ]
        self._entries.append(entry)
        self._save()

    def all_entries(self) -> list[MappingEntry]:
        """Return all mapping entries."""
        return list(self._entries)
