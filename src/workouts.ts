import type { FastMCP } from 'fastmcp';

import { z } from 'zod';

import type { WahooClient } from '../client.js';

/**
 * Register workout library tools
 */
export const registerWorkoutTools = (mcp: FastMCP, client: WahooClient, ensureAuth: () => void) => {
  // Tool: get_workouts
  mcp.addTool({
    annotations: {
      readOnlyHint: true,
      title: 'Browse Workout Library',
    },
    description:
      'Browse the complete workout library with advanced filtering for sport, duration, TSS, search terms, and sorting options. Returns workout metadata including duration, TSS, intensity, and 4DP ratings.',
    execute: async (args) => {
      ensureAuth();

      const options: Parameters<typeof client.getWorkoutLibrary>[0] = {};
      if (args.sport) options.sport = args.sport;
      if (args.search) options.search = args.search;
      if (typeof args.min_duration === 'number') options.minDuration = args.min_duration * 60;
      if (typeof args.max_duration === 'number') options.maxDuration = args.max_duration * 60;
      if (typeof args.min_tss === 'number') options.minTss = args.min_tss;
      if (typeof args.max_tss === 'number') options.maxTss = args.max_tss;
      if (args.channel) options.channel = args.channel;
      if (args.sort_by) options.sortBy = args.sort_by;
      if (args.sort_direction) options.sortDirection = args.sort_direction;

      let workouts = await client.getWorkoutLibrary(options);

      // Apply limit after fetching (client doesn't support it directly)
      if (typeof args.limit === 'number') {
        workouts = workouts.slice(0, args.limit);
      }

      return JSON.stringify({ total: workouts.length, workouts }, null, 2);
    },
    name: 'get_workouts',
    parameters: z.object({
      channel: z
        .string()
        .optional()
        .describe(
          'Filter by content channel (The Sufferfest, Inspiration, Wahoo Fitness, A Week With, ProRides, On Location, NoVid, Fitness Test)'
        ),
      limit: z.number().optional().describe('Maximum number of results (default: 50)'),
      max_duration: z.number().optional().describe('Maximum duration in minutes'),
      max_tss: z.number().optional().describe('Maximum Training Stress Score'),
      min_duration: z.number().optional().describe('Minimum duration in minutes'),
      min_tss: z.number().optional().describe('Minimum Training Stress Score'),
      search: z
        .string()
        .optional()
        .describe('Search workouts by name (case-insensitive partial match)'),
      sort_by: z
        .enum(['name', 'duration', 'tss'])
        .optional()
        .describe('Sort field (default: name)'),
      sort_direction: z.enum(['asc', 'desc']).optional().describe('Sort order (default: asc)'),
      sport: z
        .enum(['Cycling', 'Running', 'Strength', 'Yoga', 'Swimming'])
        .optional()
        .describe('Filter by workout type'),
    }),
  });

  // Tool: get_cycling_workouts
  mcp.addTool({
    annotations: {
      readOnlyHint: true,
      title: 'Browse Cycling Workouts',
    },
    description:
      'Specialized cycling workout search with filters for 4DP focus (NM/AC/MAP/FTP), channel, category, and intensity. Automatically filters for cycling workouts only.',
    execute: async (args) => {
      ensureAuth();

      const options: Parameters<typeof client.getCyclingWorkouts>[0] = {};
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

      let workouts = await client.getCyclingWorkouts(options);

      // Apply limit after fetching (client doesn't support it directly)
      if (typeof args.limit === 'number') {
        workouts = workouts.slice(0, args.limit);
      }

      return JSON.stringify({ total: workouts.length, workouts }, null, 2);
    },
    name: 'get_cycling_workouts',
    parameters: z.object({
      category: z
        .string()
        .optional()
        .describe(
          'Workout category: Endurance, Speed, Climbing, Sustained Efforts, Mixed, Technique & Drills, Racing, Active Recovery, Activation, The Knowledge, Overview, Cool Down, Fitness Test'
        ),
      channel: z
        .string()
        .optional()
        .describe(
          'Content channel: The Sufferfest, Inspiration, Wahoo Fitness, A Week With, ProRides, On Location, NoVid, Fitness Test'
        ),
      four_dp_focus: z
        .enum(['NM', 'AC', 'MAP', 'FTP'])
        .optional()
        .describe('Primary 4DP energy system (rating >= 4)'),
      intensity: z.enum(['High', 'Medium', 'Low']).optional().describe('Intensity level'),
      limit: z.number().optional().describe('Maximum results (default: 50)'),
      max_duration: z.number().optional().describe('Maximum duration in minutes'),
      max_tss: z.number().optional().describe('Maximum TSS'),
      min_duration: z.number().optional().describe('Minimum duration in minutes'),
      min_tss: z.number().optional().describe('Minimum TSS'),
      search: z.string().optional().describe('Search by workout name'),
      sort_by: z.enum(['name', 'duration', 'tss']).optional().describe('Sort field'),
      sort_direction: z.enum(['asc', 'desc']).optional().describe('Sort order'),
    }),
  });

  // Tool: get_workout_details
  mcp.addTool({
    annotations: {
      readOnlyHint: true,
      title: 'Get Workout Details',
    },
    description:
      'Get detailed information about a specific workout including intervals, power zones, equipment needed, and full workout structure.',
    execute: async (args) => {
      ensureAuth();
      const details = await client.getWorkoutDetails(args.workout_id);
      return JSON.stringify(details, null, 2);
    },
    name: 'get_workout_details',
    parameters: z.object({
      workout_id: z
        .string()
        .describe('Workout ID from calendar or library (accepts both id and workoutId)'),
    }),
  });
};
