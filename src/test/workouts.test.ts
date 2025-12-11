import type { FastMCP } from 'fastmcp';

import { describe, expect, it, vi } from 'vitest';

import { WahooClient } from '../client.js';
import { registerWorkoutTools } from '../workouts.js';

describe('Workout Tools', () => {
  it('should register all 3 workout library tools', () => {
    const mockMcp = {
      addTool: vi.fn(),
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerWorkoutTools(mockMcp, mockClient, mockEnsureAuth);

    expect(mockMcp.addTool).toHaveBeenCalledTimes(3);

    // Verify tool names
    const toolCalls = mockMcp.addTool.mock.calls;
    const toolNames = toolCalls.map((call) => call[0].name);

    expect(toolNames).toContain('get_workouts');
    expect(toolNames).toContain('get_cycling_workouts');
    expect(toolNames).toContain('get_workout_details');
  });

  it('should register all tools as read-only', () => {
    const mockMcp = {
      addTool: vi.fn(),
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerWorkoutTools(mockMcp, mockClient, mockEnsureAuth);

    // All workout tools should be read-only
    mockMcp.addTool.mock.calls.forEach((call) => {
      expect(call[0].annotations.readOnlyHint).toBe(true);
    });
  });

  it('should register get_workouts with correct configuration', () => {
    const mockMcp = {
      addTool: vi.fn(),
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerWorkoutTools(mockMcp, mockClient, mockEnsureAuth);

    const getWorkoutsTool = mockMcp.addTool.mock.calls.find(
      (call) => call[0].name === 'get_workouts'
    )?.[0];

    expect(getWorkoutsTool).toBeDefined();
    expect(getWorkoutsTool.annotations.title).toBe('Browse Workout Library');
    expect(getWorkoutsTool.description).toContain('Browse the complete workout library');
  });

  it('should register get_cycling_workouts with 4DP focus support', () => {
    const mockMcp = {
      addTool: vi.fn(),
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerWorkoutTools(mockMcp, mockClient, mockEnsureAuth);

    const cyclingTool = mockMcp.addTool.mock.calls.find(
      (call) => call[0].name === 'get_cycling_workouts'
    )?.[0];

    expect(cyclingTool).toBeDefined();
    expect(cyclingTool.description).toContain('4DP focus');
    expect(cyclingTool.annotations.title).toBe('Browse Cycling Workouts');
  });
});
