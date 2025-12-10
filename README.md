# Wahoo SYSTM MCP Server

## Overview

The Wahoo SYSTM MCP Server is a TypeScript-based Model Context Protocol server that bridges Large Language Models to the Wahoo SYSTM API, exposing training data and workout management as callable tools.

## Key Features

- 📅 **Calendar Management**: View, schedule, reschedule, and remove planned workouts
- 📚 **Workout Library**: Browse and search 1000+ workouts with advanced filtering (sport, duration, TSS, 4DP focus, intensity)
- 📋 **Workout Details**: Access complete workout structures with intervals, power zones, and equipment requirements
- 👤 **Rider Profile**: Retrieve 4DP values, rider type classification, strengths/weaknesses, and heart rate zones
- 🧪 **Fitness Test History**: Access Full Frontal and Half Monty test results with complete 4DP analysis
- 🤖 **AI Integration**: Returns JSON responses optimized for LLM consumption via MCP standard

## Compatibility

This server is designed for clients supporting the Model Context Protocol (MCP) standard:

- ✅ **Claude Desktop** - Officially supported and tested
- 🔧 **Other MCP clients** - Should work with any MCP-compatible client
- ❓ **ChatGPT** - May be possible through third-party MCP bridge tools (untested)

While this server is only tested with Claude Desktop, the MCP protocol is open and users are welcome to experiment with other clients. If you successfully use this with another client, please share your experience!

## Setup Instructions

### Prerequisites
- Node.js v20 or later
- npm package manager
- Active Wahoo SYSTM account
- (Recommended) 1Password CLI for secure credential storage

### Installation Steps

#### 1. Clone and Build

```bash
git clone https://github.com/yourusername/wahoo-systm-mcp.git
cd wahoo-systm-mcp
npm install
npm run build
```

#### 2. Configure Claude Desktop

Update the configuration file with the absolute path to the built server:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

##### Option A: 1Password Integration (Recommended)
```json
{
  "mcpServers": {
    "wahoo-systm": {
      "command": "node",
      "args": ["/absolute/path/to/wahoo-systm-mcp/build/index.js"],
      "env": {
        "WAHOO_USERNAME_1P_REF": "op://Your-Vault/Your-Item/username",
        "WAHOO_PASSWORD_1P_REF": "op://Your-Vault/Your-Item/password"
      }
    }
  }
}
```

##### Option B: Plain Environment Variables

> [!WARNING]
> This option stores your credentials in plain text in the configuration file. Use Option A (1Password) for better security.

