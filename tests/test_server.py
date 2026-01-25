"""Tests for FastMCP server tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp.exceptions import ToolError

from wahoo_systm_mcp.models import (
    EnhancedRiderProfile,
    FitnessTestDetails,
    FitnessTestResult,
    LibraryContent,
    UserPlanItem,
    WorkoutDetails,
    WorkoutEquipment,
    WorkoutMetrics,
    WorkoutRatings,
)
from wahoo_systm_mcp.server import (
    _format_date,
    _format_duration,
    get_calendar,
    get_cycling_workouts,
    get_fitness_test_details,
    get_fitness_test_history,
    get_rider_profile,
    get_workout_details,
    get_workouts,
    remove_workout,
    reschedule_workout,
    schedule_workout,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock WahooClient."""
    return MagicMock()


@pytest.fixture
def mock_context(mock_client: MagicMock) -> MagicMock:
    """Create a mock Context with client in lifespan_context."""
    ctx = MagicMock()
    ctx.lifespan_context = {"client": mock_client}
    return ctx


@pytest.fixture
def sample_user_plan_item() -> UserPlanItem:
    """Create a sample UserPlanItem for testing."""
    return UserPlanItem.model_validate(
        {
            "day": 1,
            "plannedDate": "2024-01-15",
            "rank": 1,
            "agendaId": "agenda123",
            "status": "scheduled",
            "type": "workout",
            "prospects": [],
            "plan": {
                "id": "plan1",
                "name": "Base Training",
                "color": "#FF0000",
                "description": "Base building",
                "category": "endurance",
            },
        }
    )


@pytest.fixture
def sample_library_content() -> LibraryContent:
    """Create a sample LibraryContent for testing."""
    return LibraryContent.model_validate(
        {
            "id": "content1",
            "name": "Nine Hammers",
            "mediaType": "video",
            "channel": "The Sufferfest",
            "workoutType": "Cycling",
            "category": "threshold",
            "level": "advanced",
            "duration": 3600,
            "workoutId": "workout1",
            "metrics": {
                "tss": 95,
                "intensityFactor": 0.85,
                "ratings": {"nm": 3, "ac": 4, "map": 4, "ftp": 3},
            },
        }
    )


@pytest.fixture
def sample_workout_details() -> WorkoutDetails:
    """Create a sample WorkoutDetails for testing."""
    return WorkoutDetails(
        id="workout1",
        name="Nine Hammers",
        sport="cycling",
        short_description="A classic Sufferfest workout",
        details="Full details here",
        level="advanced",
        duration_seconds=3600,
        equipment=[WorkoutEquipment(name="Trainer", description="Smart trainer")],
        metrics=WorkoutMetrics(
            intensity_factor=0.85,
            tss=95,
            ratings=WorkoutRatings(nm=3, ac=4, map_=4, ftp=3),
        ),
        graph_triggers=[{"time": 0, "value": 50, "type": "power"}],
    )


@pytest.fixture
def sample_enhanced_profile() -> EnhancedRiderProfile:
    """Create a sample EnhancedRiderProfile for testing."""
    return EnhancedRiderProfile.model_validate(
        {
            "nm": 850,
            "ac": 420,
            "map": 310,
            "ftp": 260,
            "power5s": {"status": "ok", "graphValue": 85, "value": 850},
            "power1m": {"status": "ok", "graphValue": 80, "value": 420},
            "power5m": {"status": "ok", "graphValue": 75, "value": 310},
            "power20m": {"status": "ok", "graphValue": 70, "value": 260},
            "lactateThresholdHeartRate": 168,
            "heartRateZones": [
                {"zone": 1, "name": "Recovery", "min": 100, "max": 120},
                {"zone": 2, "name": "Endurance", "min": 120, "max": 140},
            ],
            "riderType": {
                "name": "Attacker",
                "description": "Strong attacks",
                "icon": "attacker.png",
            },
            "riderWeakness": {
                "name": "Sprinter",
                "description": "Sprint focused",
                "weaknessSummary": "Low endurance",
                "weaknessDescription": "Struggles on long climbs",
                "strengthName": "Sprint",
                "strengthDescription": "Explosive power",
                "strengthSummary": "Great sprinter",
            },
            "fitnessTestRidden": True,
            "startTime": "2024-01-01T10:00:00Z",
            "endTime": "2024-01-01T11:00:00Z",
        }
    )


