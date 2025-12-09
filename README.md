# Wahoo SYSTM MCP Server

A Model Context Protocol (MCP) server that provides access to Wahoo SYSTM calendar and workout data. This allows Claude and other MCP clients to interact with your Wahoo SYSTM training plan, retrieve planned workouts, and get detailed workout information including intervals and power zones.

## Features

- **Authentication**: Securely authenticate with your Wahoo SYSTM account
- **Calendar Access**: Retrieve planned workouts for any date range
- **Workout Scheduling**: Schedule workouts from the library to your calendar
- **Library Browsing**: Browse and search the complete Wahoo SYSTM workout library with filters for sport, level, duration, and channel
- **Workout Details**: Get comprehensive workout information including:
  - Workout intervals and structure
  - Power zones (FTP, MAP, AC, NM)
  - Duration and intensity
  - Equipment requirements
  - TSS (Training Stress Score) and IF (Intensity Factor)
- **Rider Profile**: Access your 4DP profile values
- **Fitness Test History**: View all completed Full Frontal and Half Monty tests with 4DP results
- **Fitness Test Details**: Get second-by-second data and complete analysis for any fitness test

## Installation

```bash
npm install
npm run build
```

## Configuration

### Option 1: 1Password Integration (Recommended)

Store your credentials securely in 1Password and reference them via the `op` CLI.

1. **Install 1Password CLI** if you haven't already: https://1password.com/downloads/command-line

2. **Store your Wahoo SYSTM credentials in 1Password**

3. **Configure Claude Desktop** with 1Password secret references:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "wahoo-systm": {
      "command": "node",
      "args": ["/absolute/path/to/wahoo-systm-mcp/build/index.js"],
      "env": {
        "WAHOO_USERNAME_1P_REF": "op://Your-Vault/Your-Item-Name/username",
        "WAHOO_PASSWORD_1P_REF": "op://Your-Vault/Your-Item-Name/password"
      }
    }
  }
}
```

Replace the references with your actual 1Password item references. Format is: `op://vault/item/field`

To find your vault and item names, use:
```bash
op vault list
op item list
```

