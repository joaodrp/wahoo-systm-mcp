import './setup.js';
import { addDays, format } from 'date-fns';
import { describe, expect, test } from 'vitest';

import { WahooClient } from '../client.js';

async function createAuthenticatedClient(): Promise<WahooClient> {
  const { password, username } = getTestCredentials();

  if (!username || !password) {
    throw new Error('Credentials not available');
  }

  const client = new WahooClient();
  await client.authenticate({ password, username });
  return client;
}

// Test helpers
function getTestCredentials() {
  return {
    password: process.env.WAHOO_PASSWORD || process.env.TEST_WAHOO_PASSWORD,
    username: process.env.WAHOO_USERNAME || process.env.TEST_WAHOO_USERNAME,
  };
}

function hasCredentials() {
  const { password, username } = getTestCredentials();
  return !!(username && password);
}

function skipIfNoCredentials(testName: string) {
  if (!hasCredentials()) {
    console.log(`Skipping ${testName} - no credentials provided`);
    return true;
  }
  return false;
}

describe('WahooClient', () => {
  test('should create client instance', () => {
    const client = new WahooClient();
    expect(client).toBeTruthy();
  });

  test('should throw error when not authenticated', async () => {
    const client = new WahooClient();
    await expect(() => client.getCalendarWorkouts('2025-01-01', '2025-01-31')).rejects.toThrow(
      /Not authenticated/
    );
  });

  describe('Authentication', () => {
    test('should authenticate with valid credentials', async () => {
      if (skipIfNoCredentials('authentication test')) return;

      const client = await createAuthenticatedClient();
      const profile = client.getRiderProfile();
      expect(profile).toBeTruthy();
      if (!profile) return;
      expect(typeof profile.ftp === 'number').toBeTruthy();
    });
  });

  describe('getRiderProfile()', () => {
    test('should return null when not authenticated', () => {
      const client = new WahooClient();
      const profile = client.getRiderProfile();
      expect(profile).toBe(null);
    });

    test('should return 4DP profile after authentication', async () => {
      if (skipIfNoCredentials('profile test')) return;

      const client = await createAuthenticatedClient();
      const profile = client.getRiderProfile();

      expect(profile).toBeTruthy();
      if (!profile) return;
      expect(typeof profile.ftp === 'number').toBeTruthy();
      expect(typeof profile.map === 'number').toBeTruthy();
      expect(typeof profile.ac === 'number').toBeTruthy();
      expect(typeof profile.nm === 'number').toBeTruthy();
      expect(profile.ftp > 0).toBeTruthy();
      expect(profile.map > 0).toBeTruthy();
      expect(profile.ac > 0).toBeTruthy();
      expect(profile.nm > 0).toBeTruthy();
    });
  });

  describe('getCalendarWorkouts()', () => {
    test('should throw error when not authenticated', async () => {
      const client = new WahooClient();
      await expect(() => client.getCalendarWorkouts('2025-01-01', '2025-01-31')).rejects.toThrow(
        /Not authenticated/
      );
    });

    test('should get calendar workouts after authentication', async () => {
      if (skipIfNoCredentials('calendar test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getCalendarWorkouts('2025-12-01', '2025-12-31');

      expect(Array.isArray(workouts)).toBeTruthy();

      if (workouts.length > 0) {
        const workout = workouts[0];
        expect(typeof workout.day === 'number').toBeTruthy();
        expect(typeof workout.plannedDate === 'string').toBeTruthy();
        expect(typeof workout.agendaId === 'string').toBeTruthy(); // agendaId should be a string;
        expect(typeof workout.status === 'string').toBeTruthy();
        expect(Array.isArray(workout.prospects)).toBeTruthy();
      }
    });
  });

  describe('getWorkoutDetails()', () => {
    test('should throw error when not authenticated', async () => {
      const client = new WahooClient();
      await expect(client.getWorkoutDetails('some-workout-id')).rejects.toThrow(
        /Not authenticated/
      );
    });

    test('should get workout details after authentication', async () => {
      if (skipIfNoCredentials('workout details test')) return;

      const client = await createAuthenticatedClient();

      // Get a workout from the library first
      const library = await client.getWorkoutLibrary({ sport: 'Cycling' });
      expect(library.length > 0).toBeTruthy(); // Should have at least one cycling workout;

      const workoutId = library[0].workoutId;
      const details = await client.getWorkoutDetails(workoutId);

      expect(details).toBeTruthy();
      expect(typeof details.id === 'string').toBeTruthy();
      expect(typeof details.name === 'string').toBeTruthy();
      expect(typeof details.sport === 'string').toBeTruthy();
      expect(typeof details.durationSeconds === 'number').toBeTruthy();
      expect(typeof details.triggers === 'string').toBeTruthy();
    });

    test('should accept both content ID and workout ID', async () => {
      if (skipIfNoCredentials('workout details with content ID test')) return;

      const client = await createAuthenticatedClient();

      // Get a workout from the library
      const library = await client.getWorkoutLibrary({ sport: 'Cycling' });
      expect(library.length > 0).toBeTruthy(); // Should have at least one cycling workout;

      const workout = library[0];

      // Test with workoutId (should work directly)
      const detailsByWorkoutId = await client.getWorkoutDetails(workout.workoutId);
      expect(detailsByWorkoutId).toBeTruthy();
      expect(detailsByWorkoutId.name).toBeTruthy(); // Should have a name;

      // Test with content ID (should look it up and still work)
      const detailsByContentId = await client.getWorkoutDetails(workout.id);
      expect(detailsByContentId).toBeTruthy();
      expect(detailsByContentId.name).toBeTruthy(); // Should have a name;

      // Both should return the same workout (by ID)
      expect(detailsByWorkoutId.id).toBe(detailsByContentId.id);
      // NOTE: We don't check name equality with library.name because the API
      // returns different names from library vs details endpoints (see Known Limitations)
    });

    test('should include descriptions from library', async () => {
      if (skipIfNoCredentials('workout details descriptions test')) return;

      const client = await createAuthenticatedClient();

      // Get a workout from the library that has descriptions
      const library = await client.getWorkoutLibrary({ sport: 'Cycling' });
      const workoutWithDesc = library.find((w) => w.descriptions && w.descriptions.length > 0);

      if (!workoutWithDesc) {
        // If no workout has descriptions, skip this test
        console.log('Skipping descriptions test - no workouts with descriptions found');
        return;
      }

      // Get the workout details
      const details = await client.getWorkoutDetails(workoutWithDesc.workoutId);

      // Verify descriptions are included
      expect(details.descriptions).toBeTruthy(); // Should have descriptions array;
      expect(Array.isArray(details.descriptions), 'Descriptions should be an array').toBeTruthy();
      expect(details.descriptions?.length).toBeGreaterThan(0); // Should have at least one description;

      // Verify description structure
      const desc = details.descriptions?.[0];
      expect(typeof desc?.title === 'string').toBeTruthy(); // Description should have title;
      expect(typeof desc?.body === 'string').toBeTruthy(); // Description should have body;
      expect(desc?.body?.length).toBeGreaterThan(0); // Description body should not be empty;

      // Verify it matches the library description
      expect(details.descriptions).toEqual(workoutWithDesc.descriptions); // Descriptions from details should match library descriptions;
    });
  });

  describe('getWorkoutLibrary()', () => {
    test('should throw error when not authenticated', async () => {
      const client = new WahooClient();
      await expect(client.getWorkoutLibrary()).rejects.toThrow(/Not authenticated/);
    });

    test('should get all workouts when no filters provided', async () => {
      if (skipIfNoCredentials('library test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary();

      expect(Array.isArray(workouts)).toBeTruthy();
      expect(workouts.length > 0).toBeTruthy();

      const workout = workouts[0];
      expect(typeof workout.id === 'string').toBeTruthy();
      expect(typeof workout.name === 'string').toBeTruthy();
      expect(typeof workout.workoutType === 'string').toBeTruthy();
      expect(typeof workout.duration === 'number').toBeTruthy();
      expect(typeof workout.workoutId === 'string').toBeTruthy();
    });

    test('should filter by sport', async () => {
      if (skipIfNoCredentials('sport filter test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({ sport: 'Cycling' });

      expect(workouts.length > 0).toBeTruthy();
      expect(workouts.every((w) => w.workoutType === 'Cycling')).toBeTruthy();
    });

    test('should filter by max duration', async () => {
      if (skipIfNoCredentials('duration filter test')) return;

      const client = await createAuthenticatedClient();
      const maxDurationMinutes = 30;
      const maxDurationSeconds = maxDurationMinutes * 60;
      const workouts = await client.getWorkoutLibrary({
        maxDuration: maxDurationMinutes,
        sport: 'Cycling',
      });

      expect(workouts.length > 0).toBeTruthy();
      expect(workouts.every((w) => w.duration <= maxDurationSeconds)).toBeTruthy();
    });

    test('should filter by TSS range', async () => {
      if (skipIfNoCredentials('TSS filter test')) return;

      const client = await createAuthenticatedClient();
      const minTss = 40;
      const maxTss = 60;
      const workouts = await client.getWorkoutLibrary({
        maxTss,
        minTss,
        sport: 'Cycling',
      });

      expect(workouts.length > 0).toBeTruthy();
      expect(
        workouts.every(
          (w) => w.metrics?.tss !== undefined && w.metrics.tss >= minTss && w.metrics.tss <= maxTss
        )
      ).toBeTruthy();
    });

    test('should filter by channel using human-readable name', async () => {
      if (skipIfNoCredentials('channel filter test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        channel: 'On Location',
        sport: 'Cycling',
      });

      expect(workouts.length > 0).toBeTruthy(); // Should find On Location workouts;
      // All workouts should have the human-readable channel name, not the ID
      workouts.forEach((w) => {
        expect(w.channel, 'Channel should be human-readable name').toBe('On Location');
      });
    });

    test('should search workouts by name', async () => {
      if (skipIfNoCredentials('search test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        search: 'Hammer',
        sport: 'Cycling',
      });

      expect(workouts.length > 0).toBeTruthy(); // Should find workouts with "Hammer" in name;
      workouts.forEach((w) => {
        expect(
          w.name.toLowerCase().includes('hammer'),
          `Workout "${w.name}" should contain "Hammer"`
        ).toBeTruthy();
      });
    });

    test('should sort by name ascending', async () => {
      if (skipIfNoCredentials('sort by name test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        sortBy: 'name',
        sortDirection: 'asc',
        sport: 'Cycling',
      });

      expect(workouts.length > 1).toBeTruthy();

      for (let i = 1; i < Math.min(10, workouts.length); i++) {
        expect(
          workouts[i].name.localeCompare(workouts[i - 1].name) >= 0,
          `Expected ${workouts[i].name} >= ${workouts[i - 1].name}`
        ).toBeTruthy();
      }
    });

    test('should sort by duration descending', async () => {
      if (skipIfNoCredentials('sort by duration test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        sortBy: 'duration',
        sortDirection: 'desc',
        sport: 'Cycling',
      });

      expect(workouts.length > 1).toBeTruthy();

      for (let i = 1; i < Math.min(10, workouts.length); i++) {
        expect(workouts[i].duration <= workouts[i - 1].duration).toBeTruthy();
      }
    });

    test('should sort by TSS ascending', async () => {
      if (skipIfNoCredentials('sort by TSS test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        sortBy: 'tss',
        sortDirection: 'asc',
        sport: 'Cycling',
      });

      expect(workouts.length > 1).toBeTruthy();

      for (let i = 1; i < Math.min(10, workouts.length); i++) {
        const currentTss = workouts[i].metrics?.tss ?? 0;
        const previousTss = workouts[i - 1].metrics?.tss ?? 0;
        expect(currentTss >= previousTss).toBeTruthy();
      }
    });

    test('should sort by level for strength workouts', async () => {
      if (skipIfNoCredentials('sort by level test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        sortBy: 'level',
        sortDirection: 'asc',
        sport: 'Strength',
      });

      expect(workouts.length > 0).toBeTruthy();

      // Check that levels are ordered correctly where present
      const levelOrder = { Advanced: 3, Basic: 1, Intermediate: 2 };
      for (let i = 1; i < Math.min(10, workouts.length); i++) {
        if (workouts[i].level && workouts[i - 1].level) {
          const currentLevel = levelOrder[workouts[i].level as keyof typeof levelOrder] || 0;
          const previousLevel = levelOrder[workouts[i - 1].level as keyof typeof levelOrder] || 0;
          expect(currentLevel >= previousLevel).toBeTruthy();
        }
      }
    });

    test('should combine multiple filters', async () => {
      if (skipIfNoCredentials('combined filters test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        maxDuration: 60,
        maxTss: 50,
        minTss: 30,
        sortBy: 'tss',
        sortDirection: 'asc',
        sport: 'Cycling',
      });

      expect(workouts.length > 0).toBeTruthy();

      // Verify all filters are applied
      workouts.forEach((w) => {
        expect(w.workoutType).toBe('Cycling');
        expect(w.duration <= 60 * 60).toBeTruthy(); // 60 minutes
        if (w.metrics?.tss) {
          expect(w.metrics.tss >= 30).toBeTruthy();
          expect(w.metrics.tss <= 50).toBeTruthy();
        }
      });

      // Verify sorting
      for (let i = 1; i < Math.min(5, workouts.length); i++) {
        const currentTss = workouts[i].metrics?.tss ?? 0;
        const previousTss = workouts[i - 1].metrics?.tss ?? 0;
        expect(currentTss >= previousTss).toBeTruthy();
      }
    });
  });

  describe('getCyclingWorkouts()', () => {
    test('should throw error when not authenticated', async () => {
      const client = new WahooClient();
      await expect(client.getCyclingWorkouts()).rejects.toThrow(/Not authenticated/);
    });

    test('should get all cycling workouts', async () => {
      if (skipIfNoCredentials('get all cycling workouts test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getCyclingWorkouts();

      expect(workouts.length > 0).toBeTruthy();
      expect(workouts[0].workoutType).toBe('Cycling');
    });

    test('should filter by 4DP focus - FTP', async () => {
      if (skipIfNoCredentials('FTP focus test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getCyclingWorkouts({ fourDpFocus: 'FTP' });

      expect(workouts.length > 0).toBeTruthy();
      workouts.forEach((w) => {
        expect(w.metrics?.ratings?.ftp !== undefined).toBeTruthy();
        if (w.metrics?.ratings?.ftp !== undefined) {
          expect(w.metrics.ratings.ftp >= 4).toBeTruthy();
        }
      });
    });

    test('should filter by 4DP focus - MAP', async () => {
      if (skipIfNoCredentials('MAP focus test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getCyclingWorkouts({ fourDpFocus: 'MAP' });

      expect(workouts.length > 0).toBeTruthy();
      workouts.forEach((w) => {
        expect(w.metrics?.ratings?.map !== undefined).toBeTruthy();
        if (w.metrics?.ratings?.map !== undefined) {
          expect(w.metrics.ratings.map >= 4).toBeTruthy();
        }
      });
    });

    test('should filter by channel using human-readable name', async () => {
      if (skipIfNoCredentials('channel filter test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getCyclingWorkouts({ channel: 'The Sufferfest' });

      expect(workouts.length > 0).toBeTruthy(); // Should find The Sufferfest workouts;
      // All workouts should have the human-readable channel name, not the ID
      workouts.forEach((w) => {
        expect(w.channel, 'Channel should be human-readable name').toBe('The Sufferfest');
      });
    });

    test('should search cycling workouts by name', async () => {
      if (skipIfNoCredentials('cycling search test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getCyclingWorkouts({ search: 'Violator' });

      expect(workouts.length > 0).toBeTruthy(); // Should find workouts with "Violator" in name;
      workouts.forEach((w) => {
        expect(
          w.name.toLowerCase().includes('violator'),
          `Workout "${w.name}" should contain "Violator"`
        ).toBeTruthy();
      });
    });

    test('should filter by category', async () => {
      if (skipIfNoCredentials('category filter test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getCyclingWorkouts({ category: 'Endurance' });

      expect(workouts.length > 0).toBeTruthy();
      workouts.forEach((w) => {
        expect(w.category).toBe('Endurance');
      });
    });

    test('should filter by intensity', async () => {
      if (skipIfNoCredentials('intensity filter test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getCyclingWorkouts({ intensity: 'Low' });

      expect(workouts.length > 0).toBeTruthy();
      workouts.forEach((w) => {
        expect(w.intensity).toBe('Low');
      });
    });

    test('should filter by duration', async () => {
      if (skipIfNoCredentials('duration filter test')) return;

      const client = await createAuthenticatedClient();
      const maxMinutes = 30;
      const workouts = await client.getCyclingWorkouts({ maxDuration: maxMinutes });

      expect(workouts.length > 0).toBeTruthy();
      workouts.forEach((w) => {
        expect(w.duration <= maxMinutes * 60).toBeTruthy();
      });
    });

    test('should filter by TSS range', async () => {
      if (skipIfNoCredentials('TSS filter test')) return;

      const client = await createAuthenticatedClient();
      const minTss = 40;
      const maxTss = 60;
      const workouts = await client.getCyclingWorkouts({ maxTss, minTss });

      expect(workouts.length > 0).toBeTruthy();
      workouts.forEach((w) => {
        if (w.metrics?.tss !== undefined) {
          expect(w.metrics.tss >= minTss).toBeTruthy();
          expect(w.metrics.tss <= maxTss).toBeTruthy();
        }
      });
    });

    test('should combine multiple filters', async () => {
      if (skipIfNoCredentials('combined cycling filters test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getCyclingWorkouts({
        fourDpFocus: 'FTP',
        intensity: 'High',
        maxDuration: 60,
        maxTss: 60,
        minTss: 40,
        sortBy: 'tss',
        sortDirection: 'asc',
      });

      expect(workouts.length > 0).toBeTruthy();

      // Verify all filters
      workouts.forEach((w) => {
        expect(w.metrics?.ratings?.ftp && w.metrics.ratings.ftp >= 4).toBeTruthy();
        expect(w.duration <= 60 * 60).toBeTruthy();
        if (w.metrics?.tss) {
          expect(w.metrics.tss >= 40).toBeTruthy();
          expect(w.metrics.tss <= 60).toBeTruthy();
        }
        expect(w.intensity).toBe('High');
      });

      // Verify sorting
      for (let i = 1; i < Math.min(5, workouts.length); i++) {
        const currentTss = workouts[i].metrics?.tss ?? 0;
        const previousTss = workouts[i - 1].metrics?.tss ?? 0;
        expect(currentTss >= previousTss).toBeTruthy();
      }
    });
  });

  describe('scheduleWorkout', () => {
    test('should schedule a workout', async () => {
      if (skipIfNoCredentials('schedule workout test')) return;

      const client = await createAuthenticatedClient();

      // Get a short workout to schedule
      const workouts = await client.getCyclingWorkouts({
        maxDuration: 30,
        sortBy: 'duration',
        sortDirection: 'asc',
      });

      expect(workouts.length > 0).toBeTruthy();
      const workout = workouts[0];

      // Schedule it for tomorrow
      const tomorrow = addDays(new Date(), 1);
      const dateStr = `${format(tomorrow, 'yyyy-MM-dd')}T12:00:00.000Z`;

      const agendaId = await client.scheduleWorkout(workout.id, dateStr, 'Europe/Lisbon');

      expect(agendaId).toBeTruthy();
      expect(typeof agendaId).toBe('string');
      expect(agendaId.length > 0).toBeTruthy();
    });
  });

  describe('rescheduleWorkout', () => {
    test('should reschedule a workout', async () => {
      if (skipIfNoCredentials('reschedule workout test')) return;

      const client = await createAuthenticatedClient();

      // Get a short workout to schedule
      const workouts = await client.getCyclingWorkouts({
        maxDuration: 30,
        sortBy: 'duration',
        sortDirection: 'asc',
      });

      expect(workouts.length > 0).toBeTruthy();
      const workout = workouts[0];

      // Schedule it for tomorrow
      const tomorrow = addDays(new Date(), 1);
      const tomorrowStr = `${format(tomorrow, 'yyyy-MM-dd')}T12:00:00.000Z`;

      const agendaId = await client.scheduleWorkout(workout.id, tomorrowStr, 'Europe/Lisbon');

      expect(agendaId).toBeTruthy();

      // Now reschedule it to the day after tomorrow
      const dayAfter = addDays(new Date(), 2);
      const dayAfterStr = `${format(dayAfter, 'yyyy-MM-dd')}T12:00:00.000Z`;

      // Should not throw
      await client.rescheduleWorkout(agendaId, dayAfterStr, 'Europe/Lisbon');
    });
  });

  describe('removeWorkout', () => {
    test('should remove a scheduled workout', async () => {
      if (skipIfNoCredentials('remove workout test')) return;

      const client = await createAuthenticatedClient();

      // Get a short workout to schedule
      const workouts = await client.getCyclingWorkouts({
        maxDuration: 30,
        sortBy: 'duration',
        sortDirection: 'asc',
      });

      expect(workouts.length > 0).toBeTruthy();
      const workout = workouts[0];

      // Schedule it for tomorrow
      const tomorrow = addDays(new Date(), 1);
      const tomorrowStr = `${format(tomorrow, 'yyyy-MM-dd')}T12:00:00.000Z`;

      const agendaId = await client.scheduleWorkout(workout.id, tomorrowStr, 'Europe/Lisbon');

      expect(agendaId).toBeTruthy();

      // Now remove it - should not throw
      await client.removeWorkout(agendaId);
    });
  });

  describe('getFitnessTestHistory()', () => {
    test('should throw error when not authenticated', async () => {
      const client = new WahooClient();
      await expect(client.getFitnessTestHistory()).rejects.toThrow(/Not authenticated/);
    });

    test('should get fitness test history', async () => {
      if (skipIfNoCredentials('fitness test history test')) return;

      const client = await createAuthenticatedClient();
      const result = await client.getFitnessTestHistory();

      expect(result).toBeTruthy();
      expect(typeof result.total === 'number').toBeTruthy();
      expect(Array.isArray(result.activities)).toBeTruthy();

      // If there are any tests, validate the structure
      if (result.activities.length > 0) {
        const test = result.activities[0];
        expect(typeof test.id === 'string').toBeTruthy();
        expect(typeof test.name === 'string').toBeTruthy();
        expect(typeof test.completedDate === 'string').toBeTruthy();
        expect(typeof test.durationSeconds === 'number').toBeTruthy();
        expect(typeof test.tss === 'number').toBeTruthy();

        // Validate 4DP data if present
        if (test.testResults) {
          expect(typeof test.testResults.power5s.value === 'number').toBeTruthy();
          expect(typeof test.testResults.power1m.value === 'number').toBeTruthy();
          expect(typeof test.testResults.power5m.value === 'number').toBeTruthy();
          expect(typeof test.testResults.power20m.value === 'number').toBeTruthy();
          expect(typeof test.testResults.lactateThresholdHeartRate === 'number').toBeTruthy();
          expect(typeof test.testResults.riderType.name === 'string').toBeTruthy();
        }
      }
    });

    test('should support pagination', async () => {
      if (skipIfNoCredentials('fitness test pagination test')) return;

      const client = await createAuthenticatedClient();
      const result = await client.getFitnessTestHistory({
        page: 1,
        pageSize: 5,
      });

      expect(result).toBeTruthy();
      expect(result.activities.length <= 5).toBeTruthy();
    });
  });

  describe('getFitnessTestDetails()', () => {
    test('should throw error when not authenticated', async () => {
      const client = new WahooClient();
      await expect(client.getFitnessTestDetails('some-activity-id')).rejects.toThrow(
        /Not authenticated/
      );
    });

    test('should get fitness test details', async () => {
      if (skipIfNoCredentials('fitness test details test')) return;

      const client = await createAuthenticatedClient();

      // First get test history to get an activity ID
      const history = await client.getFitnessTestHistory();

      if (history.activities.length === 0) {
        console.log('Skipping fitness test details test - no test history available');
        return;
      }

      const activityId = history.activities[0].id;
      const details = await client.getFitnessTestDetails(activityId);

      // Validate basic structure
      expect(details).toBeTruthy();
      expect(details.id).toBe(activityId);
      expect(typeof details.name === 'string').toBeTruthy();
      expect(typeof details.completedDate === 'string').toBeTruthy();
      expect(typeof details.durationSeconds === 'number').toBeTruthy();
      expect(typeof details.tss === 'number').toBeTruthy();

      // Validate 4DP test results
      expect(details.testResults).toBeTruthy();
      expect(typeof details.testResults.power5s.value === 'number').toBeTruthy();
      expect(typeof details.testResults.power5s.graphValue === 'number').toBeTruthy();
      expect(typeof details.testResults.power5s.status === 'string').toBeTruthy();
      expect(typeof details.testResults.power1m.value === 'number').toBeTruthy();
      expect(typeof details.testResults.power5m.value === 'number').toBeTruthy();
      expect(typeof details.testResults.power20m.value === 'number').toBeTruthy();
      expect(typeof details.testResults.lactateThresholdHeartRate === 'number').toBeTruthy();
      expect(typeof details.testResults.riderType.name === 'string').toBeTruthy();

      // Validate profile used during test
      expect(details.profile).toBeTruthy();
      expect(typeof details.profile.ftp === 'number').toBeTruthy();
      expect(typeof details.profile.map === 'number').toBeTruthy();
      expect(typeof details.profile.ac === 'number').toBeTruthy();
      expect(typeof details.profile.nm === 'number').toBeTruthy();

      // Validate activity data arrays
      expect(Array.isArray(details.power)).toBeTruthy();
      expect(Array.isArray(details.cadence)).toBeTruthy();
      expect(Array.isArray(details.heartRate)).toBeTruthy();
      expect(details.power.length > 0).toBeTruthy();

      // Validate power bests
      expect(Array.isArray(details.powerBests)).toBeTruthy();
      expect(details.powerBests.length > 0).toBeTruthy();
      const best = details.powerBests[0];
      expect(typeof best.duration === 'number').toBeTruthy();
      expect(typeof best.value === 'number').toBeTruthy();
    });
  });
});
