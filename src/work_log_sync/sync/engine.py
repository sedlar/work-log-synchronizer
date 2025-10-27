"""Sync engine for synchronizing work logs between Clockify and BambooHR."""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from work_log_sync.bamboohr import BambooHRClient, BambooTimeEntry
from work_log_sync.clockify import ClockifyClient, ClockifyTimeEntry
from work_log_sync.config import Config
from work_log_sync.sync.mapper import TaskMapper

logger = logging.getLogger(__name__)


class SyncResult:
    """Results from a sync operation."""

    def __init__(self) -> None:
        """Initialize sync result."""
        self.entries_synced = 0
        self.entries_skipped = 0
        self.entries_failed = 0
        self.unmapped_entries: list[str] = []
        self.errors: list[str] = []

    def add_success(self) -> None:
        """Record a successful sync."""
        self.entries_synced += 1

    def add_skip(self) -> None:
        """Record a skipped entry."""
        self.entries_skipped += 1

    def add_failure(self, error: str) -> None:
        """Record a failed sync."""
        self.entries_failed += 1
        self.errors.append(error)

    def add_unmapped(self, key: str) -> None:
        """Record an unmapped entry."""
        self.unmapped_entries.append(key)

    def __str__(self) -> str:
        """String representation of results."""
        return (
            f"Synced: {self.entries_synced}, "
            f"Skipped: {self.entries_skipped}, "
            f"Failed: {self.entries_failed}, "
            f"Unmapped: {len(self.unmapped_entries)}"
        )


