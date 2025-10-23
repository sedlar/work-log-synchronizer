"""Tests for Pydantic models."""

from datetime import date, datetime, timedelta

import pytest

from work_log_sync.bamboohr import BambooTimeEntry, BambooEmployee, BambooProject, BambooTask
from work_log_sync.clockify import ClockifyTimeEntry, ClockifyProject


class TestClockifyModels:
    """Test Clockify models."""

    def test_clockify_project_creation(self) -> None:
        """Test creating a Clockify project model."""
        project = ClockifyProject(
            id="123",
            name="My Project",
            workspaceId="ws_123",
        )

        assert project.id == "123"
        assert project.name == "My Project"
        assert project.workspace_id == "ws_123"
        assert project.archived is False

    def test_clockify_time_entry_creation(self) -> None:
        """Test creating a Clockify time entry model."""
        now = datetime.now()
        end = now + timedelta(hours=2)

        entry = ClockifyTimeEntry(
            id="entry_123",
            projectId="project_123",
            taskId="task_123",
            timeInterval={
                "start": now.isoformat() + "Z",
                "end": end.isoformat() + "Z",
            },
            duration=2 * 60 * 60 * 1000,
            userId="user_123",
            workspaceId="ws_123",
        )

        assert entry.id == "entry_123"
        assert entry.project_id == "project_123"
        assert entry.task_id == "task_123"
        assert entry.duration_hours == 2.0

    def test_clockify_time_entry_start_time(self) -> None:
        """Test getting start time from Clockify entry."""
        now = datetime.now()
        entry = ClockifyTimeEntry(
            id="entry_123",
            projectId="project_123",
            timeInterval={
                "start": now.isoformat() + "Z",
                "end": (now + timedelta(hours=1)).isoformat() + "Z",
            },
            duration=60 * 60 * 1000,
            userId="user_123",
            workspaceId="ws_123",
        )

        start = entry.start_time
        assert isinstance(start, datetime)
        assert start.year == now.year
        assert start.month == now.month
        assert start.day == now.day


class TestBambooHRModels:
    """Test BambooHR models."""

    def test_bamboo_time_entry_creation(self) -> None:
        """Test creating a BambooHR time entry model."""
        entry = BambooTimeEntry(
            employeeId="1001",
            date=date.today(),
            hours=2.5,
            projectId="1",
            taskId="101",
        )

        assert entry.employee_id == "1001"
        assert entry.hours == 2.5
        assert entry.project_id == "1"

    def test_bamboo_time_entry_to_api_dict(self) -> None:
        """Test converting BambooHR entry to API dictionary."""
        entry = BambooTimeEntry(
            employeeId="1001",
            date=date(2024, 1, 15),
            hours=2.5,
            projectId="1",
            taskId="101",
            notes="Test entry",
        )

        api_dict = entry.to_api_dict()
        assert api_dict["employeeId"] == "1001"
        assert api_dict["date"] == "2024-01-15"
        assert api_dict["hours"] == 2.5
        assert api_dict["projectId"] == "1"
        assert api_dict["taskId"] == "101"
        assert api_dict["notes"] == "Test entry"

    def test_bamboo_employee_display_name(self) -> None:
        """Test employee display name."""
        employee = BambooEmployee(
            id="1001",
            firstName="John",
            lastName="Doe",
        )

        assert employee.display_name == "John Doe"

    def test_bamboo_project_creation(self) -> None:
        """Test creating a BambooHR project model."""
        project = BambooProject(id="1", name="Test Project")
        assert project.id == "1"
        assert project.name == "Test Project"

    def test_bamboo_task_creation(self) -> None:
        """Test creating a BambooHR task model."""
        task = BambooTask(id="101", name="Development")
        assert task.id == "101"
        assert task.name == "Development"
