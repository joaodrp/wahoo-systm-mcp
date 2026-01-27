"""Calendar tools for Wahoo SYSTM MCP."""

from fastmcp import Context, FastMCP

from wahoo_systm_mcp.models import (
    RemoveWorkoutResultOut,
    RescheduleWorkoutResultOut,
    ScheduleWorkoutResultOut,
    UserPlanItemOut,
)
from wahoo_systm_mcp.server.lifecycle import get_client


async def get_calendar(
    ctx: Context, start_date: str, end_date: str, time_zone: str = "UTC"
) -> list[UserPlanItemOut]:
    """Get planned workouts from Wahoo SYSTM calendar for a date range.

    Returns workout name, type, duration, planned date, and basic details.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        time_zone: Timezone for the calendar (default: UTC)

    """
    client = get_client(ctx)
    workouts = await client.get_calendar(start_date, end_date, time_zone)
    return [UserPlanItemOut.model_validate(w.model_dump()) for w in workouts]


async def schedule_workout(
    ctx: Context,
    content_id: str,
    date: str,
    time_zone: str = "UTC",
) -> ScheduleWorkoutResultOut:
    """Schedule a workout from the library to your calendar for a specific date.

    Args:
        content_id: Workout content ID from library search results (use the id field, not workoutId)
        date: Date to schedule the workout (YYYY-MM-DD format)
        time_zone: Timezone for the workout (default: UTC). Example: Europe/Lisbon, America/New_York

    """
    client = get_client(ctx)
    agenda_id = await client.schedule_workout(content_id, date, time_zone)
    return ScheduleWorkoutResultOut(
        success=True,
        agenda_id=agenda_id,
        date=date,
        time_zone=time_zone,
    )


async def reschedule_workout(
    ctx: Context,
    agenda_id: str,
    new_date: str,
    time_zone: str = "UTC",
) -> RescheduleWorkoutResultOut:
    """Move a scheduled workout to a different date.

    Args:
        agenda_id: Agenda ID from get_calendar or schedule_workout
        new_date: New date for the workout (YYYY-MM-DD format)
        time_zone: Timezone for the rescheduled workout (default: UTC)

    """
    client = get_client(ctx)
    await client.reschedule_workout(agenda_id, new_date, time_zone)
    return RescheduleWorkoutResultOut(
        success=True,
        message="Workout rescheduled successfully",
        agenda_id=agenda_id,
        new_date=new_date,
        time_zone=time_zone,
    )


async def remove_workout(ctx: Context, agenda_id: str) -> RemoveWorkoutResultOut:
    """Remove a scheduled workout from your calendar.

    Args:
        agenda_id: Agenda ID from get_calendar or schedule_workout

    """
    client = get_client(ctx)
    await client.remove_workout(agenda_id)
    return RemoveWorkoutResultOut(
        success=True,
        message="Workout removed successfully",
        agenda_id=agenda_id,
    )


def register(app: FastMCP) -> None:
    """Register calendar tools with the FastMCP app."""
    app.tool(get_calendar)
    app.tool(schedule_workout)
    app.tool(reschedule_workout)
    app.tool(remove_workout)
