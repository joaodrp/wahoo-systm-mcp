import type { FastMCP } from 'fastmcp';

import { describe, expect, it, vi } from 'vitest';

import { WahooClient } from '../client.js';
import { registerProfileTools } from '../profile.js';

describe('Profile Tools', () => {
  it('should register all 3 profile/fitness tools', () => {
    const mockMcp = {
      addTool: vi.fn(),
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerProfileTools(mockMcp, mockClient, mockEnsureAuth);

    expect(mockMcp.addTool).toHaveBeenCalledTimes(3);

    // Verify tool names
    const toolCalls = mockMcp.addTool.mock.calls;
    const toolNames = toolCalls.map((call) => call[0].name);

    expect(toolNames).toContain('get_rider_profile');
    expect(toolNames).toContain('get_fitness_test_history');
    expect(toolNames).toContain('get_fitness_test_details');
  });

  it('should register all tools as read-only', () => {
    const mockMcp = {
      addTool: vi.fn(),
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerProfileTools(mockMcp, mockClient, mockEnsureAuth);

    // All profile tools should be read-only
    mockMcp.addTool.mock.calls.forEach((call) => {
      expect(call[0].annotations.readOnlyHint).toBe(true);
    });
  });

  it('should register get_rider_profile with correct configuration', () => {
    const mockMcp = {
      addTool: vi.fn(),
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerProfileTools(mockMcp, mockClient, mockEnsureAuth);

    const profileTool = mockMcp.addTool.mock.calls.find(
      (call) => call[0].name === 'get_rider_profile'
    )?.[0];

    expect(profileTool).toBeDefined();
    expect(profileTool.annotations.title).toBe('Get Rider Profile');
    expect(profileTool.description).toContain('4DP profile');
    expect(profileTool.description).toContain('strengths/weaknesses');
  });

  it('should register fitness test tools with correct titles', () => {
    const mockMcp = {
      addTool: vi.fn(),
    } as unknown as FastMCP;
    const mockClient = {} as WahooClient;
    const mockEnsureAuth = vi.fn();

    registerProfileTools(mockMcp, mockClient, mockEnsureAuth);

    const historyTool = mockMcp.addTool.mock.calls.find(
      (call) => call[0].name === 'get_fitness_test_history'
    )?.[0];

    const detailsTool = mockMcp.addTool.mock.calls.find(
      (call) => call[0].name === 'get_fitness_test_details'
    )?.[0];

    expect(historyTool.annotations.title).toBe('Get Fitness Test History');
    expect(detailsTool.annotations.title).toBe('Get Fitness Test Details');
  });
});
