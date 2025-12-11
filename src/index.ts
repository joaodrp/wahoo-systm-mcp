#!/usr/bin/env node

import { FastMCP, UserError } from 'fastmcp';
import { z } from 'zod';
import { WahooClient } from './client.js';
import { getCredentialsFrom1Password } from './onepassword.js';
import { format } from 'date-fns';

// Initialize MCP server
const mcp = new FastMCP({
  name: 'wahoo-systm-mcp',
  version: '0.1.0',
});

// Initialize Wahoo client
const wahooClient = new WahooClient();
let isAuthenticated = false;

// Auto-authentication from environment variables
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

function ensureAuthenticated() {
  if (!isAuthenticated) {
    throw new UserError(
      'Not authenticated. Please provide WAHOO_USERNAME and WAHOO_PASSWORD environment variables.'
    );
  }
}

// Tool: get_calendar
mcp.addTool({
  name: 'get_calendar',
  description:
    'Get planned workouts from Wahoo SYSTM calendar for a date range. Returns workout name, type, duration, planned date, and basic details.',
  parameters: z.object({
    start_date: z.string().describe('Start date in YYYY-MM-DD format'),
    end_date: z.string().describe('End date in YYYY-MM-DD format'),
  }),
  execute: async (args) => {
    ensureAuthenticated();
    const workouts = await wahooClient.getCalendarWorkouts(args.start_date, args.end_date);
    return JSON.stringify(workouts, null, 2);
  },
});

// Tool: get_workout_details
mcp.addTool({
  name: 'get_workout_details',
  description:
    'Get detailed information about a specific workout including intervals, power zones, equipment needed, and full workout structure.',
  parameters: z.object({
    workout_id: z
      .string()
      .describe('Workout ID from calendar or library (accepts both id and workoutId)'),
  }),
  execute: async (args) => {
    ensureAuthenticated();
    const details = await wahooClient.getWorkoutDetails(args.workout_id);
    return JSON.stringify(details, null, 2);
  },
});

// Tool: get_rider_profile
mcp.addTool({
  name: 'get_rider_profile',
  description:
    'Get the rider 4DP profile (NM, AC, MAP, FTP) including rider type classification, strengths/weaknesses, and heart rate zones.',
  parameters: z.object({}),
  execute: async () => {
    ensureAuthenticated();
    const profile = await wahooClient.getEnhancedRiderProfile();

    if (!profile) {
      throw new UserError(
        'No rider profile found. Complete a Full Frontal or Half Monty test first.'
      );
    }

    const testDate = new Date(profile.startTime);
    const formattedDate = format(testDate, 'MMMM d, yyyy');

    return JSON.stringify(
      {
        fourDP: {
          nm: { watts: profile.nm, score: profile.power5s.value },
          ac: { watts: profile.ac, score: profile.power1m.value },
          map: { watts: profile.map, score: profile.power5m.value },
          ftp: { watts: profile.ftp, score: profile.power20m.value },
        },
        riderType: {
          name: profile.riderType.name,
          description: profile.riderType.description,
        },
        strengths: {
          name: profile.riderWeakness.strengthName,
          description: profile.riderWeakness.strengthDescription,
          summary: profile.riderWeakness.strengthSummary,
        },
        weaknesses: {
          name: profile.riderWeakness.name,
          description: profile.riderWeakness.weaknessDescription,
          summary: profile.riderWeakness.weaknessSummary,
        },
        lthr: profile.lactateThresholdHeartRate,
        heartRateZones: profile.heartRateZones,
        lastTestDate: formattedDate,
      },
      null,
      2
    );
  },
});

