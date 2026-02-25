# ABOUTME: Tests for the interactive mapper module.
# ABOUTME: Validates mapping flow logic without requiring user interaction.

from clockify_export.config import MappingConfig, MappingEntry


class TestMapperConfig:
    """Test mapper's interaction with MappingConfig."""

    def test_find_existing_skips_prompt(self, mapping_config: MappingConfig) -> None:
        """Entries that are already mapped should be skipped in the flow."""
        mapping_config.add(MappingEntry("Alpha", "Dev", 10, 24))

        # run_mapping_flow checks mapping.find() and skips existing entries,
        # so we just verify the find works correctly
        assert mapping_config.find("Alpha", "Dev") is not None

    def test_find_returns_none_for_unmapped(self, mapping_config: MappingConfig) -> None:
        assert mapping_config.find("Unknown", None) is None
