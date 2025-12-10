import './setup.js';
import { test, describe, expect } from 'vitest';

import { WahooClient } from '../client.js';
import { getCredentialsFrom1Password } from '../onepassword.js';

describe('Integration Tests', () => {
  test('should authenticate via 1Password and fetch calendar', async () => {
    const usernameRef = process.env.WAHOO_USERNAME_1P_REF;
    const passwordRef = process.env.WAHOO_PASSWORD_1P_REF;

    if (!usernameRef || !passwordRef) {
      console.log('Skipping integration test - no 1Password references provided');
      return;
    }

    // Get credentials from 1Password
    const credentials = await getCredentialsFrom1Password(usernameRef, passwordRef);
    expect(credentials.username).toBeTruthy();
    expect(credentials.password).toBeTruthy();

    // Authenticate with Wahoo SYSTM
    const client = new WahooClient();
    await client.authenticate(credentials);

    // Get rider profile
    const profile = client.getRiderProfile();
    expect(profile).toBeTruthy();
    if (!profile) return;
    expect(typeof profile.ftp === 'number').toBeTruthy();
    expect(typeof profile.map === 'number').toBeTruthy();
    expect(typeof profile.ac === 'number').toBeTruthy();
    expect(typeof profile.nm === 'number').toBeTruthy();

    // Get calendar workouts
    const today = new Date();
    const endDate = new Date(today);
    endDate.setDate(endDate.getDate() + 7);

    const startDateStr = today.toISOString().split('T')[0];
    const endDateStr = endDate.toISOString().split('T')[0];

    const workouts = await client.getCalendarWorkouts(startDateStr, endDateStr);
    expect(Array.isArray(workouts)).toBe(true);

    console.log(`✓ Found ${workouts.length} workouts in the next week`);
    console.log(
      `✓ 4DP Profile - FTP: ${profile.ftp}W, MAP: ${profile.map}W, AC: ${profile.ac}W, NM: ${profile.nm}W`
    );
  });

  test('should handle workouts without plans', async () => {
    const usernameRef = process.env.WAHOO_USERNAME_1P_REF;
    const passwordRef = process.env.WAHOO_PASSWORD_1P_REF;

    if (!usernameRef || !passwordRef) {
      console.log('Skipping plan test - no 1Password references provided');
      return;
    }

    const credentials = await getCredentialsFrom1Password(usernameRef, passwordRef);
    const client = new WahooClient();
    await client.authenticate(credentials);

    const workouts = await client.getCalendarWorkouts('2025-12-01', '2025-12-31');

    // Verify we can handle workouts with and without plans
    for (const workout of workouts) {
      if (workout.plannedDate && workout.prospects.length > 0) {
        expect(workout.agendaId).toBeTruthy(); // agendaId should be present;
        expect(workout.prospects[0].name).toBeTruthy();
        // Plan can be null, that's OK
        if (workout.plan) {
          expect(workout.plan.name).toBeTruthy();
        }
      }
    }

    console.log(
      `✓ Successfully processed ${workouts.length} workouts (including those without plans)`
    );
  });
});
