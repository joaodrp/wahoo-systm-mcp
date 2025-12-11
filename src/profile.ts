import { format } from 'date-fns';
import { type FastMCP, UserError } from 'fastmcp';
import { z } from 'zod';

import type { WahooClient } from '../client.js';

/**
 * Register profile and fitness test tools
 */
export const registerProfileTools = (mcp: FastMCP, client: WahooClient, ensureAuth: () => void) => {
  // Tool: get_rider_profile
  mcp.addTool({
    annotations: {
      readOnlyHint: true,
      title: 'Get Rider Profile',
    },
    description:
      'Get the rider 4DP profile (NM, AC, MAP, FTP) including rider type classification, strengths/weaknesses, and heart rate zones.',
    execute: async () => {
      ensureAuth();
      const profile = await client.getEnhancedRiderProfile();

      if (!profile) {
        throw new UserError(
          'No rider profile found. Complete a Full Frontal or Half Monty test first.'
        );
      }

      const testDate = new Date(profile.startTime);
      const formattedDate = format(testDate, 'MMMM d, yyyy');

      return JSON.stringify(
        {
          fourDP: {
            ac: { score: profile.power1m.value, watts: profile.ac },
            ftp: { score: profile.power20m.value, watts: profile.ftp },
            map: { score: profile.power5m.value, watts: profile.map },
            nm: { score: profile.power5s.value, watts: profile.nm },
          },
          heartRateZones: profile.heartRateZones,
          lastTestDate: formattedDate,
          lthr: profile.lactateThresholdHeartRate,
          riderType: {
            description: profile.riderType.description,
            name: profile.riderType.name,
          },
          strengths: {
            description: profile.riderWeakness.strengthDescription,
            name: profile.riderWeakness.strengthName,
            summary: profile.riderWeakness.strengthSummary,
          },
          weaknesses: {
            description: profile.riderWeakness.weaknessDescription,
            name: profile.riderWeakness.name,
            summary: profile.riderWeakness.weaknessSummary,
          },
        },
        null,
        2
      );
    },
    name: 'get_rider_profile',
    parameters: z.object({}),
  });

  // Tool: get_fitness_test_history
  mcp.addTool({
    annotations: {
      readOnlyHint: true,
      title: 'Get Fitness Test History',
    },
    description:
      'Get history of completed Full Frontal and Half Monty fitness tests with 4DP results, rider type classification, and test dates.',
    execute: async (args) => {
      ensureAuth();

      const options: Parameters<typeof client.getFitnessTestHistory>[0] = {};
      if (typeof args.page === 'number') options.page = args.page;
      if (typeof args.page_size === 'number') options.pageSize = args.page_size;

      const result = await client.getFitnessTestHistory(options);

      const formattedTests = result.activities.map((test) => {
        const testDate = new Date(test.completedDate);
        const formattedDate = format(testDate, 'MMMM d, yyyy');

        const durationHours = test.durationSeconds / 3600;
        const hours = Math.floor(durationHours);
        const minutes = Math.round((durationHours - hours) * 60);

        return {
          date: formattedDate,
          distance: `${test.distanceKm.toFixed(2)} km`,
          duration: hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`,
          fourDP: test.testResults
            ? {
                ac: {
                  score: test.testResults.power1m.graphValue,
                  watts: test.testResults.power1m.value,
                },
                ftp: {
                  score: test.testResults.power20m.graphValue,
                  watts: test.testResults.power20m.value,
                },
                map: {
                  score: test.testResults.power5m.graphValue,
                  watts: test.testResults.power5m.value,
                },
                nm: {
                  score: test.testResults.power5s.graphValue,
                  watts: test.testResults.power5s.value,
                },
              }
            : null,
          id: test.id,
          intensityFactor: test.intensityFactor,
          lthr: test.testResults?.lactateThresholdHeartRate,
          name: test.name,
          riderType: test.testResults?.riderType.name,
          tss: test.tss,
        };
      });

      return JSON.stringify({ tests: formattedTests, total: result.total }, null, 2);
    },
    name: 'get_fitness_test_history',
    parameters: z.object({
      page: z.number().optional().describe('Page number for pagination (default: 1)'),
      page_size: z.number().optional().describe('Results per page (default: 15)'),
    }),
  });

  // Tool: get_fitness_test_details
  mcp.addTool({
    annotations: {
      readOnlyHint: true,
      title: 'Get Fitness Test Details',
    },
    description:
      'Get detailed fitness test data including second-by-second power/cadence/heart rate, power curve bests, and post-test analysis.',
    execute: async (args) => {
      ensureAuth();

      const testDetails = await client.getFitnessTestDetails(args.activity_id);

      const testDate = new Date(testDetails.completedDate);
      const formattedDate = format(testDate, 'MMMM d, yyyy');

      const durationHours = testDetails.durationSeconds / 3600;
      const hours = Math.floor(durationHours);
      const minutes = Math.round((durationHours - hours) * 60);

      let analysisData = null;
      if (testDetails.analysis) {
        try {
          analysisData = JSON.parse(testDetails.analysis);
        } catch {
          analysisData = null;
        }
      }

      return JSON.stringify(
        {
          activityData: {
            cadence: testDetails.cadence,
            heartRate: testDetails.heartRate,
            power: testDetails.power,
          },
          analysis: analysisData,
          date: formattedDate,
          distance: `${testDetails.distanceKm.toFixed(2)} km`,
          duration: hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`,
          fourDP: testDetails.testResults
            ? {
                ac: {
                  score: testDetails.testResults.power1m.graphValue,
                  watts: testDetails.testResults.power1m.value,
                },
                ftp: {
                  score: testDetails.testResults.power20m.graphValue,
                  watts: testDetails.testResults.power20m.value,
                },
                map: {
                  score: testDetails.testResults.power5m.graphValue,
                  watts: testDetails.testResults.power5m.value,
                },
                nm: {
                  score: testDetails.testResults.power5s.graphValue,
                  watts: testDetails.testResults.power5s.value,
                },
              }
            : null,
          intensityFactor: testDetails.intensityFactor,
          lthr: testDetails.testResults?.lactateThresholdHeartRate,
          name: testDetails.name,
          notes: testDetails.notes,
          powerCurve: testDetails.powerBests,
          riderType: testDetails.testResults?.riderType.name,
          tss: testDetails.tss,
        },
        null,
        2
      );
    },
    name: 'get_fitness_test_details',
    parameters: z.object({
      activity_id: z.string().describe('Activity ID from get_fitness_test_history'),
    }),
  });
};
