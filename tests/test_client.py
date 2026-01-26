"""Tests for WahooClient."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from wahoo_systm_mcp.client import (
    API_URL,
    CHANNEL_ID_TO_NAME,
    FULL_FRONTAL_ID,
    HALF_MONTY_ID,
    AuthenticationError,
    WahooAPIError,
    WahooClient,
    _calculate_heart_rate_zones,
)
from wahoo_systm_mcp.types import JSONObject

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def client() -> AsyncIterator[WahooClient]:
    """Create a WahooClient instance."""
    client = WahooClient()
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def authenticated_client() -> AsyncIterator[WahooClient]:
    """Create an authenticated WahooClient instance."""
    client = WahooClient()
    client._token = "test-token"
    try:
        yield client
    finally:
        await client.close()


def mock_response(data: JSONObject, status_code: int = 200) -> httpx.Response:
    """Create a mock httpx.Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = {"data": data}
    response.text = ""
    return response


def mock_error_response(errors: list[JSONObject]) -> httpx.Response:
    """Create a mock httpx.Response with GraphQL errors."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {"errors": errors}
    response.text = ""
    return response


def mock_http_error_response(status_code: int, text: str) -> httpx.Response:
    """Create a mock httpx.Response with HTTP error."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.text = text
    return response


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestCalculateHeartRateZones:
    """Tests for _calculate_heart_rate_zones helper."""

    def test_standard_lthr(self) -> None:
        """Test zone calculation with typical LTHR."""
        zones = _calculate_heart_rate_zones(165)
        assert len(zones) == 5
        assert zones[0].zone == 1
        assert zones[0].name == "Recovery"
        assert zones[0].min == 0
        assert zones[0].max == 114  # int(165 * 0.70) - 1 = 115 - 1 = 114
        assert zones[4].zone == 5
        assert zones[4].name == "Max"
        assert zones[4].max is None

    def test_zone_boundaries(self) -> None:
        """Test that zones have correct boundary percentages."""
        lthr = 170
        zones = _calculate_heart_rate_zones(lthr)
        # Zone 2: 70-87%
        assert zones[1].min == int(lthr * 0.70) + 1
        assert zones[1].max == int(lthr * 0.87) + 1
        # Zone 4: 96-100%
        assert zones[3].min == int(lthr * 0.96)
        assert zones[3].max == int(lthr * 1.00)


# =============================================================================
# Authentication Tests
# =============================================================================


class TestAuthentication:
    """Tests for authentication functionality."""

    async def test_authenticate_success(self, client: WahooClient) -> None:
        """Test successful authentication."""
        login_response = {
            "loginUser": {
                "status": "Success",
                "message": "Logged in",
                "token": "test-token-abc123",
                "user": {
                    "id": "user123",
                },
            }
        }

        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response(login_response)

            await client.authenticate("test@example.com", "password123")

            assert client._token == "test-token-abc123"
            assert client._rider_profile is None

            # Verify request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args.args[0] == API_URL
            body = call_args.kwargs["json"]
            assert body["variables"]["username"] == "test@example.com"
            assert body["variables"]["password"] == "password123"
            assert body["variables"]["appInformation"]["platform"] == "web"

    async def test_authenticate_failure(self, client: WahooClient) -> None:
        """Test authentication failure."""
        login_response = {
            "loginUser": {
                "status": "Error",
                "message": "Invalid credentials",
                "token": "",
                "user": {},
            }
        }

        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response(login_response)

            with pytest.raises(AuthenticationError) as exc_info:
                await client.authenticate("test@example.com", "wrong-password")

            assert "Invalid credentials" in str(exc_info.value)
            assert client._token is None

    async def test_authenticate_graphql_error(self, client: WahooClient) -> None:
        """Test authentication with GraphQL error."""
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_error_response([{"message": "Rate limit exceeded"}])

            with pytest.raises(AuthenticationError) as exc_info:
                await client.authenticate("test@example.com", "password")

            assert "Rate limit exceeded" in str(exc_info.value)

    async def test_require_auth_without_token(self, client: WahooClient) -> None:
        """Test that methods requiring auth fail without authentication."""
        with pytest.raises(AuthenticationError) as exc_info:
            await client.get_calendar("2024-01-01", "2024-01-31")

        assert "Not authenticated" in str(exc_info.value)


# =============================================================================
# Calendar Tests
# =============================================================================