// Tool: schedule_workout
mcp.addTool({
  name: 'schedule_workout',
  description: 'Schedule a workout from the library to your calendar for a specific date.',
  parameters: z.object({
    content_id: z
      .string()
      .describe('Workout content ID from library search results (use the id field, not workoutId)'),
    date: z.string().describe('Date to schedule the workout (YYYY-MM-DD format)'),
    time_zone: z
      .string()
      .optional()
      .describe(
        'Timezone for the workout (default: UTC). Example: Europe/Lisbon, America/New_York'
      ),
  }),
  execute: async (args) => {
    ensureAuthenticated();
    const agendaId = await wahooClient.scheduleWorkout(
      args.content_id,
      args.date,
      args.time_zone || 'UTC'
    );
    return JSON.stringify(
      {
        success: true,
        agendaId,
        date: args.date,
        timezone: args.time_zone || 'UTC',
      },
      null,
      2
    );
  },
});

// Tool: reschedule_workout
mcp.addTool({
  name: 'reschedule_workout',
  description: 'Move a scheduled workout to a different date.',
  parameters: z.object({
    agenda_id: z.string().describe('Agenda ID from get_calendar or schedule_workout'),
    new_date: z.string().describe('New date for the workout (YYYY-MM-DD format)'),
    time_zone: z
      .string()
      .optional()
      .describe('Timezone for the rescheduled workout (default: UTC)'),
  }),
  execute: async (args) => {
    ensureAuthenticated();
    await wahooClient.rescheduleWorkout(args.agenda_id, args.new_date, args.time_zone || 'UTC');
    return JSON.stringify(
      {
        success: true,
        agendaId: args.agenda_id,
        newDate: args.new_date,
        timezone: args.time_zone || 'UTC',
        message: 'Workout rescheduled successfully',
      },
      null,
      2
    );
  },
});

// Tool: remove_workout
mcp.addTool({
  name: 'remove_workout',
  description: 'Remove a scheduled workout from your calendar.',
  parameters: z.object({
    agenda_id: z.string().describe('Agenda ID from get_calendar or schedule_workout'),
  }),
  execute: async (args) => {
    ensureAuthenticated();
    await wahooClient.removeWorkout(args.agenda_id);
    return JSON.stringify(
      {
        success: true,
        agendaId: args.agenda_id,
        message: 'Workout removed successfully',
      },
      null,
      2
    );
  },
});

// Tool: get_workouts
mcp.addTool({
  name: 'get_workouts',
  description:
    'Browse the complete workout library with advanced filtering for sport, duration, TSS, search terms, and sorting options. Returns workout metadata including duration, TSS, intensity, and 4DP ratings.',
  parameters: z.object({
    sport: z
      .enum(['Cycling', 'Running', 'Strength', 'Yoga', 'Swimming'])
      .optional()
      .describe('Filter by workout type'),
    search: z
      .string()
      .optional()
      .describe('Search workouts by name (case-insensitive partial match)'),
    min_duration: z.number().optional().describe('Minimum duration in minutes'),
    max_duration: z.number().optional().describe('Maximum duration in minutes'),
    min_tss: z.number().optional().describe('Minimum Training Stress Score'),
    max_tss: z.number().optional().describe('Maximum Training Stress Score'),
    channel: z
      .string()
      .optional()
      .describe(
        'Filter by content channel (The Sufferfest, Inspiration, Wahoo Fitness, A Week With, ProRides, On Location, NoVid, Fitness Test)'
      ),
    sort_by: z.enum(['name', 'duration', 'tss']).optional().describe('Sort field (default: name)'),
    sort_direction: z.enum(['asc', 'desc']).optional().describe('Sort order (default: asc)'),
    limit: z.number().optional().describe('Maximum number of results (default: 50)'),
  }),
  execute: async (args) => {
    ensureAuthenticated();

    const options: Parameters<typeof wahooClient.getWorkoutLibrary>[0] = {};
    if (args.sport) options.sport = args.sport;
    if (args.search) options.search = args.search;
    if (typeof args.min_duration === 'number') options.minDuration = args.min_duration * 60;
    if (typeof args.max_duration === 'number') options.maxDuration = args.max_duration * 60;
    if (typeof args.min_tss === 'number') options.minTss = args.min_tss;
    if (typeof args.max_tss === 'number') options.maxTss = args.max_tss;
    if (args.channel) options.channel = args.channel;
    if (args.sort_by) options.sortBy = args.sort_by;
    if (args.sort_direction) options.sortDirection = args.sort_direction;

    let workouts = await wahooClient.getWorkoutLibrary(options);

    // Apply limit after fetching (client doesn't support it directly)
    if (typeof args.limit === 'number') {
      workouts = workouts.slice(0, args.limit);
    }

    return JSON.stringify({ total: workouts.length, workouts }, null, 2);
  },
});

