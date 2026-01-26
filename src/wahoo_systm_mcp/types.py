"""Shared typing aliases."""

from __future__ import annotations

from typing import TypeAlias

JSONValue: TypeAlias = str | int | float | bool | None | dict[str, "JSONValue"] | list["JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]
JSONArray: TypeAlias = list[JSONValue]
FilterValue: TypeAlias = str | int | float | bool | None
