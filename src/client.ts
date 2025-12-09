import fetch from 'node-fetch';
import type {
  WahooCredentials,
  WahooAuthResponse,
  RiderProfile,
  EnhancedRiderProfile,
  HeartRateZone,
  MostRecentTestResponse,
  UserPlanItem,
  WorkoutDetails,
  LibraryResponse,
  LibraryContent,
  ScheduleWorkoutResponse,
  MoveAgendaResponse,
  DeleteAgendaResponse,
  FitnessTestResult,
  FitnessTestDetails,
  SearchActivitiesResponse,
  GetActivityResponse
} from './types.js';

const WAHOO_API_URL = 'https://api.thesufferfest.com/graphql';
const APP_VERSION = '7.12.0-web.2141';
const INSTALL_ID = 'F215B34567B35AC815329A53A2B696E5';

export class WahooClient {
  private token: string | null = null;
  private riderProfile: RiderProfile | null = null;

  async authenticate(credentials: WahooCredentials): Promise<void> {
    const query = `
      mutation Login($appInformation: AppInformation!, $username: String!, $password: String!) {
        loginUser(appInformation: $appInformation, username: $username, password: $password) {
          status
          message
          user {
            id
            fullName
            firstName
            lastName
            email
            profiles {
              riderProfile {
                nm
                ac
                map
                ftp
              }
            }
          }
          token
          failureId
        }
      }
    `;

    const variables = {
      appInformation: {
        platform: 'web',
        version: APP_VERSION,
        installId: INSTALL_ID
      },
      username: credentials.username,
      password: credentials.password
    };

    const response = await this.callAPI<WahooAuthResponse>({
      query,
      variables,
      operationName: 'Login'
    });

    if (response.data.loginUser.token) {
      this.token = response.data.loginUser.token;
      this.riderProfile = response.data.loginUser.user.profiles.riderProfile;
    } else {
      throw new Error('Authentication failed: ' + response.data.loginUser.message);
    }
  }

  async getCalendarWorkouts(startDate: string, endDate: string): Promise<UserPlanItem[]> {
    this.ensureAuthenticated();

    const query = `
      query GetUserPlansRange($startDate: Date, $endDate: Date, $queryParams: QueryParams) {
        userPlan(startDate: $startDate, endDate: $endDate, queryParams: $queryParams) {
          day
          plannedDate
          rank
          agendaId
          status
          type
          appliedTimeZone
          completionData {
            name
            date
            activityId
            durationSeconds
            style
            deleted
          }
          prospects {
            type
            name
            compatibility
            description
            style
            intensity {
              master
              nm
              ac
              map
              ftp
            }
            trainerSetting {
              mode
              level
            }
            plannedDuration
            durationType
            metrics {
              ratings {
                nm
                ac
                map
                ftp
              }
            }
            contentId
            workoutId
            notes
          }
          plan {
            id
            name
            color
            deleted
            durationDays
            startDate
            endDate
            addons
            level
            subcategory
            weakness
            description
            category
            grouping
            option
            uniqueToPlan
            type
            progression
            planDescription
            volume
          }
        }
      }
    `;

    const variables = {
      startDate: `${startDate}T00:00:00.000Z`,
      endDate: `${endDate}T23:59:59.999Z`,
      queryParams: {
        limit: 1000
      }
    };

    const response = await this.callAPI<{ data: { userPlan: UserPlanItem[] } }>({
      query,
      variables,
      operationName: 'GetUserPlansRange'
    });

    return response.data.userPlan;
  }

  async getWorkoutDetails(workoutId: string): Promise<WorkoutDetails> {
    this.ensureAuthenticated();

    const query = `
      query GetWorkouts($id: ID) {
        workouts(id: $id) {
          id
          sortOrder
          sport
          stampImage
          bannerImage
          bestFor
          equipment {
            name
            description
            thumbnail
          }
          details
          shortDescription
          level
          durationSeconds
          name
          triggers
          featuredRaces {
            name
            thumbnail
            darkBackgroundThumbnail
          }
          metrics {
            intensityFactor
            tss
            ratings {
              nm
              ac
              map
              ftp
            }
          }
          brand
          nonAppWorkout
          notes
          tags
        }
      }
    `;

    const variables = {
      id: workoutId
    };

    const response = await this.callAPI<{ data: { workouts: WorkoutDetails[] } }>({
      query,
      variables,
      operationName: 'GetWorkouts'
    });

    if (!response.data.workouts || response.data.workouts.length === 0) {
      throw new Error(`Workout with ID ${workoutId} not found`);
    }

    return response.data.workouts[0];
  }

