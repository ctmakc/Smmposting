"""Tests for scheduler module — schedules config and manager."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.scheduler.manager import ScheduleManager, ScheduleStatus
from apps.scheduler.schedules import DEFAULT_SCHEDULES, ScheduleConfig


class TestScheduleConfig:
    """Tests for ScheduleConfig dataclass."""

    def test_default_values(self):
        config = ScheduleConfig(
            schedule_id="test",
            cron="0 */6 * * *",
            workflow_type="TestWorkflow",
            task_queue="test-queue",
        )
        assert config.args == {}
        assert config.memo == {}
        assert config.execution_timeout == timedelta(minutes=30)
        assert config.overlap_policy == "SKIP"

    def test_custom_values(self):
        config = ScheduleConfig(
            schedule_id="custom",
            cron="0 0 * * *",
            workflow_type="DailyWorkflow",
            task_queue="daily",
            args={"key": "value"},
            memo={"description": "Daily job"},
            execution_timeout=timedelta(hours=1),
            overlap_policy="BUFFER_ONE",
        )
        assert config.overlap_policy == "BUFFER_ONE"
        assert config.args["key"] == "value"
        assert config.execution_timeout == timedelta(hours=1)


class TestDefaultSchedules:
    """Tests for default schedule configurations."""

    def test_default_schedules_exist(self):
        assert len(DEFAULT_SCHEDULES) >= 2

    def test_ingest_schedule(self):
        ingest = next(
            (s for s in DEFAULT_SCHEDULES if "ingest" in s.schedule_id), None
        )
        assert ingest is not None
        assert ingest.cron == "0 */6 * * *"
        assert ingest.task_queue == "ingest"
        assert ingest.workflow_type == "TrendIngestWorkflow"

    def test_planning_schedule(self):
        planning = next(
            (s for s in DEFAULT_SCHEDULES if "planning" in s.schedule_id), None
        )
        assert planning is not None
        assert planning.cron == "0 */12 * * *"
        assert planning.task_queue == "analyze"

    def test_all_schedules_have_ids(self):
        for s in DEFAULT_SCHEDULES:
            assert s.schedule_id
            assert s.cron
            assert s.task_queue


class TestScheduleManager:
    """Tests for ScheduleManager."""

    @pytest.fixture
    def mock_temporal_client(self):
        client = MagicMock()
        # create_schedule is async
        client.create_schedule = AsyncMock()
        # list_schedules is async iterator
        client.list_schedules = MagicMock()
        return client

    @pytest.fixture
    def manager(self, mock_temporal_client):
        return ScheduleManager(mock_temporal_client)

    def test_build_workflow_args_ingest(self, manager):
        config = ScheduleConfig(
            schedule_id="test-ingest",
            cron="0 */6 * * *",
            workflow_type="TrendIngestWorkflow",
            task_queue="ingest",
        )
        args = manager._build_workflow_args(
            config,
            brand_id="brand_1",
            brand_name="Test Brand",
            niches=["tech"],
            platforms=["tiktok"],
        )
        assert args["brand_id"] == "brand_1"
        assert args["niches"] == ["tech"]
        assert args["platforms"] == ["tiktok"]
        assert args["limit_per_niche"] == 10

    def test_build_workflow_args_planning(self, manager):
        config = ScheduleConfig(
            schedule_id="test-planning",
            cron="0 */12 * * *",
            workflow_type="ContentPlanningWorkflow",
            task_queue="analyze",
        )
        args = manager._build_workflow_args(
            config,
            brand_id="brand_1",
            brand_name="Test Brand",
            niches=["finance"],
            platforms=[],
        )
        assert args["brand_id"] == "brand_1"
        assert args["brand_name"] == "Test Brand"
        assert args["niches"] == ["finance"]
        assert args["num_ideas"] == 5

    def test_build_workflow_args_generic(self, manager):
        config = ScheduleConfig(
            schedule_id="test-generic",
            cron="0 0 * * *",
            workflow_type="UnknownWorkflow",
            task_queue="generic",
            args={"custom": "data"},
        )
        args = manager._build_workflow_args(
            config, brand_id="", brand_name="", niches=[], platforms=[]
        )
        assert args == {"custom": "data"}

    @pytest.mark.asyncio
    async def test_pause_schedule(self, manager, mock_temporal_client):
        mock_handle = AsyncMock()
        mock_temporal_client.get_schedule_handle.return_value = mock_handle

        await manager.pause_schedule("sched-1", note="Test pause")

        mock_temporal_client.get_schedule_handle.assert_called_once_with("sched-1")
        mock_handle.pause.assert_called_once_with(note="Test pause")

    @pytest.mark.asyncio
    async def test_unpause_schedule(self, manager, mock_temporal_client):
        mock_handle = AsyncMock()
        mock_temporal_client.get_schedule_handle.return_value = mock_handle

        await manager.unpause_schedule("sched-1")

        mock_handle.unpause.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_schedule(self, manager, mock_temporal_client):
        mock_handle = AsyncMock()
        mock_temporal_client.get_schedule_handle.return_value = mock_handle

        await manager.delete_schedule("sched-1")

        mock_handle.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_describe_schedule(self, manager, mock_temporal_client):
        mock_handle = AsyncMock()
        mock_desc = MagicMock()
        mock_desc.info.running_actions = []
        mock_desc.info.num_actions = 5
        mock_desc.info.num_actions_missed_catchup_window = 1
        mock_desc.info.recent_actions = [MagicMock()]
        mock_desc.info.next_action_times = []
        mock_desc.schedule.state.paused = False
        mock_handle.describe.return_value = mock_desc
        mock_temporal_client.get_schedule_handle.return_value = mock_handle

        status = await manager.describe_schedule("sched-1")

        assert isinstance(status, ScheduleStatus)
        assert status.schedule_id == "sched-1"
        assert status.running is False
        assert status.paused is False
        assert status.info["num_actions"] == 5


class TestScheduleStatus:
    """Tests for ScheduleStatus dataclass."""

    def test_creation(self):
        status = ScheduleStatus(
            schedule_id="test", running=True, paused=False, info={"key": "val"}
        )
        assert status.schedule_id == "test"
        assert status.running is True
        assert status.paused is False
