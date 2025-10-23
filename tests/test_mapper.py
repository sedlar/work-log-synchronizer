"""Tests for task mapper."""

import pytest

from work_log_sync.config import Config
from work_log_sync.sync.mapper import TaskMapper


class TestTaskMapper:
    """Test TaskMapper functionality."""

    def test_get_unmapped_key_project_only(self, config: Config) -> None:
        """Test generating key for project only."""
        mapper = TaskMapper(config)
        key = mapper.get_unmapped_key("My Project")

        assert key == "My Project"

    def test_get_unmapped_key_project_and_task(self, config: Config) -> None:
        """Test generating key for project and task."""
        mapper = TaskMapper(config)
        key = mapper.get_unmapped_key("My Project", "Development")

        assert key == "My Project:Development"

    def test_needs_mapping_unmapped(self, config: Config) -> None:
        """Test needs_mapping for unmapped entry."""
        mapper = TaskMapper(config)

        assert mapper.needs_mapping("unmapped:entry") is True

    def test_needs_mapping_mapped(self, config: Config) -> None:
        """Test needs_mapping for mapped entry."""
        mapper = TaskMapper(config)
        config.update_mapping(
            "project:task",
            {
                "bamboo_project_id": "1",
                "bamboo_task_id": "101",
            },
        )

        assert mapper.needs_mapping("project:task") is False

    def test_needs_mapping_skipped(self, config: Config) -> None:
        """Test needs_mapping for skipped entry."""
        mapper = TaskMapper(config)
        config.update_mapping("project:task", {"skip": True})

        # Even if skipped, it's mapped
        assert mapper.needs_mapping("project:task") is False

    def test_save_mapping(self, config: Config) -> None:
        """Test saving a mapping."""
        mapper = TaskMapper(config)
        mapping = {
            "bamboo_project_id": "1",
            "bamboo_task_id": "101",
        }

        mapper.save_mapping("project:task", mapping)

        saved = config.get_mapping_for("project:task")
        assert saved == mapping
