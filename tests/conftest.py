# ABOUTME: Pytest configuration and shared fixtures.
# ABOUTME: Provides temporary config dirs and sample Clockify objects.

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from clockify_export.clockify import ClockifyProject, ClockifyTask, ClockifyTimeEntry
from clockify_export.config import MappingConfig
from clockify_export.utils import StorageManager


@pytest.fixture
def temp_config_dir() -> Path:
    """Create a temporary configuration directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage_manager(temp_config_dir: Path) -> StorageManager:
    """Create a storage manager with temporary directory."""
    return StorageManager(temp_config_dir)


@pytest.fixture
def mapping_config(temp_config_dir: Path) -> MappingConfig:
    """Create a mapping config with temporary directory."""
    return MappingConfig(temp_config_dir)


@pytest.fixture
def sample_clockify_project() -> ClockifyProject:
    """Create a sample Clockify project."""
    return ClockifyProject(
        id="project_123",
        name="Test Project",
        workspaceId="workspace_123",
    )


@pytest.fixture
def sample_clockify_task(sample_clockify_project: ClockifyProject) -> ClockifyTask:
    """Create a sample Clockify task."""
    return ClockifyTask(
        id="task_456",
        name="Development",
        projectId=sample_clockify_project.id,
    )


@pytest.fixture
def sample_clockify_time_entry(
    sample_clockify_project: ClockifyProject,
    sample_clockify_task: ClockifyTask,
) -> ClockifyTimeEntry:
    """Create a sample Clockify time entry."""
    now = datetime.now()
    return ClockifyTimeEntry(
        id="entry_789",
        description="Working on feature X",
        projectId=sample_clockify_project.id,
        taskId=sample_clockify_task.id,
        timeInterval={
            "start": now.isoformat() + "Z",
            "end": (now + timedelta(hours=2)).isoformat() + "Z",
            "duration": "PT2H",
        },
        userId="user_123",
        workspaceId="workspace_123",
    )
