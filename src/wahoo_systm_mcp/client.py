"""Wahoo SYSTM GraphQL API client."""

from __future__ import annotations

from typing import Any

import httpx

from wahoo_systm_mcp.models import (
    AddAgendaResponse,
    DeleteAgendaResponse,
    EnhancedRiderProfile,
    FitnessTestDetails,
    FitnessTestResult,
    GetActivityResponse,
    GetUserPlansRangeResponse,
    GetWorkoutsResponse,
    HeartRateZone,
    LibraryContent,
    LibraryResponse,
    LoginResponse,
    MostRecentTestResponse,
    MoveAgendaResponse,
    RiderProfile,
    SearchActivitiesResponse,
    UserPlanItem,
    WorkoutDetails,
)

# =============================================================================
# Constants
# =============================================================================

API_URL = "https://api.thesufferfest.com/graphql"
APP_VERSION = "7.12.0-web.2141"
INSTALL_ID = "F215B34567B35AC815329A53A2B696E5"
FULL_FRONTAL_ID = "dRcyg09t6K"
HALF_MONTY_ID = "0SmbqUIZZo"

# Channel ID to human-readable name mapping
CHANNEL_ID_TO_NAME: dict[str, str] = {
    "x7jJSqJlR2": "The Sufferfest",
    "D5AqJINiQv": "Inspiration",
    "LuAEHZcJSj": "Wahoo Fitness",
    "Kl1DkB3DPD": "A Week With",
    "NTuG2YEP1D": "ProRides",
    "uKnrlcf5rC": "On Location",
    "EXy8gSV1lZ": "NoVid",
    "HJv77IZQBt": "Fitness Test",
}

# Human-readable name to channel ID mapping
CHANNEL_NAME_TO_ID: dict[str, str] = {v: k for k, v in CHANNEL_ID_TO_NAME.items()}


# =============================================================================
# Exceptions
# =============================================================================