**Important**: Make sure you have enabled 1Password CLI desktop app integration. See the [1Password CLI documentation](https://developer.1password.com/docs/cli/app-integration/) for setup instructions.

The server will automatically authenticate on startup using these credentials.

### Option 2: Environment Variables (Plain Text)

**Warning**: This stores credentials in plain text. Only use this if you don't have 1Password.

Configure Claude Desktop with plain environment variables:

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

The server will automatically authenticate on startup using these credentials.

## Usage

### Adding to Claude Desktop

See configuration options above for the full setup.

### Available Tools

#### 1. `get_calendar`

Get planned workouts from your calendar for a date range.

**Parameters:**
- `start_date` (string): Start date in YYYY-MM-DD format
- `end_date` (string): End date in YYYY-MM-DD format

**Example:**
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
```

**Returns:**
- Total workout count
- List of workouts with:
  - Date
  - Workout ID (for use with `get_workout_details`)
  - Name
  - Type (Cycling, Running, Strength, Yoga, Swimming)
  - Duration in hours
  - Description
  - Intensity ratings
  - Status
  - Plan information

#### 2. `get_workouts`

Get workouts from the Wahoo SYSTM library with filtering and sorting.

**Parameters:**
- `sport` (string, optional): Filter by sport (e.g., "Cycling", "Running", "Strength", "Yoga", "Swimming")
- `min_duration` (number, optional): Minimum duration in minutes (e.g., 30 for 30 minutes)
- `max_duration` (number, optional): Maximum duration in minutes (e.g., 120 for 2 hours)
- `min_tss` (number, optional): Minimum Training Stress Score (e.g., 20 for easy, 100+ for hard)
- `max_tss` (number, optional): Maximum Training Stress Score
- `sort_by` (string, optional): Sort by "name", "duration", or "tss" (default: "name")
- `sort_direction` (string, optional): Sort direction "asc" or "desc" (default: "asc")
- `limit` (number, optional): Maximum number of results to return (default: 50)

**Example:**
```json
{
  "sport": "Cycling",
  "max_duration": 60,
  "min_tss": 30,
  "max_tss": 60,
  "sort_by": "tss",
  "sort_direction": "asc",
  "limit": 10
}
```

**Returns:**
- Total workout count
- List of workouts with:
  - Workout ID (for use with `get_workout_details`)
  - Name
  - Sport/workout type
  - Channel/series
  - Level/intensity
  - Category
  - Duration (seconds and formatted)
  - Description excerpt
  - TSS and Intensity Factor
  - 4DP ratings (NM, AC, MAP, FTP)
  - Tags

#### 3. `get_cycling_workouts`

Get cycling workouts with filters matching the SYSTM UI. Specialized tool for browsing cycling workouts with cycling-specific filters.

**Parameters:**
- `channel` (string, optional): Filter by channel (e.g., "The Sufferfest", "Inspiration", "Wahoo Fitness", "A Week With", "ProRides", "On Location", "NoVid", "Fitness Test")
- `category` (string, optional): Filter by category (e.g., "Endurance", "Speed", "Climbing", "Sustained Efforts", "Mixed", "Technique & Drills", "Racing", "Active Recovery", "Activation", "The Knowledge", "Overview", "Cool Down", "Fitness Test")
- `four_dp_focus` (string, optional): Filter by 4DP focus - shows workouts with rating >= 4 in the specified energy system: "NM" (Neuromuscular), "AC" (Anaerobic Capacity), "MAP" (Maximal Aerobic Power), "FTP" (Functional Threshold Power)
- `min_duration` (number, optional): Minimum duration in minutes (e.g., 30 for 30 minutes)
- `max_duration` (number, optional): Maximum duration in minutes (e.g., 90 for 90 minutes)
- `min_tss` (number, optional): Minimum Training Stress Score
- `max_tss` (number, optional): Maximum Training Stress Score
- `intensity` (string, optional): Filter by intensity level: "High", "Medium", or "Low"
- `sort_by` (string, optional): Sort by "name", "duration", or "tss" (default: "name")
- `sort_direction` (string, optional): Sort direction "asc" or "desc" (default: "asc")
- `limit` (number, optional): Maximum number of results to return (default: 50)

**Example:**
```json
{
  "four_dp_focus": "FTP",
  "max_duration": 60,
  "min_tss": 40,
  "max_tss": 60,
  "intensity": "High",
  "sort_by": "tss",
  "sort_direction": "asc",
  "limit": 10
}
```

**Returns:**
Same structure as `get_workouts` - total workout count and list of workouts with all metadata including 4DP ratings, TSS, duration, description, etc.

#### 4. `get_workout_details`

Get comprehensive details about a specific workout.

**Parameters:**
- `workout_id` (string): The workout ID from `get_calendar` or `get_workouts`

**Example:**
```json
{
  "workout_id": "workout-id-here"
}
```

**Returns:**
- Workout name and sport
- Duration (seconds and formatted)
- Level/difficulty
- Full description
- Equipment needed
- Metrics (TSS, Intensity Factor, 4DP ratings)
- Complete interval structure with power zones

#### 5. `get_rider_profile`

Get your complete 4DP profile, rider type, strengths/weaknesses, and heart rate zones.

**Parameters:** None

**Returns:**
- **4DP Power Values** (with scores):
  - NM (Neuromuscular Power - 5s max)
  - AC (Anaerobic Capacity - 1m max)
  - MAP (Maximal Aerobic Power - 5m max)
  - FTP (Functional Threshold Power - 20m)
- **Rider Type**: Classification (Sprinter, Pursuiter, Time Trialist, Climber, All-Rounder, Attacker, Rouleur) with description
- **Strengths**: What you excel at
- **Weaknesses**: What needs improvement
- **LTHR**: Lactate Threshold Heart Rate
- **Heart Rate Zones**: 5 training zones calculated from LTHR
- **Test Info**: Last fitness test date and type

#### 6. `schedule_workout`

Schedule a workout for a specific date on your calendar.

**Parameters:**
- `content_id` (string): The workout content ID from `get_workouts` or `get_cycling_workouts`
- `date` (string): Date in YYYY-MM-DD format (e.g., "2025-12-15")
- `time_zone` (string, optional): Timezone (e.g., "Europe/Lisbon", "America/New_York"). Defaults to UTC if not specified.

**Example:**
```json
{
  "content_id": "idi8fUK8Ew",
  "date": "2025-12-15",
  "time_zone": "Europe/Lisbon"
}
```

**Returns:**
- Success status
- Agenda ID (unique identifier for the scheduled workout)
- Scheduled date and timezone

**Note:** The `content_id` is the `id` field from workout results, not the `workoutId`.

#### 7. `reschedule_workout`

Reschedule an existing workout to a different date.

**Parameters:**
- `agenda_id` (string): The agenda ID of the scheduled workout (from `schedule_workout` or `get_calendar`)
- `new_date` (string): New date to reschedule the workout to in YYYY-MM-DD format (e.g., "2025-12-16")
- `time_zone` (string, optional): Timezone (e.g., "Europe/Lisbon", "America/New_York"). Defaults to UTC if not specified.

**Example:**
```json
{
  "agenda_id": "1LLFcfoVUb_0",
  "new_date": "2025-12-16",
  "time_zone": "Europe/Lisbon"
}
```

**Returns:**
- Success status
- Agenda ID
- New date and timezone
- Confirmation message

#### 8. `remove_workout`

Remove/cancel a scheduled workout from your calendar.

**Parameters:**
- `agenda_id` (string): The agenda ID of the scheduled workout to remove (from `schedule_workout` or `get_calendar`)

**Example:**
```json
{
  "agenda_id": "91xKHVU1lA_0"
}
```

**Returns:**
- Success status
- Agenda ID
- Confirmation message

#### 9. `get_fitness_test_history`

Get your fitness test history from Wahoo SYSTM. Returns all completed Full Frontal and Half Monty tests with 4DP values, LTHR, rider type, TSS, and test dates. Results are sorted by date (most recent first).

**Parameters:**
- `page` (number, optional): Page number for pagination (default: 1)
- `page_size` (number, optional): Number of results per page (default: 15)

**Example:**
```json
{
  "page": 1,
  "page_size": 10
}
```

**Returns:**
- Total test count
- List of fitness tests with:
  - Test ID (for use with `get_fitness_test_details`)
  - Name (Full Frontal or Half Monty)
  - Completion date
  - Duration
  - Distance
  - TSS and Intensity Factor
  - **4DP Test Results**:
    - NM (5s power): value (W), score, status
    - AC (1m power): value (W), score, status
    - MAP (5m power): value (W), score, status
    - FTP (20m power): value (W), score, status
  - Lactate Threshold Heart Rate (LTHR)
  - Rider Type (with name, icon, description)

#### 10. `get_fitness_test_details`

Get detailed information about a specific fitness test activity. Returns second-by-second power, cadence, and heart rate data, power curve bests, test notes, profile used during test, and complete 4DP results with rider type analysis.

**Parameters:**
- `activity_id` (string): The activity ID of the fitness test (obtained from `get_fitness_test_history`)

**Example:**
```json
{
  "activity_id": "abc123xyz"
}
```

**Returns:**
- Test name and completion date
- Duration, distance, TSS, Intensity Factor
- Test notes/commentary
- **Complete 4DP Test Results**:
  - NM, AC, MAP, FTP with values, scores, and status
  - LTHR (Lactate Threshold Heart Rate)
  - Rider Type classification with description
- **Profile Used During Test**:
  - FTP, MAP, AC, NM values used
- **Activity Data** (second-by-second arrays):
  - Power data
  - Cadence data
  - Heart rate data
- **Power Curve Bests**: Top efforts across various durations (5s, 1m, 5m, 20m, etc.)
- Post-test analysis and recommendations

## Example Conversations with Claude

### Checking Your Calendar

**You:**
```
What workouts do I have planned for this week?
```

**Claude:** *[calls get_calendar - automatically authenticated]*
```
Let me check your calendar for this week. You have the following workouts planned:

December 9, 2025:
- ALL Access EF 1: Tempo Blocks (Cycling, 1h 9m)
  Description: Saddle up for the high-energy atmosphere of the EF men's & women's
  team training camp! Warm up with Jonathan Vaughters setting expectations and
  emphasizing the purpose of the camp: growth, improvement...
```

**You:**
```
Tell me more about that EF tempo workout
```

**Claude:** *[calls get_workout_details]*
```
ALL Access EF 1: Tempo Blocks is a 1h 9m cycling workout with:

Training Stress Score: 50
Intensity Factor: 0.66

Saddle up for the high-energy atmosphere of the EF men's & women's team training
camp! This tempo session is designed to give your body a decent aerobic workload.

[Full interval structure details]
```

### Finding Workouts in the Library

**You:**
```
Show me some easy cycling workouts under 60 minutes with TSS between 30 and 50, sorted by difficulty
```

**Claude:** *[calls get_workouts]*
```
I found 82 cycling workouts under 60 minutes with TSS 30-50. Here are the first 10 (easiest first):

1. Cadence Drills (Builds/Holds/Single Leg) (55m)
   TSS: 30
   This workout combines several technique driven intervals to improve your overall form

2. Kayabike (45m)
   TSS: 30
   Film (2016): The life of a group of kids and their BMX coach training in a South African township

3. Primers (44m)
   TSS: 42
   Whether you have a 4DP fitness test coming up or a group ride you want to smash

[...and 79 more workouts]
```

**You:**
```
Tell me more about Primers
```

**Claude:** *[calls get_workout_details using workout_id from browse results]*
```
Primers is a 44-minute cycling workout with:

Training Stress Score: 42
Intensity Factor: 0.76

Whether you have a 4DP® fitness test coming up, a group ride you want to smash,
that event you have been training all winter for, or even just a fun route you
want to have a great ride on, this is the workout for you...

[Full interval structure details]
```

### Finding Specific Cycling Workouts

**You:**
```
Show me high-intensity cycling workouts under 60 minutes that focus on FTP with TSS between 40 and 60
```

**Claude:** *[calls get_cycling_workouts]*
```
I found 11 FTP-focused cycling workouts matching your criteria. Here are the first 5 (sorted by TSS):

1. Micro Intervals: 3 Sets 8/6/4 x 40/20s (38m)
   TSS: 42, Intensity: High
   4DP: FTP=4, MAP=4, AC=3, NM=1
   Category: Climbing

2. FTP and MAP Over-Unders 10/8 (31m)
   TSS: 43, Intensity: High
   4DP: FTP=5, MAP=2, AC=1, NM=1
   Category: Climbing

3. Micro Intervals: Equal Work Rest 10/20/30/20/10 (42m)
   TSS: 46, Intensity: High
   4DP: FTP=4, MAP=3, AC=2, NM=1
   Category: Mixed

4. French Pyrenees: Les Baronnies (42m)
   TSS: 48, Intensity: High
   4DP: FTP=5, MAP=3, AC=2, NM=1
   Category: Mixed

5. Giro d'Italia 1 (35m)
   TSS: 48, Intensity: High
   4DP: FTP=5, MAP=4, AC=2, NM=1
   Category: Racing

[...and 6 more workouts]
```

**You:**
```
Tell me more about that Micro Intervals workout
```

**Claude:** *[calls get_workout_details]*
```
Micro Intervals: 3 Sets 8/6/4 x 40/20s is a 38-minute cycling workout with:

Training Stress Score: 42
Intensity Factor: 0.81
4DP Focus: FTP=4, MAP=4 (builds both threshold and VO2 max)

This session delivers 40/20s micro intervals to build your MAP without completely
emptying your tank. Perfect for building sustainable power at threshold.

[Full interval structure details]
```

### Scheduling a Workout

**You:**
```
Find me a short FTP workout under 45 minutes and schedule it for next Monday
```

**Claude:** *[calls get_cycling_workouts]*
```
I found several FTP-focused workouts under 45 minutes. Here's a good one:

FTP and MAP Over-Unders 10/8 (31m)
TSS: 43, Intensity: High
4DP: FTP=5, MAP=2
Category: Climbing

This workout delivers classic over-under intervals to boost both FTP and MAP.
```

**Claude:** *[calls schedule_workout with content_id, date: "2025-12-16"]*
```
✓ Workout successfully scheduled!

The workout "FTP and MAP Over-Unders 10/8" has been added to your calendar for
Monday, December 16, 2025. You can view it in your SYSTM calendar.
```

### Rescheduling a Workout

**You:**
```
I need to move Monday's workout to Tuesday instead
```

**Claude:** *[calls get_calendar to find Monday's workout]*
```
I see you have "FTP and MAP Over-Unders 10/8" scheduled for Monday, December 16.
Let me reschedule it to Tuesday, December 17.
```

**Claude:** *[calls reschedule_workout with agenda_id, new_date: "2025-12-17"]*
```
✓ Workout successfully rescheduled!

"FTP and MAP Over-Unders 10/8" has been moved from Monday, December 16 to
Tuesday, December 17, 2025.
```

### Removing a Workout

**You:**
```
Actually, I need to cancel Tuesday's workout
```

**Claude:** *[calls get_calendar to find Tuesday's workout]*
```
I see you have "FTP and MAP Over-Unders 10/8" scheduled for Tuesday, December 17.
Let me remove it from your calendar.
```

**Claude:** *[calls remove_workout with agenda_id]*
```
✓ Workout successfully removed!

"FTP and MAP Over-Unders 10/8" has been removed from your calendar.
```

### Viewing Your Profile

**You:**
```
What are my 4DP values?
```

**Claude:** *[calls get_rider_profile]*
```
Your 4DP Profile:
  NM (Neuromuscular): 1350W (Score: 1.15)
  AC (Anaerobic): 612W (Score: 0.92)
  MAP (Max Aerobic): 495W (Score: 0.88)
  FTP (Threshold): 419W (Score: 0.85)

Rider Type: All-Rounder
  "You're the complete package - powerful on the climbs, dangerous in the sprint,
  and relentless in the time trial. Like a certain Slovenian superstar, you can
  do it all. Just don't forget to let others win occasionally!"

Strengths: Sustained Power
  Your ability to maintain high power over long periods is exceptional!

Weaknesses: Sprint Efforts
  While your sprint is good, focusing on explosive efforts could make you even more dangerous.

LTHR: 178 bpm

Heart Rate Zones:
  Zone 1 (Active Recovery): 0-121 bpm
  Zone 2 (Endurance): 122-148 bpm
  Zone 3 (Tempo): 149-167 bpm
  Zone 4 (Threshold): 168-187 bpm
  Zone 5 (VO2 Max): 188+ bpm

Last Test: Full Frontal on October 28, 2025

(These might be Tadej Pogačar's numbers... but we can all dream of yellow jerseys! 🚴‍♂️)
```

### Viewing Your Fitness Test History

**You:**
```
Show me my fitness test history
```

**Claude:** *[calls get_fitness_test_history]*
```
You have completed 1 fitness test:

Full Frontal (October 28, 2025)
  Duration: 1h 10m
  TSS: 95

  4DP Results:
    NM (5s): 1350W (Score: 1.15) [Good]
    AC (1m): 612W (Score: 0.92) [Excellent]
    MAP (5m): 495W (Score: 0.88) [Excellent]
    FTP (20m): 419W (Score: 0.85) [Excellent]

  LTHR: 178 bpm
  Rider Type: All-Rounder
    "You're the complete package - powerful on the climbs, dangerous in the sprint,
    and relentless in the time trial."
```

**You:**
```
Give me the detailed analysis of that Full Frontal test
```

**Claude:** *[calls get_fitness_test_details with activity_id]*
```
Full Frontal - October 28, 2025

Test Duration: 1h 10m
TSS: 95, Intensity Factor: 0.82

4DP Test Results:
  NM (5s): 1350W (Score: 1.15) [Good]
  AC (1m): 612W (Score: 0.92) [Excellent]
  MAP (5m): 495W (Score: 0.88) [Excellent]
  FTP (20m): 419W (Score: 0.85) [Excellent]

LTHR: 178 bpm
Rider Type: All-Rounder

Profile Used During Test:
  FTP: 403W, MAP: 478W, AC: 591W, NM: 1303W

Activity Data (4,200 samples):
  Power: 287W avg, 1350W max
  Cadence: 88 rpm avg, 156 rpm max
  Heart Rate: 156 bpm avg, 185 bpm max

Power Bests:
  1. 5s: 1350W
  2. 1m: 612W
  3. 5m: 495W
  4. 20m: 419W
  [... more durations]

Analysis:
Your test shows excellent improvements across all energy systems. Your FTP increased
by 4%, indicating strong aerobic development. The higher AC and MAP values suggest
you're building strong anaerobic capacity. Focus on maintaining these gains with
targeted threshold and VO2 max work.
```

## Development

### Project Structure

```
wahoo-systm-mcp/
├── src/
│   ├── index.ts           # MCP server implementation
│   ├── client.ts          # Wahoo SYSTM API client
│   ├── types.ts           # TypeScript type definitions
│   ├── onepassword.ts     # 1Password integration
│   └── test/              # Test suite
│       ├── setup.ts
│       ├── client.test.ts
│       ├── onepassword.test.ts
│       └── integration.test.ts
├── build/                 # Compiled JavaScript (generated)
├── .env.example           # Example environment variables
├── package.json
├── tsconfig.json
└── README.md
```

### Building

```bash
npm run build
```

### Watch Mode (for development)

```bash
npm run watch
```

### Testing

Run the test suite to verify everything is working:

```bash
npm test
```

The tests will use credentials from a `.env` file. Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your 1Password references or plain credentials.

## API Information

This server uses the Wahoo SYSTM GraphQL API at `https://api.thesufferfest.com/graphql`. The implementation is based on reverse-engineering the web app's API calls.

## Security Notes

- Credentials are only stored in memory during the session
- The `.env` file is gitignored to prevent accidental commits
- Authentication tokens are not persisted between server restarts
- 1Password integration provides the most secure credential management

## Acknowledgments

This project was inspired by [suffersync](https://github.com/bakermat/suffersync) by bakermat, which syncs Wahoo SYSTM workouts to intervals.icu.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
