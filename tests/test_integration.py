"""Integration tests for Wahoo SYSTM MCP tools.

These tests run against the real Wahoo SYSTM API and require valid credentials.
They are skipped by default and can be run with: pytest -m integration

Required environment variables:
    WAHOO_USERNAME: Wahoo SYSTM account email
    WAHOO_PASSWORD: Wahoo SYSTM account password
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from wahoo_systm_mcp.client import WahooClient
from wahoo_systm_mcp.tools.calendar import (
    get_calendar,
    remove_workout,
    reschedule_workout,
    schedule_workout,
)
from wahoo_systm_mcp.tools.library import (
    get_cycling_workouts,
    get_workout_details,
    get_workouts,
)
from wahoo_systm_mcp.tools.profile import (
    get_fitness_test_details,
    get_fitness_test_history,
    get_rider_profile,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def credentials() -> tuple[str, str]:
    """Get credentials from environment variables."""
    username = os.environ.get("WAHOO_USERNAME")
    password = os.environ.get("WAHOO_PASSWORD")
    if not username or not password:
        pytest.skip("WAHOO_USERNAME and WAHOO_PASSWORD environment variables required")
    return username, password


@pytest.fixture
async def client(credentials: tuple[str, str]) -> AsyncIterator[WahooClient]:
    """Create an authenticated WahooClient."""
    username, password = credentials
    client = WahooClient()
    await client.authenticate(username, password)
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def mock_context(client: WahooClient) -> MagicMock:
    """Create a mock context with the real authenticated client."""
    ctx = MagicMock()
    ctx.lifespan_context = {"client": client}
    return ctx


@pytest.fixture
def future_test_date() -> str:
    """Get a date 60 days in the future for safe calendar operations."""
    future = datetime.now(UTC) + timedelta(days=60)
    return future.strftime("%Y-%m-%d")


@pytest.fixture
def future_reschedule_date() -> str:
    """Get a date 61 days in the future for rescheduling tests."""
    future = datetime.now(UTC) + timedelta(days=61)
    return future.strftime("%Y-%m-%d")


# =============================================================================
# Profile Tools Tests
# =============================================================================


class TestGetRiderProfile:
    """Integration tests for get_rider_profile tool."""

    async def test_returns_valid_profile(self, mock_context: MagicMock) -> None:
        """Should return a complete rider profile with 4DP values."""
        result = await get_rider_profile(mock_context)

        # Verify 4DP structure
        assert result.four_dp is not None
        assert result.four_dp.nm is not None
        assert result.four_dp.ac is not None
        assert result.four_dp.map is not None
        assert result.four_dp.ftp is not None

        # Verify power values are reasonable (> 0)
        assert result.four_dp.nm.watts > 0
        assert result.four_dp.ac.watts > 0
        assert result.four_dp.map.watts > 0
        assert result.four_dp.ftp.watts > 0

        # Verify rider type info
        assert result.rider_type is not None
        assert result.rider_type.name is not None
        assert len(result.rider_type.name) > 0

        # Verify strengths/weaknesses
        assert result.strengths is not None
        assert result.weaknesses is not None


class TestGetFitnessTestHistory:
    """Integration tests for get_fitness_test_history tool."""

    async def test_returns_test_history(self, mock_context: MagicMock) -> None:
        """Should return fitness test history with pagination info."""
        result = await get_fitness_test_history(mock_context, page=1, page_size=5)

        assert result.total >= 0
        assert isinstance(result.tests, list)

        if result.total > 0:
            test = result.tests[0]
            assert test.id is not None
            assert test.name is not None

    async def test_pagination(self, mock_context: MagicMock) -> None:
        """Should respect pagination parameters."""
        result = await get_fitness_test_history(mock_context, page=1, page_size=2)

        # Should return at most page_size items
        assert len(result.tests) <= 2

    async def test_pagination_different_pages(self, mock_context: MagicMock) -> None:
        """Should return different results for different pages."""
        # Get first page
        page1 = await get_fitness_test_history(mock_context, page=1, page_size=1)

        if page1.total < 2:
            pytest.skip("Need at least 2 fitness tests to test pagination")

        # Get second page
        page2 = await get_fitness_test_history(mock_context, page=2, page_size=1)

        # Pages should have different items
        assert len(page1.tests) == 1
        assert len(page2.tests) == 1
        assert page1.tests[0].id != page2.tests[0].id

        # Total should be consistent across pages
        assert page1.total == page2.total


class TestGetFitnessTestDetails:
    """Integration tests for get_fitness_test_details tool."""

    async def test_returns_test_details(self, mock_context: MagicMock) -> None:
        """Should return detailed fitness test data."""
        # First get a test ID from history
        history = await get_fitness_test_history(mock_context, page=1, page_size=1)

        if history.total == 0:
            pytest.skip("No fitness tests available in account")

        test_id = history.tests[0].id
        result = await get_fitness_test_details(mock_context, test_id)

        assert result.name is not None
        assert result.date is not None

        # Power curve should be present for fitness tests
        if result.power_curve:
            assert len(result.power_curve) > 0


# =============================================================================
# Library Tools Tests
# =============================================================================


class TestGetWorkouts:
    """Integration tests for get_workouts tool."""

    async def test_returns_workouts(self, mock_context: MagicMock) -> None:
        """Should return workouts from the library."""
        result = await get_workouts(mock_context, limit=10)

        assert result.total > 0
        assert len(result.workouts) > 0
        assert len(result.workouts) <= 10

        workout = result.workouts[0]
        assert workout.id is not None
        assert workout.name is not None

    async def test_filter_by_sport(self, mock_context: MagicMock) -> None:
        """Should filter workouts by sport type."""
        result = await get_workouts(mock_context, sport="Yoga", limit=5)

        # Filter returns workouts - verify we got results
        assert result.total > 0

    async def test_filter_by_duration(self, mock_context: MagicMock) -> None:
        """Should filter workouts by duration range."""
        result = await get_workouts(mock_context, min_duration=30, max_duration=45, limit=10)

        # Duration is in seconds in the model
        for workout in result.workouts:
            if workout.duration is not None:
                duration_minutes = workout.duration // 60
                assert 30 <= duration_minutes <= 45

    async def test_search_by_name(self, mock_context: MagicMock) -> None:
        """Should search workouts by name."""
        result = await get_workouts(mock_context, search="Nine Hammers", limit=5)

        assert result.total > 0
        # At least one result should contain the search term
        names = [w.name.lower() for w in result.workouts]
        assert any("nine hammers" in name for name in names)

    async def test_filter_by_tss(self, mock_context: MagicMock) -> None:
        """Should filter workouts by TSS range."""
        result = await get_workouts(mock_context, min_tss=50, max_tss=80, limit=10)

        assert result.total > 0
        for workout in result.workouts:
            if workout.metrics and workout.metrics.tss is not None:
                assert 50 <= workout.metrics.tss <= 80

    async def test_filter_by_channel(self, mock_context: MagicMock) -> None:
        """Should filter workouts by content channel."""
        result = await get_workouts(mock_context, channel="The Sufferfest", limit=10)

        assert result.total > 0
        for workout in result.workouts:
            assert workout.channel == "The Sufferfest"

    async def test_channel_id_mapping_complete(self, mock_context: MagicMock) -> None:
        """Should map all channel IDs to human-readable names.

        This test catches when Wahoo changes channel IDs - if a workout has
        a channel that's not in our mapping, it will have a raw ID instead
        of a human-readable name.
        """
        # Get a large sample of workouts to cover multiple channels
        result = await get_workouts(mock_context, limit=100)

        assert result.total > 0

        # Collect all unique channels
        channels = {w.channel for w in result.workouts if w.channel}

        # Known human-readable channel names
        known_channels = {
            "The Sufferfest",
            "Inspiration",
            "A Week With",
            "ProRides",
            "On Location",
            "NoVid",
            "Fitness Test",
            "Getting Started",
            "Wahoo RGT",
        }

        # Any channel that looks like an ID (10-char alphanumeric) is unmapped
        unmapped = {ch for ch in channels if ch not in known_channels and len(ch) == 10}

        assert not unmapped, (
            f"Unmapped channel IDs found: {unmapped}. "
            "Update CHANNEL_ID_TO_NAME in api.py with the correct mappings."
        )

    async def test_sorting(self, mock_context: MagicMock) -> None:
        """Should sort workouts by specified field."""
        result_asc = await get_workouts(
            mock_context, sort_by="duration", sort_direction="asc", limit=10
        )
        result_desc = await get_workouts(
            mock_context, sort_by="duration", sort_direction="desc", limit=10
        )

        assert result_asc.total > 0
        assert result_desc.total > 0

        # Verify ascending order
        durations_asc = [w.duration for w in result_asc.workouts if w.duration]
        if len(durations_asc) > 1:
            assert durations_asc == sorted(durations_asc)

        # Verify descending order
        durations_desc = [w.duration for w in result_desc.workouts if w.duration]
        if len(durations_desc) > 1:
            assert durations_desc == sorted(durations_desc, reverse=True)


class TestGetCyclingWorkouts:
    """Integration tests for get_cycling_workouts tool."""

    async def test_returns_cycling_only(self, mock_context: MagicMock) -> None:
        """Should return only cycling workouts."""
        result = await get_cycling_workouts(mock_context, limit=10)

        assert result.total > 0
        assert len(result.workouts) > 0
        assert len(result.workouts) <= 10
        # Cycling workouts should have metrics with ratings (4DP)
        has_cycling_metrics = any(w.metrics and w.metrics.ratings for w in result.workouts)
        assert has_cycling_metrics

    async def test_filter_by_four_dp_focus(self, mock_context: MagicMock) -> None:
        """Should filter by 4DP focus area."""
        result = await get_cycling_workouts(mock_context, four_dp_focus="FTP", limit=10)

        assert result.total > 0
        # Workouts with FTP focus should have high FTP rating
        for workout in result.workouts:
            if workout.metrics and workout.metrics.ratings:
                assert workout.metrics.ratings.ftp is not None
                assert workout.metrics.ratings.ftp >= 4

    async def test_filter_by_intensity(self, mock_context: MagicMock) -> None:
        """Should filter by intensity level."""
        result = await get_cycling_workouts(mock_context, intensity="Low", limit=10)

        assert result.total > 0
        for workout in result.workouts:
            assert workout.intensity == "Low"

    async def test_filter_by_channel(self, mock_context: MagicMock) -> None:
        """Should filter by content channel."""
        result = await get_cycling_workouts(mock_context, channel="The Sufferfest", limit=10)

        assert result.total > 0
        for workout in result.workouts:
            assert workout.channel == "The Sufferfest"

    async def test_filter_by_category(self, mock_context: MagicMock) -> None:
        """Should filter by workout category."""
        result = await get_cycling_workouts(mock_context, category="Endurance", limit=10)

        assert result.total > 0
        for workout in result.workouts:
            assert workout.category == "Endurance"

    async def test_filter_by_duration(self, mock_context: MagicMock) -> None:
        """Should filter cycling workouts by duration range."""
        result = await get_cycling_workouts(
            mock_context, min_duration=45, max_duration=60, limit=10
        )

        assert result.total > 0
        for workout in result.workouts:
            if workout.duration is not None:
                duration_minutes = workout.duration // 60
                assert 45 <= duration_minutes <= 60

    async def test_filter_by_tss(self, mock_context: MagicMock) -> None:
        """Should filter cycling workouts by TSS range."""
        result = await get_cycling_workouts(mock_context, min_tss=60, max_tss=100, limit=10)

        assert result.total > 0
        for workout in result.workouts:
            if workout.metrics and workout.metrics.tss is not None:
                assert 60 <= workout.metrics.tss <= 100

    async def test_search_by_name(self, mock_context: MagicMock) -> None:
        """Should search cycling workouts by name."""
        result = await get_cycling_workouts(mock_context, search="Revolver", limit=5)

        assert result.total > 0
        names = [w.name.lower() for w in result.workouts]
        assert any("revolver" in name for name in names)

    async def test_sorting(self, mock_context: MagicMock) -> None:
        """Should sort cycling workouts by specified field."""
        result = await get_cycling_workouts(
            mock_context, sort_by="tss", sort_direction="desc", limit=10
        )

        assert result.total > 0
        tss_values = [
            w.metrics.tss for w in result.workouts if w.metrics and w.metrics.tss is not None
        ]
        if len(tss_values) > 1:
            assert tss_values == sorted(tss_values, reverse=True)


class TestGetWorkoutDetails:
    """Integration tests for get_workout_details tool."""

    async def test_returns_workout_details(self, mock_context: MagicMock) -> None:
        """Should return detailed workout information."""
        # First get a workout ID
        workouts = await get_workouts(mock_context, limit=1)
        assert workouts.total > 0

        workout_id = workouts.workouts[0].id
        result = await get_workout_details(mock_context, workout_id)

        assert result.id is not None
        assert result.name is not None
        assert result.sport is not None

    async def test_returns_graph_triggers(self, mock_context: MagicMock) -> None:
        """Should include graph triggers for cycling workouts."""
        # Get cycling workouts which should have graph triggers
        workouts = await get_cycling_workouts(mock_context, limit=5)
        if workouts.total == 0:
            pytest.skip("No cycling workouts available")

        workout_id = workouts.workouts[0].id
        result = await get_workout_details(mock_context, workout_id)

        # Most Sufferfest workouts have graph triggers
        if result.graph_triggers:
            assert len(result.graph_triggers) > 0
            trigger = result.graph_triggers[0]
            assert trigger.time is not None


# =============================================================================
# Calendar Tools Tests
# =============================================================================


class TestGetCalendar:
    """Integration tests for get_calendar tool."""

    async def test_returns_calendar_items(self, mock_context: MagicMock) -> None:
        """Should return calendar items for date range."""
        today = datetime.now(UTC)
        start = today.strftime("%Y-%m-%d")
        end = (today + timedelta(days=30)).strftime("%Y-%m-%d")

        result = await get_calendar(mock_context, start, end)

        # Result should be a list (may be empty if no workouts scheduled)
        assert isinstance(result, list)

    async def test_with_timezone(self, mock_context: MagicMock) -> None:
        """Should handle different timezones."""
        today = datetime.now(UTC)
        start = today.strftime("%Y-%m-%d")
        end = (today + timedelta(days=7)).strftime("%Y-%m-%d")

        result = await get_calendar(mock_context, start, end, time_zone="Europe/Lisbon")

        assert isinstance(result, list)

    async def test_item_structure(
        self,
        mock_context: MagicMock,
    ) -> None:
        """Should return properly structured calendar items when present.

        Note: This test verifies the structure of any calendar item found,
        rather than scheduling a new workout, due to API propagation delays.
        """
        # Query a broad date range to find any existing calendar items
        today = datetime.now(UTC)
        start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end = (today + timedelta(days=90)).strftime("%Y-%m-%d")

        result = await get_calendar(mock_context, start, end, time_zone="UTC")

        assert isinstance(result, list)

        if len(result) == 0:
            pytest.skip("No calendar items found to verify structure")

        # Verify structure of first item
        item = result[0]
        assert item.agenda_id is not None
        assert item.planned_date is not None
        assert item.prospects is not None
        assert len(item.prospects) > 0

        prospect = item.prospects[0]
        assert prospect.name is not None
        assert prospect.type is not None


class TestCalendarCRUD:
    """Integration tests for calendar CRUD operations (schedule, reschedule, remove).

    These tests are idempotent - they create, modify, and remove workouts
    in a future date range that won't conflict with existing scheduled workouts.
    """

    async def test_schedule_reschedule_remove_workflow(
        self,
        mock_context: MagicMock,
        future_test_date: str,
        future_reschedule_date: str,
    ) -> None:
        """Should complete full workflow: schedule -> reschedule -> remove.

        Tests that the CRUD operations succeed without errors.
        Note: Calendar query verification is skipped due to API propagation delays.
        """
        # Get a workout to schedule (use a short one)
        workouts = await get_workouts(mock_context, sport="Cycling", max_duration=30, limit=1)
        assert workouts.total > 0
        workout = workouts.workouts[0]

        # Step 1: Schedule the workout
        schedule_result = await schedule_workout(
            mock_context,
            content_id=workout.id,
            date=future_test_date,
            time_zone="UTC",
        )

        assert schedule_result.success is True
        assert schedule_result.agenda_id is not None
        assert schedule_result.date == future_test_date
        agenda_id = schedule_result.agenda_id

        try:
            # Step 2: Reschedule to a different date
            reschedule_result = await reschedule_workout(
                mock_context,
                agenda_id=agenda_id,
                new_date=future_reschedule_date,
                time_zone="UTC",
            )

            assert reschedule_result.success is True
            assert reschedule_result.new_date == future_reschedule_date
            assert reschedule_result.agenda_id == agenda_id

        finally:
            # Step 3: Clean up - remove the workout
            remove_result = await remove_workout(mock_context, agenda_id=agenda_id)
            assert remove_result.success is True
            assert remove_result.agenda_id == agenda_id