  async getWorkoutLibrary(filters?: {
    sport?: string;
    channel?: string;
    level?: string;
    minDuration?: number;
    maxDuration?: number;
    minTss?: number;
    maxTss?: number;
    sortBy?: 'name' | 'duration' | 'tss' | 'level';
    sortDirection?: 'asc' | 'desc';
  }): Promise<LibraryContent[]> {
    this.ensureAuthenticated();

    const query = `
      query library($locale: Locale!, $queryParams: QueryParams, $appInformation: AppInformation!) {
        library(locale: $locale, queryParams: $queryParams, appInformation: $appInformation) {
          content {
            id
            name
            mediaType
            channel
            workoutType
            category
            level
            duration
            workoutId
            videoId
            bannerImage
            posterImage
            defaultImage
            intensity
            tags
            descriptions {
              title
              body
            }
            metrics {
              tss
              intensityFactor
              ratings {
                nm
                ac
                map
                ftp
              }
            }
          }
          sports {
            id
            workoutType
            name
            description
          }
          channels {
            id
            name
            description
          }
        }
      }
    `;

    const variables = {
      locale: 'en',
      queryParams: {
        limit: 3000
      },
      appInformation: {
        platform: 'web',
        version: APP_VERSION
      }
    };

    const response = await this.callAPI<LibraryResponse>({
      query,
      variables,
      operationName: 'library'
    });

    let content = response.data.library.content;

    // Apply client-side filters
    if (filters) {
      if (filters.sport) {
        content = content.filter(item =>
          item.workoutType?.toLowerCase() === filters.sport?.toLowerCase()
        );
      }
      if (filters.channel) {
        content = content.filter(item =>
          item.channel?.toLowerCase() === filters.channel?.toLowerCase()
        );
      }
      if (filters.level) {
        content = content.filter(item =>
          item.level?.toLowerCase() === filters.level?.toLowerCase()
        );
      }
      if (filters.minDuration !== undefined) {
        const minSeconds = filters.minDuration * 60;
        content = content.filter(item => item.duration >= minSeconds);
      }
      if (filters.maxDuration !== undefined) {
        const maxSeconds = filters.maxDuration * 60;
        content = content.filter(item => item.duration <= maxSeconds);
      }
      if (filters.minTss !== undefined) {
        content = content.filter(item => (item.metrics?.tss ?? 0) >= filters.minTss!);
      }
      if (filters.maxTss !== undefined) {
        content = content.filter(item => (item.metrics?.tss ?? 0) <= filters.maxTss!);
      }
    }

    // Apply sorting
    const sortBy = filters?.sortBy || 'name';
    const sortDirection = filters?.sortDirection || 'asc';
    const multiplier = sortDirection === 'asc' ? 1 : -1;

    content.sort((a, b) => {
      let compareValue = 0;

      switch (sortBy) {
        case 'name':
          compareValue = a.name.localeCompare(b.name);
          break;
        case 'duration':
          compareValue = a.duration - b.duration;
          break;
        case 'tss':
          compareValue = (a.metrics?.tss ?? 0) - (b.metrics?.tss ?? 0);
          break;
        case 'level':
          // Define level order: Basic < Intermediate < Advanced
          const levelOrder: Record<string, number> = { 'basic': 1, 'intermediate': 2, 'advanced': 3 };
          const aLevel = levelOrder[a.level?.toLowerCase()] ?? 0;
          const bLevel = levelOrder[b.level?.toLowerCase()] ?? 0;
          compareValue = aLevel - bLevel;
          break;
      }

      return compareValue * multiplier;
    });

    return content;
  }

  async getCyclingWorkouts(filters?: {
    channel?: string;
    category?: string;
    fourDpFocus?: 'NM' | 'AC' | 'MAP' | 'FTP';
    minDuration?: number;
    maxDuration?: number;
    minTss?: number;
    maxTss?: number;
    intensity?: 'High' | 'Medium' | 'Low';
    sortBy?: 'name' | 'duration' | 'tss';
    sortDirection?: 'asc' | 'desc';
    limit?: number;
  }): Promise<LibraryContent[]> {
    // Start with base cycling filters
    const baseFilters: any = {
      sport: 'Cycling',
      sortBy: filters?.sortBy,
      sortDirection: filters?.sortDirection
    };

    if (filters?.minDuration) baseFilters.minDuration = filters.minDuration;
    if (filters?.maxDuration) baseFilters.maxDuration = filters.maxDuration;
    if (filters?.minTss) baseFilters.minTss = filters.minTss;
    if (filters?.maxTss) baseFilters.maxTss = filters.maxTss;

    let workouts = await this.getWorkoutLibrary(baseFilters);

    // Apply cycling-specific filters
    if (filters?.channel) {
      workouts = workouts.filter(w =>
        w.channel?.toLowerCase().includes(filters.channel!.toLowerCase())
      );
    }

    if (filters?.category) {
      workouts = workouts.filter(w =>
        w.category?.toLowerCase() === filters.category!.toLowerCase()
      );
    }

    if (filters?.intensity) {
      workouts = workouts.filter(w =>
        w.intensity?.toLowerCase() === filters.intensity!.toLowerCase()
      );
    }

    // 4DP Focus filter - workouts with high rating (>= 4) in the specified energy system
    // This matches the SYSTM UI behavior: FTP filter shows 155 workouts (78 with rating=5 + 77 with rating=4)
    // MAP shows 89 workouts (45 rating=5 + 44 rating=4), etc.
    if (filters?.fourDpFocus) {
      const focus = filters.fourDpFocus.toLowerCase();
      workouts = workouts.filter(w => {
        const rating = w.metrics?.ratings?.[focus as keyof typeof w.metrics.ratings];
        return rating !== undefined && rating >= 4;
      });
    }

    // Apply limit
    const limit = filters?.limit ?? 50;
    return workouts.slice(0, limit);
  }

