"""Pytest configuration and fixtures."""

import json
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from work_log_sync.bamboohr import BambooProject, BambooTask, BambooTimeEntry, BambooEmployee
from work_log_sync.bamboohr.oauth import BambooHROAuthClient, BambooHROAuthConfig, OAuthToken
from work_log_sync.clockify import ClockifyProject, ClockifyTask, ClockifyTimeEntry
from work_log_sync.config import Config
from work_log_sync.utils import StorageManager


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
def config(temp_config_dir: Path) -> Config:
    """Create a config instance with temporary directory."""
    return Config(temp_config_dir)


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
        },
        duration=2 * 60 * 60 * 1000,  # 2 hours in milliseconds
        userId="user_123",
        workspaceId="workspace_123",
    )


@pytest.fixture
def sample_bamboo_project() -> BambooProject:
    """Create a sample BambooHR project."""
    return BambooProject(
        id="1",
        name="Test Project",
    )


@pytest.fixture
def sample_bamboo_task(sample_bamboo_project: BambooProject) -> BambooTask:
    """Create a sample BambooHR task."""
    return BambooTask(
        id="101",
        name="Development",
    )


@pytest.fixture
def sample_bamboo_employee() -> BambooEmployee:
    """Create a sample BambooHR employee."""
    return BambooEmployee(
        id="1001",
        firstName="John",
        lastName="Doe",
        email="john.doe@example.com",
    )


@pytest.fixture
def sample_bamboo_time_entry(
    sample_bamboo_employee: BambooEmployee,
    sample_bamboo_project: BambooProject,
    sample_bamboo_task: BambooTask,
) -> BambooTimeEntry:
    """Create a sample BambooHR time entry."""
    return BambooTimeEntry(
        id="10001",
        employeeId=sample_bamboo_employee.id,
        date=date.today(),
        hours=2.0,
        projectId=sample_bamboo_project.id,
        taskId=sample_bamboo_task.id,
        notes="Working on feature X",
    )


@pytest.fixture
def oauth_config() -> BambooHROAuthConfig:
    """Create a sample BambooHR OAuth configuration."""
    return BambooHROAuthConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        domain="testcompany",
    )


@pytest.fixture
def oauth_token() -> OAuthToken:
    """Create a sample OAuth token."""
    return OAuthToken(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_in=3600,
    )


@pytest.fixture
def mock_oauth_client(oauth_config: BambooHROAuthConfig, oauth_token: OAuthToken) -> MagicMock:
    """Create a mock BambooHROAuthClient."""
    mock_client = MagicMock(spec=BambooHROAuthClient)
    mock_client.get_token.return_value = oauth_token
    mock_client.config = oauth_config
    return mock_client
