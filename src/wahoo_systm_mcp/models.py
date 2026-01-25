"""Pydantic models for Wahoo SYSTM API responses."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# Core Types
# =============================================================================


class WahooCredentials(BaseModel):
    """Wahoo SYSTM login credentials."""

    username: str
    password: str


class RiderProfile(BaseModel):
    """4DP power profile values."""

    nm: int = Field(description="Neuromuscular Power (5s)")
    ac: int = Field(description="Anaerobic Capacity (1min)")
    map_: int = Field(alias="map", description="Maximal Aerobic Power (5min)")
    ftp: int = Field(description="Functional Threshold Power (20min)")

    model_config = {"populate_by_name": True}


class PowerTestValue(BaseModel):
    """Power test result with status and values."""

    status: str
    graph_value: int = Field(alias="graphValue")
    value: int

    model_config = {"populate_by_name": True}


class RiderTypeInfo(BaseModel):
    """Rider type classification info."""

    name: str
    description: str
    icon: str


class RiderWeaknessInfo(BaseModel):
    """Rider weakness and strength analysis."""

    name: str
    description: str
    weakness_summary: str = Field(alias="weaknessSummary")
    weakness_description: str = Field(alias="weaknessDescription")
    strength_name: str = Field(alias="strengthName")
    strength_description: str = Field(alias="strengthDescription")
    strength_summary: str = Field(alias="strengthSummary")

    model_config = {"populate_by_name": True}


class HeartRateZone(BaseModel):
    """Heart rate training zone."""

    zone: int
    name: str
    min: int
    max: int | None = None


class EnhancedRiderProfile(RiderProfile):
    """Extended rider profile with test values and analysis."""

    # Power values with scores
    power_5s: PowerTestValue = Field(alias="power5s")
    power_1m: PowerTestValue = Field(alias="power1m")
    power_5m: PowerTestValue = Field(alias="power5m")
    power_20m: PowerTestValue = Field(alias="power20m")

    # Heart rate data
    lactate_threshold_heart_rate: int = Field(alias="lactateThresholdHeartRate")
    heart_rate_zones: list[HeartRateZone] = Field(default_factory=list, alias="heartRateZones")

    # Rider characteristics
    rider_type: RiderTypeInfo = Field(alias="riderType")
    rider_weakness: RiderWeaknessInfo = Field(alias="riderWeakness")

    # Test metadata
    fitness_test_ridden: bool = Field(alias="fitnessTestRidden")
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")

    model_config = {"populate_by_name": True}


# =============================================================================
# Workout Types
# =============================================================================


class WorkoutIntensity(BaseModel):
    """Workout intensity ratings across energy systems."""

    master: int
    nm: int
    ac: int
    map_: int = Field(alias="map")
    ftp: int

    model_config = {"populate_by_name": True}


class WorkoutProspect(BaseModel):
    """Workout prospect in a calendar plan."""

    type: str
    name: str
    compatibility: str
    description: str
    style: str
    intensity: WorkoutIntensity
    planned_duration: int = Field(alias="plannedDuration")
    duration_type: str = Field(alias="durationType")
    content_id: str = Field(alias="contentId")
    workout_id: str = Field(alias="workoutId")
    notes: str | None = None

    model_config = {"populate_by_name": True}


class PlanInfo(BaseModel):
    """Training plan metadata."""

    id: str
    name: str
    color: str
    description: str
    category: str


class UserPlanItem(BaseModel):
    """A scheduled item in the user's training calendar."""

    day: int
    planned_date: str = Field(alias="plannedDate")
    rank: int
    agenda_id: str = Field(alias="agendaId")
    status: str
    type: str
    prospects: list[WorkoutProspect]
    plan: PlanInfo

    model_config = {"populate_by_name": True}


class WorkoutEquipment(BaseModel):
    """Equipment needed for a workout."""

    name: str
    description: str


class WorkoutDescription(BaseModel):
    """Workout description section."""

    title: str
    body: str