class SyncEngine:
    """Main synchronization engine."""

    def __init__(
        self,
        config: Config,
        clockify_client: ClockifyClient,
        bamboohr_client: BambooHRClient,
    ) -> None:
        """Initialize sync engine.

        Args:
            config: Application configuration.
            clockify_client: Clockify API client.
            bamboohr_client: BambooHR API client.
        """
        self.config = config
        self.clockify = clockify_client
        self.bamboohr = bamboohr_client
        self.mapper = TaskMapper(config)

    def sync(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
        dry_run: bool = False,
        interactive: bool = True,
    ) -> SyncResult:
        """Synchronize work logs from Clockify to BambooHR.

        Args:
            from_date: Start date for sync (uses last sync date if not provided).
            to_date: End date for sync (uses today if not provided).
            dry_run: If True, only log changes without making them.
            interactive: If True, prompt for unmapped entries.

        Returns:
            Sync results.
        """
        result = SyncResult()

        # Determine date range
        if from_date is None:
            last_sync = self.config.storage.get_last_sync_date()
            from_date = (last_sync or datetime.now() - timedelta(days=30)).date()

        if to_date is None:
            to_date = date.today()

        logger.info(f"Syncing work logs from {from_date} to {to_date}")

        try:
            # Get current user info
            user_info = self.clockify.get_current_user()
            user_id = user_info["id"]
            workspace_id = user_info["defaultWorkspace"]

            # Get Clockify entries
            start_datetime = datetime.combine(from_date, datetime.min.time())
            end_datetime = datetime.combine(to_date, datetime.max.time())

            clockify_entries = self.clockify.get_time_entries(
                workspace_id=workspace_id,
                user_id=user_id,
                start_date=start_datetime,
                end_date=end_datetime,
            )

            logger.info(f"Found {len(clockify_entries)} Clockify time entries")

            # Get projects for mapping
            projects = self.clockify.list_projects(workspace_id)
            project_map = {p.id: p for p in projects}

            # Get BambooHR employee info for current authenticated user
            # Using ID 0 returns the employee associated with the current OAuth token
            try:
                bamboo_employee = self.bamboohr.get_employee(0)
            except Exception as e:
                logger.error(f"Failed to get current employee info: {e}")
                result.add_failure(f"Could not retrieve employee information: {e}")
                return result

            employee_id = bamboo_employee.id

            # Get existing BambooHR entries
            existing_entries = self.bamboohr.get_timesheet_entries(
                employee_id=employee_id,
                start_date=from_date,
                end_date=to_date,
            )

            # Create a set of existing entries for duplicate detection
            existing_keys = {
                (e.date, str(e.project_id), str(e.task_id), e.hours) for e in existing_entries
            }

            # Sync each Clockify entry
            for entry in clockify_entries:
                try:
                    self._sync_entry(
                        entry=entry,
                        employee_id=employee_id,
                        project_map=project_map,
                        existing_keys=existing_keys,
                        result=result,
                        dry_run=dry_run,
                        interactive=interactive,
                    )
                except Exception as e:
                    logger.error(f"Failed to sync entry {entry.id}: {e}")
                    result.add_failure(str(e))

            # Update last sync date
            if not dry_run:
                self.config.storage.set_last_sync_date(datetime.now())

            logger.info(f"Sync complete: {result}")
            return result

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            result.add_failure(str(e))
            return result

    def _sync_entry(
        self,
        entry: ClockifyTimeEntry,
        employee_id: str | int,
        project_map: dict[str, Any],
        existing_keys: set[tuple[Any, ...]],
        result: SyncResult,
        dry_run: bool = False,
        interactive: bool = True,
    ) -> None:
        """Sync a single Clockify entry to BambooHR.

        Args:
            entry: Clockify time entry.
            workspace_id: Clockify workspace ID.
            employee_id: BambooHR employee ID.
            project_map: Map of project ID to project name.
            existing_keys: Set of existing entry keys for duplicate detection.
            result: Sync result object.
            dry_run: If True, don't actually create entries.
            interactive: If True, prompt for unmapped entries.
        """
        if not entry.project_id:
            logger.debug(f"Skipping entry {entry.id} with no project")
            result.add_skip()
            return

        # Get project name
        project = project_map.get(entry.project_id)
        if not project:
            logger.warning(f"Project {entry.project_id} not found")
            result.add_skip()
            return

        # Create mapping key
        task_name = None
        if entry.task_id:
            # In a real scenario, you'd fetch task name from Clockify API
            task_name = f"task_{entry.task_id}"

        mapping_key = self.mapper.get_unmapped_key(project.name, task_name)

        # Check if should skip
        if self.config.should_skip(mapping_key):
            logger.info(f"Skipping mapped entry: {mapping_key}")
            result.add_skip()
            return

        # Check if mapped
        mapping = self.config.get_mapping_for(mapping_key)
        if not mapping and interactive:
            # Prompt for mapping
            mapping = self.mapper.prompt_for_mapping(mapping_key)
            if mapping:
                self.mapper.save_mapping(mapping_key, mapping)
            else:
                result.add_unmapped(mapping_key)
                return

        if not mapping or self.config.should_skip(mapping_key):
            result.add_unmapped(mapping_key)
            return

        # Get bamboo project and task IDs
        bamboo_project_id = mapping.get("bamboo_project_id")
        bamboo_task_id = mapping.get("bamboo_task_id")

        # Project ID is required, but task ID is optional
        if not bamboo_project_id:
            result.add_unmapped(mapping_key)
            return

        # Get entry date
        entry_date = entry.start_time.date()

        # Check for duplicates
        duration_hours = entry.duration_hours
        duplicate_key = (entry_date, bamboo_project_id, bamboo_task_id, duration_hours)

        if duplicate_key in existing_keys:
            logger.info(f"Entry already exists in BambooHR: {mapping_key}")
            result.add_skip()
            return

        # Prepare BambooHR entry
        notes = entry.description or ""
        bamboo_entry = BambooTimeEntry(
            employee_id=employee_id,
            date=entry_date,
            hours=duration_hours,
            project_id=bamboo_project_id,
            task_id=bamboo_task_id,
            notes=notes,
        )

        # Create entry
        if dry_run:
            logger.info(
                f"[DRY RUN] Would create entry: {mapping_key} -> "
                f"{duration_hours}h on {entry_date}"
            )
            result.add_success()
        else:
            try:
                self.bamboohr.create_timesheet_entry(bamboo_entry)
                logger.info(
                    f"Created BambooHR entry: {mapping_key} -> "
                    f"{duration_hours}h on {entry_date}"
                )
                result.add_success()
                existing_keys.add(duplicate_key)
            except Exception as e:
                logger.error(f"Failed to create BambooHR entry: {e}")
                result.add_failure(str(e))
