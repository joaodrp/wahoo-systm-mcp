"""Shared typing aliases."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeAlias

JSONValue: TypeAlias = (
    str | int | float | bool | None | Mapping[str, "JSONValue"] | Sequence["JSONValue"]
)
JSONObject: TypeAlias = dict[str, JSONValue]
JSONArray: TypeAlias = list[JSONValue]
FilterValue: TypeAlias = str | int | float | bool | None
