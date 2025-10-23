"""Pydantic models for BambooHR API responses."""

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BambooProject(BaseModel):
    """BambooHR project model."""

    model_config = ConfigDict(populate_by_name=True)

    id: int | str
    name: str


class BambooTask(BaseModel):
    """BambooHR task model."""

    model_config = ConfigDict(populate_by_name=True)

    id: int | str
    name: str


class BambooTimeEntry(BaseModel):
    """BambooHR time entry model."""

    model_config = ConfigDict(populate_by_name=True)

    id: int | str | None = None
    employee_id: int | str = Field(alias="employeeId")
    date: date
    hours: float
    project_id: int | str = Field(alias="projectId")
    task_id: int | str = Field(alias="taskId")
    notes: str = ""

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dictionary.

        Returns:
            Dictionary for API submission.
        """
        return {
            "employeeId": str(self.employee_id),
            "date": self.date.isoformat(),
            "hours": self.hours,
            "projectId": str(self.project_id),
            "taskId": str(self.task_id),
            "notes": self.notes,
        }


class BambooEmployee(BaseModel):
    """BambooHR employee model."""

    model_config = ConfigDict(populate_by_name=True)

    id: int | str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email: str | None = None

    @property
    def display_name(self) -> str:
        """Get employee display name."""
        return f"{self.first_name} {self.last_name}"
