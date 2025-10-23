"""Tests for configuration management."""

import pytest

from work_log_sync.config import Config


class TestConfig:
    """Test Config functionality."""

    def test_init_loads_mapping(self, config: Config) -> None:
        """Test that Config loads mapping on initialization."""
        mapping = config.get_mapping()
        assert isinstance(mapping, dict)

    def test_update_mapping(self, config: Config) -> None:
        """Test updating a mapping."""
        config.update_mapping(
            "project_1:task_1",
            {
                "bamboo_project_id": "1",
                "bamboo_task_id": "101",
            },
        )

        mapping = config.get_mapping_for("project_1:task_1")
        assert mapping is not None
        assert mapping["bamboo_project_id"] == "1"
        assert mapping["bamboo_task_id"] == "101"

    def test_get_mapping_for_nonexistent(self, config: Config) -> None:
        """Test getting mapping for non-existent key."""
        mapping = config.get_mapping_for("nonexistent")
        assert mapping is None

    def test_is_mapped_true(self, config: Config) -> None:
        """Test is_mapped returns True for mapped entry."""
        config.update_mapping(
            "project_1:task_1",
            {
                "bamboo_project_id": "1",
                "bamboo_task_id": "101",
            },
        )

        assert config.is_mapped("project_1:task_1") is True

    def test_is_mapped_false(self, config: Config) -> None:
        """Test is_mapped returns False for unmapped entry."""
        assert config.is_mapped("nonexistent") is False

    def test_should_skip_true(self, config: Config) -> None:
        """Test should_skip returns True for skipped entry."""
        config.update_mapping(
            "project_1:task_1",
            {"skip": True},
        )

        assert config.should_skip("project_1:task_1") is True

    def test_should_skip_false(self, config: Config) -> None:
        """Test should_skip returns False for non-skipped entry."""
        assert config.should_skip("nonexistent") is False

    def test_is_mapped_with_skip(self, config: Config) -> None:
        """Test is_mapped returns True for skipped entry."""
        config.update_mapping(
            "project_1:task_1",
            {"skip": True},
        )

        # Should be considered "mapped" even if skipped
        assert config.is_mapped("project_1:task_1") is True

    def test_multiple_mappings(self, config: Config) -> None:
        """Test managing multiple mappings."""
        config.update_mapping(
            "project_1:task_1",
            {
                "bamboo_project_id": "1",
                "bamboo_task_id": "101",
            },
        )
        config.update_mapping(
            "project_2:task_2",
            {
                "bamboo_project_id": "2",
                "bamboo_task_id": "202",
            },
        )

        mapping1 = config.get_mapping_for("project_1:task_1")
        mapping2 = config.get_mapping_for("project_2:task_2")

        assert mapping1["bamboo_project_id"] == "1"
        assert mapping2["bamboo_project_id"] == "2"
