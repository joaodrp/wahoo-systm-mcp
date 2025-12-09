import './setup.js';
import { test, describe } from 'node:test';
import assert from 'node:assert';
import { WahooClient } from '../wahoo-client.js';

describe('WahooClient', () => {
  test('should create client instance', () => {
    const client = new WahooClient();
    assert.ok(client);
  });

  test('should throw error when not authenticated', async () => {
    const client = new WahooClient();
    await assert.rejects(
      () => client.getCalendarWorkouts('2025-01-01', '2025-01-31'),
      /Not authenticated/
    );
  });

  test('should authenticate with valid credentials', async () => {
    const client = new WahooClient();
    const username = process.env.WAHOO_USERNAME || process.env.TEST_WAHOO_USERNAME;
    const password = process.env.WAHOO_PASSWORD || process.env.TEST_WAHOO_PASSWORD;

    if (!username || !password) {
      console.log('Skipping authentication test - no credentials provided');
      return;
    }

    await client.authenticate({ username, password });
    const profile = client.getRiderProfile();
    assert.ok(profile);
    assert.ok(typeof profile.ftp === 'number');
  });

  test('should get calendar workouts after authentication', async () => {
    const client = new WahooClient();
    const username = process.env.WAHOO_USERNAME || process.env.TEST_WAHOO_USERNAME;
    const password = process.env.WAHOO_PASSWORD || process.env.TEST_WAHOO_PASSWORD;

    if (!username || !password) {
      console.log('Skipping calendar test - no credentials provided');
      return;
    }

    await client.authenticate({ username, password });
    const workouts = await client.getCalendarWorkouts('2025-12-01', '2025-12-31');
    assert.ok(Array.isArray(workouts));
  });
});
