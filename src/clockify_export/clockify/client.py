# ABOUTME: Clockify API client with pagination and retry support.
# ABOUTME: Handles authentication, workspace listing, and time entry retrieval.

import logging
import time
from datetime import datetime
from typing import Any

import httpx

from clockify_export.clockify.models import ClockifyProject, ClockifyTask, ClockifyTimeEntry

logger = logging.getLogger(__name__)

PAGE_SIZE = 50
RETRY_DELAY_SECONDS = 2


class ClockifyClient:
    """Client for Clockify API."""

    BASE_URL = "https://api.clockify.me/api/v1"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"X-Api-Key": self.api_key},
            timeout=30.0,
        )

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Make an HTTP request with retry-once on 5xx/network errors."""
        try:
            response = self.client.request(method, url, **kwargs)
            if response.status_code >= 500:
                logger.warning(f"Server error {response.status_code}, retrying once...")
                time.sleep(RETRY_DELAY_SECONDS)
                response = self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TransportError:
            logger.warning("Network error, retrying once...")
            time.sleep(RETRY_DELAY_SECONDS)
            response = self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response

    def get_current_user(self) -> dict[str, Any]:
        """Get current authenticated user info."""
        response = self._request("GET", "/user")
        return response.json()

    def get_user_id(self) -> str:
        """Get current user's ID."""
        user = self.get_current_user()
        return user["id"]

    def list_workspaces(self) -> list[dict[str, Any]]:
        """List all workspaces the user has access to."""
        response = self._request("GET", "/workspaces")
        return response.json()

    def list_projects(self, workspace_id: str) -> list[ClockifyProject]:
        """List all projects in a workspace (paginated)."""
        all_projects: list[ClockifyProject] = []
        page = 1
        while True:
            response = self._request(
                "GET",
                f"/workspaces/{workspace_id}/projects",
                params={"page": page, "page-size": PAGE_SIZE},
            )
            data = response.json()
            if not data:
                break
            all_projects.extend(ClockifyProject(**item) for item in data)
            if len(data) < PAGE_SIZE:
                break
            page += 1
        return all_projects

    def list_tasks(self, workspace_id: str, project_id: str) -> list[ClockifyTask]:
        """List all tasks in a project (paginated)."""
        all_tasks: list[ClockifyTask] = []
        page = 1
        while True:
            response = self._request(
                "GET",
                f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
                params={"page": page, "page-size": PAGE_SIZE},
            )
            data = response.json()
            if not data:
                break
            all_tasks.extend(ClockifyTask(**item) for item in data)
            if len(data) < PAGE_SIZE:
                break
            page += 1
        return all_tasks

    def get_time_entries(
        self,
        workspace_id: str,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[ClockifyTimeEntry]:
        """Get time entries for a user (paginated)."""
        params: dict[str, Any] = {"page-size": PAGE_SIZE}

        if start_date:
            params["start"] = start_date.isoformat() + "Z"
        if end_date:
            params["end"] = end_date.isoformat() + "Z"

        all_entries: list[ClockifyTimeEntry] = []
        page = 1
        while True:
            params["page"] = page
            response = self._request(
                "GET",
                f"/workspaces/{workspace_id}/user/{user_id}/time-entries",
                params=params,
            )
            data = response.json()
            if not data:
                break
            all_entries.extend(ClockifyTimeEntry(**item) for item in data)
            if len(data) < PAGE_SIZE:
                break
            page += 1
        return all_entries

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "ClockifyClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
