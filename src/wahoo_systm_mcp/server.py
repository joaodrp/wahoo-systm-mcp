"""FastMCP server with Wahoo SYSTM tools."""

import json
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.lifespan import lifespan

from wahoo_systm_mcp.client import WahooClient
from wahoo_systm_mcp.onepassword import get_credentials


@lifespan
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Initialize shared resources for the server lifetime."""
    username, password = get_credentials()
    client = WahooClient()
    await client.authenticate(username, password)
    try:
        yield {"client": client}
    finally:
        await client.close()


mcp = FastMCP("wahoo-systm", lifespan=app_lifespan)


def _get_client(ctx: Context) -> WahooClient:
    """Get the authenticated WahooClient from context."""
    client: WahooClient = ctx.lifespan_context["client"]
    return client


def _format_date(iso_date: str) -> str:
    """Format ISO date string to human-readable format."""
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y")
    except (ValueError, AttributeError):
        return iso_date


def _format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


# =============================================================================
# Calendar Tools
# =============================================================================


@mcp.tool
async def get_calendar(
    ctx: Context, start_date: str, end_date: str, time_zone: str = "UTC"
) -> list[dict[str, Any]]:
    """Get planned workouts from Wahoo SYSTM calendar for a date range.

    Returns workout name, type, duration, planned date, and basic details.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        time_zone: Timezone for the calendar (default: UTC)
    """
    client = _get_client(ctx)
    workouts = await client.get_calendar(start_date, end_date, time_zone)
    return [w.model_dump(by_alias=True) for w in workouts]


@mcp.tool
async def schedule_workout(
    ctx: Context,
    content_id: str,
    date: str,
    time_zone: str = "UTC",
) -> dict[str, Any]:
    """Schedule a workout from the library to your calendar for a specific date.

    Args:
        content_id: Workout content ID from library search results (use the id field, not workoutId)
        date: Date to schedule the workout (YYYY-MM-DD format)
        time_zone: Timezone for the workout (default: UTC). Example: Europe/Lisbon, America/New_York
    """
    client = _get_client(ctx)
    agenda_id = await client.schedule_workout(content_id, date, time_zone)
    return {
        "success": True,
        "agendaId": agenda_id,
        "date": date,
        "timezone": time_zone,
    }


@mcp.tool
async def reschedule_workout(
    ctx: Context,
    agenda_id: str,
    new_date: str,
    time_zone: str = "UTC",
) -> dict[str, Any]:
    """Move a scheduled workout to a different date.

    Args:
        agenda_id: Agenda ID from get_calendar or schedule_workout
        new_date: New date for the workout (YYYY-MM-DD format)
        time_zone: Timezone for the rescheduled workout (default: UTC)
    """
    client = _get_client(ctx)
    await client.reschedule_workout(agenda_id, new_date, time_zone)
    return {
        "success": True,
        "message": "Workout rescheduled successfully",
        "agendaId": agenda_id,
        "newDate": new_date,
        "timezone": time_zone,
    }


@mcp.tool
async def remove_workout(ctx: Context, agenda_id: str) -> dict[str, Any]:
    """Remove a scheduled workout from your calendar.

    Args:
        agenda_id: Agenda ID from get_calendar or schedule_workout
    """
    client = _get_client(ctx)
    await client.remove_workout(agenda_id)
    return {
        "success": True,
        "message": "Workout removed successfully",
        "agendaId": agenda_id,
    }


# =============================================================================
# Workout Library Tools
# =============================================================================


@mcp.tool
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
) -> dict[str, Any]:
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
    client = _get_client(ctx)

    filters: dict[str, Any] = {}
    if sport:
        filters["sport"] = sport
    if search:
        filters["search"] = search
    if min_duration is not None:
        filters["min_duration"] = min_duration
    if max_duration is not None:
        filters["max_duration"] = max_duration
    if min_tss is not None:
        filters["min_tss"] = min_tss
    if max_tss is not None:
        filters["max_tss"] = max_tss
    if channel:
        filters["channel"] = channel
    if sort_by:
        filters["sort_by"] = sort_by
    if sort_direction:
        filters["sort_direction"] = sort_direction
    if limit is not None:
        filters["limit"] = limit

    workouts = await client.get_workout_library(filters if filters else None)

    return {
        "total": len(workouts),
        "workouts": [w.model_dump(by_alias=True) for w in workouts],
    }


@mcp.tool
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
) -> dict[str, Any]:
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
    client = _get_client(ctx)

    filters: dict[str, Any] = {}
    if search:
        filters["search"] = search
    if min_duration is not None:
        filters["min_duration"] = min_duration
    if max_duration is not None:
        filters["max_duration"] = max_duration
    if min_tss is not None:
        filters["min_tss"] = min_tss
    if max_tss is not None:
        filters["max_tss"] = max_tss
    if channel:
        filters["channel"] = channel
    if category:
        filters["category"] = category
    if four_dp_focus:
        filters["four_dp_focus"] = four_dp_focus
    if intensity:
        filters["intensity"] = intensity
    if sort_by:
        filters["sort_by"] = sort_by
    if sort_direction:
        filters["sort_direction"] = sort_direction
    if limit is not None:
        filters["limit"] = limit

    workouts = await client.get_cycling_workouts(filters if filters else None)

    return {
        "total": len(workouts),
        "workouts": [w.model_dump(by_alias=True) for w in workouts],
    }


@mcp.tool
async def get_workout_details(ctx: Context, workout_id: str) -> dict[str, Any]:
    """Get detailed information about a specific workout.

    Includes intervals, power zones, equipment needed, and full workout structure.

    Args:
        workout_id: Workout ID from calendar or library (accepts both id and workoutId)
    """
    client = _get_client(ctx)
    details = await client.get_workout_details(workout_id)
    return details.model_dump(by_alias=True)


# =============================================================================
# Profile Tools
# =============================================================================


@mcp.tool
async def get_rider_profile(ctx: Context) -> dict[str, Any]:
    """Get the rider 4DP profile (NM, AC, MAP, FTP).

    Includes rider type classification, strengths/weaknesses, and heart rate zones.
    """
    client = _get_client(ctx)
    profile = await client.get_enhanced_rider_profile()

    if not profile:
        raise ToolError("No rider profile found. Complete a Full Frontal or Half Monty test first.")

    return {
        "fourDP": {
            "nm": {"watts": profile.nm, "score": profile.power_5s.graph_value},
            "ac": {"watts": profile.ac, "score": profile.power_1m.graph_value},
            "map": {"watts": profile.map_, "score": profile.power_5m.graph_value},
            "ftp": {"watts": profile.ftp, "score": profile.power_20m.graph_value},
        },
        "riderType": {
            "name": profile.rider_type.name,
            "description": profile.rider_type.description,
        },
        "strengths": {
            "name": profile.rider_weakness.strength_name,
            "description": profile.rider_weakness.strength_description,
            "summary": profile.rider_weakness.strength_summary,
        },
        "weaknesses": {
            "name": profile.rider_weakness.name,
            "description": profile.rider_weakness.weakness_description,
            "summary": profile.rider_weakness.weakness_summary,
        },
        "lthr": profile.lactate_threshold_heart_rate,
        "heartRateZones": [z.model_dump() for z in profile.heart_rate_zones],
        "lastTestDate": _format_date(profile.start_time),
    }


@mcp.tool
async def get_fitness_test_history(
    ctx: Context,
    page: int = 1,
    page_size: int = 15,
) -> dict[str, Any]:
    """Get history of completed Full Frontal and Half Monty fitness tests.

    Returns 4DP results, rider type classification, and test dates.

    Args:
        page: Page number for pagination (default: 1)
        page_size: Results per page (default: 15)
    """
    client = _get_client(ctx)
    activities, total = await client.get_fitness_test_history(page, page_size)

    formatted_tests = []
    for test in activities:
        formatted = {
            "id": test.id,
            "name": test.name,
            "date": _format_date(test.completed_date),
            "duration": _format_duration(test.duration_seconds),
            "distance": f"{test.distance_km:.2f} km",
            "tss": test.tss,
            "intensityFactor": test.intensity_factor,
        }

        if test.test_results:
            formatted["fourDP"] = {
                "nm": {
                    "watts": test.test_results.power_5s.value,
                    "score": test.test_results.power_5s.graph_value,
                },
                "ac": {
                    "watts": test.test_results.power_1m.value,
                    "score": test.test_results.power_1m.graph_value,
                },
                "map": {
                    "watts": test.test_results.power_5m.value,
                    "score": test.test_results.power_5m.graph_value,
                },
                "ftp": {
                    "watts": test.test_results.power_20m.value,
                    "score": test.test_results.power_20m.graph_value,
                },
            }
            formatted["lthr"] = test.test_results.lactate_threshold_heart_rate
            formatted["riderType"] = test.test_results.rider_type.name

        formatted_tests.append(formatted)

    return {
        "tests": formatted_tests,
        "total": total,
    }


@mcp.tool
async def get_fitness_test_details(ctx: Context, activity_id: str) -> dict[str, Any]:
    """Get detailed fitness test data.

    Includes second-by-second power/cadence/heart rate, power curve bests, and post-test analysis.

    Args:
        activity_id: Activity ID from get_fitness_test_history
    """
    client = _get_client(ctx)
    details = await client.get_fitness_test_details(activity_id)

    # Parse analysis JSON if present
    analysis_data = None
    if details.analysis:
        try:
            analysis_data = json.loads(details.analysis)
        except json.JSONDecodeError:
            analysis_data = None

    return {
        "name": details.name,
        "date": _format_date(details.completed_date),
        "duration": _format_duration(details.duration_seconds),
        "distance": f"{details.distance_km:.2f} km",
        "tss": details.tss,
        "intensityFactor": details.intensity_factor,
        "notes": details.notes,
        "fourDP": {
            "nm": {
                "watts": details.test_results.power_5s.value,
                "score": details.test_results.power_5s.graph_value,
            },
            "ac": {
                "watts": details.test_results.power_1m.value,
                "score": details.test_results.power_1m.graph_value,
            },
            "map": {
                "watts": details.test_results.power_5m.value,
                "score": details.test_results.power_5m.graph_value,
            },
            "ftp": {
                "watts": details.test_results.power_20m.value,
                "score": details.test_results.power_20m.graph_value,
            },
        },
        "lthr": details.test_results.lactate_threshold_heart_rate,
        "riderType": details.test_results.rider_type.name,
        "powerCurve": [{"duration": pb.duration, "value": pb.value} for pb in details.power_bests],
        "activityData": {
            "power": details.power,
            "cadence": details.cadence,
            "heartRate": details.heart_rate,
        },
        "analysis": analysis_data,
    }
