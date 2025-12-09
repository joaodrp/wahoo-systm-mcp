import fetch from 'node-fetch';
import type {
  WahooCredentials,
  WahooAuthResponse,
  RiderProfile,
  UserPlanItem,
  WorkoutDetails
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

  getRiderProfile(): RiderProfile | null {
    return this.riderProfile;
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
