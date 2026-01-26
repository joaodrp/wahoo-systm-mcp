"""Pydantic models for Wahoo SYSTM API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator

from wahoo_systm_mcp.types import JSONValue


class RiderProfile(BaseModel):
    """4DP power profile values."""

    nm: int = Field(description="Neuromuscular Power (5s)")
    ac: int = Field(description="Anaerobic Capacity (1min)")
    map_: int = Field(alias="map", description="Maximal Aerobic Power (5min)")
    ftp: int = Field(description="Functional Threshold Power (20min)")
    lthr: float | None = Field(default=None, alias="lthr")
    cadence_threshold: int | None = Field(default=None, alias="cadenceThreshold")

    model_config = {"populate_by_name": True}


class PowerTestValue(BaseModel):
    """Power test result with status and values."""

    status: str
    graph_value: float = Field(alias="graphValue")
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
    lactate_threshold_heart_rate: float = Field(alias="lactateThresholdHeartRate")
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

    master: int | None = None
    nm: int | None = None
    ac: int | None = None
    map_: int | None = Field(default=None, alias="map")
    ftp: int | None = None

    model_config = {"populate_by_name": True}


class WorkoutProspectMetrics(BaseModel):
    """Metrics attached to a workout prospect."""

    ratings: WorkoutRatings | None = None


class TrainerSetting(BaseModel):
    """Trainer settings for a workout prospect."""

    mode: str | None = None
    level: int | None = None


def _normalize_graph_triggers(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        times = value.get("time")
        values = value.get("value")
        types = value.get("type")
        if (
            not isinstance(times, list)
            or not isinstance(values, list)
            or not isinstance(types, list)
        ):
            return value
        length = min(len(times), len(values), len(types))
        return [{"time": times[i], "value": values[i], "type": types[i]} for i in range(length)]
    return value


class WorkoutGraphTrigger(BaseModel):
    """Graph trigger data point for a workout."""

    time: int
    value: float | int
    type: str


class WorkoutProspect(BaseModel):
    """Workout prospect in a calendar plan."""

    type: str
    name: str
    compatibility: str | None = None
    description: str | None = None
    style: str | None = None
    intensity: WorkoutIntensity | None = None
    trainer_setting: TrainerSetting | None = Field(default=None, alias="trainerSetting")
    planned_duration: float | None = Field(default=None, alias="plannedDuration")
    duration_type: str | None = Field(default=None, alias="durationType")
    metrics: WorkoutProspectMetrics | None = None
    content_id: str | None = Field(default=None, alias="contentId")
    workout_id: str | None = Field(default=None, alias="workoutId")
    notes: str | None = None
    four_dp_workout_graph: list[WorkoutGraphTrigger] | None = Field(
        default=None, alias="fourDPWorkoutGraph"
    )

    @field_validator("four_dp_workout_graph", mode="before")
    @classmethod
    def normalize_four_dp_workout_graph(cls, value: object) -> object:
        return _normalize_graph_triggers(value)

    model_config = {"populate_by_name": True}


class PlanInfo(BaseModel):
    """Training plan metadata."""

    id: str
    name: str
    color: str | None = None
    description: str | None = None
    category: str | None = None
    grouping: str | None = None
    level: str | None = None
    type: str | None = None


class PlanLinkData(BaseModel):
    """Linked activity data for a calendar item."""

    name: str | None = None
    date: str | None = None
    activity_id: str | None = Field(default=None, alias="activityId")
    duration_seconds: int | None = Field(default=None, alias="durationSeconds")
    style: str | None = None
    deleted: bool | None = None

    model_config = {"populate_by_name": True}


class UserPlanItem(BaseModel):
    """A scheduled item in the user's training calendar."""

    day: int | None = None
    planned_date: str | None = Field(default=None, alias="plannedDate")
    rank: int | None = None
    agenda_id: str | None = Field(default=None, alias="agendaId")
    status: str | None = None
    type: str | None = None
    applied_time_zone: str | None = Field(default=None, alias="appliedTimeZone")
    wahoo_workout_id: str | int | None = Field(default=None, alias="wahooWorkoutId")
    completion_data: PlanLinkData | None = Field(default=None, alias="completionData")
    link_data: PlanLinkData | None = Field(default=None, alias="linkData")
    prospects: list[WorkoutProspect] | None = None
    plan: PlanInfo | None = None

    model_config = {"populate_by_name": True}


class WorkoutEquipment(BaseModel):
    """Equipment needed for a workout."""

    name: str | None = None
    description: str | None = None
    thumbnail: str | None = None


class WorkoutDescription(BaseModel):
    """Workout description section."""

    title: str | None = None
    body: str | None = None


class WorkoutRatings(BaseModel):
    """4DP intensity ratings for a workout."""

    nm: int | None = None
    ac: int | None = None
    map_: int | None = Field(default=None, alias="map")
    ftp: int | None = None

    model_config = {"populate_by_name": True}


