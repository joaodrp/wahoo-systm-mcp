# Wahoo SYSTM MCP Server

A Model Context Protocol (MCP) server that provides access to Wahoo SYSTM calendar and workout data. This allows Claude and other MCP clients to interact with your Wahoo SYSTM training plan, retrieve planned workouts, and get detailed workout information including intervals and power zones.

## Features

- **Authentication**: Securely authenticate with your Wahoo SYSTM account
- **Calendar Access**: Retrieve planned workouts for any date range
- **Workout Details**: Get comprehensive workout information including:
  - Workout intervals and structure
  - Power zones (FTP, MAP, AC, NM)
  - Duration and intensity
  - Equipment requirements
  - TSS (Training Stress Score) and IF (Intensity Factor)
- **Rider Profile**: Access your 4DP profile values

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

#### 2. `get_workout_details`

Get comprehensive details about a specific workout.

**Parameters:**
- `workout_id` (string): The workout ID from `get_calendar`

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

#### 3. `get_rider_profile`

Get your 4DP profile values.

**Parameters:** None

**Returns:**
- FTP (Functional Threshold Power)
- MAP (Maximal Aerobic Power)
- AC (Anaerobic Capacity)
- NM (Neuromuscular Power)

## Example Conversation with Claude

**You:**
```
What workouts do I have planned for this week?
```

**Claude:** *[calls get_calendar - automatically authenticated]*
```
Let me check your calendar for this week. You have the following workouts planned:

December 9, 2025:
- ALL Access EF 1: Tempo Blocks (Cycling, 1.2h)
  Description: Saddle up for the high-energy atmosphere of the EF men's & women's
  team training camp! Warm up with Jonathan Vaughters and meet the team over some
  golf practice. Push through 5 tempo blocks on the stunning roads of Girona.
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
4DP Focus: FTP ✭✭✭✩✩ (minimal NM, AC, MAP work)

This is a tempo session designed to give your body a decent aerobic workload without
adding significant fatigue. Perfect for base training.

Structure:
- Warm Up: 15 minutes progressive (55% → 100% FTP)
- Main Effort: 5 sets of 4 minutes @ 80% FTP (RPE 5) with 4-minute recovery between sets
- Extra Volume: 30 minutes @ 60% FTP
- Cool Down: 5 minutes @ 50% FTP

At no point should you feel you are anywhere near your limits - this keeps your fatigue
level steady or brings it down.
```

**You:**
```
What are my 4DP values?
```

**Claude:** *[calls get_rider_profile]*
```
Your 4DP Profile:
- FTP: 419W (Functional Threshold Power)
- MAP: 495W (Maximal Aerobic Power)
- AC: 612W (Anaerobic Capacity)
- NM: 1350W (Neuromuscular Power)
```

## Development

### Project Structure

```
wahoo-systm-mcp/
├── src/
│   ├── index.ts           # MCP server implementation
│   ├── wahoo-client.ts    # Wahoo SYSTM API client
│   ├── types.ts           # TypeScript type definitions
│   ├── onepassword.ts     # 1Password integration
│   └── test/              # Test suite
│       ├── setup.ts
│       ├── wahoo-client.test.ts
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
