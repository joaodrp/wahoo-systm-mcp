import type { FastMCP } from 'fastmcp';

import { describe, expect, it, vi } from 'vitest';

import { WahooClient } from '../client.js';
import { registerWorkoutTools } from '../workouts.js';

describe('Workout Tools', () => {
  it('should register all 3 workout library tools', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerWorkoutTools(mockMcp, mockClient, mockEnsureAuth);

    expect(addToolMock).toHaveBeenCalledTimes(3);

    // Verify tool names
    const toolCalls = addToolMock.mock.calls as Array<[{ name: string }]>;
    const toolNames = toolCalls.map((call) => call[0].name);

    expect(toolNames).toContain('get_workouts');
    expect(toolNames).toContain('get_cycling_workouts');
    expect(toolNames).toContain('get_workout_details');
  });

  it('should register all tools as read-only', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerWorkoutTools(mockMcp, mockClient, mockEnsureAuth);

    // All workout tools should be read-only
    (addToolMock.mock.calls as Array<[{ annotations?: { readOnlyHint?: boolean } }]>).forEach(
      (call) => {
        expect(call[0].annotations?.readOnlyHint).toBe(true);
      }
    );
  });

  it('should register get_workouts with correct configuration', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerWorkoutTools(mockMcp, mockClient, mockEnsureAuth);

    const getWorkoutsTool = (
      addToolMock.mock.calls as Array<
        [{ annotations?: { title?: string }; description?: string; name: string }]
      >
    ).find((call) => call[0].name === 'get_workouts')?.[0];

    expect(getWorkoutsTool).toBeDefined();
    expect(getWorkoutsTool!.annotations!.title).toBe('Browse Workout Library');
    expect(getWorkoutsTool!.description).toContain('Browse the complete workout library');
  });

  it('should register get_cycling_workouts with 4DP focus support', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerWorkoutTools(mockMcp, mockClient, mockEnsureAuth);

    const cyclingTool = (
      addToolMock.mock.calls as Array<
        [{ annotations?: { title?: string }; description?: string; name: string }]
      >
    ).find((call) => call[0].name === 'get_cycling_workouts')?.[0];

    expect(cyclingTool).toBeDefined();
    expect(cyclingTool!.description).toContain('4DP focus');
    expect(cyclingTool!.annotations!.title).toBe('Browse Cycling Workouts');
  });
});
