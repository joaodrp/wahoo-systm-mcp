"""Wahoo SYSTM GraphQL API client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import AsyncClient, HTTPError, TimeoutException

from wahoo_systm_mcp.client.config import ClientConfig
from wahoo_systm_mcp.client.models import (
    AddAgendaResponse,
    DeleteAgendaResponse,
    EnhancedRiderProfile,
    FitnessTestDetails,
    FitnessTestResult,
    GetActivityResponse,
    GetUserPlansRangeResponse,
    GetWorkoutActivitiesResponse,
    GetWorkoutsResponse,
    HeartRateZone,
    LibraryContent,
    LibraryResponse,
    LoginResponse,
    MostRecentTestResponse,
    MoveAgendaResponse,
    RiderProfile,
    UserPlanItem,
    WorkoutDetails,
)
from wahoo_systm_mcp.client.queries import (
    ADD_AGENDA_MUTATION,
    DELETE_AGENDA_MUTATION,
    GET_ACTIVITY_QUERY,
    GET_USER_PLANS_RANGE_QUERY,
    GET_WORKOUT_ACTIVITIES_QUERY,
    GET_WORKOUTS_QUERY,
    IMPERSONATE_MUTATION,
    LIBRARY_QUERY,
    LOGIN_MUTATION,
    MOST_RECENT_TEST_QUERY,
    MOVE_AGENDA_MUTATION,
)

if TYPE_CHECKING:
    from wahoo_systm_mcp.types import FilterParams, JSONObject, JSONValue

# =============================================================================
# Constants
# =============================================================================

FULL_FRONTAL_ID = "dRcyg09t6K"
HALF_MONTY_ID = "0SmbqUIZZo"

# Channel ID to human-readable name mapping
CHANNEL_ID_TO_NAME: dict[str, str] = {
    "MvDmhsvEBR": "The Sufferfest",
    "y11gocEkS1": "Inspiration",
    "Ct5ivN5m1p": "A Week With",
    "zG7zYnMbH9": "ProRides",
    "0MEmGeS5js": "On Location",
    "Wmrk3N9mqG": "NoVid",
    "Fw2pE7Dp04": "Fitness Test",
    "XovWbVRkx6": "Getting Started",
    "tXmnHtjJAK": "Wahoo RGT",
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


# =============================================================================
# Helper Functions
# =============================================================================


def _calculate_heart_rate_zones(lthr: float) -> list[HeartRateZone]:
    """Calculate heart rate training zones based on cTHR (UI-aligned).

    Matches the athlete profile UI ranges:
    - Z1 Recovery: < 70%
    - Z2 Endurance: 70-87%
    - Z3 Tempo: 88-95%
    - Z4 Threshold: 96-100%
    - Z5 Max: > 100%
    """
    if lthr <= 0:
        return []

    min_endurance = int(lthr * 0.70)
    max_endurance = int(lthr * 0.87) + 1
    min_tempo = int(lthr * 0.88)
    max_tempo = int(lthr * 0.95)
    min_threshold = int(lthr * 0.96)
    max_threshold = int(lthr * 1.00)

    return [
        HeartRateZone(zone=1, name="Recovery", min=0, max=max(min_endurance - 1, 0)),
        HeartRateZone(zone=2, name="Endurance", min=min_endurance + 1, max=max_endurance),
        HeartRateZone(zone=3, name="Tempo", min=min_tempo, max=max_tempo),
        HeartRateZone(zone=4, name="Threshold", min=min_threshold, max=max_threshold),
        HeartRateZone(zone=5, name="Max", min=max_threshold + 1, max=None),
    ]


# =============================================================================
# Client
# =============================================================================


class WahooClient:
    """Async client for the Wahoo SYSTM GraphQL API."""

    def __init__(self, config: ClientConfig | None = None) -> None:
        """Initialize the client."""
        self._config = config or ClientConfig.from_env()
        self._token: str | None = None
        self._rider_profile: RiderProfile | None = None
        self._client: AsyncClient = AsyncClient(timeout=self._config.timeout)

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

    def _app_information(self) -> JSONObject:
        """Build app information payload for GraphQL queries."""
        app_info: JSONObject = {
            "platform": self._config.app_platform,
            "version": self._config.app_version,
        }
        if self._config.install_id:
            app_info["installId"] = self._config.install_id
        return app_info

    async def _call_api(
        self,
        query: str,
        variables: JSONObject | None = None,
        operation_name: str | None = None,
        require_auth: bool = True,
    ) -> JSONObject:
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
            "X-App-Version": self._config.app_version,
        }
        if self._config.install_id:
            headers["X-Install-Id"] = self._config.install_id

        if require_auth:
            token = self._require_auth()
            headers["Authorization"] = f"Bearer {token}"

        body: JSONObject = {"query": query}
        if variables is not None:
            body["variables"] = variables
        if operation_name is not None:
            body["operationName"] = operation_name

        try:
            response = await self._client.post(self._config.api_url, json=body, headers=headers)
        except TimeoutException as e:
            raise WahooAPIError("API request timed out") from e
        except HTTPError as e:
            raise WahooAPIError(f"HTTP error while calling API: {e}") from e

        if response.status_code != 200:
            raise WahooAPIError(
                f"API request failed: {response.text}",
                status_code=response.status_code,
            )

        try:
            result = response.json()
        except ValueError as e:
            raise WahooAPIError("API response was not valid JSON") from e

        if not isinstance(result, dict):
            raise WahooAPIError("API response was not a JSON object")

        errors_value = result.get("errors")
        if isinstance(errors_value, list) and errors_value:
            errors = errors_value
            error_message = errors[0].get("message", "Unknown error") if errors else "Unknown error"
            raise WahooAPIError(f"GraphQL error: {error_message}")

        data_value = result.get("data")
        if isinstance(data_value, dict):
            return data_value
        return {}

    async def authenticate(self, username: str, password: str) -> None:
        """Authenticate with Wahoo SYSTM.

        Args:
            username: The user's email address.
            password: The user's password.

        Raises:
            AuthenticationError: If authentication fails.
        """
        variables: JSONObject = {
            "username": username,
            "password": password,
            "appInformation": self._app_information(),
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

        if response.login_user.status.lower() != "success":
            raise AuthenticationError(
                f"Authentication failed: {response.login_user.message or 'Unknown error'}"
            )

        self._token = response.login_user.token

        # Profile data is fetched on demand to ensure latest values.

    async def get_calendar(
        self, start_date: str, end_date: str, time_zone: str = "UTC"
    ) -> list[UserPlanItem]:
        """Get planned workouts from calendar for a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            time_zone: Timezone for the calendar (e.g., "Europe/Lisbon").

        Returns:
            List of scheduled workout items.
        """
        query_params: JSONObject = {"limit": 1000}
        variables: JSONObject = {
            "startDate": start_date,
            "endDate": end_date,
            "queryParams": query_params,
            "timezone": time_zone,
        }

        data = await self._call_api(
            GET_USER_PLANS_RANGE_QUERY,
            variables=variables,
            operation_name="GetUserPlansRange",
        )

        response = GetUserPlansRangeResponse.model_validate(data)
        return response.user_plan

    async def get_workout_details(self, workout_id: str) -> WorkoutDetails:
        """Get detailed information about a specific workout.

        Accepts a workoutId, or a library content id (contentId). If a contentId is
        provided, the library is queried to map it to a workoutId.

        Args:
            workout_id: The workout ID or content ID.

        Returns:
            Detailed workout information.

        Raises:
            WahooAPIError: If workout not found or API error.
        """
        workout = await self._get_workout_details_by_id(workout_id)
        if workout:
            return workout

        # Try mapping contentId -> workoutId
        content = await self.get_workout_library()
        match = next((c for c in content if c.id == workout_id), None)
        if match and match.workout_id:
            mapped = await self._get_workout_details_by_id(match.workout_id)
            if mapped:
                return mapped

        raise WahooAPIError(f"Workout not found: {workout_id}")

    async def _get_workout_details_by_id(self, workout_id: str) -> WorkoutDetails | None:
        """Fetch workout details by workoutId, returning None when not found."""
        ids: list[JSONValue] = [workout_id]
        variables: JSONObject = {
            "ids": ids,
        }

        data = await self._call_api(
            GET_WORKOUTS_QUERY,
            variables=variables,
            operation_name="GetWorkoutCollection",
        )

        response = GetWorkoutsResponse.model_validate(data)
        workouts = response.workouts
        return workouts[0] if workouts else None

    async def get_workout_library(
        self, filters: FilterParams | None = None
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
        variables: JSONObject = {
            "locale": self._config.default_locale,
            "appInformation": self._app_information(),
        }

        data = await self._call_api(
            LIBRARY_QUERY,
            variables=variables,
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
            if isinstance(sport, str):
                filtered = [
                    c
                    for c in filtered
                    if c.workout_type and c.workout_type.lower() == sport.lower()
                ]

        if "channel" in filters:
            channel = filters["channel"]
            if isinstance(channel, str):
                filtered = [
                    c for c in filtered if c.channel and c.channel.lower() == channel.lower()
                ]

        if "category" in filters:
            category = filters["category"]
            if isinstance(category, str):
                filtered = [
                    c for c in filtered if c.category and c.category.lower() == category.lower()
                ]

        if "intensity" in filters:
            intensity = filters["intensity"]
            if isinstance(intensity, str):
                filtered = [
                    c for c in filtered if c.intensity and c.intensity.lower() == intensity.lower()
                ]

        if "min_duration" in filters:
            min_duration = filters["min_duration"]
            if isinstance(min_duration, (int, float)):
                min_seconds = min_duration * 60
                filtered = [c for c in filtered if c.duration and c.duration >= min_seconds]

        if "max_duration" in filters:
            max_duration = filters["max_duration"]
            if isinstance(max_duration, (int, float)):
                max_seconds = max_duration * 60
                filtered = [c for c in filtered if c.duration and c.duration <= max_seconds]

        if "min_tss" in filters:
            min_tss = filters["min_tss"]
            if isinstance(min_tss, (int, float)):
                filtered = [
                    c
                    for c in filtered
                    if c.metrics and c.metrics.tss is not None and c.metrics.tss >= min_tss
                ]

        if "max_tss" in filters:
            max_tss = filters["max_tss"]
            if isinstance(max_tss, (int, float)):
                filtered = [
                    c
                    for c in filtered
                    if c.metrics and c.metrics.tss is not None and c.metrics.tss <= max_tss
                ]

        if "search" in filters:
            search = filters["search"]
            if isinstance(search, str):
                filtered = [c for c in filtered if search.lower() in c.name.lower()]

        # Apply sorting
        sort_by_value = filters.get("sort_by", "name")
        sort_by = sort_by_value if isinstance(sort_by_value, str) else "name"
        sort_direction_value = filters.get("sort_direction", "asc")
        sort_desc = (
            sort_direction_value.lower() == "desc"
            if isinstance(sort_direction_value, str)
            else False
        )

        if sort_by == "name":
            filtered.sort(key=lambda c: c.name.lower(), reverse=sort_desc)
        elif sort_by == "duration":
            filtered.sort(key=lambda c: c.duration or 0, reverse=sort_desc)
        elif sort_by == "tss":
            filtered.sort(
                key=lambda c: (c.metrics.tss if c.metrics and c.metrics.tss else 0),
                reverse=sort_desc,
            )

        # Apply limit
        if "limit" in filters:
            limit = filters["limit"]
            if isinstance(limit, int):
                filtered = filtered[:limit]

        return filtered

    async def get_cycling_workouts(
        self, filters: FilterParams | None = None
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
        cycling_filters: FilterParams = {"sport": "Cycling", **(filters or {})}
        content = await self.get_workout_library(cycling_filters)

        # Apply 4DP focus filter
        if filters and "four_dp_focus" in filters:
            focus_value = filters["four_dp_focus"]
            if not isinstance(focus_value, str):
                return content
            focus = focus_value.upper()
            result = []
            for c in content:
                if c.metrics and c.metrics.ratings:
                    rating = 0
                    if focus == "NM":
                        rating = c.metrics.ratings.nm or 0
                    elif focus == "AC":
                        rating = c.metrics.ratings.ac or 0
                    elif focus == "MAP":
                        rating = c.metrics.ratings.map_ or 0
                    elif focus == "FTP":
                        rating = c.metrics.ratings.ftp or 0
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
        variables: JSONObject = {
            "contentId": content_id,
            "date": date,
            "timeZone": time_zone,
        }

        data = await self._call_api(
            ADD_AGENDA_MUTATION,
            variables=variables,
            operation_name="AddAgenda",
        )

        response = AddAgendaResponse.model_validate(data)

        if response.add_agenda.status.lower() != "success":
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
        variables: JSONObject = {
            "agendaId": agenda_id,
            "date": new_date,
            "timeZone": time_zone,
        }

        data = await self._call_api(
            MOVE_AGENDA_MUTATION,
            variables=variables,
            operation_name="MoveAgenda",
        )

        response = MoveAgendaResponse.model_validate(data)

        if response.move_agenda.status.lower() != "success":
            raise WahooAPIError("Failed to reschedule workout")

    async def remove_workout(self, agenda_id: str) -> None:
        """Remove a scheduled workout from the calendar.

        Args:
            agenda_id: The agenda ID from get_calendar or schedule_workout.

        Raises:
            WahooAPIError: If removal fails.
        """
        variables: JSONObject = {
            "agendaId": agenda_id,
        }

        data = await self._call_api(
            DELETE_AGENDA_MUTATION,
            variables=variables,
            operation_name="DeleteAgenda",
        )

        response = DeleteAgendaResponse.model_validate(data)

        if response.delete_agenda.status.lower() != "success":
            raise WahooAPIError("Failed to remove workout")

    async def get_current_profile(self) -> RiderProfile | None:
        """Get the current rider 4DP profile used for workout targets.

        Returns:
            The rider's 4DP profile (NM, AC, MAP, FTP) or None if not available.
        """
        if self._rider_profile:
            return self._rider_profile

        session_token = self._require_auth()
        variables: JSONObject = {
            "appInformation": self._app_information(),
            "sessionToken": session_token,
        }
        data = await self._call_api(
            IMPERSONATE_MUTATION,
            variables=variables,
            operation_name="Impersonate",
            require_auth=False,
        )

        result_value = data.get("impersonateUser")
        if not isinstance(result_value, dict):
            return self._rider_profile
        result = result_value

        token_value = result.get("token")
        if isinstance(token_value, str) and token_value:
            self._token = token_value

        user_value = result.get("user")
        if isinstance(user_value, dict):
            profiles_value = user_value.get("profiles")
            if isinstance(profiles_value, dict):
                rider_profile_value = profiles_value.get("riderProfile")
                if isinstance(rider_profile_value, dict):
                    self._rider_profile = RiderProfile.model_validate(rider_profile_value)

        return self._rider_profile

    async def get_latest_test_profile(self) -> EnhancedRiderProfile | None:
        """Get the latest fitness test profile with analysis metadata.

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

        Fetches activities completed using Full Frontal or Half Monty workouts.

        Args:
            page: Page number (1-indexed).
            page_size: Number of results per page.

        Returns:
            Tuple of (list of test results, total count of fitness tests).
        """
        variables: JSONObject = {
            "workoutIds": [FULL_FRONTAL_ID, HALF_MONTY_ID],
            "pageInformation": {"page": page, "pageSize": page_size},
        }

        data = await self._call_api(
            GET_WORKOUT_ACTIVITIES_QUERY,
            variables=variables,
            operation_name="GetWorkoutActivities",
        )

        response = GetWorkoutActivitiesResponse.model_validate(data)
        return (
            response.get_workout_activities.activities,
            response.get_workout_activities.count,
        )

    async def get_fitness_test_details(self, activity_id: str) -> FitnessTestDetails:
        """Get detailed data for a specific fitness test.

        Args:
            activity_id: The activity ID from get_fitness_test_history.

        Returns:
            Detailed test data including power/cadence/HR time series.

        Raises:
            WahooAPIError: If activity not found or API error.
        """
        variables: JSONObject = {
            "activityId": activity_id,
        }

        data = await self._call_api(
            GET_ACTIVITY_QUERY,
            variables=variables,
            operation_name="GetActivity",
        )

        response = GetActivityResponse.model_validate(data)
        return response.activity
