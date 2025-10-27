"""Tests for sync engine."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from work_log_sync.config import Config
from work_log_sync.sync import SyncEngine, SyncResult


class TestSyncResult:
    """Test SyncResult functionality."""

    def test_initialization(self) -> None:
        """Test SyncResult initialization."""
        result = SyncResult()

        assert result.entries_synced == 0
        assert result.entries_skipped == 0
        assert result.entries_failed == 0
        assert result.unmapped_entries == []
        assert result.errors == []

    def test_add_success(self) -> None:
        """Test recording successful sync."""
        result = SyncResult()
        result.add_success()

        assert result.entries_synced == 1

    def test_add_skip(self) -> None:
        """Test recording skipped entry."""
        result = SyncResult()
        result.add_skip()

        assert result.entries_skipped == 1

    def test_add_failure(self) -> None:
        """Test recording failed sync."""
        result = SyncResult()
        result.add_failure("Test error")

        assert result.entries_failed == 1
        assert "Test error" in result.errors

    def test_add_unmapped(self) -> None:
        """Test recording unmapped entry."""
        result = SyncResult()
        result.add_unmapped("project:task")

        assert len(result.unmapped_entries) == 1
        assert "project:task" in result.unmapped_entries

    def test_str_representation(self) -> None:
        """Test string representation."""
        result = SyncResult()
        result.add_success()
        result.add_skip()
        result.add_failure("error")

        result_str = str(result)
        assert "Synced: 1" in result_str
        assert "Skipped: 1" in result_str
        assert "Failed: 1" in result_str


class TestSyncEngine:
    """Test SyncEngine functionality."""

    def test_initialization(self, config: Config) -> None:
        """Test SyncEngine initialization."""
        mock_clockify = MagicMock()
        mock_bamboohr = MagicMock()

        engine = SyncEngine(
            config=config,
            clockify_client=mock_clockify,
            bamboohr_client=mock_bamboohr,
        )

        assert engine.config == config
        assert engine.clockify == mock_clockify
        assert engine.bamboohr == mock_bamboohr

    def test_sync_no_entries(self, config: Config) -> None:
        """Test sync with no entries."""
        mock_clockify = MagicMock()
        mock_bamboohr = MagicMock()
        mock_clockify.get_user_id.return_value = "user_123"
        mock_clockify.get_current_user.return_value = {
            "id": "user_123",
            "defaultWorkspace": "ws_123",
        }
        mock_clockify.get_time_entries.return_value = []
        mock_clockify.list_projects.return_value = []
        mock_bamboohr.list_projects.return_value = []
        mock_bamboohr.get_employees.return_value = []

        engine = SyncEngine(
            config=config,
            clockify_client=mock_clockify,
            bamboohr_client=mock_bamboohr,
        )

        result = engine.sync(
            from_date=date(2024, 1, 1),
            to_date=date(2024, 1, 2),
            dry_run=True,
            interactive=False,
        )

        assert result.entries_synced == 0
        assert result.entries_skipped == 0

    def test_sync_with_error(self, config: Config) -> None:
        """Test sync handling errors gracefully."""
        mock_clockify = MagicMock()
        mock_bamboohr = MagicMock()
        mock_clockify.get_user_id.side_effect = Exception("API error")

        engine = SyncEngine(
            config=config,
            clockify_client=mock_clockify,
            bamboohr_client=mock_bamboohr,
        )

        result = engine.sync(
            from_date=date(2024, 1, 1),
            to_date=date(2024, 1, 2),
            dry_run=True,
            interactive=False,
        )

        assert result.entries_failed > 0
        assert len(result.errors) > 0

    def test_sync_dry_run_mode(self, config: Config) -> None:
        """Test sync in dry-run mode."""
        mock_clockify = MagicMock()
        mock_bamboohr = MagicMock()

        mock_clockify.get_user_id.return_value = "user_123"
        mock_clockify.get_current_user.return_value = {
            "id": "user_123",
            "defaultWorkspace": "ws_123",
        }
        mock_clockify.get_time_entries.return_value = []
        mock_clockify.list_projects.return_value = []
        mock_bamboohr.list_projects.return_value = []
        mock_bamboohr.get_employees.return_value = []

        engine = SyncEngine(
            config=config,
            clockify_client=mock_clockify,
            bamboohr_client=mock_bamboohr,
        )

        # In dry-run mode, last_sync_date should not be updated
        result = engine.sync(
            from_date=date(2024, 1, 1),
            to_date=date(2024, 1, 2),
            dry_run=True,
            interactive=False,
        )

        # Verify create_timesheet_entry was not called
        mock_bamboohr.create_timesheet_entry.assert_not_called()
