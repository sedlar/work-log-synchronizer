# ABOUTME: Tests for the export engine.
# ABOUTME: Validates timezone conversion, merging, overlap detection, and JSON output.

import tempfile
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from clockify_export.clockify.models import ClockifyTimeEntry
from clockify_export.config import MappingConfig, MappingEntry
from clockify_export.export import ExportEntry, build_export, generate_json, ExportResult


def _make_entry(
    entry_id: str,
    project_id: str,
    task_id: str | None,
    start: str,
    end: str,
    description: str = "",
) -> ClockifyTimeEntry:
    """Helper to create a ClockifyTimeEntry."""
    return ClockifyTimeEntry(
        id=entry_id,
        description=description,
        projectId=project_id,
        taskId=task_id,
        timeInterval={"start": start, "end": end, "duration": "PT1H"},
        userId="user_1",
        workspaceId="ws_1",
    )


def _make_mapping(config_dir: Path) -> MappingConfig:
    mapping = MappingConfig(config_dir)
    mapping.add(MappingEntry("Project Alpha", "Development", 10, 24))
    mapping.add(MappingEntry("Project Alpha", "Review", 10, 25))
    mapping.add(MappingEntry("Internal", None, 5, None))
    return mapping


class TestBuildExport:
    """Test the build_export function."""

    def test_basic_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping = _make_mapping(Path(tmpdir))
            entries = [
                _make_entry("e1", "p1", "t1", "2026-02-25T08:00:00Z", "2026-02-25T12:00:00Z", "Work"),
            ]
            project_names = {"p1": "Project Alpha"}
            task_names = {"t1": "Development"}

            result = build_export(entries, project_names, task_names, mapping, ZoneInfo("UTC"))

            assert len(result.entries) == 1
            assert result.entries[0].date == date(2026, 2, 25)
            assert result.entries[0].start == "08:00"
            assert result.entries[0].end == "12:00"
            assert result.entries[0].project_id == 10
            assert result.entries[0].task_id == 24

    def test_timezone_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping = _make_mapping(Path(tmpdir))
            entries = [
                _make_entry("e1", "p1", "t1", "2026-02-25T08:00:00Z", "2026-02-25T12:00:00Z"),
            ]
            project_names = {"p1": "Project Alpha"}
            task_names = {"t1": "Development"}

            # CET = UTC+1
            result = build_export(entries, project_names, task_names, mapping, ZoneInfo("Europe/Prague"))

            assert result.entries[0].start == "09:00"
            assert result.entries[0].end == "13:00"

    def test_merges_adjacent_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping = _make_mapping(Path(tmpdir))
            entries = [
                _make_entry("e1", "p1", "t1", "2026-02-25T08:00:00Z", "2026-02-25T10:00:00Z", "Part 1"),
                _make_entry("e2", "p1", "t1", "2026-02-25T10:00:00Z", "2026-02-25T12:00:00Z", "Part 2"),
            ]
            project_names = {"p1": "Project Alpha"}
            task_names = {"t1": "Development"}

            result = build_export(entries, project_names, task_names, mapping, ZoneInfo("UTC"))

            assert len(result.entries) == 1
            assert result.entries[0].start == "08:00"
            assert result.entries[0].end == "12:00"
            assert result.entries[0].note == "Part 1; Part 2"

    def test_does_not_merge_different_projects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping = _make_mapping(Path(tmpdir))
            entries = [
                _make_entry("e1", "p1", "t1", "2026-02-25T08:00:00Z", "2026-02-25T10:00:00Z"),
                _make_entry("e2", "p1", "t2", "2026-02-25T10:00:00Z", "2026-02-25T12:00:00Z"),
            ]
            project_names = {"p1": "Project Alpha"}
            task_names = {"t1": "Development", "t2": "Review"}

            result = build_export(entries, project_names, task_names, mapping, ZoneInfo("UTC"))

            assert len(result.entries) == 2

    def test_detects_overlaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping = _make_mapping(Path(tmpdir))
            entries = [
                _make_entry("e1", "p1", "t1", "2026-02-25T08:00:00Z", "2026-02-25T11:00:00Z"),
                _make_entry("e2", "p1", "t2", "2026-02-25T10:00:00Z", "2026-02-25T12:00:00Z"),
            ]
            project_names = {"p1": "Project Alpha"}
            task_names = {"t1": "Development", "t2": "Review"}

            result = build_export(entries, project_names, task_names, mapping, ZoneInfo("UTC"))

            assert len(result.warnings) == 1
            assert "Overlap" in result.warnings[0]

    def test_unmapped_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping = _make_mapping(Path(tmpdir))
            entries = [
                _make_entry("e1", "p_unknown", None, "2026-02-25T08:00:00Z", "2026-02-25T12:00:00Z"),
            ]
            project_names = {"p_unknown": "Unknown Project"}
            task_names = {}

            result = build_export(entries, project_names, task_names, mapping, ZoneInfo("UTC"))

            assert len(result.entries) == 0
            assert "Unknown Project" in result.unmapped

    def test_skips_running_timers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping = _make_mapping(Path(tmpdir))
            entry = ClockifyTimeEntry(
                id="e1",
                projectId="p1",
                taskId="t1",
                timeInterval={"start": "2026-02-25T08:00:00Z", "duration": "PT0S"},
                userId="u1",
                workspaceId="ws1",
            )
            project_names = {"p1": "Project Alpha"}
            task_names = {"t1": "Development"}

            result = build_export([entry], project_names, task_names, mapping, ZoneInfo("UTC"))

            assert len(result.entries) == 0

    def test_project_only_mapping(self) -> None:
        """Test mapping with task=None (matches any task)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping = _make_mapping(Path(tmpdir))
            entries = [
                _make_entry("e1", "p_int", None, "2026-02-25T08:00:00Z", "2026-02-25T09:00:00Z"),
            ]
            project_names = {"p_int": "Internal"}
            task_names = {}

            result = build_export(entries, project_names, task_names, mapping, ZoneInfo("UTC"))

            assert len(result.entries) == 1
            assert result.entries[0].project_id == 5
            assert result.entries[0].task_id is None


class TestGenerateJson:
    """Test JSON output generation."""

    def test_structure(self) -> None:
        result = ExportResult(
            entries=[
                ExportEntry(
                    date=date(2026, 2, 25),
                    start="09:00",
                    end="12:00",
                    note="Work",
                    project_id=10,
                    task_id=24,
                )
            ]
        )
        output = generate_json(result, date(2026, 2, 25), date(2026, 2, 28))

        assert "metadata" in output
        assert output["metadata"]["source"] == "clockify"
        assert output["metadata"]["date_range"]["from"] == "2026-02-25"
        assert output["metadata"]["date_range"]["to"] == "2026-02-28"
        assert len(output["entries"]) == 1
        assert output["entries"][0]["date"] == "2026-02-25"
        assert output["entries"][0]["start"] == "09:00"
        assert output["entries"][0]["end"] == "12:00"
        assert output["entries"][0]["projectId"] == 10
        assert output["entries"][0]["taskId"] == 24