class WahooAPIError(Exception):
    """Base exception for Wahoo API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(WahooAPIError):
    """Raised when authentication fails or token is missing."""

    pass


# =============================================================================
# GraphQL Queries
# =============================================================================

LOGIN_MUTATION = """
mutation LoginUser($input: LoginUserInput!) {
  loginUser(input: $input) {
    status
    message
    token
    user {
      id
      profiles {
        fitness {
          nm
          ac
          map
          ftp
        }
      }
    }
  }
}
"""

MOST_RECENT_TEST_QUERY = """
query MostRecentTest {
  mostRecentTest {
    status
    message
    fitnessTestRidden
    riderType {
      name
      description
      icon
    }
    riderWeakness {
      name
      description
      weaknessSummary
      weaknessDescription
      strengthName
      strengthDescription
      strengthSummary
    }
    power5s {
      status
      graphValue
      value
    }
    power1m {
      status
      graphValue
      value
    }
    power5m {
      status
      graphValue
      value
    }
    power20m {
      status
      graphValue
      value
    }
    lactateThresholdHeartRate
    startTime
    endTime
  }
}
"""

GET_USER_PLANS_RANGE_QUERY = """
query GetUserPlansRange($input: GetUserPlansRangeInput!) {
  getUserPlansRange(input: $input) {
    status
    message
    items {
      day
      plannedDate
      rank
      agendaId
      status
      type
      prospects {
        type
        name
        compatibility
        description
        style
        intensity {
          master
          nm
          ac
          map
          ftp
        }
        plannedDuration
        durationType
        contentId
        workoutId
        notes
      }
      plan {
        id
        name
        color
        description
        category
      }
    }
  }
}
"""

GET_WORKOUTS_QUERY = """
query GetWorkouts($input: GetWorkoutsInput!) {
  getWorkouts(input: $input) {
    workouts {
      id
      name
      sport
      shortDescription
      details
      level
      durationSeconds
      equipment {
        name
        description
      }
      descriptions {
        title
        body
      }
      metrics {
        intensityFactor
        tss
        ratings {
          nm
          ac
          map
          ftp
        }
      }
      triggers
    }
  }
}
"""

LIBRARY_QUERY = """
query Library {
  library {
    content {
      id
      name
      mediaType
      channel
      workoutType
      category
      level
      duration
      workoutId
      videoId
      bannerImage
      posterImage
      defaultImage
      intensity
      tags
      descriptions {
        title
        body
      }
      metrics {
        tss
        intensityFactor
        ratings {
          nm
          ac
          map
          ftp
        }
      }
    }
    sports {
      id
      workoutType
      name
      description
    }
    channels {
      id
      name
      description
    }
  }
}
"""

ADD_AGENDA_MUTATION = """
mutation AddAgenda($input: AddAgendaInput!) {
  addAgenda(input: $input) {
    status
    message
    agendaId
  }
}
"""

MOVE_AGENDA_MUTATION = """
mutation MoveAgenda($input: MoveAgendaInput!) {
  moveAgenda(input: $input) {
    status
  }
}
"""

DELETE_AGENDA_MUTATION = """
mutation DeleteAgenda($input: DeleteAgendaInput!) {
  deleteAgenda(input: $input) {
    status
  }
}
"""

SEARCH_ACTIVITIES_QUERY = """
query SearchActivities($input: SearchActivitiesInput!) {
  searchActivities(input: $input) {
    activities {
      id
      name
      completedDate
      durationSeconds
      distanceKm
      tss
      intensityFactor
      testResults {
        power5s {
          status
          graphValue
          value
        }
        power1m {
          status
          graphValue
          value
        }
        power5m {
          status
          graphValue
          value
        }
        power20m {
          status
          graphValue
          value
        }
        lactateThresholdHeartRate
        riderType {
          name
          description
          icon
        }
      }
    }
    total
  }
}
"""

GET_ACTIVITY_QUERY = """
query GetActivity($input: GetActivityInput!) {
  getActivity(input: $input) {
    id
    name
    completedDate
    durationSeconds
    distanceKm
    tss
    intensityFactor
    notes
    testResults {
      power5s {
        status
        graphValue
        value
      }
      power1m {
        status
        graphValue
        value
      }
      power5m {
        status
        graphValue
        value
      }
      power20m {
        status
        graphValue
        value
      }
      lactateThresholdHeartRate
      riderType {
        name
        description
        icon
      }
    }
    profile {
      nm
      ac
      map
      ftp
    }
    power
    cadence
    heartRate
    powerBests {
      duration
      value
    }
    analysis
  }
}
"""


# =============================================================================
# Helper Functions
# =============================================================================


def _calculate_heart_rate_zones(lthr: int) -> list[HeartRateZone]:
    """Calculate heart rate training zones based on lactate threshold heart rate.

    Uses standard zone percentages:
    - Zone 1 (Recovery): < 81% LTHR
    - Zone 2 (Endurance): 81-89% LTHR
    - Zone 3 (Tempo): 90-93% LTHR
    - Zone 4 (Threshold): 94-99% LTHR
    - Zone 5 (VO2 Max): 100-105% LTHR
    - Zone 6 (Anaerobic): > 105% LTHR

    Args:
        lthr: Lactate threshold heart rate in BPM.

    Returns:
        List of heart rate zones with calculated ranges.
    """
    return [
        HeartRateZone(zone=1, name="Recovery", min=0, max=int(lthr * 0.81) - 1),
        HeartRateZone(zone=2, name="Endurance", min=int(lthr * 0.81), max=int(lthr * 0.89)),
        HeartRateZone(zone=3, name="Tempo", min=int(lthr * 0.90), max=int(lthr * 0.93)),
        HeartRateZone(zone=4, name="Threshold", min=int(lthr * 0.94), max=int(lthr * 0.99)),
        HeartRateZone(zone=5, name="VO2 Max", min=int(lthr * 1.00), max=int(lthr * 1.05)),
        HeartRateZone(zone=6, name="Anaerobic", min=int(lthr * 1.06), max=None),
    ]


# =============================================================================
# Client
# =============================================================================


class WahooClient:
    """Async client for the Wahoo SYSTM GraphQL API."""

    def __init__(self) -> None:
        """Initialize the client."""
        self._token: str | None = None
        self._rider_profile: RiderProfile | None = None
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _require_auth(self) -> str:
        """Check authentication and return token.

        Returns:
            The authentication token.

        Raises:
            AuthenticationError: If not authenticated.
        """
        if self._token is None:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")
        return self._token

    async def _call_api(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
        require_auth: bool = True,
    ) -> dict[str, Any]:
        """Make a GraphQL API call.

        Args:
            query: The GraphQL query or mutation.
            variables: Optional variables for the query.
            operation_name: Optional operation name.
            require_auth: Whether authentication is required.

        Returns:
            The data field from the GraphQL response.

        Raises:
            AuthenticationError: If auth required but not authenticated.
            WahooAPIError: If the API returns an error.
        """
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-App-Version": APP_VERSION,
            "X-Install-Id": INSTALL_ID,
        }

        if require_auth:
            token = self._require_auth()
            headers["Authorization"] = f"Bearer {token}"

        body: dict[str, Any] = {"query": query}
        if variables is not None:
            body["variables"] = variables
        if operation_name is not None:
            body["operationName"] = operation_name

        response = await self._client.post(API_URL, json=body, headers=headers)

        if response.status_code != 200:
            raise WahooAPIError(
                f"API request failed: {response.text}",
                status_code=response.status_code,
            )

        result: dict[str, Any] = response.json()

        if "errors" in result:
            errors = result["errors"]
            error_message = errors[0].get("message", "Unknown error") if errors else "Unknown error"
            raise WahooAPIError(f"GraphQL error: {error_message}")

        data: dict[str, Any] = result.get("data", {})
        return data

    async def authenticate(self, username: str, password: str) -> None:
        """Authenticate with Wahoo SYSTM.

        Args:
            username: The user's email address.
            password: The user's password.

        Raises:
            AuthenticationError: If authentication fails.
        """
        variables = {
            "input": {
                "email": username,
                "password": password,
            }
        }

        try:
            data = await self._call_api(
                LOGIN_MUTATION,
                variables=variables,
                operation_name="LoginUser",
                require_auth=False,
            )
        except WahooAPIError as e:
            raise AuthenticationError(f"Authentication failed: {e.message}") from e

        response = LoginResponse.model_validate(data)

        if response.login_user.status != "success":
            raise AuthenticationError(
                f"Authentication failed: {response.login_user.message or 'Unknown error'}"
            )

        self._token = response.login_user.token

        # Extract rider profile from user data
        user_data = response.login_user.user
        profiles = user_data.get("profiles", {})
        fitness = profiles.get("fitness")
        if fitness:
            self._rider_profile = RiderProfile.model_validate(fitness)

    async def get_calendar(self, start_date: str, end_date: str) -> list[UserPlanItem]:
        """Get planned workouts from calendar for a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            List of scheduled workout items.
        """
        variables = {
            "input": {
                "startDate": start_date,
                "endDate": end_date,
            }
        }

        data = await self._call_api(
            GET_USER_PLANS_RANGE_QUERY,
            variables=variables,
            operation_name="GetUserPlansRange",
        )

        response = GetUserPlansRangeResponse.model_validate(data)
        return response.get_user_plans_range.items

    async def get_workout_details(self, workout_id: str) -> WorkoutDetails:
        """Get detailed information about a specific workout.

        Args:
            workout_id: The workout ID.

        Returns:
            Detailed workout information.

        Raises:
            WahooAPIError: If workout not found or API error.
        """
        variables = {
            "input": {
                "workoutIds": [workout_id],
            }
        }

        data = await self._call_api(
            GET_WORKOUTS_QUERY,
            variables=variables,
            operation_name="GetWorkouts",
        )

        response = GetWorkoutsResponse.model_validate(data)
        workouts = response.get_workouts.workouts

        if not workouts:
            raise WahooAPIError(f"Workout not found: {workout_id}")

        return workouts[0]

    async def get_workout_library(
        self, filters: dict[str, Any] | None = None
    ) -> list[LibraryContent]:
        """Get workouts from the library with optional filtering.

        Args:
            filters: Optional filters to apply. Supported keys:
                - sport: Filter by workout type (e.g., "Cycling", "Running")
                - channel: Filter by channel name
                - category: Filter by category
                - intensity: Filter by intensity level
                - min_duration: Minimum duration in minutes
                - max_duration: Maximum duration in minutes
                - min_tss: Minimum TSS
                - max_tss: Maximum TSS
                - search: Search term for workout name
                - sort_by: Sort field ("name", "duration", "tss")
                - sort_direction: Sort direction ("asc", "desc")
                - limit: Maximum results to return

        Returns:
            List of matching library content.
        """
        data = await self._call_api(
            LIBRARY_QUERY,
            operation_name="Library",
        )

        response = LibraryResponse.model_validate(data)
        content = response.library.content

        # Convert channel IDs to human-readable names
        for item in content:
            if item.channel in CHANNEL_ID_TO_NAME:
                item.channel = CHANNEL_ID_TO_NAME[item.channel]

        if filters is None:
            return content

        # Apply filters client-side
        filtered = content

        if "sport" in filters:
            sport = filters["sport"]
            filtered = [c for c in filtered if c.workout_type.lower() == sport.lower()]

        if "channel" in filters:
            channel = filters["channel"]
            filtered = [c for c in filtered if c.channel.lower() == channel.lower()]

        if "category" in filters:
            category = filters["category"]
            filtered = [c for c in filtered if c.category.lower() == category.lower()]

        if "intensity" in filters:
            intensity = filters["intensity"]
            filtered = [
                c for c in filtered if c.intensity and c.intensity.lower() == intensity.lower()
            ]

        if "min_duration" in filters:
            min_seconds = filters["min_duration"] * 60
            filtered = [c for c in filtered if c.duration >= min_seconds]

        if "max_duration" in filters:
            max_seconds = filters["max_duration"] * 60
            filtered = [c for c in filtered if c.duration <= max_seconds]

        if "min_tss" in filters:
            min_tss = filters["min_tss"]
            filtered = [
                c for c in filtered if c.metrics and c.metrics.tss and c.metrics.tss >= min_tss
            ]

        if "max_tss" in filters:
            max_tss = filters["max_tss"]
            filtered = [
                c for c in filtered if c.metrics and c.metrics.tss and c.metrics.tss <= max_tss
            ]

        if "search" in filters:
            search = filters["search"].lower()
            filtered = [c for c in filtered if search in c.name.lower()]

        # Apply sorting
        sort_by = filters.get("sort_by", "name")
        sort_desc = filters.get("sort_direction", "asc") == "desc"

        if sort_by == "name":
            filtered.sort(key=lambda c: c.name.lower(), reverse=sort_desc)
        elif sort_by == "duration":
            filtered.sort(key=lambda c: c.duration, reverse=sort_desc)
        elif sort_by == "tss":
            filtered.sort(
                key=lambda c: (c.metrics.tss if c.metrics and c.metrics.tss else 0),
                reverse=sort_desc,
            )

        # Apply limit
        if "limit" in filters:
            filtered = filtered[: filters["limit"]]

        return filtered

    async def get_cycling_workouts(
        self, filters: dict[str, Any] | None = None
    ) -> list[LibraryContent]:
        """Get cycling workouts from the library.

        This is a convenience method that automatically filters for cycling workouts
        and supports additional cycling-specific filters.

        Args:
            filters: Optional filters. Supports all get_workout_library filters plus:
                - four_dp_focus: Filter by 4DP energy system (NM, AC, MAP, FTP)
                  where rating >= 4

        Returns:
            List of matching cycling workouts.
        """
        cycling_filters = {"sport": "Cycling", **(filters or {})}
        content = await self.get_workout_library(cycling_filters)

        # Apply 4DP focus filter
        if filters and "four_dp_focus" in filters:
            focus = filters["four_dp_focus"].upper()
            result = []
            for c in content:
                if c.metrics and c.metrics.ratings:
                    rating = 0
                    if focus == "NM":
                        rating = c.metrics.ratings.nm
                    elif focus == "AC":
                        rating = c.metrics.ratings.ac
                    elif focus == "MAP":
                        rating = c.metrics.ratings.map_
                    elif focus == "FTP":
                        rating = c.metrics.ratings.ftp
                    if rating >= 4:
                        result.append(c)
            return result

        return content

    async def schedule_workout(self, content_id: str, date: str, time_zone: str = "UTC") -> str:
        """Schedule a workout from the library to a specific date.

        Args:
            content_id: The content ID from library search results.
            date: The date to schedule (YYYY-MM-DD format).
            time_zone: Timezone for the workout (e.g., "Europe/Lisbon").

        Returns:
            The agenda ID of the scheduled workout.

        Raises:
            WahooAPIError: If scheduling fails.
        """
        variables = {
            "input": {
                "contentId": content_id,
                "date": date,
                "timeZone": time_zone,
            }
        }

        data = await self._call_api(
            ADD_AGENDA_MUTATION,
            variables=variables,
            operation_name="AddAgenda",
        )

        response = AddAgendaResponse.model_validate(data)

        if response.add_agenda.status != "success":
            raise WahooAPIError(
                f"Failed to schedule workout: {response.add_agenda.message or 'Unknown error'}"
            )

        return response.add_agenda.agenda_id

    async def reschedule_workout(
        self, agenda_id: str, new_date: str, time_zone: str = "UTC"
    ) -> None:
        """Move a scheduled workout to a different date.

        Args:
            agenda_id: The agenda ID from get_calendar or schedule_workout.
            new_date: The new date (YYYY-MM-DD format).
            time_zone: Timezone for the workout.

        Raises:
            WahooAPIError: If rescheduling fails.
        """
        variables = {
            "input": {
                "agendaId": agenda_id,
                "newDate": new_date,
                "timeZone": time_zone,
            }
        }

        data = await self._call_api(
            MOVE_AGENDA_MUTATION,
            variables=variables,
            operation_name="MoveAgenda",
        )

        response = MoveAgendaResponse.model_validate(data)

        if response.move_agenda.status != "success":
            raise WahooAPIError("Failed to reschedule workout")

    async def remove_workout(self, agenda_id: str) -> None:
        """Remove a scheduled workout from the calendar.

        Args:
            agenda_id: The agenda ID from get_calendar or schedule_workout.

        Raises:
            WahooAPIError: If removal fails.
        """
        variables = {
            "input": {
                "agendaId": agenda_id,
            }
        }

        data = await self._call_api(
            DELETE_AGENDA_MUTATION,
            variables=variables,
            operation_name="DeleteAgenda",
        )

        response = DeleteAgendaResponse.model_validate(data)

        if response.delete_agenda.status != "success":
            raise WahooAPIError("Failed to remove workout")

    async def get_rider_profile(self) -> RiderProfile | None:
        """Get the basic rider 4DP profile.

        Returns:
            The rider's 4DP profile (NM, AC, MAP, FTP) or None if not available.
        """
        return self._rider_profile

    async def get_enhanced_rider_profile(self) -> EnhancedRiderProfile | None:
        """Get the enhanced rider profile with full test results and analysis.

        Returns:
            Enhanced profile including rider type, weakness analysis,
            and heart rate zones, or None if no test has been completed.
        """
        data = await self._call_api(
            MOST_RECENT_TEST_QUERY,
            operation_name="MostRecentTest",
        )

        response = MostRecentTestResponse.model_validate(data)
        test_data = response.most_recent_test

        if not test_data.fitness_test_ridden:
            return None

        # Calculate heart rate zones
        hr_zones = _calculate_heart_rate_zones(test_data.lactate_threshold_heart_rate)

        return EnhancedRiderProfile(
            nm=test_data.power_5s.value,
            ac=test_data.power_1m.value,
            map=test_data.power_5m.value,
            ftp=test_data.power_20m.value,
            power5s=test_data.power_5s,
            power1m=test_data.power_1m,
            power5m=test_data.power_5m,
            power20m=test_data.power_20m,
            lactateThresholdHeartRate=test_data.lactate_threshold_heart_rate,
            heartRateZones=hr_zones,
            riderType=test_data.rider_type,
            riderWeakness=test_data.rider_weakness,
            fitnessTestRidden=test_data.fitness_test_ridden,
            startTime=test_data.start_time,
            endTime=test_data.end_time,
        )

    async def get_fitness_test_history(
        self, page: int = 1, page_size: int = 15
    ) -> tuple[list[FitnessTestResult], int]:
        """Get history of completed fitness tests.

        Args:
            page: Page number (1-indexed).
            page_size: Number of results per page.

        Returns:
            Tuple of (list of test results, total count).
        """
        offset = (page - 1) * page_size

        variables = {
            "input": {
                "workoutIds": [FULL_FRONTAL_ID, HALF_MONTY_ID],
                "limit": page_size,
                "offset": offset,
            }
        }

        data = await self._call_api(
            SEARCH_ACTIVITIES_QUERY,
            variables=variables,
            operation_name="SearchActivities",
        )

        response = SearchActivitiesResponse.model_validate(data)
        return response.search_activities.activities, response.search_activities.total

    async def get_fitness_test_details(self, activity_id: str) -> FitnessTestDetails:
        """Get detailed data for a specific fitness test.

        Args:
            activity_id: The activity ID from get_fitness_test_history.

        Returns:
            Detailed test data including power/cadence/HR time series.

        Raises:
            WahooAPIError: If activity not found or API error.
        """
        variables = {
            "input": {
                "activityId": activity_id,
            }
        }

        data = await self._call_api(
            GET_ACTIVITY_QUERY,
            variables=variables,
            operation_name="GetActivity",
        )

        response = GetActivityResponse.model_validate(data)
        return response.get_activity
