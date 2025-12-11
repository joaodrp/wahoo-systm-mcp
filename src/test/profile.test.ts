import type { FastMCP } from 'fastmcp';

import { describe, expect, it, vi } from 'vitest';

import { WahooClient } from '../client.js';
import { registerProfileTools } from '../profile.js';

describe('Profile Tools', () => {
  it('should register all 3 profile/fitness tools', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerProfileTools(mockMcp, mockClient, mockEnsureAuth);

    expect(addToolMock).toHaveBeenCalledTimes(3);

    // Verify tool names
    const toolCalls = addToolMock.mock.calls as Array<[{ name: string }]>;
    const toolNames = toolCalls.map((call) => call[0].name);

    expect(toolNames).toContain('get_rider_profile');
    expect(toolNames).toContain('get_fitness_test_history');
    expect(toolNames).toContain('get_fitness_test_details');
  });

  it('should register all tools as read-only', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerProfileTools(mockMcp, mockClient, mockEnsureAuth);

    // All profile tools should be read-only
    (addToolMock.mock.calls as Array<[{ annotations?: { readOnlyHint?: boolean } }]>).forEach(
      (call) => {
        expect(call[0].annotations?.readOnlyHint).toBe(true);
      }
    );
  });

  it('should register get_rider_profile with correct configuration', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerProfileTools(mockMcp, mockClient, mockEnsureAuth);

    const profileTool = (
      addToolMock.mock.calls as Array<
        [{ annotations?: { title?: string }; description?: string; name: string }]
      >
    ).find((call) => call[0].name === 'get_rider_profile')?.[0];

    expect(profileTool).toBeDefined();
    expect(profileTool!.annotations!.title).toBe('Get Rider Profile');
    expect(profileTool!.description).toContain('4DP profile');
    expect(profileTool!.description).toContain('strengths/weaknesses');
  });

  it('should register fitness test tools with correct titles', () => {
    const addToolMock = vi.fn();
    const mockMcp = {
      addTool: addToolMock,
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerProfileTools(mockMcp, mockClient, mockEnsureAuth);

    const calls = addToolMock.mock.calls as Array<
      [{ annotations?: { title?: string }; name: string }]
    >;
    const historyTool = calls.find((call) => call[0].name === 'get_fitness_test_history')?.[0];

    const detailsTool = calls.find((call) => call[0].name === 'get_fitness_test_details')?.[0];

    expect(historyTool!.annotations!.title).toBe('Get Fitness Test History');
    expect(detailsTool!.annotations!.title).toBe('Get Fitness Test Details');
  });
});