class WorkoutMetrics(BaseModel):
    """Workout training metrics."""

    intensity_factor: float | None = Field(default=None, alias="intensityFactor")
    tss: int | None = None
    ratings: WorkoutRatings | None = None

    model_config = {"populate_by_name": True}


class WorkoutDetails(BaseModel):
    """Detailed workout information."""

    id: str
    name: str
    sport: str | None = None
    short_description: str | None = Field(default=None, alias="shortDescription")
    details: str | None = None
    level: str | None = None
    duration_seconds: int | None = Field(default=None, alias="durationSeconds")
    equipment: list[WorkoutEquipment] | None = None
    descriptions: list[WorkoutDescription] | None = None
    metrics: WorkoutMetrics | None = None
    graph_triggers: list[WorkoutGraphTrigger] | None = Field(default=None, alias="graphTriggers")

    @field_validator("graph_triggers", mode="before")
    @classmethod
    def normalize_graph_triggers(cls, value: object) -> object:
        return _normalize_graph_triggers(value)

    model_config = {"populate_by_name": True}


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
    channel: str | None = None
    workout_type: str | None = Field(default=None, alias="workoutType")
    category: str | None = None
    level: str | None = None
    duration: int | None = None
    workout_id: str | None = Field(default=None, alias="workoutId")
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
    description: str | None = None

    model_config = {"populate_by_name": True}


class ChannelInfo(BaseModel):
    """Content channel info."""

    id: str
    name: str
    description: str | None = None


# =============================================================================
# Fitness Test Types
# =============================================================================


class FitnessTestResults(BaseModel):
    """Test results from a fitness test activity."""

    power_5s: PowerTestValue = Field(alias="power5s")
    power_1m: PowerTestValue = Field(alias="power1m")
    power_5m: PowerTestValue = Field(alias="power5m")
    power_20m: PowerTestValue = Field(alias="power20m")
    lactate_threshold_heart_rate: float = Field(alias="lactateThresholdHeartRate")
    rider_type: RiderTypeInfo = Field(alias="riderType")

    model_config = {"populate_by_name": True}


class FitnessTestResult(BaseModel):
    """Summary of a completed fitness test."""

    id: str
    name: str
    completed_date: str | None = Field(default=None, alias="completedDate")
    duration_seconds: int | None = Field(default=None, alias="durationSeconds")
    distance_km: float | None = Field(default=None, alias="distanceKm")
    tss: int | None = None
    intensity_factor: float | None = Field(default=None, alias="intensityFactor")
    test_results: FitnessTestResults | None = Field(default=None, alias="testResults")
    workout_id: str | None = Field(default=None, alias="workoutId")
    content_id: str | None = Field(default=None, alias="contentId")
    analysis: str | None = None

    model_config = {"populate_by_name": True}


class PowerBest(BaseModel):
    """Power curve best effort."""

    duration: int
    value: int


class FitnessTestDetails(BaseModel):
    """Detailed fitness test data including time series."""

    id: str
    name: str
    completed_date: str | None = Field(default=None, alias="completedDate")
    duration_seconds: int | None = Field(default=None, alias="durationSeconds")
    distance_km: float | None = Field(default=None, alias="distanceKm")
    tss: int | None = None
    intensity_factor: float | None = Field(default=None, alias="intensityFactor")
    notes: str | None = None
    test_results: FitnessTestResults | None = Field(default=None, alias="testResults")
    profile: RiderProfile | None = None
    power: list[int] | None = None
    cadence: list[int] | None = None
    heart_rate: list[int] | None = Field(default=None, alias="heartRate")
    power_bests: list[PowerBest] | None = Field(default=None, alias="powerBests")
    analysis: str | None = None

    model_config = {"populate_by_name": True}


# =============================================================================
# GraphQL Response Wrappers
# =============================================================================


class LoginUserData(BaseModel):
    """Login response user data."""

    status: str
    message: str | None = None
    token: str
    user: dict[str, JSONValue]  # Contains nested profiles


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
    lactate_threshold_heart_rate: float = Field(alias="lactateThresholdHeartRate")
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
    count: int


class SearchActivitiesResponse(BaseModel):
    """GraphQL search activities response."""

    search_activities: SearchActivitiesData = Field(alias="searchActivities")

    model_config = {"populate_by_name": True}


class GetWorkoutActivitiesResponse(BaseModel):
    """GraphQL get workout activities response."""

    get_workout_activities: SearchActivitiesData = Field(alias="getWorkoutActivities")

    model_config = {"populate_by_name": True}


class GetActivityResponse(BaseModel):
    """GraphQL get activity response."""

    activity: FitnessTestDetails

    model_config = {"populate_by_name": True}


class GetUserPlansRangeResponse(BaseModel):
    """GraphQL get user plans range response."""

    user_plan: list[UserPlanItem] = Field(alias="userPlan")

    model_config = {"populate_by_name": True}


class GetWorkoutsResponse(BaseModel):
    """GraphQL get workouts response."""

    workouts: list[WorkoutDetails]

    model_config = {"populate_by_name": True}
