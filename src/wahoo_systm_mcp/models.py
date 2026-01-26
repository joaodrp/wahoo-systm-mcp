"""Output models for MCP tools."""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field

from wahoo_systm_mcp.types import JSONValue


class ToolModel(BaseModel):
    """Base model for tool outputs."""

    model_config = {"populate_by_name": True}


class WorkoutRatingsOut(ToolModel):
    nm: int | None = None
    ac: int | None = None
    map: int | None = Field(default=None, validation_alias=AliasChoices("map", "map_"))
    ftp: int | None = None


class WorkoutIntensityOut(ToolModel):
    master: int | None = None
    nm: int | None = None
    ac: int | None = None
    map: int | None = Field(default=None, validation_alias=AliasChoices("map", "map_"))
    ftp: int | None = None


class WorkoutMetricsOut(ToolModel):
    intensity_factor: float | None = None
    tss: int | None = None
    ratings: WorkoutRatingsOut | None = None


class WorkoutProspectMetricsOut(ToolModel):
    ratings: WorkoutRatingsOut | None = None


class TrainerSettingOut(ToolModel):
    mode: str | None = None
    level: int | None = None


class WorkoutGraphTriggerOut(ToolModel):
    time: int
    value: float | int
    type: str


class WorkoutProspectOut(ToolModel):
    type: str
    name: str
    compatibility: str | None = None
    description: str | None = None
    style: str | None = None
    intensity: WorkoutIntensityOut | None = None
    trainer_setting: TrainerSettingOut | None = None
    planned_duration: float | None = None
    duration_type: str | None = None
    metrics: WorkoutProspectMetricsOut | None = None
    content_id: str | None = None
    workout_id: str | None = None
    notes: str | None = None
    four_dp_workout_graph: list[WorkoutGraphTriggerOut] | None = None


class PlanInfoOut(ToolModel):
    id: str
    name: str
    color: str | None = None
    description: str | None = None
    category: str | None = None
    grouping: str | None = None
    level: str | None = None
    type: str | None = None


class PlanLinkDataOut(ToolModel):
    name: str | None = None
    date: str | None = None
    activity_id: str | None = None
    duration_seconds: int | None = None
    style: str | None = None
    deleted: bool | None = None


class UserPlanItemOut(ToolModel):
    day: int | None = None
    planned_date: str | None = None
    rank: int | None = None
    agenda_id: str | None = None
    status: str | None = None
    type: str | None = None
    applied_time_zone: str | None = None
    wahoo_workout_id: str | int | None = None
    completion_data: PlanLinkDataOut | None = None
    link_data: PlanLinkDataOut | None = None
    prospects: list[WorkoutProspectOut] | None = None
    plan: PlanInfoOut | None = None


class WorkoutEquipmentOut(ToolModel):
    name: str | None = None
    description: str | None = None
    thumbnail: str | None = None


class WorkoutDescriptionOut(ToolModel):
    title: str | None = None
    body: str | None = None


class WorkoutDetailsOut(ToolModel):
    id: str
    name: str
    sport: str | None = None
    short_description: str | None = None
    details: str | None = None
    level: str | None = None
    duration_seconds: int | None = None
    equipment: list[WorkoutEquipmentOut] | None = None
    descriptions: list[WorkoutDescriptionOut] | None = None
    metrics: WorkoutMetricsOut | None = None
    graph_triggers: list[WorkoutGraphTriggerOut] | None = None


class LibraryMetricsOut(ToolModel):
    tss: int | None = None
    intensity_factor: float | None = None
    ratings: WorkoutRatingsOut | None = None


class LibraryContentOut(ToolModel):
    id: str
    name: str
    media_type: str
    channel: str | None = None
    workout_type: str | None = None
    category: str | None = None
    level: str | None = None
    duration: int | None = None
    workout_id: str | None = None
    video_id: str | None = None
    banner_image: str | None = None
    poster_image: str | None = None
    default_image: str | None = None
    intensity: str | None = None
    tags: list[str] | None = None
    descriptions: list[WorkoutDescriptionOut] | None = None
    metrics: LibraryMetricsOut | None = None


class WorkoutsResultOut(ToolModel):
    total: int
    workouts: list[LibraryContentOut]


class ScheduleWorkoutResultOut(ToolModel):
    success: bool
    agenda_id: str
    date: str
    time_zone: str


class RescheduleWorkoutResultOut(ToolModel):
    success: bool
    message: str
    agenda_id: str
    new_date: str
    time_zone: str


class RemoveWorkoutResultOut(ToolModel):
    success: bool
    message: str
    agenda_id: str


class HeartRateZoneOut(ToolModel):
    zone: int
    name: str
    min: int
    max: int | None = None


class FourDPValueOut(ToolModel):
    watts: int
    score: float


class FourDPProfileOut(ToolModel):
    nm: FourDPValueOut
    ac: FourDPValueOut
    map: FourDPValueOut
    ftp: FourDPValueOut


class RiderTypeOut(ToolModel):
    name: str
    description: str


class StrengthWeaknessOut(ToolModel):
    name: str
    description: str
    summary: str


class RiderProfileOut(ToolModel):
    four_dp: FourDPProfileOut
    rider_type: RiderTypeOut
    strengths: StrengthWeaknessOut
    weaknesses: StrengthWeaknessOut
    lthr: float | None = None
    heart_rate_zones: list[HeartRateZoneOut]
    last_test_date: str | None = None


class FitnessTestSummaryOut(ToolModel):
    id: str
    name: str
    date: str | None = None
    duration: str | None = None
    distance: str | None = None
    tss: int | None = None
    intensity_factor: float | None = None
    four_dp: FourDPProfileOut | None = None
    lthr: float | None = None
    rider_type: str | None = None


class FitnessTestHistoryOut(ToolModel):
    tests: list[FitnessTestSummaryOut]
    total: int


class PowerCurvePointOut(ToolModel):
    duration: int
    value: int


class ActivityDataOut(ToolModel):
    power: list[int] | None = None
    cadence: list[int] | None = None
    heart_rate: list[int] | None = None


class FitnessTestDetailsOut(ToolModel):
    name: str
    date: str | None = None
    duration: str | None = None
    distance: str | None = None
    tss: int | None = None
    intensity_factor: float | None = None
    notes: str | None = None
    four_dp: FourDPProfileOut | None = None
    lthr: float | None = None
    rider_type: str | None = None
    power_curve: list[PowerCurvePointOut]
    activity_data: ActivityDataOut
    analysis: JSONValue | None = None