// Tool: get_cycling_workouts
mcp.addTool({
  name: 'get_cycling_workouts',
  description:
    'Specialized cycling workout search with filters for 4DP focus (NM/AC/MAP/FTP), channel, category, and intensity. Automatically filters for cycling workouts only.',
  parameters: z.object({
    search: z.string().optional().describe('Search by workout name'),
    min_duration: z.number().optional().describe('Minimum duration in minutes'),
    max_duration: z.number().optional().describe('Maximum duration in minutes'),
    min_tss: z.number().optional().describe('Minimum TSS'),
    max_tss: z.number().optional().describe('Maximum TSS'),
    channel: z
      .string()
      .optional()
      .describe(
        'Content channel: The Sufferfest, Inspiration, Wahoo Fitness, A Week With, ProRides, On Location, NoVid, Fitness Test'
      ),
    category: z
      .string()
      .optional()
      .describe(
        'Workout category: Endurance, Speed, Climbing, Sustained Efforts, Mixed, Technique & Drills, Racing, Active Recovery, Activation, The Knowledge, Overview, Cool Down, Fitness Test'
      ),
    four_dp_focus: z
      .enum(['NM', 'AC', 'MAP', 'FTP'])
      .optional()
      .describe('Primary 4DP energy system (rating >= 4)'),
    intensity: z.enum(['High', 'Medium', 'Low']).optional().describe('Intensity level'),
    sort_by: z.enum(['name', 'duration', 'tss']).optional().describe('Sort field'),
    sort_direction: z.enum(['asc', 'desc']).optional().describe('Sort order'),
    limit: z.number().optional().describe('Maximum results (default: 50)'),
  }),
  execute: async (args) => {
    ensureAuthenticated();

    const options: Parameters<typeof wahooClient.getCyclingWorkouts>[0] = {};
    if (args.search) options.search = args.search;
    if (typeof args.min_duration === 'number') options.minDuration = args.min_duration * 60;
    if (typeof args.max_duration === 'number') options.maxDuration = args.max_duration * 60;
    if (typeof args.min_tss === 'number') options.minTss = args.min_tss;
    if (typeof args.max_tss === 'number') options.maxTss = args.max_tss;
    if (args.channel) options.channel = args.channel;
    if (args.category) options.category = args.category;
    if (args.four_dp_focus) options.fourDpFocus = args.four_dp_focus;
    if (args.intensity) options.intensity = args.intensity;
    if (args.sort_by) options.sortBy = args.sort_by;
    if (args.sort_direction) options.sortDirection = args.sort_direction;
    if (typeof args.limit === 'number') options.limit = args.limit;

    let workouts = await wahooClient.getCyclingWorkouts(options);

    // Apply limit after fetching (client doesn't support it directly)
    if (typeof args.limit === 'number') {
      workouts = workouts.slice(0, args.limit);
    }

    return JSON.stringify({ total: workouts.length, workouts }, null, 2);
  },
});

