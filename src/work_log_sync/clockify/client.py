"""Clockify API client."""

import logging
from datetime import datetime
from typing import Any

import httpx

from work_log_sync.clockify.models import ClockifyProject, ClockifyTask, ClockifyTimeEntry
from work_log_sync.utils import StorageManager

logger = logging.getLogger(__name__)


class ClockifyClient:
    """Client for Clockify API."""

    BASE_URL = "https://api.clockify.me/api/v1"

    def __init__(self, api_key: str | None = None, storage: StorageManager | None = None) -> None:
        """Initialize Clockify client.

        Args:
            api_key: Clockify API key. If None, will try to load from storage.
            storage: StorageManager instance for token caching.
        """
        self.storage = storage or StorageManager()
        self.api_key = api_key or self.storage.get_token("clockify")

        if not self.api_key:
            raise ValueError("Clockify API key not provided or found in storage")

        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"X-Api-Key": self.api_key},
            timeout=30.0,
        )

    def get_current_user(self) -> dict[str, Any]:
        """Get current authenticated user.

        Returns:
            User information.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        response = self.client.get("/user")
        response.raise_for_status()
        return response.json()

    def get_user_id(self) -> str:
        """Get current user's ID.

        Returns:
            User ID.
        """
        user = self.get_current_user()
        return user["id"]

    def list_projects(self, workspace_id: str) -> list[ClockifyProject]:
        """List all projects in a workspace.

        Args:
            workspace_id: Workspace ID.

        Returns:
            List of projects.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        response = self.client.get(f"/workspaces/{workspace_id}/projects")
        response.raise_for_status()
        data = response.json()

        projects = []
        for item in data:
            projects.append(ClockifyProject(**item))
        return projects

    def list_tasks(self, workspace_id: str, project_id: str) -> list[ClockifyTask]:
        """List all tasks in a project.

        Args:
            workspace_id: Workspace ID.
            project_id: Project ID.

        Returns:
            List of tasks.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        response = self.client.get(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks"
        )
        response.raise_for_status()
        data = response.json()

        tasks = []
        for item in data:
            tasks.append(ClockifyTask(**item))
        return tasks

    def get_time_entries(
        self,
        workspace_id: str,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[ClockifyTimeEntry]:
        """Get time entries for a user.

        Args:
            workspace_id: Workspace ID.
            user_id: User ID.
            start_date: Start date for filtering (inclusive).
            end_date: End date for filtering (inclusive).

        Returns:
            List of time entries.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        params: dict[str, Any] = {}

        if start_date:
            params["start"] = start_date.isoformat() + "Z"
        if end_date:
            params["end"] = end_date.isoformat() + "Z"

        response = self.client.get(
            f"/workspaces/{workspace_id}/user/{user_id}/time-entries",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        entries = []
        for item in data:
            entries.append(ClockifyTimeEntry(**item))
        return entries

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "ClockifyClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