  async scheduleWorkout(contentId: string, date: string, timeZone?: string): Promise<string> {
    this.ensureAuthenticated();

    const query = `
      mutation AddUserPlanItem($contentId: ID!, $date: Date!, $timeZone: TimeZone!, $rank: Int) {
        addAgenda(contentId: $contentId, date: $date, timeZone: $timeZone, rank: $rank) {
          status
          message
          agendaId
        }
      }
    `;

    // Default timezone to UTC if not provided
    const tz = timeZone || 'UTC';

    // Default rank to 200 (seems to be the standard priority)
    const variables = {
      contentId,
      date,
      timeZone: tz,
      rank: 200
    };

    const response = await this.callAPI<ScheduleWorkoutResponse>({
      query,
      variables,
      operationName: 'AddUserPlanItem'
    });

    if (response.data.addAgenda.status !== 'Success') {
      throw new Error(`Failed to schedule workout: ${response.data.addAgenda.message}`);
    }

    return response.data.addAgenda.agendaId;
  }

  async rescheduleWorkout(agendaId: string, newDate: string, timeZone?: string): Promise<void> {
    this.ensureAuthenticated();

    const query = `
      mutation MoveAgenda($agendaId: ID!, $date: Date!, $rank: Int, $timeZone: TimeZone) {
        moveAgenda(agendaId: $agendaId, date: $date, rank: $rank, timeZone: $timeZone) {
          status
        }
      }
    `;

    // Default timezone to UTC if not provided
    const tz = timeZone || 'UTC';

    // Default rank to 200 (seems to be the standard priority)
    const variables = {
      agendaId,
      date: newDate,
      rank: 200,
      timeZone: tz
    };

    const response = await this.callAPI<MoveAgendaResponse>({
      query,
      variables,
      operationName: 'MoveAgenda'
    });

    if (response.data.moveAgenda.status !== 'Success') {
      throw new Error(`Failed to reschedule workout`);
    }
  }

  async removeWorkout(agendaId: string): Promise<void> {
    this.ensureAuthenticated();

    const query = `
      mutation DeleteAgenda($agendaId: ID!) {
        deleteAgenda(agendaId: $agendaId) {
          status
        }
      }
    `;

    const variables = {
      agendaId
    };

    const response = await this.callAPI<DeleteAgendaResponse>({
      query,
      variables,
      operationName: 'DeleteAgenda'
    });

    if (response.data.deleteAgenda.status !== 'Success') {
      throw new Error(`Failed to remove workout`);
    }
  }

  getRiderProfile(): RiderProfile | null {
    return this.riderProfile;
  }

  async getEnhancedRiderProfile(): Promise<EnhancedRiderProfile | null> {
    this.ensureAuthenticated();

    const query = `
      query MostRecentTest {
        mostRecentTest {
          status
          message
          fitnessTestRidden
          riderType {
            name
            description
            icon
          }
          riderWeakness {
            name
            description
            weaknessSummary
            weaknessDescription
            strengthName
            strengthDescription
            strengthSummary
          }
          power5s {
            status
            graphValue
            value
          }
          power1m {
            status
            graphValue
            value
          }
          power5m {
            status
            graphValue
            value
          }
          power20m {
            status
            graphValue
            value
          }
          lactateThresholdHeartRate
          startTime
          endTime
        }
      }
    `;

    const response = await this.callAPI<MostRecentTestResponse>({
      query,
      variables: {},
      operationName: 'MostRecentTest'
    });

    const testData = response.data.mostRecentTest;

    if (!testData || testData.status !== 'ok') {
      return null;
    }

    // Calculate HR zones from LTHR
    const heartRateZones = this.calculateHeartRateZones(testData.lactateThresholdHeartRate);

    return {
      // Basic 4DP values
      nm: testData.power5s.value,
      ac: testData.power1m.value,
      map: testData.power5m.value,
      ftp: testData.power20m.value,

      // Enhanced power data
      power5s: testData.power5s,
      power1m: testData.power1m,
      power5m: testData.power5m,
      power20m: testData.power20m,

      // Heart rate data
      lactateThresholdHeartRate: testData.lactateThresholdHeartRate,
      heartRateZones,

      // Rider characteristics
      riderType: testData.riderType,
      riderWeakness: testData.riderWeakness,

      // Test metadata
      fitnessTestRidden: testData.fitnessTestRidden,
      startTime: testData.startTime,
      endTime: testData.endTime
    };
  }

