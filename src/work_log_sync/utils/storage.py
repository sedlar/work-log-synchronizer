"""Storage and configuration management for work log synchronizer."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class StorageManager:
    """Manages configuration, state, and token storage."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize storage manager.

        Args:
            config_dir: Directory to store configuration. Defaults to ~/.work-log-sync/
        """
        self.config_dir = config_dir or Path.home() / ".work-log-sync"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.mapping_file = self.config_dir / "mapping.yaml"
        self.state_file = self.config_dir / "state.json"
        self.tokens_file = self.config_dir / "tokens.json"

    def load_mapping(self) -> dict[str, Any]:
        """Load project/task mapping configuration.

        Returns:
            Mapping configuration dictionary.
        """
        if self.mapping_file.exists():
            with open(self.mapping_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_mapping(self, mapping: dict[str, Any]) -> None:
        """Save project/task mapping configuration.

        Args:
            mapping: Mapping configuration to save.
        """
        with open(self.mapping_file, "w") as f:
            yaml.dump(mapping, f, default_flow_style=False, sort_keys=False)

    def load_state(self) -> dict[str, Any]:
        """Load synchronization state.

        Returns:
            State dictionary with last sync timestamp, etc.
        """
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {}

    def save_state(self, state: dict[str, Any]) -> None:
        """Save synchronization state.

        Args:
            state: State dictionary to save.
        """
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def get_last_sync_date(self) -> datetime | None:
        """Get the date of the last successful synchronization.

        Returns:
            Last sync datetime or None if never synced.
        """
        state = self.load_state()
        if "last_sync_date" in state:
            return datetime.fromisoformat(state["last_sync_date"])
        return None

    def set_last_sync_date(self, date: datetime) -> None:
        """Set the last successful synchronization date.

        Args:
            date: The synchronization datetime.
        """
        state = self.load_state()
        state["last_sync_date"] = date.isoformat()
        self.save_state(state)

    def load_tokens(self) -> dict[str, str]:
        """Load cached authentication tokens.

        Returns:
            Dictionary of service names to tokens.
        """
        if self.tokens_file.exists():
            with open(self.tokens_file) as f:
                return json.load(f)
        return {}

    def save_tokens(self, tokens: dict[str, str]) -> None:
        """Save authentication tokens.

        Args:
            tokens: Dictionary of service names to tokens.
        """
        # Restrict file permissions for security
        self.tokens_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tokens_file, "w") as f:
            json.dump(tokens, f)
        # Set restrictive permissions (user read/write only)
        self.tokens_file.chmod(0o600)

    def get_token(self, service: str) -> str | None:
        """Get cached token for a service.

        Args:
            service: Service name (e.g., "clockify", "bamboohr").

        Returns:
            Token if available, None otherwise.
        """
        tokens = self.load_tokens()
        return tokens.get(service)

    def set_token(self, service: str, token: str) -> None:
        """Save token for a service.

        Args:
            service: Service name.
            token: Authentication token.
        """
        tokens = self.load_tokens()
        tokens[service] = token
        self.save_tokens(tokens)
