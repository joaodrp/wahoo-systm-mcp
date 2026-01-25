<div align="center">
  <h1>Wahoo SYSTM MCP Server</h1>
  <p>Python MCP server bridging LLMs to the Wahoo SYSTM API for training data and workout management.</p>
  <p>
    <a href="https://github.com/joaodrp/wahoo-systm-mcp/actions/workflows/ci.yml">
      <img alt="CI" src="https://github.com/joaodrp/wahoo-systm-mcp/actions/workflows/ci.yml/badge.svg">
    </a>
    <a href="https://github.com/joaodrp/wahoo-systm-mcp/releases">
      <img alt="Release" src="https://img.shields.io/github/v/release/joaodrp/wahoo-systm-mcp">
    </a>
    <a href="LICENSE">
      <img alt="License" src="https://img.shields.io/github/license/joaodrp/wahoo-systm-mcp">
    </a>
    <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
  </p>
</div>

Built with [FastMCP 3.0](https://github.com/jlowin/fastmcp) for a clean, modern implementation.

## Key Features

- **Calendar Management**: View, schedule, reschedule, and remove planned workouts
- **Workout Library**: Browse and search 1000+ workouts with advanced filtering (sport, duration, TSS, 4DP focus, intensity)
- **Workout Details**: Access complete workout structures with interval targets, equipment requirements, and key metrics
- **Rider Profile**: Retrieve current 4DP values, rider type classification, strengths/weaknesses, cTHR, and heart rate zones
- **Fitness Test History**: Access Full Frontal and Half Monty test results with complete 4DP analysis
- **AI Integration**: Returns structured JSON responses optimized for LLM consumption via MCP standard

## Compatibility

This server is designed for clients supporting the Model Context Protocol (MCP) standard:

- **Claude Desktop** - Officially supported and tested
- **Other MCP clients** - Should work with any MCP-compatible client

## Setup Instructions

### Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) package manager
- Active Wahoo SYSTM account
- (Recommended) 1Password CLI for secure credential storage

### Installation Steps

#### 1. Clone and Install

```bash
git clone https://github.com/joaodrp/wahoo-systm-mcp.git
cd wahoo-systm-mcp
uv sync
```

#### 2. Configure Claude Desktop

Update the configuration file with the absolute path to the project:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

##### Option A: 1Password Integration (Recommended)

```json
{
  "mcpServers": {
    "wahoo-systm": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/wahoo-systm-mcp", "python", "-m", "wahoo_systm_mcp"],
      "env": {
        "WAHOO_USERNAME_1P_REF": "op://Your-Vault/Your-Item/username",
        "WAHOO_PASSWORD_1P_REF": "op://Your-Vault/Your-Item/password"
      }
    }
  }
}
```

##### Option B: Plain Environment Variables

> **Warning**: This option stores your credentials in plain text in the configuration file. Use Option A (1Password) for better security.

```json
{
  "mcpServers": {
    "wahoo-systm": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/wahoo-systm-mcp", "python", "-m", "wahoo_systm_mcp"],
      "env": {
        "WAHOO_USERNAME": "your_email@example.com",
        "WAHOO_PASSWORD": "your_password"
      }
    }
  }
}
```

#### 3. 1Password Setup (if using Option A)

- Install [1Password CLI](https://1password.com/downloads/command-line)
- Enable [CLI desktop app integration](https://developer.1password.com/docs/cli/app-integration/)
- Store Wahoo SYSTM credentials in 1Password
- Find your vault/item: `op vault list` and `op item list`

#### 4. Restart Claude

Restart Claude Desktop to load the configuration.

### Environment Variables

#### Option A (1Password)

| Variable | Purpose |
|----------|---------|
| `WAHOO_USERNAME_1P_REF` | 1Password reference for Wahoo SYSTM username |
| `WAHOO_PASSWORD_1P_REF` | 1Password reference for Wahoo SYSTM password |

#### Option B (Plain Environment Variables)

| Variable | Purpose |
|----------|---------|
| `WAHOO_USERNAME` | Wahoo SYSTM email address |
| `WAHOO_PASSWORD` | Wahoo SYSTM password |

#### Optional Overrides

These are advanced escape hatches. You should not need to set them in normal use. If something breaks, please open an issue; these can be used as a temporary workaround while the server is updated.

| Variable | Purpose |
|----------|---------|
| `WAHOO_APP_VERSION` | Override the app version sent to Wahoo SYSTM (defaults to the bundled value) |
| `WAHOO_INSTALL_ID` | Optional install identifier (omitted if unset) |
| `WAHOO_LOCALE` | Override the default locale (defaults to `en`) |

The server automatically authenticates on startup and maintains the session for the duration of the process.

## Available Tools

### Calendar & Scheduling

- `get_calendar`: Retrieve planned workouts for a date range with full workout details and agenda IDs
- `schedule_workout`: Add a workout from the library to your calendar for a specific date
- `reschedule_workout`: Move a scheduled workout to a different date
- `remove_workout`: Cancel/remove a scheduled workout from your calendar

### Workout Library

> **Note**: Currently, only cycling has a specialized workout search tool (`get_cycling_workouts`) with sport-specific filters like 4DP focus and cycling categories. For other sports (Running, Strength, Yoga, Swimming), use the general `get_workouts` tool.

- `get_workouts`: Browse entire workout library with filters for sport, duration, TSS, search terms, and sorting options
- `get_cycling_workouts`: Specialized cycling workout search with 4DP focus, channel, category, and intensity filters
- `get_workout_details`: Get complete workout information including interval targets, equipment, and TSS

### Rider Profile

- `get_rider_profile`: Retrieve current 4DP values (NM, AC, MAP, FTP), rider type classification, strengths/weaknesses, cTHR, and heart rate zones

Notes:
- Heart rate zones are computed from cTHR to match the athlete profile UI.
- The response includes the last test date for context.

### Fitness Tests

- `get_fitness_test_history`: List all completed Full Frontal and Half Monty tests with 4DP results, rider type, and dates
- `get_fitness_test_details`: Access detailed test data including second-by-second power/cadence/HR, power curve bests, and analysis

## Example Usage

### Calendar Management

- "What's on my SYSTM calendar this week?"
- "Schedule Nine Hammers for Saturday"
- "Move tomorrow's workout to Thursday"
- "Remove Friday's workout from SYSTM"

### Workout Discovery

- "Find a 45-60 minute sweet spot workout"
- "What SYSTM workouts target MAP?"
- "Show me Sufferfest cycling workouts under 1 hour"
- "Find a low intensity recovery ride"

### Workout Details

- "Tell me about The Omnium workout"
- "What's the structure of Half Monty?"

### 4DP Profile & Testing

- "What's my current 4DP profile?"
- "Show my fitness test history"
- "Compare my last two Full Frontal results"

## Development

### Project Structure

```
wahoo-systm-mcp/
├── src/
│   └── wahoo_systm_mcp/
│       ├── __init__.py        # Package init
│       ├── __main__.py        # Entry point for python -m
│       ├── server.py          # FastMCP server + tool registrations
│       ├── client.py          # WahooClient (GraphQL API)
│       ├── models.py          # Pydantic models
│       └── onepassword.py     # 1Password credential retrieval
├── tests/
│   ├── conftest.py            # Shared fixtures
│   ├── test_client.py         # WahooClient tests
│   ├── test_models.py         # Pydantic model tests
│   ├── test_onepassword.py    # 1Password tests
│   └── test_server.py         # MCP tool tests
├── pyproject.toml             # Project config (PEP 621)
└── README.md                  # This file
```

### Setup Development Environment

```bash
# Install all dependencies including dev
uv sync --dev

# Run the server
uv run python -m wahoo_systm_mcp
```

### Testing

```bash
# Run all tests with coverage
uv run pytest

# Run tests without coverage
uv run pytest --no-cov

# Run specific test file
uv run pytest tests/test_client.py

# Verbose output
uv run pytest -v
```

### Linting & Type Checking

```bash
# Lint with ruff
uv run ruff check .

# Auto-fix lint issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Type check with mypy
uv run mypy src
```

## API Information

This server uses the Wahoo SYSTM GraphQL API at `https://api.thesufferfest.com/graphql`. The implementation is based on reverse-engineering the web app's API calls.

## Security Notes

- Credentials are only stored in memory during the session
- Authentication tokens are not persisted between server restarts
- 1Password integration provides the most secure credential management

## Acknowledgments

This project was inspired by [suffersync](https://github.com/bakermat/suffersync) by bakermat, which syncs Wahoo SYSTM workouts to intervals.icu.

## Contributing & License

Contributions are welcome via pull requests. Licensed under the MIT License.
