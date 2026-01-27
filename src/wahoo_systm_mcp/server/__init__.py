"""Server package for Wahoo SYSTM MCP."""

from wahoo_systm_mcp.server.app import mcp
from wahoo_systm_mcp.server.lifecycle import app_lifespan
from wahoo_systm_mcp.tools.calendar import (
    get_calendar,
    remove_workout,
    reschedule_workout,
    schedule_workout,
)
from wahoo_systm_mcp.tools.library import (
    get_cycling_workouts,
    get_workout_details,
    get_workouts,
)
from wahoo_systm_mcp.tools.profile import (
    get_fitness_test_details,
    get_fitness_test_history,
    get_rider_profile,
)

__all__ = [
    "app_lifespan",
    "get_calendar",
    "get_cycling_workouts",
    "get_fitness_test_details",
    "get_fitness_test_history",
    "get_rider_profile",
    "get_workout_details",
    "get_workouts",
    "mcp",
    "remove_workout",
    "reschedule_workout",
    "schedule_workout",
]