class WorkoutRatings(BaseModel):
    """4DP intensity ratings for a workout."""

    nm: int
    ac: int
    map_: int = Field(alias="map")
    ftp: int

    model_config = {"populate_by_name": True}


class WorkoutMetrics(BaseModel):
    """Workout training metrics."""

    intensity_factor: float = Field(alias="intensityFactor")
    tss: int
    ratings: WorkoutRatings

    model_config = {"populate_by_name": True}


class WorkoutDetails(BaseModel):
    """Detailed workout information."""

    id: str
    name: str
    sport: str
    short_description: str = Field(alias="shortDescription")
    details: str
    level: str
    duration_seconds: int = Field(alias="durationSeconds")
    equipment: list[WorkoutEquipment]
    descriptions: list[WorkoutDescription] | None = None
    metrics: WorkoutMetrics
    triggers: str  # JSON string containing interval data

    model_config = {"populate_by_name": True}

    @field_validator("triggers", mode="before")
    @classmethod
    def parse_triggers(cls, v: Any) -> str:
        """Ensure triggers is a JSON string."""
        if isinstance(v, dict):
            return json.dumps(v)
        return v


class LibraryMetrics(BaseModel):
    """Optional metrics for library content."""

    tss: int | None = None
    intensity_factor: float | None = Field(default=None, alias="intensityFactor")
    ratings: WorkoutRatings | None = None

    model_config = {"populate_by_name": True}


class LibraryContent(BaseModel):
    """Workout content from the library."""

    id: str
    name: str
    media_type: str = Field(alias="mediaType")
    channel: str
    workout_type: str = Field(alias="workoutType")
    category: str
    level: str
    duration: int
    workout_id: str = Field(alias="workoutId")
    video_id: str | None = Field(default=None, alias="videoId")
    banner_image: str | None = Field(default=None, alias="bannerImage")
    poster_image: str | None = Field(default=None, alias="posterImage")
    default_image: str | None = Field(default=None, alias="defaultImage")
    intensity: str | None = None
    tags: list[str] | None = None
    descriptions: list[WorkoutDescription] | None = None
    metrics: LibraryMetrics | None = None

    model_config = {"populate_by_name": True}


class SportInfo(BaseModel):
    """Sport/activity type info."""

    id: str
    workout_type: str = Field(alias="workoutType")
    name: str
    description: str

    model_config = {"populate_by_name": True}


class ChannelInfo(BaseModel):
    """Content channel info."""

    id: str
    name: str
    description: str


# =============================================================================
# Fitness Test Types
# =============================================================================


class FitnessTestResults(BaseModel):
    """Test results from a fitness test activity."""

    power_5s: PowerTestValue = Field(alias="power5s")
    power_1m: PowerTestValue = Field(alias="power1m")
    power_5m: PowerTestValue = Field(alias="power5m")
    power_20m: PowerTestValue = Field(alias="power20m")
    lactate_threshold_heart_rate: int = Field(alias="lactateThresholdHeartRate")
    rider_type: RiderTypeInfo = Field(alias="riderType")

    model_config = {"populate_by_name": True}


class FitnessTestResult(BaseModel):
    """Summary of a completed fitness test."""

    id: str
    name: str
    completed_date: str = Field(alias="completedDate")
    duration_seconds: int = Field(alias="durationSeconds")
    distance_km: float = Field(alias="distanceKm")
    tss: int
    intensity_factor: float = Field(alias="intensityFactor")
    test_results: FitnessTestResults | None = Field(default=None, alias="testResults")

    model_config = {"populate_by_name": True}


class PowerBest(BaseModel):
    """Power curve best effort."""

    duration: int
    value: int


class FitnessTestDetails(BaseModel):
    """Detailed fitness test data including time series."""

    id: str
    name: str
    completed_date: str = Field(alias="completedDate")
    duration_seconds: int = Field(alias="durationSeconds")
    distance_km: float = Field(alias="distanceKm")
    tss: int
    intensity_factor: float = Field(alias="intensityFactor")
    notes: str
    test_results: FitnessTestResults = Field(alias="testResults")
    profile: RiderProfile
    power: list[int]
    cadence: list[int]
    heart_rate: list[int] = Field(alias="heartRate")
    power_bests: list[PowerBest] = Field(alias="powerBests")
    analysis: str

    model_config = {"populate_by_name": True}