// Tool: get_fitness_test_history
mcp.addTool({
  name: 'get_fitness_test_history',
  description:
    'Get history of completed Full Frontal and Half Monty fitness tests with 4DP results, rider type classification, and test dates.',
  parameters: z.object({
    page: z.number().optional().describe('Page number for pagination (default: 1)'),
    page_size: z.number().optional().describe('Results per page (default: 15)'),
  }),
  execute: async (args) => {
    ensureAuthenticated();

    const options: Parameters<typeof wahooClient.getFitnessTestHistory>[0] = {};
    if (typeof args.page === 'number') options.page = args.page;
    if (typeof args.page_size === 'number') options.pageSize = args.page_size;

    const result = await wahooClient.getFitnessTestHistory(options);

    const formattedTests = result.activities.map((test) => {
      const testDate = new Date(test.completedDate);
      const formattedDate = format(testDate, 'MMMM d, yyyy');

      const durationHours = test.durationSeconds / 3600;
      const hours = Math.floor(durationHours);
      const minutes = Math.round((durationHours - hours) * 60);

      return {
        id: test.id,
        name: test.name,
        date: formattedDate,
        duration: hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`,
        distance: `${test.distanceKm.toFixed(2)} km`,
        tss: test.tss,
        intensityFactor: test.intensityFactor,
        fourDP: test.testResults
          ? {
              nm: {
                watts: test.testResults.power5s.value,
                score: test.testResults.power5s.graphValue,
              },
              ac: {
                watts: test.testResults.power1m.value,
                score: test.testResults.power1m.graphValue,
              },
              map: {
                watts: test.testResults.power5m.value,
                score: test.testResults.power5m.graphValue,
              },
              ftp: {
                watts: test.testResults.power20m.value,
                score: test.testResults.power20m.graphValue,
              },
            }
          : null,
        lthr: test.testResults?.lactateThresholdHeartRate,
        riderType: test.testResults?.riderType.name,
      };
    });

    return JSON.stringify({ total: result.total, tests: formattedTests }, null, 2);
  },
});

// Tool: get_fitness_test_details
mcp.addTool({
  name: 'get_fitness_test_details',
  description:
    'Get detailed fitness test data including second-by-second power/cadence/heart rate, power curve bests, and post-test analysis.',
  parameters: z.object({
    activity_id: z.string().describe('Activity ID from get_fitness_test_history'),
  }),
  execute: async (args) => {
    ensureAuthenticated();

    const testDetails = await wahooClient.getFitnessTestDetails(args.activity_id);

    const testDate = new Date(testDetails.completedDate);
    const formattedDate = format(testDate, 'MMMM d, yyyy');

    const durationHours = testDetails.durationSeconds / 3600;
    const hours = Math.floor(durationHours);
    const minutes = Math.round((durationHours - hours) * 60);

    let analysisData = null;
    if (testDetails.analysis) {
      try {
        analysisData = JSON.parse(testDetails.analysis);
      } catch {
        analysisData = null;
      }
    }

    return JSON.stringify(
      {
        name: testDetails.name,
        date: formattedDate,
        duration: hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`,
        distance: `${testDetails.distanceKm.toFixed(2)} km`,
        tss: testDetails.tss,
        intensityFactor: testDetails.intensityFactor,
        notes: testDetails.notes,
        fourDP: testDetails.testResults
          ? {
              nm: {
                watts: testDetails.testResults.power5s.value,
                score: testDetails.testResults.power5s.graphValue,
              },
              ac: {
                watts: testDetails.testResults.power1m.value,
                score: testDetails.testResults.power1m.graphValue,
              },
              map: {
                watts: testDetails.testResults.power5m.value,
                score: testDetails.testResults.power5m.graphValue,
              },
              ftp: {
                watts: testDetails.testResults.power20m.value,
                score: testDetails.testResults.power20m.graphValue,
              },
            }
          : null,
        riderType: testDetails.testResults?.riderType.name,
        lthr: testDetails.testResults?.lactateThresholdHeartRate,
        activityData: {
          power: testDetails.power,
          cadence: testDetails.cadence,
          heartRate: testDetails.heartRate,
        },
        powerCurve: testDetails.powerBests,
        analysis: analysisData,
      },
      null,
      2
    );
  },
});

// Start the server
async function main() {
  await autoAuthenticate();
  mcp.start({ transportType: 'stdio' });
  console.error('Wahoo SYSTM MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error in main():', error);
  process.exit(1);
});
