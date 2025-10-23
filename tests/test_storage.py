"""Tests for storage manager."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from work_log_sync.utils import StorageManager


class TestStorageManager:
    """Test StorageManager functionality."""

    def test_init_creates_directory(self, temp_config_dir: Path) -> None:
        """Test that initialization creates the config directory."""
        assert temp_config_dir.exists()
        storage = StorageManager(temp_config_dir)
        assert storage.config_dir == temp_config_dir

    def test_mapping_persistence(self, storage_manager: StorageManager) -> None:
        """Test saving and loading mappings."""
        mapping = {
            "projects": {
                "project_1:task_1": {
                    "bamboo_project_id": "1",
                    "bamboo_task_id": "101",
                }
            }
        }

        storage_manager.save_mapping(mapping)
        loaded = storage_manager.load_mapping()

        assert loaded == mapping

    def test_state_persistence(self, storage_manager: StorageManager) -> None:
        """Test saving and loading state."""
        state = {
            "last_sync_date": "2024-01-01T12:00:00",
            "last_sync_count": 5,
        }

        storage_manager.save_state(state)
        loaded = storage_manager.load_state()

        assert loaded == state

    def test_token_persistence(self, storage_manager: StorageManager) -> None:
        """Test saving and loading tokens."""
        tokens = {
            "clockify": "test_clockify_key",
            "bamboohr": "test_bamboohr_key",
        }

        storage_manager.save_tokens(tokens)
        loaded = storage_manager.load_tokens()

        assert loaded == tokens

    def test_get_set_token(self, storage_manager: StorageManager) -> None:
        """Test getting and setting individual tokens."""
        storage_manager.set_token("clockify", "my_api_key")
        token = storage_manager.get_token("clockify")

        assert token == "my_api_key"

    def test_get_nonexistent_token(self, storage_manager: StorageManager) -> None:
        """Test getting a token that doesn't exist."""
        token = storage_manager.get_token("nonexistent")
        assert token is None

    def test_last_sync_date(self, storage_manager: StorageManager) -> None:
        """Test getting and setting last sync date."""
        now = datetime.now()
        storage_manager.set_last_sync_date(now)

        loaded = storage_manager.get_last_sync_date()
        assert loaded is not None
        # Allow for small time differences due to microseconds
        assert abs((loaded - now).total_seconds()) < 1

    def test_last_sync_date_none(self, storage_manager: StorageManager) -> None:
        """Test getting last sync date when not set."""
        last_sync = storage_manager.get_last_sync_date()
        assert last_sync is None

    def test_empty_mapping_default(self, storage_manager: StorageManager) -> None:
        """Test that loading non-existent mapping returns empty dict."""
        mapping = storage_manager.load_mapping()
        assert mapping == {}

    def test_empty_state_default(self, storage_manager: StorageManager) -> None:
        """Test that loading non-existent state returns empty dict."""
        state = storage_manager.load_state()
        assert state == {}

    def test_empty_tokens_default(self, storage_manager: StorageManager) -> None:
        """Test that loading non-existent tokens returns empty dict."""
        tokens = storage_manager.load_tokens()
        assert tokens == {}
