# ABOUTME: Pydantic models for Clockify API responses.
# ABOUTME: Includes timezone conversion and minute-rounding helpers.

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field


def parse_iso8601_duration(duration_str: str) -> float:
    """Parse ISO 8601 duration string to hours."""
    if not duration_str:
        return 0.0

    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?"
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


def round_to_minute(dt: datetime) -> datetime:
    """Round a datetime to the nearest minute."""
    if dt.second >= 30:
        dt = dt.replace(second=0, microsecond=0)
        from datetime import timedelta

        dt += timedelta(minutes=1)
    else:
        dt = dt.replace(second=0, microsecond=0)
    return dt


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

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    description: str | None = None
    tag_ids: list[str] | None = Field(default=None, alias="tagIds")
    user_id: str = Field(alias="userId")
    billable: bool = False
    task_id: str | None = Field(default=None, alias="taskId")
    project_id: str | None = Field(default=None, alias="projectId")
    workspace_id: str = Field(alias="workspaceId")
    time_interval: dict[str, str] = Field(alias="timeInterval")

    @property
    def start_time(self) -> datetime:
        """Get start time of entry (UTC)."""
        start_str = self.time_interval.get("start", "")
        return datetime.fromisoformat(start_str.replace("Z", "+00:00"))

    @property
    def end_time(self) -> datetime | None:
        """Get end time of entry (UTC)."""
        end_str = self.time_interval.get("end")
        if not end_str:
            return None
        return datetime.fromisoformat(end_str.replace("Z", "+00:00"))

    @property
    def duration_hours(self) -> float:
        """Get duration in hours from ISO 8601 duration string."""
        duration_str = self.time_interval.get("duration", "PT0H")
        return parse_iso8601_duration(duration_str)

    def local_start_time(self, tz: ZoneInfo) -> datetime:
        """Get start time converted to local timezone, rounded to nearest minute."""
        return round_to_minute(self.start_time.astimezone(tz))

    def local_end_time(self, tz: ZoneInfo) -> datetime | None:
        """Get end time converted to local timezone, rounded to nearest minute."""
        if self.end_time is None:
            return None
        return round_to_minute(self.end_time.astimezone(tz))
