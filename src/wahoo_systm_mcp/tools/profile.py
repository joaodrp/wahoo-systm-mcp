"""Profile and fitness test tools for Wahoo SYSTM MCP."""

import json
from datetime import datetime

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError

from wahoo_systm_mcp.client.api import _calculate_heart_rate_zones
from wahoo_systm_mcp.models import (
    ActivityDataOut,
    FitnessTestDetailsOut,
    FitnessTestHistoryOut,
    FitnessTestSummaryOut,
    FourDPProfileOut,
    FourDPValueOut,
    HeartRateZoneOut,
    PowerCurvePointOut,
    RiderProfileOut,
    RiderTypeOut,
    StrengthWeaknessOut,
)
from wahoo_systm_mcp.server.lifecycle import get_client


def _format_date(iso_date: str | None) -> str | None:
    """Format ISO date string to human-readable format.

    Returns None if the input is None or cannot be parsed as a valid ISO date.
    """
    if not iso_date:
        return None
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y")
    except (ValueError, AttributeError):
        return None


def _format_duration(seconds: int | None) -> str | None:
    """Format duration in seconds to human-readable string."""
    if seconds is None:
        return None
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


async def get_rider_profile(ctx: Context) -> RiderProfileOut:
    """Get the rider 4DP profile (NM, AC, MAP, FTP).

    Includes rider type classification, strengths/weaknesses, and heart rate zones.
    """
    client = get_client(ctx)
    enhanced = await client.get_latest_test_profile()
    current_profile = await client.get_current_profile()

    if not enhanced:
        raise ToolError("No rider profile found. Complete a Full Frontal or Half Monty test first.")

    watts_profile = current_profile or enhanced
    lthr_value = (
        current_profile.lthr if current_profile else None
    ) or enhanced.lactate_threshold_heart_rate
    heart_rate_zones = _calculate_heart_rate_zones(lthr_value) if lthr_value else []

    heart_rate_out = [HeartRateZoneOut.model_validate(z.model_dump()) for z in heart_rate_zones]
    return RiderProfileOut(
        four_dp=FourDPProfileOut(
            nm=FourDPValueOut(watts=watts_profile.nm, score=enhanced.power_5s.graph_value),
            ac=FourDPValueOut(watts=watts_profile.ac, score=enhanced.power_1m.graph_value),
            map=FourDPValueOut(watts=watts_profile.map_, score=enhanced.power_5m.graph_value),
            ftp=FourDPValueOut(watts=watts_profile.ftp, score=enhanced.power_20m.graph_value),
        ),
        rider_type=RiderTypeOut(
            name=enhanced.rider_type.name,
            description=enhanced.rider_type.description,
        ),
        strengths=StrengthWeaknessOut(
            name=enhanced.rider_weakness.strength_name,
            description=enhanced.rider_weakness.strength_description,
            summary=enhanced.rider_weakness.strength_summary,
        ),
        weaknesses=StrengthWeaknessOut(
            name=enhanced.rider_weakness.name,
            description=enhanced.rider_weakness.weakness_description,
            summary=enhanced.rider_weakness.weakness_summary,
        ),
        lthr=lthr_value,
        heart_rate_zones=heart_rate_out,
        last_test_date=_format_date(enhanced.start_time),
    )


async def get_fitness_test_history(
    ctx: Context,
    page: int = 1,
    page_size: int = 15,
) -> FitnessTestHistoryOut:
    """Get history of completed Full Frontal and Half Monty fitness tests.

    Returns 4DP results, rider type classification, and test dates.

    Args:
        page: Page number for pagination (default: 1)
        page_size: Results per page (default: 15)
    """
    client = get_client(ctx)
    activities, total = await client.get_fitness_test_history(page, page_size)

    formatted_tests: list[FitnessTestSummaryOut] = []
    for test in activities:
        formatted = FitnessTestSummaryOut(
            id=test.id,
            name=test.name,
            date=_format_date(test.completed_date),
            duration=_format_duration(test.duration_seconds),
            distance=f"{test.distance_km:.2f} km" if test.distance_km is not None else None,
            tss=test.tss,
            intensity_factor=test.intensity_factor,
        )

        if test.test_results:
            formatted.four_dp = FourDPProfileOut(
                nm=FourDPValueOut(
                    watts=test.test_results.power_5s.value,
                    score=test.test_results.power_5s.graph_value,
                ),
                ac=FourDPValueOut(
                    watts=test.test_results.power_1m.value,
                    score=test.test_results.power_1m.graph_value,
                ),
                map=FourDPValueOut(
                    watts=test.test_results.power_5m.value,
                    score=test.test_results.power_5m.graph_value,
                ),
                ftp=FourDPValueOut(
                    watts=test.test_results.power_20m.value,
                    score=test.test_results.power_20m.graph_value,
                ),
            )
            formatted.lthr = test.test_results.lactate_threshold_heart_rate
            formatted.rider_type = test.test_results.rider_type.name

        formatted_tests.append(formatted)

    return FitnessTestHistoryOut(tests=formatted_tests, total=total)


async def get_fitness_test_details(ctx: Context, activity_id: str) -> FitnessTestDetailsOut:
    """Get detailed fitness test data.

    Includes second-by-second power/cadence/heart rate, power curve bests, and post-test analysis.

    Args:
        activity_id: Activity ID from get_fitness_test_history
    """
    client = get_client(ctx)
    details = await client.get_fitness_test_details(activity_id)

    # Parse analysis JSON if present
    analysis_data = None
    if details.analysis:
        try:
            analysis_data = json.loads(details.analysis)
        except json.JSONDecodeError:
            analysis_data = None

    power_values = list(details.power) if details.power is not None else None
    cadence_values = list(details.cadence) if details.cadence is not None else None
    heart_rate_values = list(details.heart_rate) if details.heart_rate is not None else None

    four_dp = None
    if details.test_results:
        four_dp = FourDPProfileOut(
            nm=FourDPValueOut(
                watts=details.test_results.power_5s.value,
                score=details.test_results.power_5s.graph_value,
            ),
            ac=FourDPValueOut(
                watts=details.test_results.power_1m.value,
                score=details.test_results.power_1m.graph_value,
            ),
            map=FourDPValueOut(
                watts=details.test_results.power_5m.value,
                score=details.test_results.power_5m.graph_value,
            ),
            ftp=FourDPValueOut(
                watts=details.test_results.power_20m.value,
                score=details.test_results.power_20m.graph_value,
            ),
        )

    activity_data = ActivityDataOut(
        power=power_values,
        cadence=cadence_values,
        heart_rate=heart_rate_values,
    )

    power_curve = (
        [PowerCurvePointOut(duration=pb.duration, value=pb.value) for pb in details.power_bests]
        if details.power_bests
        else []
    )

    return FitnessTestDetailsOut(
        name=details.name,
        date=_format_date(details.completed_date),
        duration=_format_duration(details.duration_seconds),
        distance=f"{details.distance_km:.2f} km" if details.distance_km is not None else None,
        tss=details.tss,
        intensity_factor=details.intensity_factor,
        notes=details.notes,
        four_dp=four_dp,
        lthr=(details.test_results.lactate_threshold_heart_rate if details.test_results else None),
        rider_type=details.test_results.rider_type.name if details.test_results else None,
        power_curve=power_curve,
        activity_data=activity_data,
        analysis=analysis_data,
    )


def register(app: FastMCP) -> None:
    """Register profile tools with the FastMCP app."""
    app.tool(get_rider_profile)
    app.tool(get_fitness_test_history)
    app.tool(get_fitness_test_details)