  async getFitnessTestHistory(options?: {
    page?: number;
    pageSize?: number;
  }): Promise<{ activities: FitnessTestResult[]; total: number }> {
    this.ensureAuthenticated();

    // Hardcoded workout IDs for fitness tests in the SYSTM library
    // dRcyg09t6K = Full Frontal (4DP Test)
    // 0SmbqUIZZo = Half Monty
    // These are the only two fitness test workouts in the library
    const fitnessTestWorkoutIds = ['dRcyg09t6K', '0SmbqUIZZo'];

    const query = `
      query GetWorkoutActivities($workoutIds: [ID]!, $pageInformation: PageInformation!) {
        getWorkoutActivities(workoutIds: $workoutIds, pageInformation: $pageInformation) {
          activities {
            id
            name
            completedDate
            durationSeconds
            distanceKm
            tss
            intensityFactor
            testResults {
              power5s {
                status
                graphValue
                value
              }
              power1m {
                status
                graphValue
                value
              }
              power5m {
                status
                graphValue
                value
              }
              power20m {
                status
                graphValue
                value
              }
              lactateThresholdHeartRate
              riderType {
                name
                icon
                description
              }
            }
          }
          count
        }
      }
    `;

    const variables = {
      workoutIds: fitnessTestWorkoutIds,
      pageInformation: {
        page: options?.page || 1,
        pageSize: options?.pageSize || 15
      }
    };

    const response = await this.callAPI<{
      data: {
        getWorkoutActivities: {
          activities: FitnessTestResult[];
          count: number;
        };
      };
    }>({
      query,
      variables,
      operationName: 'GetWorkoutActivities'
    });

    return {
      activities: response.data.getWorkoutActivities.activities,
      total: response.data.getWorkoutActivities.count
    };
  }

  async getFitnessTestDetails(activityId: string): Promise<FitnessTestDetails> {
    this.ensureAuthenticated();

    const query = `
      query GetActivity($id: ID!) {
        activity(id: $id) {
          id
          name
          completedDate
          durationSeconds
          distanceKm
          tss
          intensityFactor
          notes
          testResults {
            power5s {
              status
              graphValue
              value
            }
            power1m {
              status
              graphValue
              value
            }
            power5m {
              status
              graphValue
              value
            }
            power20m {
              status
              graphValue
              value
            }
            lactateThresholdHeartRate
            riderType {
              name
              icon
              description
            }
          }
          profile {
            ftp
            map
            ac
            nm
          }
          power
          cadence
          heartRate
          powerBests {
            duration
            value
          }
          analysis
        }
      }
    `;

    const variables = {
      id: activityId
    };

    const response = await this.callAPI<{
      data: {
        activity: FitnessTestDetails;
      };
    }>({
      query,
      variables,
      operationName: 'GetActivity'
    });

    return response.data.activity;
  }

  private calculateHeartRateZones(lthr: number): HeartRateZone[] {
    return [
      {
        zone: 1,
        name: 'Active Recovery',
        min: 0,
        max: Math.round(lthr * 0.68)
      },
      {
        zone: 2,
        name: 'Endurance',
        min: Math.round(lthr * 0.68) + 1,
        max: Math.round(lthr * 0.83)
      },
      {
        zone: 3,
        name: 'Tempo',
        min: Math.round(lthr * 0.83) + 1,
        max: Math.round(lthr * 0.94)
      },
      {
        zone: 4,
        name: 'Threshold',
        min: Math.round(lthr * 0.94) + 1,
        max: Math.round(lthr * 1.05)
      },
      {
        zone: 5,
        name: 'VO2 Max',
        min: Math.round(lthr * 1.05) + 1,
        max: null
      }
    ];
  }

  private ensureAuthenticated(): void {
    if (!this.token) {
      throw new Error('Not authenticated. Please call authenticate() first.');
    }
  }

  private async callAPI<T>(payload: {
    query: string;
    variables: Record<string, unknown>;
    operationName: string;
  }): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(WAHOO_API_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    const data = await response.json() as T;
    return data;
  }
}
