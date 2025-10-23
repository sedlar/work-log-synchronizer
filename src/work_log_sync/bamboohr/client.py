"""BambooHR API client."""

import base64
import logging
from datetime import date
from typing import Any

import httpx

from work_log_sync.bamboohr.models import BambooEmployee, BambooProject, BambooTask, BambooTimeEntry
from work_log_sync.utils import StorageManager

logger = logging.getLogger(__name__)


class BambooHRClient:
    """Client for BambooHR API."""

    BASE_URL = "https://api.bamboohr.com/api/gateway.php"

    def __init__(
        self,
        domain: str,
        api_key: str | None = None,
        storage: StorageManager | None = None,
    ) -> None:
        """Initialize BambooHR client.

        Args:
            domain: BambooHR domain/subdomain (e.g., 'mycompany').
            api_key: BambooHR API key. If None, will try to load from storage.
            storage: StorageManager instance for token caching.

        Raises:
            ValueError: If API key is not provided or found.
        """
        self.domain = domain
        self.storage = storage or StorageManager()
        self.api_key = api_key or self.storage.get_token("bamboohr")

        if not self.api_key:
            raise ValueError("BambooHR API key not provided or found in storage")

        # BambooHR uses Basic Auth with API key as username
        auth_string = base64.b64encode(f"{self.api_key}:x".encode()).decode()

        self.client = httpx.Client(
            base_url=f"{self.BASE_URL}/{domain}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Basic {auth_string}",
            },
            timeout=30.0,
        )

    def get_employees(self) -> list[BambooEmployee]:
        """Get list of all employees.

        Returns:
            List of employees.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        response = self.client.get("/v1/employees/directory")
        response.raise_for_status()
        data = response.json()

        employees = []
        for item in data.get("employees", []):
            employees.append(BambooEmployee(**item))
        return employees

    def get_employee(self, employee_id: int | str) -> BambooEmployee:
        """Get employee details.

        Args:
            employee_id: Employee ID.

        Returns:
            Employee information.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        response = self.client.get(f"/v1/employees/{employee_id}")
        response.raise_for_status()
        return BambooEmployee(**response.json())

    def list_projects(self) -> list[BambooProject]:
        """List all projects.

        Returns:
            List of projects.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        response = self.client.get("/v1/projects")
        response.raise_for_status()
        data = response.json()

        projects = []
        for item in data.get("projects", []):
            projects.append(BambooProject(**item))
        return projects

    def get_project(self, project_id: int | str) -> BambooProject:
        """Get project details.

        Args:
            project_id: Project ID.

        Returns:
            Project information.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        response = self.client.get(f"/v1/projects/{project_id}")
        response.raise_for_status()
        return BambooProject(**response.json())

    def list_project_tasks(self, project_id: int | str) -> list[BambooTask]:
        """List tasks for a project.

        Args:
            project_id: Project ID.

        Returns:
            List of tasks.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        response = self.client.get(f"/v1/projects/{project_id}/tasks")
        response.raise_for_status()
        data = response.json()

        tasks = []
        for item in data.get("tasks", []):
            tasks.append(BambooTask(**item))
        return tasks

    def get_timesheet_entries(
        self,
        employee_id: int | str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[BambooTimeEntry]:
        """Get timesheet entries for an employee.

        Args:
            employee_id: Employee ID.
            start_date: Start date filter.
            end_date: End date filter.

        Returns:
            List of timesheet entries.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        params: dict[str, str] = {}
        if start_date:
            params["start"] = start_date.isoformat()
        if end_date:
            params["end"] = end_date.isoformat()

        response = self.client.get(
            f"/v1/employees/{employee_id}/timesheets",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        entries = []
        for item in data.get("timesheets", []):
            entries.append(BambooTimeEntry(**item))
        return entries

    def create_timesheet_entry(self, entry: BambooTimeEntry) -> BambooTimeEntry:
        """Create a new timesheet entry.

        Args:
            entry: Timesheet entry to create.

        Returns:
            Created entry with ID.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        payload = entry.to_api_dict()

        response = self.client.post(
            f"/v1/employees/{entry.employee_id}/timesheets",
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        entry.id = result.get("id")
        return entry

    def update_timesheet_entry(self, entry_id: int | str, entry: BambooTimeEntry) -> None:
        """Update an existing timesheet entry.

        Args:
            entry_id: Timesheet entry ID.
            entry: Updated entry data.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        payload = entry.to_api_dict()

        response = self.client.put(
            f"/v1/timesheets/{entry_id}",
            json=payload,
        )
        response.raise_for_status()

    def delete_timesheet_entry(self, entry_id: int | str) -> None:
        """Delete a timesheet entry.

        Args:
            entry_id: Timesheet entry ID.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        response = self.client.delete(f"/v1/timesheets/{entry_id}")
        response.raise_for_status()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "BambooHRClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
