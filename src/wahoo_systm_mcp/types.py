"""Shared typing aliases."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias, TypedDict

from pydantic.types import JsonValue as PydanticJsonValue

JSONValue: TypeAlias = PydanticJsonValue
JSONObject: TypeAlias = dict[str, JSONValue]
JSONMapping: TypeAlias = Mapping[str, JSONValue]
JSONArray: TypeAlias = list[JSONValue]
FilterValue: TypeAlias = str | int | float | bool | None


class FilterParams(TypedDict, total=False):
    """Typed filter parameters for workout library queries."""

    sport: str
    channel: str
    category: str
    intensity: str
    min_duration: int | float
    max_duration: int | float
    min_tss: int | float
    max_tss: int | float
    search: str
    sort_by: str
    sort_direction: str
    limit: int
    four_dp_focus: str