@pytest.fixture
def sample_fitness_test_result() -> FitnessTestResult:
    """Create a sample FitnessTestResult for testing."""
    return FitnessTestResult.model_validate(
        {
            "id": "test1",
            "name": "Full Frontal",
            "completedDate": "2024-01-10T10:00:00Z",
            "durationSeconds": 4200,
            "distanceKm": 35.5,
            "tss": 110,
            "intensityFactor": 0.92,
            "testResults": {
                "power5s": {"status": "ok", "graphValue": 85, "value": 850},
                "power1m": {"status": "ok", "graphValue": 80, "value": 420},
                "power5m": {"status": "ok", "graphValue": 75, "value": 310},
                "power20m": {"status": "ok", "graphValue": 70, "value": 260},
                "lactateThresholdHeartRate": 168,
                "riderType": {
                    "name": "Attacker",
                    "description": "Strong",
                    "icon": "attacker.png",
                },
            },
        }
    )


@pytest.fixture
def sample_fitness_test_details() -> FitnessTestDetails:
    """Create a sample FitnessTestDetails for testing."""
    return FitnessTestDetails.model_validate(
        {
            "id": "test1",
            "name": "Full Frontal",
            "completedDate": "2024-01-10T10:00:00Z",
            "durationSeconds": 4200,
            "distanceKm": 35.5,
            "tss": 110,
            "intensityFactor": 0.92,
            "notes": "Felt strong",
            "testResults": {
                "power5s": {"status": "ok", "graphValue": 85, "value": 850},
                "power1m": {"status": "ok", "graphValue": 80, "value": 420},
                "power5m": {"status": "ok", "graphValue": 75, "value": 310},
                "power20m": {"status": "ok", "graphValue": 70, "value": 260},
                "lactateThresholdHeartRate": 168,
                "riderType": {
                    "name": "Attacker",
                    "description": "Strong",
                    "icon": "attacker.png",
                },
            },
            "profile": {"nm": 850, "ac": 420, "map": 310, "ftp": 260},
            "power": [100, 150, 200],
            "cadence": [80, 85, 90],
            "heartRate": [120, 140, 160],
            "powerBests": [
                {"duration": 5, "value": 850},
                {"duration": 60, "value": 420},
            ],
            "analysis": '{"summary": "Great test"}',
        }
    )


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestFormatDate:
    """Tests for _format_date helper."""

    def test_iso_date_with_z(self) -> None:
        result = _format_date("2024-01-15T10:30:00Z")
        assert "January" in result
        assert "15" in result
        assert "2024" in result

    def test_iso_date_with_offset(self) -> None:
        result = _format_date("2024-06-20T15:00:00+02:00")
        assert "June" in result
        assert "20" in result

    def test_invalid_date(self) -> None:
        result = _format_date("invalid-date")
        assert result == "invalid-date"


class TestFormatDuration:
    """Tests for _format_duration helper."""

    def test_hours_and_minutes(self) -> None:
        assert _format_duration(3900) == "1h 5m"

    def test_only_minutes(self) -> None:
        assert _format_duration(1800) == "30m"

    def test_exact_hour(self) -> None:
        assert _format_duration(3600) == "1h 0m"


# =============================================================================
# Calendar Tool Tests
# =============================================================================


