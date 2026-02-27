# ABOUTME: Persistent storage for clockify-export configuration.
# ABOUTME: Manages config.yaml and mapping.yaml in ~/.config/clockify-export/.

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "clockify-export"


class StorageManager:
    """Manages config.yaml and mapping.yaml persistence."""

    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "config.yaml"
        self.mapping_file = self.config_dir / "mapping.yaml"

    def load_config(self) -> dict[str, Any]:
        """Load application config (API key, workspace ID)."""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_config(self, config: dict[str, Any]) -> None:
        """Save application config."""
        with open(self.config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def get_api_key(self) -> str | None:
        """Get Clockify API key from config."""
        config = self.load_config()
        value: str | None = config.get("clockify", {}).get("api_key")
        return value

    def get_workspace_id(self) -> str | None:
        """Get Clockify workspace ID from config."""
        config = self.load_config()
        value: str | None = config.get("clockify", {}).get("workspace_id")
        return value

    def load_mapping(self) -> dict[str, Any]:
        """Load project/task mapping configuration."""
        if self.mapping_file.exists():
            with open(self.mapping_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_mapping(self, mapping: dict[str, Any]) -> None:
        """Save project/task mapping configuration."""
        with open(self.mapping_file, "w") as f:
            yaml.dump(mapping, f, default_flow_style=False, sort_keys=False)
