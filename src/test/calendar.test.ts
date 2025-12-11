import type { FastMCP } from 'fastmcp';

import { describe, expect, it, vi } from 'vitest';

import { registerCalendarTools } from '../calendar.js';
import { WahooClient } from '../client.js';

describe('Calendar Tools', () => {
  it('should register all 4 calendar tools', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerCalendarTools(mockMcp, mockClient, mockEnsureAuth);

    expect(addToolMock).toHaveBeenCalledTimes(4);

    // Verify tool names
    const toolCalls = addToolMock.mock.calls as Array<[{ name: string }]>;
    const toolNames = toolCalls.map((call) => call[0].name);

    expect(toolNames).toContain('get_calendar');
    expect(toolNames).toContain('schedule_workout');
    expect(toolNames).toContain('reschedule_workout');
    expect(toolNames).toContain('remove_workout');
  });

  it('should register get_calendar with correct annotations', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerCalendarTools(mockMcp, mockClient, mockEnsureAuth);

    const getCalendarTool = (
      addToolMock.mock.calls as Array<
        [{ annotations?: Record<string, unknown>; description?: string; name: string }]
      >
    ).find((call) => call[0].name === 'get_calendar')?.[0];

    expect(getCalendarTool).toBeDefined();
    expect(getCalendarTool!.annotations).toEqual({
      readOnlyHint: true,
      title: 'Get Calendar Workouts',
    });
    expect(getCalendarTool!.description).toContain('Get planned workouts');
  });

  it('should register write operations with destructive hints', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerCalendarTools(mockMcp, mockClient, mockEnsureAuth);

    const scheduleWorkoutTool = (
      addToolMock.mock.calls as Array<[{ annotations?: Record<string, unknown>; name: string }]>
    ).find((call) => call[0].name === 'schedule_workout')?.[0];

    expect(scheduleWorkoutTool!.annotations).toEqual({
      destructiveHint: true,
      readOnlyHint: false,
      title: 'Schedule Workout',
    });
  });

  it('should register idempotent operations correctly', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerCalendarTools(mockMcp, mockClient, mockEnsureAuth);

    const calls = addToolMock.mock.calls as Array<
      [{ annotations?: Record<string, unknown>; name: string }]
    >;
    const rescheduleTool = calls.find((call) => call[0].name === 'reschedule_workout')?.[0];

    expect(rescheduleTool!.annotations).toMatchObject({
      destructiveHint: true,
      idempotentHint: true,
      readOnlyHint: false,
    });

    const removeTool = calls.find((call) => call[0].name === 'remove_workout')?.[0];

    expect(removeTool!.annotations).toMatchObject({
      destructiveHint: true,
      idempotentHint: true,
      readOnlyHint: false,
    });
  });
});
