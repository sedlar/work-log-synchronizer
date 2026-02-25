# ABOUTME: Parser for BambooHR js-timesheet-data.json files.
# ABOUTME: Extracts available projects and tasks for mapping configuration.

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BambooTask:
    """A BambooHR task within a project."""

    id: int
    name: str


@dataclass
class BambooProject:
    """A BambooHR project with its tasks."""

    id: int
    name: str
    tasks: list[BambooTask] = field(default_factory=list)


def parse_timesheet_data(path: Path) -> list[BambooProject]:
    """Parse projectsWithTasks from a js-timesheet-data JSON file.

    The tasks.byId field is [] when empty and {} when populated.
    """
    with open(path) as f:
        data = json.load(f)

    projects_data = data.get("projectsWithTasks", {})
    by_id = projects_data.get("byId", {})

    # byId could be [] if empty
    if isinstance(by_id, list):
        return []

    projects: list[BambooProject] = []
    for project_data in by_id.values():
        tasks = _parse_tasks(project_data.get("tasks", {}))
        projects.append(
            BambooProject(
                id=project_data["id"],
                name=project_data["name"],
                tasks=tasks,
            )
        )

    projects.sort(key=lambda p: p.name)
    return projects


def _parse_tasks(tasks_data: dict[str, Any]) -> list[BambooTask]:
    """Parse tasks from a project's tasks field."""
    by_id = tasks_data.get("byId", [])

    # byId is [] when empty, {} when populated
    if isinstance(by_id, list):
        return []

    tasks = [
        BambooTask(id=task_data["id"], name=task_data["name"])
        for task_data in by_id.values()
    ]
    tasks.sort(key=lambda t: t.name)
    return tasks