```json
{
  "mcpServers": {
    "wahoo-systm": {
      "command": "node",
      "args": ["/absolute/path/to/wahoo-systm-mcp/build/index.js"],
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

The server automatically authenticates on startup and maintains the session for the duration of the process.

## Available Tools

### 📅 Calendar & Scheduling
- `get_calendar`: Retrieve planned workouts for a date range with full workout details and agenda IDs
- `schedule_workout`: Add a workout from the library to your calendar for a specific date
- `reschedule_workout`: Move a scheduled workout to a different date
- `remove_workout`: Cancel/remove a scheduled workout from your calendar

### 📚 Workout Library

> [!NOTE]
> Currently, only cycling has a specialized workout search tool (`get_cycling_workouts`) with sport-specific filters like 4DP focus and cycling categories. For other sports (Running, Strength, Yoga, Swimming), use the general `get_workouts` tool. Specialized commands for other sports may be added in future releases.

- `get_workouts`: Browse entire workout library with filters for sport, duration, TSS, search terms, and sorting options
- `get_cycling_workouts`: Specialized cycling workout search with 4DP focus, channel, category, and intensity filters
- `get_workout_details`: Get complete workout information including intervals, power zones, equipment, and TSS

### 👤 Rider Profile
- `get_rider_profile`: Retrieve 4DP values (NM, AC, MAP, FTP), rider type classification, strengths/weaknesses, LTHR, and heart rate zones

### 🧪 Fitness Tests
- `get_fitness_test_history`: List all completed Full Frontal and Half Monty tests with 4DP results, rider type, and dates
- `get_fitness_test_details`: Access detailed test data including second-by-second power/cadence/HR, power curve bests, and analysis

## Example Usage

### Calendar Management

- "What's on my SYSTM calendar this week?"
- "Schedule Nine Hammers for Saturday"
- "Move tomorrow's workout to Thursday"
- "Remove Friday's workout from SYSTM"
- "Clear my SYSTM calendar for next week"

### Workout Discovery

- "Find a 45-60 minute sweet spot workout"
- "What SYSTM workouts target MAP?"
- "Show me Sufferfest cycling workouts under 1 hour"
- "Find a low intensity recovery ride"
- "What NoVid workouts are available?"
- "Search for workouts with 'Hammer' in the name"
- "List high intensity workouts between 30-45 minutes"
- "What workouts focus on FTP development?"

### Workout Details

- "Tell me about The Omnium workout"
- "What's the structure of Half Monty?"
- "How long is Full Frontal and what does it test?"

### 4DP Profile & Testing

- "What's my current 4DP profile?"
- "Show my fitness test history"
- "Compare my last two Full Frontal results"
- "When was my last Half Monty?"
- "How has my FTP progressed over time?"

### Planning & Recommendations

- "Suggest a SYSTM workout for an easy day"
- "What's a good opener workout before a race?"
- "Find a workout similar to Tempo with Surges"
- "I have 90 minutes - what SYSTM ride should I do?"

## Tool Parameters and Returns

### Calendar & Scheduling Tools

#### `get_calendar`

- **Parameters:**
  - `start_date` (required):
    - Type: `string`
    - Description: Start date for calendar range
    - Format: YYYY-MM-DD
  - `end_date` (required):
    - Type: `string`
    - Description: End date for calendar range
    - Format: YYYY-MM-DD

- **Output:** JSON array of workout objects with:
  - `date`: Scheduled date
  - `agendaId`: Unique identifier for scheduled workout
  - `workoutId`: Workout identifier
  - `name`: Workout name
  - `type`: Sport type (Cycling, Running, Strength, Yoga, Swimming)
  - `duration`: Duration in seconds
  - `description`: Workout description
  - `completed`: Completion status
  - `plan`: Associated training plan information (if applicable)

#### `schedule_workout`

- **Parameters:**
  - `content_id` (required):
    - Type: `string`
    - Description: The workout content ID from library search results (use the `id` field, not `workoutId`)
  - `date` (required):
    - Type: `string`
    - Description: Target date for scheduling
    - Format: YYYY-MM-DD
  - `time_zone` (optional):
    - Type: `string`
    - Description: Timezone for the scheduled workout
    - Default: UTC
    - Example: "Europe/Lisbon", "America/New_York"

- **Output:** Object with:
  - `success`: Boolean indicating success
  - `agendaId`: Generated agenda ID for future operations
  - `date`: Scheduled date with timezone

#### `reschedule_workout`

- **Parameters:**
  - `agenda_id` (required):
    - Type: `string`
    - Description: The unique agenda identifier from `get_calendar` or `schedule_workout`
  - `new_date` (required):
    - Type: `string`
    - Description: New target date
    - Format: YYYY-MM-DD
  - `time_zone` (optional):
    - Type: `string`
    - Description: Timezone for the rescheduled workout
    - Default: UTC

- **Output:** Object with:
  - `success`: Boolean indicating success
  - `agendaId`: Agenda ID of rescheduled workout
  - `newDate`: New scheduled date with timezone
  - `message`: Confirmation message

#### `remove_workout`

- **Parameters:**
  - `agenda_id` (required):
    - Type: `string`
    - Description: The unique agenda identifier from `get_calendar` or `schedule_workout`

- **Output:** Object with:
  - `success`: Boolean indicating success
  - `agendaId`: Agenda ID of removed workout
  - `message`: Confirmation message

### Workout Library Tools

#### `get_workouts`

- **Parameters:**
  - `sport` (optional):
    - Type: `string`
    - Description: Filter by workout type
    - Options: "Cycling", "Running", "Strength", "Yoga", "Swimming"
  - `search` (optional):
    - Type: `string`
    - Description: Search workouts by name (case-insensitive partial match)
  - `min_duration` (optional):
    - Type: `number`
    - Description: Minimum duration filter in minutes
  - `max_duration` (optional):
    - Type: `number`
    - Description: Maximum duration filter in minutes
  - `min_tss` (optional):
    - Type: `number`
    - Description: Minimum Training Stress Score
  - `max_tss` (optional):
    - Type: `number`
    - Description: Maximum Training Stress Score
  - `sort_by` (optional):
    - Type: `string`
    - Description: Sort field
    - Options: "name", "duration", "tss"
    - Default: "name"
  - `sort_direction` (optional):
    - Type: `string`
    - Description: Sort order
    - Options: "asc", "desc"
    - Default: "asc"
  - `limit` (optional):
    - Type: `number`
    - Description: Maximum number of results
    - Default: 50

- **Output:** Object with:
  - `total`: Total workout count
  - `workouts`: JSON array of workout objects with:
    - `id`: Content ID (for scheduling)
    - `workoutId`: Workout identifier
    - `name`: Workout name
    - `sport`: Sport type
    - `channel`: Content channel/series
    - `level`: Difficulty level
    - `category`: Workout category
    - `duration`: Duration in seconds
    - `durationFormatted`: Human-readable duration
    - `description`: Workout description
    - `tss`: Training Stress Score
    - `intensityFactor`: Intensity Factor
    - `fourDP`: 4DP ratings (NM, AC, MAP, FTP)
    - `tags`: Array of tags

#### `get_cycling_workouts`

- **Parameters:** All `get_workouts` parameters plus:
  - `channel` (optional):
    - Type: `string`
    - Description: Filter by content channel
    - Options: "The Sufferfest", "Inspiration", "Wahoo Fitness", "A Week With", "ProRides", "On Location", "NoVid", "Fitness Test"
  - `category` (optional):
    - Type: `string`
    - Description: Filter by workout category
    - Options: "Endurance", "Speed", "Climbing", "Sustained Efforts", "Mixed", "Technique & Drills", "Racing", "Active Recovery", "Activation", "The Knowledge", "Overview", "Cool Down", "Fitness Test"
  - `four_dp_focus` (optional):
    - Type: `string`
    - Description: Filter by primary 4DP energy system (rating >= 4)
    - Options: "NM" (Neuromuscular), "AC" (Anaerobic Capacity), "MAP" (Maximal Aerobic Power), "FTP" (Functional Threshold Power)
  - `intensity` (optional):
    - Type: `string`
    - Description: Filter by intensity level
    - Options: "High", "Medium", "Low"

- **Output:** Same as `get_workouts`.

#### `get_workout_details`

- **Parameters:**
  - `workout_id` (required):
    - Type: `string`
    - Description: Workout identifier from calendar or library (accepts both `id` and `workoutId`)

- **Output:** Object with:
  - `name`: Workout name
  - `sport`: Sport type
  - `duration`: Duration in seconds
  - `durationFormatted`: Human-readable duration
  - `level`: Difficulty level
  - `description`: Full workout description
  - `equipment`: Required equipment list
  - `tss`: Training Stress Score
  - `intensityFactor`: Intensity Factor
  - `fourDP`: 4DP ratings (NM, AC, MAP, FTP)
  - `intervals`: Complete interval structure with power zones and cadence targets

### Rider Profile Tools

#### `get_rider_profile`

- **Parameters:** None

- **Output:** Object with:
  - `fourDP`: 4DP power values with scores
    - `nm`: Neuromuscular power (watts) and score
    - `ac`: Anaerobic Capacity (watts) and score
    - `map`: Maximal Aerobic Power (watts) and score
    - `ftp`: Functional Threshold Power (watts) and score
  - `riderType`: Classification (Sprinter, Pursuiter, Time Trialist, Climber, All-Rounder, Attacker, Rouleur)
  - `riderTypeDescription`: Detailed rider type description
  - `strengths`: Identified strengths
  - `weaknesses`: Identified weaknesses
  - `lthr`: Lactate Threshold Heart Rate
  - `heartRateZones`: 5 heart rate training zones
  - `lastTestDate`: Date of last fitness test
  - `lastTestType`: Type of last fitness test

### Fitness Test Tools

#### `get_fitness_test_history`

- **Parameters:**
  - `page` (optional):
    - Type: `number`
    - Description: Page number for pagination
    - Default: 1
  - `page_size` (optional):
    - Type: `number`
    - Description: Number of results per page
    - Default: 15

- **Output:** Object with:
  - `total`: Total test count
  - `tests`: JSON array of fitness test objects (sorted by date, most recent first) with:
    - `activityId`: Test activity identifier
    - `name`: Test name (Full Frontal or Half Monty)
    - `date`: Completion date
    - `duration`: Duration in seconds
    - `distance`: Distance covered
    - `tss`: Training Stress Score
    - `intensityFactor`: Intensity Factor
    - `fourDPResults`: Complete 4DP results
      - `nm`: Neuromuscular power (watts, score, status)
      - `ac`: Anaerobic Capacity (watts, score, status)
      - `map`: Maximal Aerobic Power (watts, score, status)
      - `ftp`: Functional Threshold Power (watts, score, status)
    - `lthr`: Lactate Threshold Heart Rate
    - `riderType`: Rider type classification
    - `riderTypeDescription`: Rider type description

#### `get_fitness_test_details`

- **Parameters:**
  - `activity_id` (required):
    - Type: `string`
    - Description: Activity identifier from `get_fitness_test_history`

- **Output:** Object with:
  - `name`: Test name
  - `date`: Completion date
  - `duration`: Duration in seconds
  - `distance`: Distance covered
  - `tss`: Training Stress Score
  - `intensityFactor`: Intensity Factor
  - `notes`: Test notes
  - `fourDPResults`: Complete 4DP results with rider type analysis
  - `profileValues`: Profile values used during test
  - `activityData`: Second-by-second data arrays
    - `power`: Power data array
    - `cadence`: Cadence data array
    - `heartRate`: Heart rate data array
  - `powerCurve`: Power curve bests across all durations
  - `analysis`: Post-test analysis with recommendations

## Known Limitations

### Workout Name Inconsistencies

The Wahoo SYSTM API returns different workout names depending on the endpoint. Library endpoints may include challenge prefixes or event suffixes, while the details endpoint returns canonical names (sometimes with "On Location -" prefix).

**Always use workout IDs for matching and lookups, not names.** Both `id` (content ID) and `workoutId` fields work with `get_workout_details`.

## Development

### Project Structure
```
wahoo-systm-mcp/
├── src/
│   ├── index.ts           # MCP server implementation
│   ├── client.ts          # Wahoo SYSTM API client
│   ├── types.ts           # TypeScript type definitions
│   ├── schemas.ts         # Zod validation schemas
│   ├── onepassword.ts     # 1Password integration
│   └── test/              # Test suite (Vitest)
├── build/                 # Compiled JavaScript (generated)
├── package.json           # Project dependencies and scripts
├── tsconfig.json          # TypeScript configuration
├── vitest.config.ts       # Vitest test configuration
├── eslint.config.mjs      # ESLint configuration
├── .prettierrc            # Prettier configuration
├── .env.example           # Example environment variables
├── .gitignore             # Git ignore patterns
└── README.md              # Project documentation
```

### Building & Development

```bash
# Build the project
npm run build

# Watch mode (auto-rebuild on changes)
npm run watch
```

### Testing

Create a `.env` file with your credentials for testing:
```bash
cp .env.example .env
# Edit .env with your 1Password references or plain credentials
```

Then run the tests:

```bash
# Run all tests
npm test

# Watch mode (re-runs on file changes)
npm run test:watch

# Coverage report
npm run test:coverage

# Interactive UI
npm run test:ui
```

### Linting & Formatting

```bash
# Check for linting errors
npm run lint

# Fix linting errors automatically
npm run lint:fix

# Format code with Prettier
npm run format

# Check formatting (without writing)
npm run format:check
```

## API Information

This server uses the Wahoo SYSTM GraphQL API at `https://api.thesufferfest.com/graphql`. The implementation is based on reverse-engineering the web app's API calls.

## Security Notes

- Credentials are only stored in memory during the session
- The `.env` file is gitignored to prevent accidental commits
- Authentication tokens are not persisted between server restarts
- 1Password integration provides the most secure credential management

## Acknowledgments

This project was inspired by [suffersync](https://github.com/bakermat/suffersync) by bakermat, which syncs Wahoo SYSTM workouts to intervals.icu.

## Contributing & License

Contributions are welcome via pull requests. Licensed under the MIT License.
