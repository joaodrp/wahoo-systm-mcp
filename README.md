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
    <img alt="Python" src="https://img.shields.io/badge/python-3.11--3.14-blue">
  </p>
</div>

## Key features

- **Calendar Management**: View, schedule, reschedule, and remove planned workouts
- **Workout Library**: Browse and search 1000+ workouts with advanced filtering (sport, duration, TSS, 4DP focus, intensity)
- **Workout Details**: Access complete workout structures with interval targets, equipment requirements, and key metrics
- **Rider Profile**: Retrieve current 4DP values, rider type classification, strengths/weaknesses, cTHR, and heart rate zones
- **Fitness Test History**: Access Full Frontal and Half Monty test results with complete 4DP analysis
- **AI Integration**: Returns structured JSON responses optimized for LLM consumption via MCP standard

## Compatible clients

Any Model Context Protocol (MCP) compatible client should work. See the [Model Context Protocol: Getting Started](https://modelcontextprotocol.io/docs/getting-started/intro) introduction for a general overview.

## Setup instructions

### Prerequisites

- Active [Wahoo SYSTM](https://systm.wahoofitness.com/) account

### Installation options

Choose one of the following methods based on your MCP client:

#### Option A: MCPB bundle (recommended for Claude Desktop)

No dependencies required. Download the `.mcpb` bundle from the
[Releases](https://github.com/joaodrp/wahoo-systm-mcp/releases) page,
double-click to open with Claude Desktop, and follow the prompts to enter
your credentials.

#### Option B: Direct install via uvx

Requires [uv](https://docs.astral.sh/uv/) to be installed. No local clone needed. See client-specific instructions below.

#### Option C: Local clone (for development)

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/joaodrp/wahoo-systm-mcp.git
cd wahoo-systm-mcp
uv sync
```

### Client configuration

<details>
<summary><strong>Claude Desktop</strong></summary>

Use Option A (MCPB Bundle) above for the easiest setup.

#### Manual configuration (alternative)

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "wahoo-systm": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/joaodrp/wahoo-systm-mcp.git", "wahoo-systm-mcp"],
      "env": {
        "WAHOO_USERNAME": "your_email@example.com",
        "WAHOO_PASSWORD": "your_password"
      }
    }
  }
}
```

Docs: [Claude Desktop MCP setup](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop)

</details>

<details>
<summary><strong>Claude Code</strong></summary>

Add the server with credentials:

```bash
claude mcp add wahoo-systm \
  -e WAHOO_USERNAME=your_email@example.com \
  -e WAHOO_PASSWORD=your_password \
  -- uvx --from git+https://github.com/joaodrp/wahoo-systm-mcp.git wahoo-systm-mcp
```

Verify the configuration:

```bash
claude mcp get wahoo-systm
```

Alternatively, if you installed via Claude Desktop, you can import servers:

```bash
claude mcp add-from-claude-desktop
```

Docs: [Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)

</details>

<details>
<summary><strong>ChatGPT</strong> (remote MCP only)</summary>

ChatGPT currently supports only remote MCP servers (not local). Run the HTTP
server mode and host it somewhere reachable, then add it via Settings →
Apps & Connectors → Create.

Docs: [Developer Mode + MCP connectors](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt-beta)
and [Apps & Connectors](https://help.openai.com/en/articles/11487775/)

</details>

<details>
<summary><strong>OpenCode</strong></summary>

Add an MCP server under `mcp` in your OpenCode config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "wahoo-systm": {
      "type": "local",
      "command": "uvx",
      "args": ["--from", "git+https://github.com/joaodrp/wahoo-systm-mcp.git", "wahoo-systm-mcp"],
      "env": {
        "WAHOO_USERNAME": "your_email@example.com",
        "WAHOO_PASSWORD": "your_password"
      }
    }
  }
}
```

Docs: [OpenCode MCP servers](https://opencode.ai/docs/mcp-servers/)

</details>

### HTTP server mode (optional)

If you want to run this server over HTTP (for web-based or remote MCP clients), use the
HTTP entrypoint:

```bash
uv run wahoo-systm-mcp-server
```

If you did not clone the repo, you can run it directly with `uvx`:

```bash
uvx --from git+https://github.com/joaodrp/wahoo-systm-mcp.git wahoo-systm-mcp-server
```

You can override the host/port or transport using environment variables:

```bash
HTTP_HOST=0.0.0.0 HTTP_PORT=9000 uv run wahoo-systm-mcp-server
```

### Environment variables

| Variable | Purpose |
|----------|---------|
| `WAHOO_USERNAME` | Wahoo SYSTM email address |
| `WAHOO_PASSWORD` | Wahoo SYSTM password |
| `HTTP_HOST` | HTTP bind host (HTTP mode only, default: `127.0.0.1`) |
| `HTTP_PORT` | HTTP bind port (HTTP mode only, default: `8000`) |
| `HTTP_TRANSPORT` | HTTP transport (`http`, `streamable-http`, `sse`) |

The server automatically authenticates on startup and maintains the session for the duration of the process.

## Available tools

### Calendar and scheduling

- `get_calendar`: Retrieve planned workouts for a date range with full workout details and agenda IDs
- `schedule_workout`: Add a workout from the library to your calendar for a specific date
- `reschedule_workout`: Move a scheduled workout to a different date
- `remove_workout`: Cancel/remove a scheduled workout from your calendar

### Workout library

> [!NOTE]
> Currently, only cycling has a specialized workout search tool (`get_cycling_workouts`) with sport-specific filters like 4DP focus and cycling categories. For other sports (Running, Strength, Yoga, Swimming), use the general `get_workouts` tool.

- `get_workouts`: Browse entire workout library with filters for sport, duration, TSS, search terms, and sorting options
- `get_cycling_workouts`: Specialized cycling workout search with 4DP focus, channel, category, and intensity filters
- `get_workout_details`: Get complete workout information including interval targets, equipment, and TSS

### Rider profile

- `get_rider_profile`: Retrieve current 4DP values (NM, AC, MAP, FTP), rider type classification, strengths/weaknesses, cTHR, and heart rate zones

> [!NOTE]
> Heart rate zones are computed from cTHR to match the athlete profile UI.
> The response includes the last test date for context.

### Fitness tests

- `get_fitness_test_history`: List all completed Full Frontal and Half Monty tests with 4DP results, rider type, and dates
- `get_fitness_test_details`: Access detailed test data including second-by-second power/cadence/HR, power curve bests, and analysis

## Example usage

### Calendar management

- "What's on my SYSTM calendar this week?"
- "Schedule Nine Hammers for Saturday"
- "Move tomorrow's workout to Thursday"
- "Remove Friday's workout from SYSTM"

### Workout discovery

- "Find a 45-60 minute sweet spot workout"
- "What SYSTM workouts target MAP?"
- "Show me Sufferfest cycling workouts under 1 hour"
- "Find a low intensity recovery ride"

### Workout details

- "Tell me about The Omnium workout"
- "What's the structure of Half Monty?"

### 4DP profile and testing

- "What's my current 4DP profile?"
- "Show my fitness test history"
- "Compare my last two Full Frontal results"

## Development

### Project structure

```
wahoo-systm-mcp/
├── src/
│   └── wahoo_systm_mcp/
│       ├── __init__.py
│       ├── __main__.py        # Stdio entry point
│       ├── main.py            # HTTP entry point
│       ├── models.py          # MCP tool response models
│       ├── types.py           # Shared typing aliases
│       ├── server/
│       │   ├── __init__.py
│       │   ├── app.py         # FastMCP app builder
│       │   ├── config.py      # HTTP config
│       │   ├── lifecycle.py   # Lifespan management
│       │   └── register.py    # Tool registration
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── calendar.py
│       │   ├── library.py
│       │   └── profile.py
│       └── client/
│           ├── __init__.py
│           ├── api.py         # WahooClient (GraphQL)
│           ├── config.py      # API configuration
│           ├── models.py      # API response models
│           └── queries.py     # GraphQL queries
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Shared fixtures
│   ├── test_client.py
│   ├── test_entrypoints.py    # CLI entry point tests
│   ├── test_integration.py    # Integration tests
│   ├── test_models.py
│   └── test_server.py
├── docs/
│   └── wahoo-graphql-spec.md  # API specification
├── .github/
│   └── workflows/             # CI/CD pipelines
├── .env.example               # Environment template
├── .mcpbignore                # MCPB bundle exclusions
├── justfile                   # Development commands
├── manifest.json              # MCPB bundle manifest
├── pyproject.toml
├── CHANGELOG.md
└── README.md
```

### Setup development environment

```bash
# Install all dependencies
just install

# Or manually with uv
uv sync --dev
```

Copy `.env.example` to `.env` and fill in your Wahoo SYSTM credentials for local development.

### Development commands

Run `just` to see all available commands:

```bash
just           # List all commands
just test      # Run unit tests
just test-cov  # Run tests with coverage
just lint      # Lint with ruff
just typecheck # Type check with mypy
just check     # Run all checks (lint + typecheck)
just format    # Format code
just fix       # Fix lint issues and format
just serve     # Run the MCP server
```

### Testing

```bash
# Unit tests (no credentials needed)
just test

# Unit tests with coverage
just test-cov

# Integration tests (requires .env with credentials)
just test-integration

# All tests (unit + integration)
just test-all
```

### Linting and type checking

```bash
just lint      # Lint with ruff
just typecheck # Type check with mypy
just check     # Run both
just fix       # Auto-fix issues and format
```

## API information

This server uses the Wahoo SYSTM GraphQL API at `https://api.thesufferfest.com/graphql`. The implementation is based on reverse-engineering the web app's API calls.

## Security notes

- Credentials are only stored in memory during the session
- Authentication tokens are not persisted between server restarts

## Acknowledgments

This project was inspired by [suffersync](https://github.com/bakermat/suffersync) by bakermat, which syncs Wahoo SYSTM workouts to intervals.icu.

## Contributing and license

Contributions are welcome via pull requests. Licensed under the MIT License.