class TestGetCalendar:
    """Tests for get_calendar method."""

    async def test_get_calendar_success(self, authenticated_client: WahooClient) -> None:
        """Test fetching calendar items."""
        calendar_response = {
            "userPlan": [
                {
                    "day": 1,
                    "plannedDate": "2024-01-15",
                    "rank": 1,
                    "agendaId": "agenda123",
                    "status": "scheduled",
                    "type": "workout",
                    "prospects": [
                        {
                            "type": "workout",
                            "name": "Nine Hammers",
                            "compatibility": "full",
                            "description": "A classic",
                            "style": "endurance",
                            "intensity": {
                                "master": 4,
                                "nm": 3,
                                "ac": 4,
                                "map": 4,
                                "ftp": 3,
                            },
                            "plannedDuration": 3600,
                            "durationType": "fixed",
                            "contentId": "content1",
                            "workoutId": "workout1",
                        }
                    ],
                    "plan": {
                        "id": "plan1",
                        "name": "Base Training",
                        "color": "#FF0000",
                        "description": "Base building",
                        "category": "endurance",
                    },
                }
            ]
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(calendar_response)

            items = await authenticated_client.get_calendar("2024-01-01", "2024-01-31")

            assert len(items) == 1
            assert items[0].agenda_id == "agenda123"
            assert items[0].planned_date == "2024-01-15"
            assert items[0].prospects[0].name == "Nine Hammers"

    async def test_get_calendar_empty(self, authenticated_client: WahooClient) -> None:
        """Test fetching empty calendar."""
        calendar_response = {"userPlan": []}

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(calendar_response)

            items = await authenticated_client.get_calendar("2024-01-01", "2024-01-31")

            assert len(items) == 0


# =============================================================================
# Workout Library Tests
# =============================================================================


class TestGetWorkoutLibrary:
    """Tests for get_workout_library method."""

    async def test_get_library_no_filters(self, authenticated_client: WahooClient) -> None:
        """Test fetching library without filters."""
        library_response = {
            "library": {
                "content": [
                    {
                        "id": "content1",
                        "name": "Nine Hammers",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",  # Sufferfest ID
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
                    },
                    {
                        "id": "content2",
                        "name": "Yoga Session",
                        "mediaType": "video",
                        "channel": "LuAEHZcJSj",  # Wahoo Fitness ID
                        "workoutType": "Yoga",
                        "category": "recovery",
                        "level": "beginner",
                        "duration": 1800,
                        "workoutId": "workout2",
                    },
                ],
                "sports": [],
                "channels": [],
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(library_response)

            content = await authenticated_client.get_workout_library()

            assert len(content) == 2
            # Channel IDs should be converted to names
            assert content[0].channel == "The Sufferfest"
            assert content[1].channel == "Wahoo Fitness"

    async def test_get_library_with_sport_filter(self, authenticated_client: WahooClient) -> None:
        """Test filtering by sport type."""
        library_response = {
            "library": {
                "content": [
                    {
                        "id": "content1",
                        "name": "Nine Hammers",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "threshold",
                        "level": "advanced",
                        "duration": 3600,
                        "workoutId": "workout1",
                    },
                    {
                        "id": "content2",
                        "name": "Yoga Session",
                        "mediaType": "video",
                        "channel": "LuAEHZcJSj",
                        "workoutType": "Yoga",
                        "category": "recovery",
                        "level": "beginner",
                        "duration": 1800,
                        "workoutId": "workout2",
                    },
                ],
                "sports": [],
                "channels": [],
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(library_response)

            content = await authenticated_client.get_workout_library({"sport": "Cycling"})

            assert len(content) == 1
            assert content[0].name == "Nine Hammers"

    async def test_get_library_with_duration_filter(
        self, authenticated_client: WahooClient
    ) -> None:
        """Test filtering by duration range."""
        library_response = {
            "library": {
                "content": [
                    {
                        "id": "content1",
                        "name": "Short Workout",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "threshold",
                        "level": "advanced",
                        "duration": 1800,  # 30 min
                        "workoutId": "workout1",
                    },
                    {
                        "id": "content2",
                        "name": "Long Workout",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "endurance",
                        "level": "intermediate",
                        "duration": 5400,  # 90 min
                        "workoutId": "workout2",
                    },
                ],
                "sports": [],
                "channels": [],
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(library_response)

            content = await authenticated_client.get_workout_library(
                {"min_duration": 45, "max_duration": 120}  # 45-120 minutes
            )

            assert len(content) == 1
            assert content[0].name == "Long Workout"

    async def test_get_library_with_tss_filter(self, authenticated_client: WahooClient) -> None:
        """Test filtering by TSS range."""
        library_response = {
            "library": {
                "content": [
                    {
                        "id": "content1",
                        "name": "Easy Ride",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "recovery",
                        "level": "beginner",
                        "duration": 1800,
                        "workoutId": "workout1",
                        "metrics": {"tss": 30, "intensityFactor": 0.5, "ratings": None},
                    },
                    {
                        "id": "content2",
                        "name": "Hard Ride",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "threshold",
                        "level": "advanced",
                        "duration": 3600,
                        "workoutId": "workout2",
                        "metrics": {
                            "tss": 95,
                            "intensityFactor": 0.85,
                            "ratings": {"nm": 3, "ac": 4, "map": 4, "ftp": 3},
                        },
                    },
                ],
                "sports": [],
                "channels": [],
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(library_response)

            content = await authenticated_client.get_workout_library(
                {"min_tss": 50, "max_tss": 100}
            )

            assert len(content) == 1
            assert content[0].name == "Hard Ride"

    async def test_get_library_with_search(self, authenticated_client: WahooClient) -> None:
        """Test searching by name."""
        library_response = {
            "library": {
                "content": [
                    {
                        "id": "content1",
                        "name": "Nine Hammers",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "threshold",
                        "level": "advanced",
                        "duration": 3600,
                        "workoutId": "workout1",
                    },
                    {
                        "id": "content2",
                        "name": "The Shovel",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "endurance",
                        "level": "intermediate",
                        "duration": 5400,
                        "workoutId": "workout2",
                    },
                ],
                "sports": [],
                "channels": [],
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(library_response)

            content = await authenticated_client.get_workout_library({"search": "hammer"})

            assert len(content) == 1
            assert content[0].name == "Nine Hammers"

    async def test_get_library_with_sorting(self, authenticated_client: WahooClient) -> None:
        """Test sorting results."""
        library_response = {
            "library": {
                "content": [
                    {
                        "id": "content1",
                        "name": "B Workout",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "threshold",
                        "level": "advanced",
                        "duration": 3600,
                        "workoutId": "workout1",
                    },
                    {
                        "id": "content2",
                        "name": "A Workout",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "endurance",
                        "level": "intermediate",
                        "duration": 1800,
                        "workoutId": "workout2",
                    },
                ],
                "sports": [],
                "channels": [],
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(library_response)

            # Sort by name ascending (default)
            content = await authenticated_client.get_workout_library(
                {"sort_by": "name", "sort_direction": "asc"}
            )
            assert content[0].name == "A Workout"

            # Sort by duration descending
            content = await authenticated_client.get_workout_library(
                {"sort_by": "duration", "sort_direction": "desc"}
            )
            assert content[0].name == "B Workout"

    async def test_get_library_with_limit(self, authenticated_client: WahooClient) -> None:
        """Test limiting results."""
        library_response = {
            "library": {
                "content": [
                    {
                        "id": f"content{i}",
                        "name": f"Workout {i}",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "threshold",
                        "level": "advanced",
                        "duration": 3600,
                        "workoutId": f"workout{i}",
                    }
                    for i in range(10)
                ],
                "sports": [],
                "channels": [],
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(library_response)

            content = await authenticated_client.get_workout_library({"limit": 3})

            assert len(content) == 3


class TestGetCyclingWorkouts:
    """Tests for get_cycling_workouts method."""

    async def test_get_cycling_workouts_basic(self, authenticated_client: WahooClient) -> None:
        """Test fetching cycling workouts."""
        library_response = {
            "library": {
                "content": [
                    {
                        "id": "content1",
                        "name": "Nine Hammers",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "threshold",
                        "level": "advanced",
                        "duration": 3600,
                        "workoutId": "workout1",
                    },
                    {
                        "id": "content2",
                        "name": "Yoga Session",
                        "mediaType": "video",
                        "channel": "LuAEHZcJSj",
                        "workoutType": "Yoga",
                        "category": "recovery",
                        "level": "beginner",
                        "duration": 1800,
                        "workoutId": "workout2",
                    },
                ],
                "sports": [],
                "channels": [],
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(library_response)

            content = await authenticated_client.get_cycling_workouts()

            assert len(content) == 1
            assert content[0].name == "Nine Hammers"
            assert content[0].workout_type == "Cycling"

    async def test_get_cycling_workouts_four_dp_focus(
        self, authenticated_client: WahooClient
    ) -> None:
        """Test filtering by 4DP focus."""
        library_response = {
            "library": {
                "content": [
                    {
                        "id": "content1",
                        "name": "High MAP Workout",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "threshold",
                        "level": "advanced",
                        "duration": 3600,
                        "workoutId": "workout1",
                        "metrics": {
                            "tss": 95,
                            "intensityFactor": 0.85,
                            "ratings": {"nm": 2, "ac": 3, "map": 5, "ftp": 3},
                        },
                    },
                    {
                        "id": "content2",
                        "name": "FTP Builder",
                        "mediaType": "video",
                        "channel": "x7jJSqJlR2",
                        "workoutType": "Cycling",
                        "category": "endurance",
                        "level": "intermediate",
                        "duration": 5400,
                        "workoutId": "workout2",
                        "metrics": {
                            "tss": 80,
                            "intensityFactor": 0.75,
                            "ratings": {"nm": 1, "ac": 2, "map": 2, "ftp": 5},
                        },
                    },
                ],
                "sports": [],
                "channels": [],
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(library_response)

            # Filter for MAP focus (rating >= 4)
            content = await authenticated_client.get_cycling_workouts({"four_dp_focus": "MAP"})

            assert len(content) == 1
            assert content[0].name == "High MAP Workout"

            # Filter for FTP focus
            content = await authenticated_client.get_cycling_workouts({"four_dp_focus": "FTP"})

            assert len(content) == 1
            assert content[0].name == "FTP Builder"


# =============================================================================
# Schedule/Reschedule/Remove Workout Tests
# =============================================================================


class TestScheduleWorkout:
    """Tests for schedule_workout method."""

    async def test_schedule_workout_success(self, authenticated_client: WahooClient) -> None:
        """Test successfully scheduling a workout."""
        add_response = {
            "addAgenda": {
                "status": "success",
                "message": None,
                "agendaId": "new-agenda-123",
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(add_response)

            agenda_id = await authenticated_client.schedule_workout(
                "content123", "2024-02-15", "Europe/Lisbon"
            )

            assert agenda_id == "new-agenda-123"

            # Verify request body
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert body["variables"]["contentId"] == "content123"
            assert body["variables"]["date"] == "2024-02-15"
            assert body["variables"]["timeZone"] == "Europe/Lisbon"

    async def test_schedule_workout_failure(self, authenticated_client: WahooClient) -> None:
        """Test scheduling failure."""
        add_response = {
            "addAgenda": {
                "status": "error",
                "message": "Content not found",
                "agendaId": "",
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(add_response)

            with pytest.raises(WahooAPIError) as exc_info:
                await authenticated_client.schedule_workout("invalid-content", "2024-02-15")

            assert "Content not found" in str(exc_info.value)


class TestRescheduleWorkout:
    """Tests for reschedule_workout method."""

    async def test_reschedule_workout_success(self, authenticated_client: WahooClient) -> None:
        """Test successfully rescheduling a workout."""
        move_response = {"moveAgenda": {"status": "success"}}

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(move_response)

            await authenticated_client.reschedule_workout(
                "agenda123", "2024-02-20", "America/New_York"
            )

            # Verify request body
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert body["variables"]["agendaId"] == "agenda123"
            assert body["variables"]["date"] == "2024-02-20"
            assert body["variables"]["timeZone"] == "America/New_York"

    async def test_reschedule_workout_failure(self, authenticated_client: WahooClient) -> None:
        """Test rescheduling failure."""
        move_response = {"moveAgenda": {"status": "error"}}

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(move_response)

            with pytest.raises(WahooAPIError) as exc_info:
                await authenticated_client.reschedule_workout("agenda123", "2024-02-20")

            assert "Failed to reschedule" in str(exc_info.value)


class TestRemoveWorkout:
    """Tests for remove_workout method."""

    async def test_remove_workout_success(self, authenticated_client: WahooClient) -> None:
        """Test successfully removing a workout."""
        delete_response = {"deleteAgenda": {"status": "success"}}

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(delete_response)

            await authenticated_client.remove_workout("agenda123")

            # Verify request body
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert body["variables"]["agendaId"] == "agenda123"

    async def test_remove_workout_failure(self, authenticated_client: WahooClient) -> None:
        """Test removal failure."""
        delete_response = {"deleteAgenda": {"status": "error"}}

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(delete_response)

            with pytest.raises(WahooAPIError) as exc_info:
                await authenticated_client.remove_workout("agenda123")

            assert "Failed to remove" in str(exc_info.value)


# =============================================================================
# Rider Profile Tests
# =============================================================================


class TestGetRiderProfile:
    """Tests for get_rider_profile method."""

    async def test_get_current_profile_after_auth(self, authenticated_client: WahooClient) -> None:
        """Test getting current profile after authentication."""
        from wahoo_systm_mcp.models import RiderProfile

        authenticated_client._rider_profile = RiderProfile(nm=850, ac=420, map=310, ftp=260)

        profile = await authenticated_client.get_current_profile()

        assert profile is not None
        assert profile.nm == 850
        assert profile.ftp == 260

    async def test_get_current_profile_none(self, authenticated_client: WahooClient) -> None:
        """Test fetching current profile when not cached."""
        authenticated_client._rider_profile = None

        response = {
            "impersonateUser": {
                "status": "Success",
                "message": None,
                "user": {
                    "profiles": {"riderProfile": {"nm": 850, "ac": 420, "map": 310, "ftp": 260}},
                },
                "token": "new-token-xyz",
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(response)
            profile = await authenticated_client.get_current_profile()

        assert profile is not None
        assert profile.ftp == 260
        assert authenticated_client._token == "new-token-xyz"


class TestGetLatestTestProfile:
    """Tests for get_latest_test_profile method."""

    async def test_get_enhanced_profile_success(self, authenticated_client: WahooClient) -> None:
        """Test getting enhanced rider profile."""
        test_response = {
            "mostRecentTest": {
                "status": "success",
                "message": None,
                "fitnessTestRidden": True,
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
                "power5s": {"status": "ok", "graphValue": 85, "value": 850},
                "power1m": {"status": "ok", "graphValue": 80, "value": 420},
                "power5m": {"status": "ok", "graphValue": 75, "value": 310},
                "power20m": {"status": "ok", "graphValue": 70, "value": 260},
                "lactateThresholdHeartRate": 168,
                "startTime": "2024-01-01T10:00:00Z",
                "endTime": "2024-01-01T11:00:00Z",
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(test_response)

            profile = await authenticated_client.get_latest_test_profile()

            assert profile is not None
            assert profile.nm == 850
            assert profile.ftp == 260
            assert profile.rider_type.name == "Attacker"
            assert profile.lactate_threshold_heart_rate == 168
            assert len(profile.heart_rate_zones) == 5
            assert profile.heart_rate_zones[0].name == "Recovery"

    async def test_get_enhanced_profile_no_test(self, authenticated_client: WahooClient) -> None:
        """Test getting enhanced profile when no test has been ridden."""
        test_response = {
            "mostRecentTest": {
                "status": "success",
                "message": None,
                "fitnessTestRidden": False,
                "riderType": {"name": "", "description": "", "icon": ""},
                "riderWeakness": {
                    "name": "",
                    "description": "",
                    "weaknessSummary": "",
                    "weaknessDescription": "",
                    "strengthName": "",
                    "strengthDescription": "",
                    "strengthSummary": "",
                },
                "power5s": {"status": "none", "graphValue": 0, "value": 0},
                "power1m": {"status": "none", "graphValue": 0, "value": 0},
                "power5m": {"status": "none", "graphValue": 0, "value": 0},
                "power20m": {"status": "none", "graphValue": 0, "value": 0},
                "lactateThresholdHeartRate": 0,
                "startTime": "",
                "endTime": "",
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(test_response)

            profile = await authenticated_client.get_latest_test_profile()

            assert profile is None


# =============================================================================
# Fitness Test History Tests
# =============================================================================


class TestGetFitnessTestHistory:
    """Tests for get_fitness_test_history method."""

    async def test_get_history_success(self, authenticated_client: WahooClient) -> None:
        """Test fetching fitness test history."""
        search_response = {
            "searchActivities": {
                "activities": [
                    {
                        "id": "test1",
                        "name": "Full Frontal",
                        "completedDate": "2024-01-10T10:00:00Z",
                        "durationSeconds": 4200,
                        "distanceKm": 35.5,
                        "tss": 110,
                        "intensityFactor": 0.92,
                        "workoutId": FULL_FRONTAL_ID,
                        "testResults": {
                            "power5s": {"status": "ok", "graphValue": 85, "value": 850},
                            "power1m": {"status": "ok", "graphValue": 80, "value": 420},
                            "power5m": {"status": "ok", "graphValue": 75, "value": 310},
                            "power20m": {"status": "ok", "graphValue": 70, "value": 260},
                            "lactateThresholdHeartRate": 168,
                            "riderType": {
                                "name": "Attacker",
                                "description": "Strong",
                                "icon": "a.png",
                            },
                        },
                    }
                ],
                "count": 1,
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(search_response)

            results, total = await authenticated_client.get_fitness_test_history()

            assert len(results) == 1
            assert total == 1
            assert results[0].name == "Full Frontal"
            assert results[0].test_results is not None
            assert results[0].test_results.power_5s.value == 850

            # Verify workout IDs filter
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert FULL_FRONTAL_ID in body["variables"]["search"]["workoutIds"]
            assert HALF_MONTY_ID in body["variables"]["search"]["workoutIds"]

    async def test_get_history_pagination(self, authenticated_client: WahooClient) -> None:
        """Test pagination parameters."""
        search_response = {
            "searchActivities": {
                "activities": [],
                "count": 0,
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(search_response)

            await authenticated_client.get_fitness_test_history(page=3, page_size=10)

            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert body["variables"]["page"]["page"] == 3
            assert body["variables"]["page"]["pageSize"] == 10


class TestGetFitnessTestDetails:
    """Tests for get_fitness_test_details method."""

    async def test_get_details_success(self, authenticated_client: WahooClient) -> None:
        """Test fetching fitness test details."""
        activity_response = {
            "activity": {
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
                        "icon": "a.png",
                    },
                },
                "profile": {"nm": 850, "ac": 420, "map": 310, "ftp": 260},
                "power": [100, 150, 200, 250],
                "cadence": [80, 85, 90, 95],
                "heartRate": [120, 140, 160, 170],
                "powerBests": [
                    {"duration": 5, "value": 850},
                    {"duration": 60, "value": 420},
                ],
                "analysis": "Great test performance",
            }
        }

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(activity_response)

            details = await authenticated_client.get_fitness_test_details("test1")

            assert details.id == "test1"
            assert details.name == "Full Frontal"
            assert details.notes == "Felt strong"
            assert len(details.power) == 4
            assert len(details.power_bests) == 2
            assert details.profile.ftp == 260


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    async def test_http_error(self, authenticated_client: WahooClient) -> None:
        """Test handling HTTP errors."""
        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_http_error_response(500, "Internal Server Error")

            with pytest.raises(WahooAPIError) as exc_info:
                await authenticated_client.get_calendar("2024-01-01", "2024-01-31")

            assert exc_info.value.status_code == 500

    async def test_graphql_error(self, authenticated_client: WahooClient) -> None:
        """Test handling GraphQL errors."""
        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_error_response([{"message": "Invalid query"}])

            with pytest.raises(WahooAPIError) as exc_info:
                await authenticated_client.get_calendar("2024-01-01", "2024-01-31")

            assert "Invalid query" in str(exc_info.value)

    async def test_workout_not_found(self, authenticated_client: WahooClient) -> None:
        """Test handling workout not found."""
        workouts_response = {"workouts": []}

        with patch.object(
            authenticated_client._client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response(workouts_response)
            authenticated_client.get_workout_library = AsyncMock(return_value=[])

            with pytest.raises(WahooAPIError) as exc_info:
                await authenticated_client.get_workout_details("nonexistent")

            assert "not found" in str(exc_info.value)


# =============================================================================
# Client Lifecycle Tests
# =============================================================================


class TestClientLifecycle:
    """Tests for client lifecycle management."""

    async def test_close_client(self, client: WahooClient) -> None:
        """Test closing the client."""
        with patch.object(client._client, "aclose", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    def test_channel_id_mapping(self) -> None:
        """Test channel ID to name mapping is complete."""
        assert len(CHANNEL_ID_TO_NAME) == 8
        assert "x7jJSqJlR2" in CHANNEL_ID_TO_NAME
        assert CHANNEL_ID_TO_NAME["x7jJSqJlR2"] == "The Sufferfest"
