#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from '@modelcontextprotocol/sdk/types.js';
import { WahooClient } from './wahoo-client.js';
import { getCredentialsFrom1Password } from './onepassword.js';

const server = new Server(
  {
    name: 'wahoo-systm-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const wahooClient = new WahooClient();
let isAuthenticated = false;

// Try to auto-authenticate from environment variables if provided
const ONEPASSWORD_USERNAME_REF = process.env.WAHOO_USERNAME_1P_REF;
const ONEPASSWORD_PASSWORD_REF = process.env.WAHOO_PASSWORD_1P_REF;
const PLAIN_USERNAME = process.env.WAHOO_USERNAME;
const PLAIN_PASSWORD = process.env.WAHOO_PASSWORD;

async function autoAuthenticate(): Promise<void> {
  // Try 1Password first
  if (ONEPASSWORD_USERNAME_REF && ONEPASSWORD_PASSWORD_REF) {
    try {
      const credentials = await getCredentialsFrom1Password(
        ONEPASSWORD_USERNAME_REF,
        ONEPASSWORD_PASSWORD_REF
      );
      await wahooClient.authenticate(credentials);
      isAuthenticated = true;
      console.error('Auto-authenticated with Wahoo SYSTM using 1Password credentials');
      return;
    } catch (error) {
      console.error('Failed to auto-authenticate with 1Password:', error instanceof Error ? error.message : String(error));
    }
  }

  // Fallback to plain text credentials
  if (PLAIN_USERNAME && PLAIN_PASSWORD) {
    try {
      await wahooClient.authenticate({
        username: PLAIN_USERNAME,
        password: PLAIN_PASSWORD
      });
      isAuthenticated = true;
      console.error('Auto-authenticated with Wahoo SYSTM using plain credentials');
    } catch (error) {
      console.error('Failed to auto-authenticate with plain credentials:', error instanceof Error ? error.message : String(error));
    }
  }
}

// Tool definitions
const tools: Tool[] = [
  {
    name: 'get_calendar',
    description: 'Get planned workouts from Wahoo SYSTM calendar for a date range. Returns workout name, type, duration, planned date, and basic details.',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: {
          type: 'string',
          description: 'Start date in YYYY-MM-DD format'
        },
        end_date: {
          type: 'string',
          description: 'End date in YYYY-MM-DD format'
        }
      },
      required: ['start_date', 'end_date']
    }
  },
  {
    name: 'get_workout_details',
    description: 'Get detailed information about a specific workout including intervals, power zones, equipment needed, and full workout structure.',
    inputSchema: {
      type: 'object',
      properties: {
        workout_id: {
          type: 'string',
          description: 'The workout ID (obtained from get_calendar)'
        }
      },
      required: ['workout_id']
    }
  },
  {
    name: 'get_rider_profile',
    description: 'Get the authenticated user\'s 4DP profile values (FTP, MAP, AC, NM). Must be authenticated first.',
    inputSchema: {
      type: 'object',
      properties: {},
      required: []
    }
  }
];

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'get_calendar': {
        if (!isAuthenticated) {
          throw new Error('Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.');
        }

        if (!args || typeof args !== 'object') {
          throw new Error('Invalid arguments');
        }
        const { start_date, end_date } = args as { start_date?: unknown; end_date?: unknown };
        if (typeof start_date !== 'string' || typeof end_date !== 'string') {
          throw new Error('start_date and end_date must be strings in YYYY-MM-DD format');
        }
        const workouts = await wahooClient.getCalendarWorkouts(start_date, end_date);

        // Format the response to be more readable
        const formattedWorkouts = workouts
          .filter(item => item.plannedDate && item.prospects.length > 0)
          .map(item => ({
            date: item.plannedDate.split('T')[0],
            workout: {
              id: item.prospects[0].workoutId,
              name: item.prospects[0].name,
              type: item.prospects[0].type,
              duration_hours: item.prospects[0].plannedDuration,
              description: item.prospects[0].description,
              intensity: item.prospects[0].intensity,
              status: item.status
            },
            plan: item.plan ? {
              name: item.plan.name,
              category: item.plan.category
            } : null
          }));

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                total_workouts: formattedWorkouts.length,
                workouts: formattedWorkouts
              }, null, 2)
            }
          ]
        };
      }

      case 'get_workout_details': {
        if (!isAuthenticated) {
          throw new Error('Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.');
        }

        if (!args || typeof args !== 'object') {
          throw new Error('Invalid arguments');
        }
        const { workout_id } = args as { workout_id?: unknown };
        if (typeof workout_id !== 'string') {
          throw new Error('workout_id must be a string');
        }
        const workout = await wahooClient.getWorkoutDetails(workout_id);

        // Parse the triggers JSON if it exists
        let intervals = null;
        if (workout.triggers) {
          try {
            intervals = JSON.parse(workout.triggers);
          } catch (e) {
            intervals = 'Unable to parse workout intervals';
          }
        }

        const formattedWorkout = {
          id: workout.id,
          name: workout.name,
          sport: workout.sport,
          duration_seconds: workout.durationSeconds,
          duration_formatted: `${Math.floor(workout.durationSeconds / 3600)}h ${Math.floor((workout.durationSeconds % 3600) / 60)}m`,
          level: workout.level,
          description: workout.details,
          short_description: workout.shortDescription,
          equipment: workout.equipment,
          metrics: {
            intensity_factor: workout.metrics.intensityFactor,
            tss: workout.metrics.tss,
            ratings: workout.metrics.ratings
          },
          intervals: intervals
        };

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(formattedWorkout, null, 2)
            }
          ]
        };
      }

      case 'get_rider_profile': {
        if (!isAuthenticated) {
          throw new Error('Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.');
        }

        const profile = wahooClient.getRiderProfile();

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                profile: profile,
                description: {
                  ftp: 'Functional Threshold Power (watts)',
                  map: 'Maximal Aerobic Power (watts)',
                  ac: 'Anaerobic Capacity (watts)',
                  nm: 'Neuromuscular Power (watts)'
                }
              }, null, 2)
            }
          ]
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ error: errorMessage }, null, 2)
        }
      ],
      isError: true
    };
  }
});

// Start the server
async function main() {
  // Try to auto-authenticate if 1Password references are provided
  await autoAuthenticate();

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Wahoo SYSTM MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error in main():', error);
  process.exit(1);
});
