# ABOUTME: Export engine that converts Clockify entries to BambooHR-ready JSON.
# ABOUTME: Handles timezone conversion, merging adjacent entries, and overlap detection.

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from clockify_export.clockify.models import ClockifyTimeEntry
from clockify_export.config import MappingConfig

logger = logging.getLogger(__name__)


@dataclass
class ExportEntry:
    """A single time entry ready for BambooHR export."""

    date: date
    start: str  # HH:MM
    end: str  # HH:MM
    note: str
    project_id: int
    task_id: int | None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "date": self.date.isoformat(),
            "start": self.start,
            "end": self.end,
            "note": self.note,
            "projectId": self.project_id,
            "taskId": self.task_id,
        }
        return result


@dataclass
class ExportResult:
    """Result of an export operation."""

    entries: list[ExportEntry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unmapped: list[str] = field(default_factory=list)


def build_export(
    time_entries: list[ClockifyTimeEntry],
    project_names: dict[str, str],
    task_names: dict[str, str],
    mapping: MappingConfig,
    timezone: ZoneInfo,
) -> ExportResult:
    """Convert Clockify time entries to export entries.

    Args:
        time_entries: Raw Clockify time entries.
        project_names: Map of Clockify project ID to project name.
        task_names: Map of Clockify task ID to task name.
        mapping: The project/task mapping configuration.
        timezone: Timezone for converting UTC times to local.
    """
    result = ExportResult()
    converted: list[ExportEntry] = []

    for entry in time_entries:
        if entry.end_time is None:
            logger.warning(f"Skipping running timer entry: {entry.id}")
            continue

        project_name = project_names.get(entry.project_id or "", "")
        task_name = task_names.get(entry.task_id or "") if entry.task_id else None

        if not project_name:
            result.unmapped.append(f"(no project) - {entry.description or entry.id}")
            continue

        mapping_entry = mapping.find(project_name, task_name)
        if mapping_entry is None:
            key = f"{project_name}:{task_name}" if task_name else project_name
            result.unmapped.append(key)
            continue

        local_start = entry.local_start_time(timezone)
        local_end = entry.local_end_time(timezone)
        if local_end is None:
            continue

        converted.append(
            ExportEntry(
                date=local_start.date(),
                start=local_start.strftime("%H:%M"),
                end=local_end.strftime("%H:%M"),
                note=entry.description or "",
                project_id=mapping_entry.bamboo_project_id,
                task_id=mapping_entry.bamboo_task_id,
            )
        )

    # Sort by date then start time
    converted.sort(key=lambda e: (e.date, e.start))

    # Merge back-to-back entries with same project/task
    merged = _merge_adjacent(converted)

    # Detect overlaps
    result.warnings.extend(_detect_overlaps(merged))

    result.entries = merged
    return result


def _merge_adjacent(entries: list[ExportEntry]) -> list[ExportEntry]:
    """Merge entries that are back-to-back with the same project and task."""
    if not entries:
        return []

    merged: list[ExportEntry] = [entries[0]]
    for entry in entries[1:]:
        prev = merged[-1]
        if (
            prev.date == entry.date
            and prev.end == entry.start
            and prev.project_id == entry.project_id
            and prev.task_id == entry.task_id
        ):
            # Merge: extend end time, combine notes
            notes = [prev.note, entry.note]
            combined_note = "; ".join(n for n in notes if n)
            merged[-1] = ExportEntry(
                date=prev.date,
                start=prev.start,
                end=entry.end,
                note=combined_note,
                project_id=prev.project_id,
                task_id=prev.task_id,
            )
        else:
            merged.append(entry)

    return merged


def _detect_overlaps(entries: list[ExportEntry]) -> list[str]:
    """Detect overlapping entries on the same day."""
    warnings: list[str] = []
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            a, b = entries[i], entries[j]
            if a.date != b.date:
                continue
            # Overlap if a.start < b.end and b.start < a.end
            if a.start < b.end and b.start < a.end:
                warnings.append(f"Overlap on {a.date}: {a.start}-{a.end} and {b.start}-{b.end}")
    return warnings


def generate_json(result: ExportResult, from_date: date, to_date: date) -> dict[str, Any]:
    """Generate the final JSON output structure."""
    return {
        "metadata": {
            "exported_at": datetime.now(ZoneInfo("UTC")).isoformat(),
            "source": "clockify",
            "date_range": {
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
            },
        },
        "entries": [entry.to_dict() for entry in result.entries],
    }
