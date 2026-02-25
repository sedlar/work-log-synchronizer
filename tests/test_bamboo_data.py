# ABOUTME: Tests for BambooHR js-timesheet-data.json parser.
# ABOUTME: Validates project/task extraction including empty-list edge cases.

import json
import tempfile
from pathlib import Path

from clockify_export.bamboo_data import parse_timesheet_data


class TestParseTimesheetData:
    """Test parsing of js-timesheet-data.json files."""

    def _write_json(self, data: dict) -> Path:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(data, f)
        f.close()
        return Path(f.name)

    def test_parses_projects(self) -> None:
        path = self._write_json({
            "projectsWithTasks": {
                "byId": {
                    "5": {"id": 5, "name": "Administration", "tasks": {"byId": [], "allIds": []}},
                    "9": {
                        "id": 9, "name": "Development",
                        "tasks": {
                            "byId": {
                                "15": {"id": 15, "name": "Content"},
                                "16": {"id": 16, "name": "Brand"},
                            },
                            "allIds": ["15", "16"],
                        },
                    },
                },
                "allIds": ["5", "9"],
            }
        })
        projects = parse_timesheet_data(path)

        assert len(projects) == 2
        # Sorted by name
        assert projects[0].name == "Administration"
        assert projects[0].tasks == []
        assert projects[1].name == "Development"
        assert len(projects[1].tasks) == 2

    def test_empty_tasks_as_list(self) -> None:
        """tasks.byId is [] when empty."""
        path = self._write_json({
            "projectsWithTasks": {
                "byId": {
                    "5": {"id": 5, "name": "Admin", "tasks": {"byId": [], "allIds": []}},
                },
                "allIds": ["5"],
            }
        })
        projects = parse_timesheet_data(path)
        assert len(projects) == 1
        assert projects[0].tasks == []

    def test_empty_projects(self) -> None:
        """Empty projectsWithTasks."""
        path = self._write_json({
            "projectsWithTasks": {"byId": {}, "allIds": []}
        })
        projects = parse_timesheet_data(path)
        assert projects == []

    def test_projects_byid_as_list(self) -> None:
        """projectsWithTasks.byId is [] when empty."""
        path = self._write_json({
            "projectsWithTasks": {"byId": [], "allIds": []}
        })
        projects = parse_timesheet_data(path)
        assert projects == []

    def test_tasks_sorted_by_name(self) -> None:
        path = self._write_json({
            "projectsWithTasks": {
                "byId": {
                    "1": {
                        "id": 1, "name": "Project",
                        "tasks": {
                            "byId": {
                                "3": {"id": 3, "name": "Zebra"},
                                "1": {"id": 1, "name": "Apple"},
                            },
                            "allIds": ["3", "1"],
                        },
                    },
                },
                "allIds": ["1"],
            }
        })
        projects = parse_timesheet_data(path)
        assert projects[0].tasks[0].name == "Apple"
        assert projects[0].tasks[1].name == "Zebra"

    def test_with_real_data(self) -> None:
        """Test with the actual js-timesheet-data.json if available."""
        real_path = Path("/home/martin/development/work-log-synchronizer/js-timesheet-data.json")
        if not real_path.exists():
            return

        projects = parse_timesheet_data(real_path)
        assert len(projects) > 0

        # Check known project from the real data
        admin = [p for p in projects if p.name == "Administration"]
        assert len(admin) == 1
        assert admin[0].id == 5
        assert admin[0].tasks == []

        # Check project with tasks
        maintenance = [p for p in projects if p.name == "Maintenance local platforms"]
        assert len(maintenance) == 1
        assert len(maintenance[0].tasks) > 0
