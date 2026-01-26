# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-25

### Changed

- Rewritten from TypeScript to Python using FastMCP 3.0
- Now uses `uv` for dependency management
- Pydantic v2 for data validation

### Added

- 98 unit tests with 92% coverage
- Type hints throughout with mypy strict mode
- ruff for linting and formatting

## [0.1.1] - 2024-12-11

### Fixed

- Resolve TypeScript compilation errors in imports and tests

## [0.1.0] - 2024-12-10

### Added

#### Calendar Management
- View planned workouts for any date range with `get_calendar`
- Schedule workouts from the library to your calendar with `schedule_workout`
- Reschedule existing workouts to different dates with `reschedule_workout`
- Remove workouts from your calendar with `remove_workout`

#### Workout Library
- Browse entire workout library with `get_workouts` (1000+ workouts)
- Search workouts by name, sport, duration, and TSS
- Specialized cycling workout search with `get_cycling_workouts`
- Filter by 4DP focus (NM, AC, MAP, FTP), channel, category, and intensity
- Get complete workout details including intervals and power zones with `get_workout_details`

#### Profile & Testing
- Access your 4DP profile with power values and rider type classification
- View complete fitness test history (Full Frontal and Half Monty)
- Get detailed test analysis with second-by-second data and power curves
- View heart rate zones and LTHR

#### Security
- Plain environment variable credentials supported

[1.0.0]: https://github.com/joaodrp/wahoo-systm-mcp/compare/v0.1.1...v1.0.0
[0.1.1]: https://github.com/joaodrp/wahoo-systm-mcp/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/joaodrp/wahoo-systm-mcp/releases/tag/v0.1.0
