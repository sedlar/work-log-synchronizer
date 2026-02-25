# ABOUTME: Tests for StorageManager config/mapping persistence.
# ABOUTME: Validates YAML loading, saving, and default values.

from pathlib import Path

from clockify_export.utils import StorageManager


class TestStorageManager:
    """Test StorageManager functionality."""

    def test_init_creates_directory(self, temp_config_dir: Path) -> None:
        """Test that initialization creates the config directory."""
        assert temp_config_dir.exists()
        storage = StorageManager(temp_config_dir)
        assert storage.config_dir == temp_config_dir

    def test_config_persistence(self, storage_manager: StorageManager) -> None:
        """Test saving and loading config."""
        config = {
            "clockify": {
                "api_key": "test-key",
                "workspace_id": "ws-123",
            }
        }
        storage_manager.save_config(config)
        loaded = storage_manager.load_config()
        assert loaded == config

    def test_get_api_key(self, storage_manager: StorageManager) -> None:
        """Test getting API key from config."""
        storage_manager.save_config({"clockify": {"api_key": "my-key", "workspace_id": "ws"}})
        assert storage_manager.get_api_key() == "my-key"

    def test_get_api_key_missing(self, storage_manager: StorageManager) -> None:
        """Test getting API key when not configured."""
        assert storage_manager.get_api_key() is None

    def test_get_workspace_id(self, storage_manager: StorageManager) -> None:
        """Test getting workspace ID from config."""
        storage_manager.save_config({"clockify": {"api_key": "k", "workspace_id": "ws-456"}})
        assert storage_manager.get_workspace_id() == "ws-456"

    def test_mapping_persistence(self, storage_manager: StorageManager) -> None:
        """Test saving and loading mappings."""
        mapping = {
            "mappings": [
                {
                    "clockify_project": "Project Alpha",
                    "clockify_task": "Development",
                    "bamboo_project_id": 10,
                    "bamboo_task_id": 24,
                }
            ]
        }
        storage_manager.save_mapping(mapping)
        loaded = storage_manager.load_mapping()
        assert loaded == mapping

    def test_empty_config_default(self, storage_manager: StorageManager) -> None:
        """Test that loading non-existent config returns empty dict."""
        assert storage_manager.load_config() == {}

    def test_empty_mapping_default(self, storage_manager: StorageManager) -> None:
        """Test that loading non-existent mapping returns empty dict."""
        assert storage_manager.load_mapping() == {}