# =============================================================================
# GraphQL Response Wrappers
# =============================================================================


class LoginUserData(BaseModel):
    """Login response user data."""

    status: str
    message: str
    token: str
    user: dict[str, Any]  # Contains nested profiles


class LoginResponse(BaseModel):
    """GraphQL login response."""

    login_user: LoginUserData = Field(alias="loginUser")

    model_config = {"populate_by_name": True}


class MostRecentTestData(BaseModel):
    """Most recent test response data."""

    status: str
    message: str | None
    fitness_test_ridden: bool = Field(alias="fitnessTestRidden")
    rider_type: RiderTypeInfo = Field(alias="riderType")
    rider_weakness: RiderWeaknessInfo = Field(alias="riderWeakness")
    power_5s: PowerTestValue = Field(alias="power5s")
    power_1m: PowerTestValue = Field(alias="power1m")
    power_5m: PowerTestValue = Field(alias="power5m")
    power_20m: PowerTestValue = Field(alias="power20m")
    lactate_threshold_heart_rate: int = Field(alias="lactateThresholdHeartRate")
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")

    model_config = {"populate_by_name": True}


class MostRecentTestResponse(BaseModel):
    """GraphQL most recent test response."""

    most_recent_test: MostRecentTestData = Field(alias="mostRecentTest")

    model_config = {"populate_by_name": True}


class LibraryData(BaseModel):
    """Library response data."""

    content: list[LibraryContent]
    sports: list[SportInfo]
    channels: list[ChannelInfo]


class LibraryResponse(BaseModel):
    """GraphQL library response."""

    library: LibraryData


class AddAgendaData(BaseModel):
    """Add agenda response data."""

    status: str
    message: str | None
    agenda_id: str = Field(alias="agendaId")

    model_config = {"populate_by_name": True}


class AddAgendaResponse(BaseModel):
    """GraphQL add agenda response."""

    add_agenda: AddAgendaData = Field(alias="addAgenda")

    model_config = {"populate_by_name": True}


class MoveAgendaData(BaseModel):
    """Move agenda response data."""

    status: str


class MoveAgendaResponse(BaseModel):
    """GraphQL move agenda response."""

    move_agenda: MoveAgendaData = Field(alias="moveAgenda")

    model_config = {"populate_by_name": True}


class DeleteAgendaData(BaseModel):
    """Delete agenda response data."""

    status: str


class DeleteAgendaResponse(BaseModel):
    """GraphQL delete agenda response."""

    delete_agenda: DeleteAgendaData = Field(alias="deleteAgenda")

    model_config = {"populate_by_name": True}


class SearchActivitiesData(BaseModel):
    """Search activities response data."""

    activities: list[FitnessTestResult]
    total: int


class SearchActivitiesResponse(BaseModel):
    """GraphQL search activities response."""

    search_activities: SearchActivitiesData = Field(alias="searchActivities")

    model_config = {"populate_by_name": True}


class GetActivityResponse(BaseModel):
    """GraphQL get activity response."""

    get_activity: FitnessTestDetails = Field(alias="getActivity")

    model_config = {"populate_by_name": True}


class GetUserPlansRangeData(BaseModel):
    """Get user plans range response data."""

    status: str
    message: str | None
    items: list[UserPlanItem]


class GetUserPlansRangeResponse(BaseModel):
    """GraphQL get user plans range response."""

    get_user_plans_range: GetUserPlansRangeData = Field(alias="getUserPlansRange")

    model_config = {"populate_by_name": True}


class WorkoutDetailsData(BaseModel):
    """Get workouts response data."""

    workouts: list[WorkoutDetails]


class GetWorkoutsResponse(BaseModel):
    """GraphQL get workouts response."""

    get_workouts: WorkoutDetailsData = Field(alias="getWorkouts")

    model_config = {"populate_by_name": True}
