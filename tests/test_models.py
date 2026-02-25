# ABOUTME: Tests for Clockify Pydantic models.
# ABOUTME: Validates model creation, time parsing, timezone conversion, and rounding.

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from clockify_export.clockify import ClockifyProject, ClockifyTimeEntry
from clockify_export.clockify.models import parse_iso8601_duration, round_to_minute


class TestClockifyModels:
    """Test Clockify models."""

    def test_clockify_project_creation(self) -> None:
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
        now = datetime.now()
        end = now + timedelta(hours=2)

        entry = ClockifyTimeEntry(
            id="entry_123",
            projectId="project_123",
            taskId="task_123",
            timeInterval={
                "start": now.isoformat() + "Z",
                "end": end.isoformat() + "Z",
                "duration": "PT2H",
            },
            userId="user_123",
            workspaceId="ws_123",
        )

        assert entry.id == "entry_123"
        assert entry.project_id == "project_123"
        assert entry.task_id == "task_123"
        assert entry.duration_hours == 2.0

    def test_clockify_time_entry_start_time(self) -> None:
        now = datetime.now()
        entry = ClockifyTimeEntry(
            id="entry_123",
            projectId="project_123",
            timeInterval={
                "start": now.isoformat() + "Z",
                "end": (now + timedelta(hours=1)).isoformat() + "Z",
                "duration": "PT1H",
            },
            userId="user_123",
            workspaceId="ws_123",
        )

        start = entry.start_time
        assert isinstance(start, datetime)
        assert start.year == now.year


class TestTimezoneConversion:
    """Test timezone conversion and rounding."""

    def test_round_to_minute_rounds_down(self) -> None:
        dt = datetime(2026, 2, 25, 9, 30, 15)
        result = round_to_minute(dt)
        assert result == datetime(2026, 2, 25, 9, 30, 0)

    def test_round_to_minute_rounds_up(self) -> None:
        dt = datetime(2026, 2, 25, 9, 30, 45)
        result = round_to_minute(dt)
        assert result == datetime(2026, 2, 25, 9, 31, 0)

    def test_round_to_minute_exact(self) -> None:
        dt = datetime(2026, 2, 25, 9, 30, 0)
        result = round_to_minute(dt)
        assert result == datetime(2026, 2, 25, 9, 30, 0)

    def test_round_to_minute_boundary(self) -> None:
        """Rounding at 30 seconds should round up."""
        dt = datetime(2026, 2, 25, 9, 59, 30)
        result = round_to_minute(dt)
        assert result == datetime(2026, 2, 25, 10, 0, 0)

    def test_local_start_time(self) -> None:
        entry = ClockifyTimeEntry(
            id="e1",
            timeInterval={
                "start": "2026-02-25T08:00:00Z",
                "end": "2026-02-25T12:00:00Z",
                "duration": "PT4H",
            },
            userId="u1",
            workspaceId="ws1",
        )
        tz = ZoneInfo("Europe/Prague")
        local = entry.local_start_time(tz)
        # UTC+1 in February (CET)
        assert local.hour == 9
        assert local.minute == 0

    def test_local_end_time(self) -> None:
        entry = ClockifyTimeEntry(
            id="e1",
            timeInterval={
                "start": "2026-02-25T08:00:00Z",
                "end": "2026-02-25T12:00:00Z",
                "duration": "PT4H",
            },
            userId="u1",
            workspaceId="ws1",
        )
        tz = ZoneInfo("Europe/Prague")
        local = entry.local_end_time(tz)
        assert local is not None
        assert local.hour == 13
        assert local.minute == 0


class TestIsoDuration:
    """Test ISO 8601 duration parsing."""

    def test_hours_only(self) -> None:
        assert parse_iso8601_duration("PT4H") == 4.0

    def test_minutes_only(self) -> None:
        assert parse_iso8601_duration("PT30M") == 0.5

    def test_hours_and_minutes(self) -> None:
        assert parse_iso8601_duration("PT1H30M") == 1.5

    def test_empty_string(self) -> None:
        assert parse_iso8601_duration("") == 0.0
