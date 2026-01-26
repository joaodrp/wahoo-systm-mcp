"""Server package for Wahoo SYSTM MCP."""

from wahoo_systm_mcp.server.app import mcp  # noqa: F401
from wahoo_systm_mcp.server.lifecycle import app_lifespan  # noqa: F401
from wahoo_systm_mcp.tools.calendar import (  # noqa: F401
    get_calendar,
    remove_workout,
    reschedule_workout,
    schedule_workout,
)
from wahoo_systm_mcp.tools.library import (  # noqa: F401
    get_cycling_workouts,
    get_workout_details,
    get_workouts,
)
from wahoo_systm_mcp.tools.profile import (  # noqa: F401
    get_fitness_test_details,
    get_fitness_test_history,
    get_rider_profile,
)

__all__ = [
    "app_lifespan",
    "mcp",
    "get_calendar",
    "schedule_workout",
    "reschedule_workout",
    "remove_workout",
    "get_workouts",
    "get_cycling_workouts",
    "get_workout_details",
    "get_rider_profile",
    "get_fitness_test_history",
    "get_fitness_test_details",
]
