"""Pydantic models for Clockify API responses."""

from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field


def parse_iso8601_duration(duration_str: str) -> float:
    """Parse ISO 8601 duration string to hours.

    Args:
        duration_str: Duration in ISO 8601 format (e.g., 'PT4H', 'PT30M', 'PT1H30M')

    Returns:
        Duration in hours as a float.
    """
    if not duration_str:
        return 0.0

    # Pattern for ISO 8601 duration: PT[n]H[n]M[n]S
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?'
    match = re.match(pattern, duration_str)

    if not match:
        return 0.0

    hours, minutes, seconds = match.groups()
    total_hours = 0.0

    if hours:
        total_hours += float(hours)
    if minutes:
        total_hours += float(minutes) / 60
    if seconds:
        total_hours += float(seconds) / 3600

    return total_hours


class ClockifyProject(BaseModel):
    """Clockify project model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    workspace_id: str = Field(alias="workspaceId")
    archived: bool = False


class ClockifyTag(BaseModel):
    """Clockify tag model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str


class ClockifyTask(BaseModel):
    """Clockify task model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    project_id: str = Field(alias="projectId")
    assigned: bool = False


class ClockifyTimeEntry(BaseModel):
    """Clockify time entry model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    description: str | None = None
    tag_ids: list[str] | None = Field(default=None, alias="tagIds")
    user_id: str = Field(alias="userId")
    billable: bool = False
    task_id: str | None = Field(default=None, alias="taskId")
    project_id: str | None = Field(default=None, alias="projectId")
    workspace_id: str = Field(alias="workspaceId")
    time_interval: dict[str, str] = Field(alias="timeInterval")
    custom_field_values: list = Field(default_factory=list, alias="customFieldValues")
    type: str = "REGULAR"
    kiosk_id: str | None = Field(default=None, alias="kioskId")
    hourly_rate: float | None = Field(default=None, alias="hourlyRate")
    cost_rate: float | None = Field(default=None, alias="costRate")
    is_locked: bool = Field(default=False, alias="isLocked")

    @property
    def start_time(self) -> datetime:
        """Get start time of entry."""
        start_str = self.time_interval.get("start", "")
        return datetime.fromisoformat(start_str.replace("Z", "+00:00"))

    @property
    def end_time(self) -> datetime | None:
        """Get end time of entry."""
        end_str = self.time_interval.get("end")
        if not end_str:
            return None
        return datetime.fromisoformat(end_str.replace("Z", "+00:00"))

    @property
    def duration_hours(self) -> float:
        """Get duration in hours from ISO 8601 duration string."""
        duration_str = self.time_interval.get("duration", "PT0H")
        return parse_iso8601_duration(duration_str)
