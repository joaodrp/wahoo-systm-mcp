#!/usr/bin/env node

import { FastMCP, UserError } from 'fastmcp';

import { registerCalendarTools } from './calendar.js';
import { WahooClient } from './client.js';
import { getCredentialsFrom1Password } from './onepassword.js';
import { registerProfileTools } from './profile.js';
import { registerWorkoutTools } from './workouts.js';

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
        password: PLAIN_PASSWORD,
        username: PLAIN_USERNAME,
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

// Register all MCP tools
registerCalendarTools(mcp, wahooClient, ensureAuthenticated);
registerWorkoutTools(mcp, wahooClient, ensureAuthenticated);
registerProfileTools(mcp, wahooClient, ensureAuthenticated);

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