class TestGetCalendar:
    """Tests for get_calendar tool."""

    async def test_returns_calendar_items(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
        sample_user_plan_item: UserPlanItem,
    ) -> None:
        mock_client.get_calendar = AsyncMock(return_value=[sample_user_plan_item])

        result = await get_calendar(mock_context, "2024-01-01", "2024-01-31")

        mock_client.get_calendar.assert_called_once_with("2024-01-01", "2024-01-31", "UTC")
        assert len(result) == 1
        assert result[0]["agendaId"] == "agenda123"

    async def test_returns_empty_list(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        mock_client.get_calendar = AsyncMock(return_value=[])

        result = await get_calendar(mock_context, "2024-01-01", "2024-01-31")

        assert result == []


class TestScheduleWorkout:
    """Tests for schedule_workout tool."""

    async def test_schedules_workout(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        mock_client.schedule_workout = AsyncMock(return_value="new-agenda-id")

        result = await schedule_workout(mock_context, "content123", "2024-01-15", "Europe/Lisbon")

        mock_client.schedule_workout.assert_called_once_with(
            "content123", "2024-01-15", "Europe/Lisbon"
        )
        assert result["success"] is True
        assert result["agendaId"] == "new-agenda-id"
        assert result["timezone"] == "Europe/Lisbon"

    async def test_default_timezone(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        mock_client.schedule_workout = AsyncMock(return_value="agenda-id")

        result = await schedule_workout(mock_context, "content123", "2024-01-15")

        mock_client.schedule_workout.assert_called_once_with("content123", "2024-01-15", "UTC")
        assert result["timezone"] == "UTC"


class TestRescheduleWorkout:
    """Tests for reschedule_workout tool."""

    async def test_reschedules_workout(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        mock_client.reschedule_workout = AsyncMock(return_value=None)

        result = await reschedule_workout(
            mock_context, "agenda123", "2024-02-01", "America/New_York"
        )

        mock_client.reschedule_workout.assert_called_once_with(
            "agenda123", "2024-02-01", "America/New_York"
        )
        assert result["success"] is True
        assert result["newDate"] == "2024-02-01"


class TestRemoveWorkout:
    """Tests for remove_workout tool."""

    async def test_removes_workout(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        mock_client.remove_workout = AsyncMock(return_value=None)

        result = await remove_workout(mock_context, "agenda123")

        mock_client.remove_workout.assert_called_once_with("agenda123")
        assert result["success"] is True
        assert result["agendaId"] == "agenda123"


# =============================================================================
# Workout Library Tool Tests
# =============================================================================


class TestGetWorkouts:
    """Tests for get_workouts tool."""

    async def test_returns_workouts_no_filters(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
        sample_library_content: LibraryContent,
    ) -> None:
        mock_client.get_workout_library = AsyncMock(return_value=[sample_library_content])

        result = await get_workouts(mock_context)

        mock_client.get_workout_library.assert_called_once_with({"limit": 50})
        assert result["total"] == 1
        assert result["workouts"][0]["name"] == "Nine Hammers"

    async def test_passes_filters(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        mock_client.get_workout_library = AsyncMock(return_value=[])

        await get_workouts(
            mock_context,
            sport="Cycling",
            search="Hammers",
            min_duration=30,
            max_duration=60,
            min_tss=50,
            max_tss=100,
            channel="The Sufferfest",
            sort_by="tss",
            sort_direction="desc",
            limit=10,
        )

        call_args = mock_client.get_workout_library.call_args[0][0]
        assert call_args["sport"] == "Cycling"
        assert call_args["search"] == "Hammers"
        assert call_args["min_duration"] == 30
        assert call_args["max_duration"] == 60
        assert call_args["limit"] == 10


class TestGetCyclingWorkouts:
    """Tests for get_cycling_workouts tool."""

    async def test_returns_cycling_workouts(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
        sample_library_content: LibraryContent,
    ) -> None:
        mock_client.get_cycling_workouts = AsyncMock(return_value=[sample_library_content])

        result = await get_cycling_workouts(mock_context, four_dp_focus="FTP")

        call_args = mock_client.get_cycling_workouts.call_args[0][0]
        assert call_args["four_dp_focus"] == "FTP"
        assert result["total"] == 1


class TestGetWorkoutDetails:
    """Tests for get_workout_details tool."""

    async def test_returns_details(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
        sample_workout_details: WorkoutDetails,
    ) -> None:
        mock_client.get_workout_details = AsyncMock(return_value=sample_workout_details)

        result = await get_workout_details(mock_context, "workout1")

        mock_client.get_workout_details.assert_called_once_with("workout1")
        assert result["name"] == "Nine Hammers"
        assert result["durationSeconds"] == 3600


# =============================================================================
# Profile Tool Tests
# =============================================================================


class TestGetRiderProfile:
    """Tests for get_rider_profile tool."""

    async def test_returns_profile(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
        sample_enhanced_profile: EnhancedRiderProfile,
    ) -> None:
        from wahoo_systm_mcp.models import RiderProfile

        mock_client.get_enhanced_rider_profile = AsyncMock(return_value=sample_enhanced_profile)
        mock_client.get_rider_profile = AsyncMock(
            return_value=RiderProfile(nm=900, ac=450, map=320, ftp=300, lthr=170)
        )

        result = await get_rider_profile(mock_context)

        assert result["fourDP"]["nm"]["watts"] == 900
        assert result["fourDP"]["ftp"]["score"] == 70
        assert result["riderType"]["name"] == "Attacker"
        assert result["lthr"] == 170
        assert len(result["heartRateZones"]) == 5
        assert result["heartRateZones"][0]["name"] == "Recovery"

    async def test_raises_error_when_no_profile(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        mock_client.get_enhanced_rider_profile = AsyncMock(return_value=None)
        mock_client.get_rider_profile = AsyncMock(return_value=None)

        with pytest.raises(ToolError) as exc_info:
            await get_rider_profile(mock_context)

        assert "No rider profile found" in str(exc_info.value)


class TestGetFitnessTestHistory:
    """Tests for get_fitness_test_history tool."""

    async def test_returns_history(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
        sample_fitness_test_result: FitnessTestResult,
    ) -> None:
        mock_client.get_fitness_test_history = AsyncMock(
            return_value=([sample_fitness_test_result], 1)
        )

        result = await get_fitness_test_history(mock_context)

        mock_client.get_fitness_test_history.assert_called_once_with(1, 15)
        assert result["total"] == 1
        assert result["tests"][0]["name"] == "Full Frontal"
        assert result["tests"][0]["fourDP"]["nm"]["watts"] == 850

    async def test_pagination(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        mock_client.get_fitness_test_history = AsyncMock(return_value=([], 0))

        await get_fitness_test_history(mock_context, page=2, page_size=10)

        mock_client.get_fitness_test_history.assert_called_once_with(2, 10)


class TestGetFitnessTestDetails:
    """Tests for get_fitness_test_details tool."""

    async def test_returns_details(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
        sample_fitness_test_details: FitnessTestDetails,
    ) -> None:
        mock_client.get_fitness_test_details = AsyncMock(return_value=sample_fitness_test_details)

        result = await get_fitness_test_details(mock_context, "test1")

        mock_client.get_fitness_test_details.assert_called_once_with("test1")
        assert result["name"] == "Full Frontal"
        assert result["notes"] == "Felt strong"
        assert result["fourDP"]["nm"]["watts"] == 850
        assert len(result["powerCurve"]) == 2
        assert result["activityData"]["power"] == [100, 150, 200]
        assert result["analysis"]["summary"] == "Great test"

    async def test_handles_invalid_analysis_json(
        self,
        mock_context: MagicMock,
        mock_client: MagicMock,
        sample_fitness_test_details: FitnessTestDetails,
    ) -> None:
        sample_fitness_test_details.analysis = "not valid json"
        mock_client.get_fitness_test_details = AsyncMock(return_value=sample_fitness_test_details)

        result = await get_fitness_test_details(mock_context, "test1")

        assert result["analysis"] is None
