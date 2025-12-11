import type { FastMCP } from 'fastmcp';

import { z } from 'zod';

import type { WahooClient } from '../client.js';

/**
 * Register calendar management tools
 */
export const registerCalendarTools = (
  mcp: FastMCP,
  client: WahooClient,
  ensureAuth: () => void
) => {
  // Tool: get_calendar
  mcp.addTool({
    annotations: {
      readOnlyHint: true,
      title: 'Get Calendar Workouts',
    },
    description:
      'Get planned workouts from Wahoo SYSTM calendar for a date range. Returns workout name, type, duration, planned date, and basic details.',
    execute: async (args) => {
      ensureAuth();
      const workouts = await client.getCalendarWorkouts(args.start_date, args.end_date);
      return JSON.stringify(workouts, null, 2);
    },
    name: 'get_calendar',
    parameters: z.object({
      end_date: z.string().describe('End date in YYYY-MM-DD format'),
      start_date: z.string().describe('Start date in YYYY-MM-DD format'),
    }),
  });

  // Tool: schedule_workout
  mcp.addTool({
    annotations: {
      destructiveHint: true,
      readOnlyHint: false,
      title: 'Schedule Workout',
    },
    description: 'Schedule a workout from the library to your calendar for a specific date.',
    execute: async (args) => {
      ensureAuth();
      const agendaId = await client.scheduleWorkout(
        args.content_id,
        args.date,
        args.time_zone || 'UTC'
      );
      return JSON.stringify(
        {
          agendaId,
          date: args.date,
          success: true,
          timezone: args.time_zone || 'UTC',
        },
        null,
        2
      );
    },
    name: 'schedule_workout',
    parameters: z.object({
      content_id: z
        .string()
        .describe(
          'Workout content ID from library search results (use the id field, not workoutId)'
        ),
      date: z.string().describe('Date to schedule the workout (YYYY-MM-DD format)'),
      time_zone: z
        .string()
        .optional()
        .describe(
          'Timezone for the workout (default: UTC). Example: Europe/Lisbon, America/New_York'
        ),
    }),
  });

  // Tool: reschedule_workout
  mcp.addTool({
    annotations: {
      destructiveHint: true,
      idempotentHint: true,
      readOnlyHint: false,
      title: 'Reschedule Workout',
    },
    description: 'Move a scheduled workout to a different date.',
    execute: async (args) => {
      ensureAuth();
      await client.rescheduleWorkout(args.agenda_id, args.new_date, args.time_zone || 'UTC');
      return JSON.stringify(
        {
          agendaId: args.agenda_id,
          message: 'Workout rescheduled successfully',
          newDate: args.new_date,
          success: true,
          timezone: args.time_zone || 'UTC',
        },
        null,
        2
      );
    },
    name: 'reschedule_workout',
    parameters: z.object({
      agenda_id: z.string().describe('Agenda ID from get_calendar or schedule_workout'),
      new_date: z.string().describe('New date for the workout (YYYY-MM-DD format)'),
      time_zone: z
        .string()
        .optional()
        .describe('Timezone for the rescheduled workout (default: UTC)'),
    }),
  });

  // Tool: remove_workout
  mcp.addTool({
    annotations: {
      destructiveHint: true,
      idempotentHint: true,
      readOnlyHint: false,
      title: 'Remove Workout',
    },
    description: 'Remove a scheduled workout from your calendar.',
    execute: async (args) => {
      ensureAuth();
      await client.removeWorkout(args.agenda_id);
      return JSON.stringify(
        {
          agendaId: args.agenda_id,
          message: 'Workout removed successfully',
          success: true,
        },
        null,
        2
      );
    },
    name: 'remove_workout',
    parameters: z.object({
      agenda_id: z.string().describe('Agenda ID from get_calendar or schedule_workout'),
    }),
  });
};
