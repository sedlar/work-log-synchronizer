"""Pydantic models for Clockify API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
    project_id: str | None = Field(default=None, alias="projectId")
    task_id: str | None = Field(default=None, alias="taskId")
    time_interval: dict[str, str] = Field(alias="timeInterval")
    duration: int  # in milliseconds
    user_id: str = Field(alias="userId")
    workspace_id: str = Field(alias="workspaceId")
    tags: list[ClockifyTag] = Field(default_factory=list)
    billable: bool = False

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
        """Get duration in hours."""
        return self.duration / (1000 * 60 * 60)
