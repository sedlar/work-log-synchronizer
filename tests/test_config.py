# ABOUTME: Tests for MappingConfig and MappingEntry.
# ABOUTME: Validates find, add, persistence, and fallback behavior.

from clockify_export.config import MappingConfig, MappingEntry


class TestMappingEntry:
    """Test MappingEntry dataclass."""

    def test_to_dict(self) -> None:
        entry = MappingEntry(
            clockify_project="Alpha",
            clockify_task="Dev",
            bamboo_project_id=10,
            bamboo_task_id=24,
        )
        d = entry.to_dict()
        assert d["clockify_project"] == "Alpha"
        assert d["clockify_task"] == "Dev"
        assert d["bamboo_project_id"] == 10
        assert d["bamboo_task_id"] == 24

    def test_from_dict(self) -> None:
        entry = MappingEntry.from_dict(
            {
                "clockify_project": "Alpha",
                "clockify_task": None,
                "bamboo_project_id": 5,
                "bamboo_task_id": None,
            }
        )
        assert entry.clockify_project == "Alpha"
        assert entry.clockify_task is None
        assert entry.bamboo_project_id == 5
        assert entry.bamboo_task_id is None

    def test_from_dict_missing_task(self) -> None:
        entry = MappingEntry.from_dict(
            {
                "clockify_project": "Alpha",
                "bamboo_project_id": 5,
            }
        )
        assert entry.clockify_task is None
        assert entry.bamboo_task_id is None


class TestMappingConfig:
    """Test MappingConfig functionality."""

    def test_empty_by_default(self, mapping_config: MappingConfig) -> None:
        assert mapping_config.all_entries() == []

    def test_add_and_find(self, mapping_config: MappingConfig) -> None:
        entry = MappingEntry("Alpha", "Dev", 10, 24)
        mapping_config.add(entry)

        found = mapping_config.find("Alpha", "Dev")
        assert found is not None
        assert found.bamboo_project_id == 10
        assert found.bamboo_task_id == 24

    def test_find_not_found(self, mapping_config: MappingConfig) -> None:
        assert mapping_config.find("Nonexistent", None) is None

    def test_find_falls_back_to_project_only(self, mapping_config: MappingConfig) -> None:
        """When no exact match, fall back to task=None mapping."""
        entry = MappingEntry("Alpha", None, 10, None)
        mapping_config.add(entry)

        found = mapping_config.find("Alpha", "SomeTask")
        assert found is not None
        assert found.bamboo_project_id == 10

    def test_find_prefers_exact_match(self, mapping_config: MappingConfig) -> None:
        general = MappingEntry("Alpha", None, 10, None)
        specific = MappingEntry("Alpha", "Dev", 10, 24)
        mapping_config.add(general)
        mapping_config.add(specific)

        found = mapping_config.find("Alpha", "Dev")
        assert found is not None
        assert found.bamboo_task_id == 24

    def test_add_overwrites_existing(self, mapping_config: MappingConfig) -> None:
        mapping_config.add(MappingEntry("Alpha", "Dev", 10, 24))
        mapping_config.add(MappingEntry("Alpha", "Dev", 10, 99))

        found = mapping_config.find("Alpha", "Dev")
        assert found is not None
        assert found.bamboo_task_id == 99
        assert len(mapping_config.all_entries()) == 1

    def test_persistence(self, mapping_config: MappingConfig) -> None:
        """Test that entries survive reload."""
        mapping_config.add(MappingEntry("Alpha", "Dev", 10, 24))

        # Reload from disk
        reloaded = MappingConfig(mapping_config.storage.config_dir)
        found = reloaded.find("Alpha", "Dev")
        assert found is not None
        assert found.bamboo_project_id == 10

    def test_multiple_entries(self, mapping_config: MappingConfig) -> None:
        mapping_config.add(MappingEntry("Alpha", "Dev", 10, 24))
        mapping_config.add(MappingEntry("Beta", None, 5, None))

        assert len(mapping_config.all_entries()) == 2
        assert mapping_config.find("Alpha", "Dev") is not None
        assert mapping_config.find("Beta", None) is not None
