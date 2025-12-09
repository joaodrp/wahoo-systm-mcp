import './setup.js';
import { test, describe } from 'node:test';
import assert from 'node:assert';
import { WahooClient } from '../client.js';

// Test helpers
function getTestCredentials() {
  return {
    username: process.env.WAHOO_USERNAME || process.env.TEST_WAHOO_USERNAME,
    password: process.env.WAHOO_PASSWORD || process.env.TEST_WAHOO_PASSWORD
  };
}

function hasCredentials() {
  const { username, password } = getTestCredentials();
  return !!(username && password);
}

async function createAuthenticatedClient(): Promise<WahooClient> {
  const { username, password } = getTestCredentials();

  if (!username || !password) {
    throw new Error('Credentials not available');
  }

  const client = new WahooClient();
  await client.authenticate({ username, password });
  return client;
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
    assert.ok(client);
  });

  test('should throw error when not authenticated', async () => {
    const client = new WahooClient();
    await assert.rejects(
      () => client.getCalendarWorkouts('2025-01-01', '2025-01-31'),
      /Not authenticated/
    );
  });

  describe('Authentication', () => {
    test('should authenticate with valid credentials', async () => {
      if (skipIfNoCredentials('authentication test')) return;

      const client = await createAuthenticatedClient();
      const profile = client.getRiderProfile();
      assert.ok(profile);
      assert.ok(typeof profile.ftp === 'number');
    });
  });

  describe('getRiderProfile()', () => {
    test('should return null when not authenticated', () => {
      const client = new WahooClient();
      const profile = client.getRiderProfile();
      assert.strictEqual(profile, null);
    });

    test('should return 4DP profile after authentication', async () => {
      if (skipIfNoCredentials('profile test')) return;

      const client = await createAuthenticatedClient();
      const profile = client.getRiderProfile();

      assert.ok(profile);
      assert.ok(typeof profile.ftp === 'number');
      assert.ok(typeof profile.map === 'number');
      assert.ok(typeof profile.ac === 'number');
      assert.ok(typeof profile.nm === 'number');
      assert.ok(profile.ftp > 0);
      assert.ok(profile.map > 0);
      assert.ok(profile.ac > 0);
      assert.ok(profile.nm > 0);
    });
  });

  describe('getCalendarWorkouts()', () => {
    test('should throw error when not authenticated', async () => {
      const client = new WahooClient();
      await assert.rejects(
        () => client.getCalendarWorkouts('2025-01-01', '2025-01-31'),
        /Not authenticated/
      );
    });

    test('should get calendar workouts after authentication', async () => {
      if (skipIfNoCredentials('calendar test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getCalendarWorkouts('2025-12-01', '2025-12-31');

      assert.ok(Array.isArray(workouts));

      if (workouts.length > 0) {
        const workout = workouts[0];
        assert.ok(typeof workout.day === 'number');
        assert.ok(typeof workout.plannedDate === 'string');
        assert.ok(typeof workout.status === 'string');
        assert.ok(Array.isArray(workout.prospects));
      }
    });
  });

  describe('getWorkoutDetails()', () => {
    test('should throw error when not authenticated', async () => {
      const client = new WahooClient();
      await assert.rejects(
        () => client.getWorkoutDetails('some-workout-id'),
        /Not authenticated/
      );
    });

    test('should get workout details after authentication', async () => {
      if (skipIfNoCredentials('workout details test')) return;

      const client = await createAuthenticatedClient();

      // Get a workout from the library first
      const library = await client.getWorkoutLibrary({ sport: 'Cycling' });
      assert.ok(library.length > 0, 'Should have at least one cycling workout');

      const workoutId = library[0].workoutId;
      const details = await client.getWorkoutDetails(workoutId);

      assert.ok(details);
      assert.ok(typeof details.id === 'string');
      assert.ok(typeof details.name === 'string');
      assert.ok(typeof details.sport === 'string');
      assert.ok(typeof details.durationSeconds === 'number');
      assert.ok(typeof details.triggers === 'string');
    });
  });

  describe('getWorkoutLibrary()', () => {
    test('should throw error when not authenticated', async () => {
      const client = new WahooClient();
      await assert.rejects(
        () => client.getWorkoutLibrary(),
        /Not authenticated/
      );
    });

    test('should get all workouts when no filters provided', async () => {
      if (skipIfNoCredentials('library test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary();

      assert.ok(Array.isArray(workouts));
      assert.ok(workouts.length > 0);

      const workout = workouts[0];
      assert.ok(typeof workout.id === 'string');
      assert.ok(typeof workout.name === 'string');
      assert.ok(typeof workout.workoutType === 'string');
      assert.ok(typeof workout.duration === 'number');
      assert.ok(typeof workout.workoutId === 'string');
    });

    test('should filter by sport', async () => {
      if (skipIfNoCredentials('sport filter test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({ sport: 'Cycling' });

      assert.ok(workouts.length > 0);
      assert.ok(workouts.every(w => w.workoutType === 'Cycling'));
    });

    test('should filter by max duration', async () => {
      if (skipIfNoCredentials('duration filter test')) return;

      const client = await createAuthenticatedClient();
      const maxDurationHours = 0.5;
      const maxDurationSeconds = maxDurationHours * 3600;
      const workouts = await client.getWorkoutLibrary({
        sport: 'Cycling',
        maxDuration: maxDurationHours
      });

      assert.ok(workouts.length > 0);
      assert.ok(workouts.every(w => w.duration <= maxDurationSeconds));
    });

    test('should filter by TSS range', async () => {
      if (skipIfNoCredentials('TSS filter test')) return;

      const client = await createAuthenticatedClient();
      const minTss = 40;
      const maxTss = 60;
      const workouts = await client.getWorkoutLibrary({
        sport: 'Cycling',
        minTss,
        maxTss
      });

      assert.ok(workouts.length > 0);
      assert.ok(workouts.every(w =>
        w.metrics?.tss !== undefined &&
        w.metrics.tss >= minTss &&
        w.metrics.tss <= maxTss
      ));
    });

    test('should sort by name ascending', async () => {
      if (skipIfNoCredentials('sort by name test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        sport: 'Cycling',
        sortBy: 'name',
        sortDirection: 'asc'
      });

      assert.ok(workouts.length > 1);

      for (let i = 1; i < Math.min(10, workouts.length); i++) {
        assert.ok(
          workouts[i].name.localeCompare(workouts[i - 1].name) >= 0,
          `Expected ${workouts[i].name} >= ${workouts[i - 1].name}`
        );
      }
    });

    test('should sort by duration descending', async () => {
      if (skipIfNoCredentials('sort by duration test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        sport: 'Cycling',
        sortBy: 'duration',
        sortDirection: 'desc'
      });

      assert.ok(workouts.length > 1);

      for (let i = 1; i < Math.min(10, workouts.length); i++) {
        assert.ok(
          workouts[i].duration <= workouts[i - 1].duration,
          `Expected ${workouts[i].duration} <= ${workouts[i - 1].duration}`
        );
      }
    });

    test('should sort by TSS ascending', async () => {
      if (skipIfNoCredentials('sort by TSS test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        sport: 'Cycling',
        sortBy: 'tss',
        sortDirection: 'asc'
      });

      assert.ok(workouts.length > 1);

      for (let i = 1; i < Math.min(10, workouts.length); i++) {
        const currentTss = workouts[i].metrics?.tss ?? 0;
        const previousTss = workouts[i - 1].metrics?.tss ?? 0;
        assert.ok(
          currentTss >= previousTss,
          `Expected ${currentTss} >= ${previousTss}`
        );
      }
    });

    test('should sort by level for strength workouts', async () => {
      if (skipIfNoCredentials('sort by level test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        sport: 'Strength',
        sortBy: 'level',
        sortDirection: 'asc'
      });

      assert.ok(workouts.length > 0);

      // Check that levels are ordered correctly where present
      const levelOrder = { 'Basic': 1, 'Intermediate': 2, 'Advanced': 3 };
      for (let i = 1; i < Math.min(10, workouts.length); i++) {
        if (workouts[i].level && workouts[i - 1].level) {
          const currentLevel = levelOrder[workouts[i].level as keyof typeof levelOrder] || 0;
          const previousLevel = levelOrder[workouts[i - 1].level as keyof typeof levelOrder] || 0;
          assert.ok(
            currentLevel >= previousLevel,
            `Expected ${workouts[i].level} >= ${workouts[i - 1].level}`
          );
        }
      }
    });

    test('should combine multiple filters', async () => {
      if (skipIfNoCredentials('combined filters test')) return;

      const client = await createAuthenticatedClient();
      const workouts = await client.getWorkoutLibrary({
        sport: 'Cycling',
        maxDuration: 1,
        minTss: 30,
        maxTss: 50,
        sortBy: 'tss',
        sortDirection: 'asc'
      });

      assert.ok(workouts.length > 0);

      // Verify all filters are applied
      workouts.forEach(w => {
        assert.strictEqual(w.workoutType, 'Cycling');
        assert.ok(w.duration <= 3600); // 1 hour
        if (w.metrics?.tss) {
          assert.ok(w.metrics.tss >= 30);
          assert.ok(w.metrics.tss <= 50);
        }
      });

      // Verify sorting
      for (let i = 1; i < Math.min(5, workouts.length); i++) {
        const currentTss = workouts[i].metrics?.tss ?? 0;
        const previousTss = workouts[i - 1].metrics?.tss ?? 0;
        assert.ok(currentTss >= previousTss);
      }
    });
  });
});
