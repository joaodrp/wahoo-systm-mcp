#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { WahooClient } from './client.js';
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
      console.error(
        'Failed to auto-authenticate with 1Password:',
        error instanceof Error ? error.message : String(error)
      );
    }
  }

  // Fallback to plain text credentials
  if (PLAIN_USERNAME && PLAIN_PASSWORD) {
    try {
      await wahooClient.authenticate({
        username: PLAIN_USERNAME,
        password: PLAIN_PASSWORD,
      });
      isAuthenticated = true;
      console.error('Auto-authenticated with Wahoo SYSTM using plain credentials');
    } catch (error) {
      console.error(
        'Failed to auto-authenticate with plain credentials:',
        error instanceof Error ? error.message : String(error)
      );
    }
  }
}

// Tool definitions
const tools: Tool[] = [
  {
    name: 'get_calendar',
    description:
      'Get planned workouts from Wahoo SYSTM calendar for a date range. Returns workout name, type, duration, planned date, and basic details.',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: {
          type: 'string',
          description: 'Start date in YYYY-MM-DD format',
        },
        end_date: {
          type: 'string',
          description: 'End date in YYYY-MM-DD format',
        },
      },
      required: ['start_date', 'end_date'],
    },
  },
  {
    name: 'get_workout_details',
    description:
      'Get detailed information about a specific workout including intervals, power zones, equipment needed, and full workout structure.',
    inputSchema: {
      type: 'object',
      properties: {
        workout_id: {
          type: 'string',
          description: 'The workout ID (obtained from get_calendar)',
        },
      },
      required: ['workout_id'],
    },
  },
  {
    name: 'get_rider_profile',
    description:
      "Get the authenticated user's 4DP profile values (FTP, MAP, AC, NM). Must be authenticated first.",
    inputSchema: {
      type: 'object',
      properties: {},
      required: [],
    },
  },
  {
    name: 'schedule_workout',
    description:
      'Schedule a workout for a specific date. The contentId can be obtained from get_workouts or get_cycling_workouts results.',
    inputSchema: {
      type: 'object',
      properties: {
        content_id: {
          type: 'string',
          description:
            'The content ID of the workout to schedule (from get_workouts/get_cycling_workouts)',
        },
        date: {
          type: 'string',
          description: 'Date to schedule the workout in YYYY-MM-DD format (e.g., "2025-12-15")',
        },
        time_zone: {
          type: 'string',
          description:
            'Optional timezone (e.g., "Europe/Lisbon", "America/New_York"). Defaults to UTC if not specified.',
        },
      },
      required: ['content_id', 'date'],
    },
  },
  {
    name: 'reschedule_workout',
    description:
      'Reschedule an existing workout to a different date. The agendaId can be obtained from schedule_workout or get_calendar results.',
    inputSchema: {
      type: 'object',
      properties: {
        agenda_id: {
          type: 'string',
          description:
            'The agenda ID of the scheduled workout (from schedule_workout or get_calendar)',
        },
        new_date: {
          type: 'string',
          description:
            'New date to reschedule the workout to in YYYY-MM-DD format (e.g., "2025-12-16")',
        },
        time_zone: {
          type: 'string',
          description:
            'Optional timezone (e.g., "Europe/Lisbon", "America/New_York"). Defaults to UTC if not specified.',
        },
      },
      required: ['agenda_id', 'new_date'],
    },
  },
  {
    name: 'remove_workout',
    description:
      'Remove/cancel a scheduled workout from your calendar. The agendaId can be obtained from schedule_workout or get_calendar results.',
    inputSchema: {
      type: 'object',
      properties: {
        agenda_id: {
          type: 'string',
          description:
            'The agenda ID of the scheduled workout to remove (from schedule_workout or get_calendar)',
        },
      },
      required: ['agenda_id'],
    },
  },
  {
    name: 'get_workouts',
    description:
      'Get workouts from the Wahoo SYSTM library. Filter by sport, duration, and TSS. Sort by name, duration, or TSS. Returns a list of workouts with their metadata.',
    inputSchema: {
      type: 'object',
      properties: {
        sport: {
          type: 'string',
          description:
            'Filter by sport/workout type (e.g., Cycling, Running, Strength, Yoga, Swimming)',
        },
        search: {
          type: 'string',
          description:
            'Search for workouts by name (case-insensitive, partial match). Example: "Nine Hammers", "tempo", "Violator"',
        },
        min_duration: {
          type: 'number',
          description: 'Minimum workout duration in minutes (e.g., 30 for 30 minutes)',
        },
        max_duration: {
          type: 'number',
          description: 'Maximum workout duration in minutes (e.g., 120 for 2 hours)',
        },
        min_tss: {
          type: 'number',
          description: 'Minimum Training Stress Score (e.g., 20 for easy, 100+ for hard)',
        },
        max_tss: {
          type: 'number',
          description: 'Maximum Training Stress Score',
        },
        sort_by: {
          type: 'string',
          enum: ['name', 'duration', 'tss'],
          description: 'Sort workouts by: name (default), duration, or tss',
        },
        sort_direction: {
          type: 'string',
          enum: ['asc', 'desc'],
          description: 'Sort direction: asc (default) or desc',
        },
        limit: {
          type: 'number',
          description: 'Maximum number of results to return (default: 50)',
        },
      },
      required: [],
    },
  },
  {
    name: 'get_cycling_workouts',
    description:
      'Get cycling workouts with filters matching the SYSTM UI. Filter by channel, category, 4DP focus (NM/AC/MAP/FTP), duration range, and intensity. Returns cycling workouts with metadata.',
    inputSchema: {
      type: 'object',
      properties: {
        channel: {
          type: 'string',
          description:
            'Filter by channel: The Sufferfest, Inspiration, Wahoo Fitness, A Week With, ProRides, On Location, NoVid, Fitness Test',
        },
        category: {
          type: 'string',
          description:
            'Filter by category: Activation, Active Recovery, Climbing, Cool Down, Endurance, Fitness Test, Mixed, Overview, Racing, Speed, Sustained Efforts, Technique & Drills, The Knowledge',
        },
        four_dp_focus: {
          type: 'string',
          enum: ['NM', 'AC', 'MAP', 'FTP'],
          description:
            'Filter by 4DP focus - workouts that target this energy system (rating >= 4): NM (Neuromuscular), AC (Anaerobic Capacity), MAP (Maximal Aerobic Power), FTP (Functional Threshold Power)',
        },
        search: {
          type: 'string',
          description:
            'Search for workouts by name (case-insensitive, partial match). Example: "Nine Hammers", "tempo", "Violator"',
        },
        min_duration: {
          type: 'number',
          description: 'Minimum workout duration in minutes (e.g., 30 for 30 minutes)',
        },
        max_duration: {
          type: 'number',
          description: 'Maximum workout duration in minutes (e.g., 90 for 90 minutes)',
        },
        min_tss: {
          type: 'number',
          description: 'Minimum Training Stress Score',
        },
        max_tss: {
          type: 'number',
          description: 'Maximum Training Stress Score',
        },
        intensity: {
          type: 'string',
          enum: ['High', 'Medium', 'Low'],
          description: 'Filter by intensity level',
        },
        sort_by: {
          type: 'string',
          enum: ['name', 'duration', 'tss'],
          description: 'Sort workouts by: name (default), duration, or tss',
        },
        sort_direction: {
          type: 'string',
          enum: ['asc', 'desc'],
          description: 'Sort direction: asc (default) or desc',
        },
        limit: {
          type: 'number',
          description: 'Maximum number of results to return (default: 50)',
        },
      },
      required: [],
    },
  },
  {
    name: 'get_fitness_test_history',
    description:
      'Get your fitness test history from Wahoo SYSTM. Returns all completed Full Frontal and Half Monty tests with 4DP values (NM, AC, MAP, FTP), LTHR, rider type, TSS, and test dates. Results are sorted by date (most recent first).',
    inputSchema: {
      type: 'object',
      properties: {
        page: {
          type: 'number',
          description: 'Page number for pagination (default: 1)',
        },
        page_size: {
          type: 'number',
          description: 'Number of results per page (default: 15)',
        },
      },
      required: [],
    },
  },
  {
    name: 'get_fitness_test_details',
    description:
      'Get detailed information about a specific fitness test activity. Returns second-by-second power, cadence, and heart rate data, power curve bests, test notes, profile used during test, and complete 4DP results with rider type analysis.',
    inputSchema: {
      type: 'object',
      properties: {
        activity_id: {
          type: 'string',
          description:
            'The activity ID of the fitness test (obtained from get_fitness_test_history)',
        },
      },
      required: ['activity_id'],
    },
  },
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
          throw new Error(
            'Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.'
          );
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
          .filter((item) => item.plannedDate && item.prospects.length > 0)
          .map((item) => ({
            date: item.plannedDate.split('T')[0],
            agenda_id: item.agendaId,
            workout: {
              id: item.prospects[0].workoutId,
              name: item.prospects[0].name,
              type: item.prospects[0].type,
              duration_hours: item.prospects[0].plannedDuration,
              description: item.prospects[0].description,
              intensity: item.prospects[0].intensity,
              status: item.status,
            },
            plan: item.plan
              ? {
                  name: item.plan.name,
                  category: item.plan.category,
                }
              : null,
          }));

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  total_workouts: formattedWorkouts.length,
                  workouts: formattedWorkouts,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'get_workout_details': {
        if (!isAuthenticated) {
          throw new Error(
            'Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.'
          );
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
          descriptions: workout.descriptions,
          equipment: workout.equipment,
          metrics: {
            intensity_factor: workout.metrics.intensityFactor,
            tss: workout.metrics.tss,
            ratings: workout.metrics.ratings,
          },
          intervals: intervals,
        };

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(formattedWorkout, null, 2),
            },
          ],
        };
      }

      case 'get_rider_profile': {
        if (!isAuthenticated) {
          throw new Error(
            'Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.'
          );
        }

        const enhancedProfile = await wahooClient.getEnhancedRiderProfile();

        if (!enhancedProfile) {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(
                  {
                    error:
                      'No fitness test data available. Please complete a Full Frontal or Half Monty test in SYSTM.',
                  },
                  null,
                  2
                ),
              },
            ],
          };
        }

        // Format the test date
        const testDate = new Date(enhancedProfile.startTime);
        const formattedDate = testDate.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  fourDP: {
                    nm: {
                      watts: enhancedProfile.nm,
                      score: enhancedProfile.power5s.graphValue.toFixed(2),
                      description: 'Neuromuscular Power (5s max effort)',
                    },
                    ac: {
                      watts: enhancedProfile.ac,
                      score: enhancedProfile.power1m.graphValue.toFixed(2),
                      description: 'Anaerobic Capacity (1m max effort)',
                    },
                    map: {
                      watts: enhancedProfile.map,
                      score: enhancedProfile.power5m.graphValue.toFixed(2),
                      description: 'Maximal Aerobic Power (5m max effort)',
                    },
                    ftp: {
                      watts: enhancedProfile.ftp,
                      score: enhancedProfile.power20m.graphValue.toFixed(2),
                      description: 'Functional Threshold Power (20m effort)',
                    },
                  },
                  riderType: {
                    name: enhancedProfile.riderType.name,
                    description: enhancedProfile.riderType.description,
                    icon: enhancedProfile.riderType.icon,
                  },
                  strengths: {
                    name: enhancedProfile.riderWeakness.strengthName,
                    summary: enhancedProfile.riderWeakness.strengthSummary,
                    description: enhancedProfile.riderWeakness.strengthDescription,
                  },
                  weaknesses: {
                    name: enhancedProfile.riderWeakness.name,
                    summary: enhancedProfile.riderWeakness.weaknessSummary,
                    description: enhancedProfile.riderWeakness.weaknessDescription,
                  },
                  heartRate: {
                    lthr: Math.round(enhancedProfile.lactateThresholdHeartRate),
                    zones: enhancedProfile.heartRateZones.map((zone) => ({
                      zone: zone.zone,
                      name: zone.name,
                      range: zone.max ? `${zone.min}-${zone.max} bpm` : `${zone.min}+ bpm`,
                    })),
                  },
                  testInfo: {
                    completed: enhancedProfile.fitnessTestRidden,
                    date: formattedDate,
                  },
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'schedule_workout': {
        if (!isAuthenticated) {
          throw new Error(
            'Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.'
          );
        }

        if (!args || typeof args !== 'object') {
          throw new Error('Invalid arguments');
        }

        const { content_id, date, time_zone } = args as {
          content_id?: unknown;
          date?: unknown;
          time_zone?: unknown;
        };

        if (typeof content_id !== 'string') {
          throw new Error('content_id must be a string');
        }
        if (typeof date !== 'string') {
          throw new Error('date must be a string in YYYY-MM-DD format');
        }

        // Convert YYYY-MM-DD to ISO 8601 format
        // The API expects a full ISO 8601 timestamp
        const isoDate = `${date}T12:00:00.000Z`;

        const tz = time_zone && typeof time_zone === 'string' ? time_zone : undefined;

        const agendaId = await wahooClient.scheduleWorkout(content_id, isoDate, tz);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  success: true,
                  agenda_id: agendaId,
                  content_id: content_id,
                  scheduled_date: date,
                  time_zone: tz || 'UTC',
                  message: `Workout successfully scheduled for ${date}`,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'reschedule_workout': {
        if (!isAuthenticated) {
          throw new Error(
            'Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.'
          );
        }

        if (!args || typeof args !== 'object') {
          throw new Error('Invalid arguments');
        }

        const { agenda_id, new_date, time_zone } = args as {
          agenda_id?: unknown;
          new_date?: unknown;
          time_zone?: unknown;
        };

        if (typeof agenda_id !== 'string') {
          throw new Error('agenda_id must be a string');
        }

        if (typeof new_date !== 'string') {
          throw new Error('new_date must be a string in YYYY-MM-DD format');
        }

        // Convert YYYY-MM-DD to ISO 8601 format
        const isoDate = `${new_date}T00:00:00.000Z`;
        const tz = time_zone && typeof time_zone === 'string' ? time_zone : undefined;

        await wahooClient.rescheduleWorkout(agenda_id, isoDate, tz);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  success: true,
                  agenda_id: agenda_id,
                  new_date: new_date,
                  time_zone: tz || 'UTC',
                  message: `Workout successfully rescheduled to ${new_date}`,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'remove_workout': {
        if (!isAuthenticated) {
          throw new Error(
            'Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.'
          );
        }

        if (!args || typeof args !== 'object') {
          throw new Error('Invalid arguments');
        }

        const { agenda_id } = args as {
          agenda_id?: unknown;
        };

        if (typeof agenda_id !== 'string') {
          throw new Error('agenda_id must be a string');
        }

        await wahooClient.removeWorkout(agenda_id);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  success: true,
                  agenda_id: agenda_id,
                  message: `Workout successfully removed from calendar`,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'get_workouts': {
        if (!isAuthenticated) {
          throw new Error(
            'Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.'
          );
        }

        const filters: {
          sport?: string;
          search?: string;
          minDuration?: number;
          maxDuration?: number;
          minTss?: number;
          maxTss?: number;
          sortBy?: 'name' | 'duration' | 'tss';
          sortDirection?: 'asc' | 'desc';
        } = {};

        if (args && typeof args === 'object') {
          const params = args as Record<string, unknown>;
          if (typeof params.sport === 'string') filters.sport = params.sport;
          if (typeof params.search === 'string') filters.search = params.search;
          if (typeof params.min_duration === 'number') filters.minDuration = params.min_duration;
          if (typeof params.max_duration === 'number') filters.maxDuration = params.max_duration;
          if (typeof params.min_tss === 'number') filters.minTss = params.min_tss;
          if (typeof params.max_tss === 'number') filters.maxTss = params.max_tss;
          if (
            typeof params.sort_by === 'string' &&
            ['name', 'duration', 'tss'].includes(params.sort_by)
          ) {
            filters.sortBy = params.sort_by as 'name' | 'duration' | 'tss';
          }
          if (
            typeof params.sort_direction === 'string' &&
            ['asc', 'desc'].includes(params.sort_direction)
          ) {
            filters.sortDirection = params.sort_direction as 'asc' | 'desc';
          }
        }

        const library = await wahooClient.getWorkoutLibrary(filters);

        // Apply limit
        const limit =
          args &&
          typeof args === 'object' &&
          typeof (args as Record<string, unknown>).limit === 'number'
            ? ((args as Record<string, unknown>).limit as number)
            : 50;
        const limitedLibrary = library.slice(0, limit);

        // Format the response
        const formattedWorkouts = limitedLibrary.map((item) => {
          const durationHours = item.duration / 3600;
          const hours = Math.floor(durationHours);
          const minutes = Math.round((durationHours - hours) * 60);

          return {
            id: item.id,
            workout_id: item.workoutId,
            name: item.name,
            sport: item.workoutType,
            channel: item.channel,
            level: item.level || item.intensity || 'N/A',
            category: item.category,
            duration_seconds: item.duration,
            duration_formatted: hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`,
            description: item.descriptions?.[0]?.body?.substring(0, 400) + '...' || '',
            tss: item.metrics?.tss,
            intensity_factor: item.metrics?.intensityFactor,
            ratings_4dp: item.metrics?.ratings
              ? {
                  ftp: item.metrics.ratings.ftp,
                  map: item.metrics.ratings.map,
                  ac: item.metrics.ratings.ac,
                  nm: item.metrics.ratings.nm,
                }
              : null,
            tags: item.tags,
          };
        });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  total_found: library.length,
                  returned: formattedWorkouts.length,
                  workouts: formattedWorkouts,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'get_cycling_workouts': {
        if (!isAuthenticated) {
          throw new Error(
            'Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.'
          );
        }

        const filters: {
          channel?: string;
          category?: string;
          fourDpFocus?: 'NM' | 'AC' | 'MAP' | 'FTP';
          search?: string;
          minDuration?: number;
          maxDuration?: number;
          minTss?: number;
          maxTss?: number;
          intensity?: 'High' | 'Medium' | 'Low';
          sortBy?: 'name' | 'duration' | 'tss';
          sortDirection?: 'asc' | 'desc';
          limit?: number;
        } = {};

        if (args && typeof args === 'object') {
          const params = args as Record<string, unknown>;
          if (typeof params.channel === 'string') filters.channel = params.channel;
          if (typeof params.category === 'string') filters.category = params.category;
          if (
            typeof params.four_dp_focus === 'string' &&
            ['NM', 'AC', 'MAP', 'FTP'].includes(params.four_dp_focus)
          ) {
            filters.fourDpFocus = params.four_dp_focus as 'NM' | 'AC' | 'MAP' | 'FTP';
          }
          if (typeof params.search === 'string') filters.search = params.search;
          if (typeof params.min_duration === 'number') filters.minDuration = params.min_duration;
          if (typeof params.max_duration === 'number') filters.maxDuration = params.max_duration;
          if (typeof params.min_tss === 'number') filters.minTss = params.min_tss;
          if (typeof params.max_tss === 'number') filters.maxTss = params.max_tss;
          if (
            typeof params.intensity === 'string' &&
            ['High', 'Medium', 'Low'].includes(params.intensity)
          ) {
            filters.intensity = params.intensity as 'High' | 'Medium' | 'Low';
          }
          if (
            typeof params.sort_by === 'string' &&
            ['name', 'duration', 'tss'].includes(params.sort_by)
          ) {
            filters.sortBy = params.sort_by as 'name' | 'duration' | 'tss';
          }
          if (
            typeof params.sort_direction === 'string' &&
            ['asc', 'desc'].includes(params.sort_direction)
          ) {
            filters.sortDirection = params.sort_direction as 'asc' | 'desc';
          }
          if (typeof params.limit === 'number') filters.limit = params.limit;
        }

        const cyclingWorkouts = await wahooClient.getCyclingWorkouts(filters);

        // Format the response (same as get_workouts)
        const formattedWorkouts = cyclingWorkouts.map((item) => {
          const durationHours = item.duration / 3600;
          const hours = Math.floor(durationHours);
          const minutes = Math.round((durationHours - hours) * 60);

          return {
            id: item.id,
            workout_id: item.workoutId,
            name: item.name,
            sport: item.workoutType,
            channel: item.channel,
            category: item.category,
            intensity: item.intensity || 'N/A',
            duration_seconds: item.duration,
            duration_formatted: hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`,
            description: item.descriptions?.[0]?.body?.substring(0, 400) + '...' || '',
            tss: item.metrics?.tss,
            intensity_factor: item.metrics?.intensityFactor,
            ratings_4dp: item.metrics?.ratings
              ? {
                  ftp: item.metrics.ratings.ftp,
                  map: item.metrics.ratings.map,
                  ac: item.metrics.ratings.ac,
                  nm: item.metrics.ratings.nm,
                }
              : null,
            tags: item.tags,
          };
        });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  total_found: cyclingWorkouts.length,
                  returned: formattedWorkouts.length,
                  workouts: formattedWorkouts,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'get_fitness_test_history': {
        if (!isAuthenticated) {
          throw new Error(
            'Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.'
          );
        }

        const options: {
          page?: number;
          pageSize?: number;
        } = {};

        if (args && typeof args === 'object') {
          const params = args as Record<string, unknown>;
          if (typeof params.page === 'number') options.page = params.page;
          if (typeof params.page_size === 'number') options.pageSize = params.page_size;
        }

        const result = await wahooClient.getFitnessTestHistory(options);

        // Format the response
        const formattedTests = result.activities.map((test) => {
          const testDate = new Date(test.completedDate);
          const formattedDate = testDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          });

          const durationHours = test.durationSeconds / 3600;
          const hours = Math.floor(durationHours);
          const minutes = Math.round((durationHours - hours) * 60);

          return {
            id: test.id,
            name: test.name,
            completed_date: formattedDate,
            duration: hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`,
            tss: test.tss,
            intensity_factor: test.intensityFactor,
            fourDP: test.testResults
              ? {
                  nm: {
                    watts: test.testResults.power5s.value,
                    score: test.testResults.power5s.graphValue.toFixed(2),
                  },
                  ac: {
                    watts: test.testResults.power1m.value,
                    score: test.testResults.power1m.graphValue.toFixed(2),
                  },
                  map: {
                    watts: test.testResults.power5m.value,
                    score: test.testResults.power5m.graphValue.toFixed(2),
                  },
                  ftp: {
                    watts: test.testResults.power20m.value,
                    score: test.testResults.power20m.graphValue.toFixed(2),
                  },
                }
              : null,
            lthr: test.testResults ? Math.round(test.testResults.lactateThresholdHeartRate) : null,
            rider_type: test.testResults?.riderType.name || null,
          };
        });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  total: result.total,
                  tests: formattedTests,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'get_fitness_test_details': {
        if (!isAuthenticated) {
          throw new Error(
            'Not authenticated. Please configure WAHOO_USERNAME/WAHOO_PASSWORD or WAHOO_USERNAME_1P_REF/WAHOO_PASSWORD_1P_REF environment variables.'
          );
        }

        if (!args || typeof args !== 'object') {
          throw new Error('Invalid arguments');
        }

        const { activity_id } = args as { activity_id?: unknown };

        if (typeof activity_id !== 'string') {
          throw new Error('activity_id must be a string');
        }

        const testDetails = await wahooClient.getFitnessTestDetails(activity_id);

        // Format the response
        const testDate = new Date(testDetails.completedDate);
        const formattedDate = testDate.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        });

        const durationHours = testDetails.durationSeconds / 3600;
        const hours = Math.floor(durationHours);
        const minutes = Math.round((durationHours - hours) * 60);

        // Parse analysis JSON if it exists
        let analysisData = null;
        if (testDetails.analysis) {
          try {
            analysisData = JSON.parse(testDetails.analysis);
          } catch (e) {
            analysisData = 'Unable to parse analysis data';
          }
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  id: testDetails.id,
                  name: testDetails.name,
                  completed_date: formattedDate,
                  duration: hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`,
                  tss: testDetails.tss,
                  intensity_factor: testDetails.intensityFactor,
                  notes: testDetails.notes || '',
                  fourDP: {
                    nm: {
                      watts: testDetails.testResults.power5s.value,
                      score: testDetails.testResults.power5s.graphValue.toFixed(2),
                      status: testDetails.testResults.power5s.status,
                    },
                    ac: {
                      watts: testDetails.testResults.power1m.value,
                      score: testDetails.testResults.power1m.graphValue.toFixed(2),
                      status: testDetails.testResults.power1m.status,
                    },
                    map: {
                      watts: testDetails.testResults.power5m.value,
                      score: testDetails.testResults.power5m.graphValue.toFixed(2),
                      status: testDetails.testResults.power5m.status,
                    },
                    ftp: {
                      watts: testDetails.testResults.power20m.value,
                      score: testDetails.testResults.power20m.graphValue.toFixed(2),
                      status: testDetails.testResults.power20m.status,
                    },
                  },
                  lthr: Math.round(testDetails.testResults.lactateThresholdHeartRate),
                  rider_type: {
                    name: testDetails.testResults.riderType.name,
                    description: testDetails.testResults.riderType.description,
                  },
                  profile_used: testDetails.profile,
                  power_data: {
                    length: testDetails.power.length,
                    avg: testDetails.power.reduce((a, b) => a + b, 0) / testDetails.power.length,
                    max: Math.max(...testDetails.power),
                  },
                  heart_rate_data: {
                    length: testDetails.heartRate.length,
                    avg:
                      testDetails.heartRate.reduce((a, b) => a + b, 0) /
                      testDetails.heartRate.length,
                    max: Math.max(...testDetails.heartRate),
                  },
                  cadence_data: {
                    length: testDetails.cadence.length,
                    avg:
                      testDetails.cadence.reduce((a, b) => a + b, 0) / testDetails.cadence.length,
                  },
                  power_bests: testDetails.powerBests.map((best) => ({
                    duration_seconds: best.duration,
                    power: best.value,
                  })),
                  analysis: analysisData,
                },
                null,
                2
              ),
            },
          ],
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
          text: JSON.stringify({ error: errorMessage }, null, 2),
        },
      ],
      isError: true,
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
