"""Workout library tools for Wahoo SYSTM MCP."""

from typing import TYPE_CHECKING, Literal, TypeAlias, cast

from fastmcp import Context, FastMCP

from wahoo_systm_mcp.models import LibraryContentOut, WorkoutDetailsOut, WorkoutsResultOut
from wahoo_systm_mcp.server.lifecycle import get_client

if TYPE_CHECKING:
    from wahoo_systm_mcp.types import FilterParams
else:
    FilterParams: TypeAlias = dict[str, object]


def _build_filters(
    **kwargs: str | int | None,
) -> FilterParams:
    """Build a filter dictionary from keyword arguments, excluding None values."""
    return cast("FilterParams", {k: v for k, v in kwargs.items() if v is not None})


async def get_workouts(
    ctx: Context,
    sport: Literal["Cycling", "Running", "Strength", "Yoga", "Swimming"] | None = None,
    search: str | None = None,
    min_duration: int | None = None,
    max_duration: int | None = None,
    min_tss: int | None = None,
    max_tss: int | None = None,
    channel: str | None = None,
    sort_by: Literal["name", "duration", "tss"] | None = None,
    sort_direction: Literal["asc", "desc"] | None = None,
    limit: int | None = 50,
) -> WorkoutsResultOut:
    """Browse the complete workout library with advanced filtering.

    Returns workout metadata including duration, TSS, intensity, and 4DP ratings.

    Args:
        sport: Filter by workout type
        search: Search workouts by name (case-insensitive partial match)
        min_duration: Minimum duration in minutes
        max_duration: Maximum duration in minutes
        min_tss: Minimum Training Stress Score
        max_tss: Maximum Training Stress Score
        channel: Filter by content channel (The Sufferfest, Inspiration, Wahoo Fitness,
                 A Week With, ProRides, On Location, NoVid, Fitness Test)
        sort_by: Sort field (default: name)
        sort_direction: Sort order (default: asc)
        limit: Maximum number of results (default: 50)
    """
    client = get_client(ctx)
    filters = _build_filters(
        sport=sport,
        search=search,
        min_duration=min_duration,
        max_duration=max_duration,
        min_tss=min_tss,
        max_tss=max_tss,
        channel=channel,
        sort_by=sort_by,
        sort_direction=sort_direction,
        limit=limit,
    )

    workouts = await client.get_workout_library(filters if filters else None)
    output = [LibraryContentOut.model_validate(w.model_dump()) for w in workouts]
    return WorkoutsResultOut(total=len(output), workouts=output)


async def get_cycling_workouts(
    ctx: Context,
    search: str | None = None,
    min_duration: int | None = None,
    max_duration: int | None = None,
    min_tss: int | None = None,
    max_tss: int | None = None,
    channel: str | None = None,
    category: str | None = None,
    four_dp_focus: Literal["NM", "AC", "MAP", "FTP"] | None = None,
    intensity: Literal["High", "Medium", "Low"] | None = None,
    sort_by: Literal["name", "duration", "tss"] | None = None,
    sort_direction: Literal["asc", "desc"] | None = None,
    limit: int | None = 50,
) -> WorkoutsResultOut:
    """Specialized cycling workout search with 4DP focus filtering.

    Automatically filters for cycling workouts only.

    Args:
        search: Search by workout name
        min_duration: Minimum duration in minutes
        max_duration: Maximum duration in minutes
        min_tss: Minimum TSS
        max_tss: Maximum TSS
        channel: Content channel (The Sufferfest, Inspiration, Wahoo Fitness,
                 A Week With, ProRides, On Location, NoVid, Fitness Test)
        category: Workout category (Endurance, Speed, Climbing, Sustained Efforts,
                  Mixed, Technique & Drills, Racing, Active Recovery, Activation,
                  The Knowledge, Overview, Cool Down, Fitness Test)
        four_dp_focus: Primary 4DP energy system (rating >= 4)
        intensity: Intensity level
        sort_by: Sort field
        sort_direction: Sort order
        limit: Maximum results (default: 50)
    """
    client = get_client(ctx)
    filters = _build_filters(
        search=search,
        min_duration=min_duration,
        max_duration=max_duration,
        min_tss=min_tss,
        max_tss=max_tss,
        channel=channel,
        category=category,
        four_dp_focus=four_dp_focus,
        intensity=intensity,
        sort_by=sort_by,
        sort_direction=sort_direction,
        limit=limit,
    )

    workouts = await client.get_cycling_workouts(filters if filters else None)
    output = [LibraryContentOut.model_validate(w.model_dump()) for w in workouts]
    return WorkoutsResultOut(total=len(output), workouts=output)


async def get_workout_details(ctx: Context, workout_id: str) -> WorkoutDetailsOut:
    """Get detailed information about a specific workout.

    Includes graph triggers, equipment needed, and full workout structure.

    Args:
        workout_id: Workout ID from calendar or library (accepts both id and workoutId)
    """
    client = get_client(ctx)
    details = await client.get_workout_details(workout_id)
    return WorkoutDetailsOut.model_validate(details.model_dump())


def register(app: FastMCP) -> None:
    """Register library tools with the FastMCP app."""
    app.tool(get_workouts)
    app.tool(get_cycling_workouts)
    app.tool(get_workout_details)
