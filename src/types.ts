export interface WahooCredentials {
  username: string;
  password: string;
}

export interface WahooAuthResponse {
  data: {
    loginUser: {
      status: string;
      message: string;
      token: string;
      user: {
        id: string;
        fullName: string;
        profiles: {
          riderProfile: RiderProfile;
        };
      };
    };
  };
}

export interface RiderProfile {
  nm: number;  // Neuromuscular Power (5s)
  ac: number;  // Anaerobic Capacity (1m)
  map: number; // Maximal Aerobic Power (5m)
  ftp: number; // Functional Threshold Power (20m)
}

export interface TestValue {
  status: string;
  graphValue: number;
  value: number;
}

export interface RiderTypeInfo {
  name: string;
  description: string;
  icon: string;
}

export interface RiderWeaknessInfo {
  name: string;
  description: string;
  weaknessSummary: string;
  weaknessDescription: string;
  strengthName: string;
  strengthDescription: string;
  strengthSummary: string;
}

export interface HeartRateZone {
  zone: number;
  name: string;
  min: number;
  max: number | null;
}

export interface EnhancedRiderProfile extends RiderProfile {
  // Power values with scores
  power5s: TestValue;
  power1m: TestValue;
  power5m: TestValue;
  power20m: TestValue;

  // Heart rate data
  lactateThresholdHeartRate: number;
  heartRateZones: HeartRateZone[];

  // Rider characteristics
  riderType: RiderTypeInfo;
  riderWeakness: RiderWeaknessInfo;

  // Test metadata
  fitnessTestRidden: boolean;
  startTime: string;
  endTime: string;
}

export interface MostRecentTestResponse {
  data: {
    mostRecentTest: {
      status: string;
      message: string | null;
      fitnessTestRidden: boolean;
      riderType: RiderTypeInfo;
      riderWeakness: RiderWeaknessInfo;
      power5s: TestValue;
      power1m: TestValue;
      power5m: TestValue;
      power20m: TestValue;
      lactateThresholdHeartRate: number;
      startTime: string;
      endTime: string;
    };
  };
}

export interface WorkoutProspect {
  type: string;
  name: string;
  compatibility: string;
  description: string;
  style: string;
  intensity: {
    master: number;
    nm: number;
    ac: number;
    map: number;
    ftp: number;
  };
  plannedDuration: number;
  durationType: string;
  contentId: string;
  workoutId: string;
  notes?: string;
}

export interface UserPlanItem {
  day: number;
  plannedDate: string;
  rank: number;
  status: string;
  type: string;
  prospects: WorkoutProspect[];
  plan: {
    id: string;
    name: string;
    color: string;
    description: string;
    category: string;
  };
}

export interface WorkoutDetails {
  id: string;
  name: string;
  sport: string;
  shortDescription: string;
  details: string;
  level: string;
  durationSeconds: number;
  equipment: Array<{
    name: string;
    description: string;
  }>;
  metrics: {
    intensityFactor: number;
    tss: number;
    ratings: {
      nm: number;
      ac: number;
      map: number;
      ftp: number;
    };
  };
  triggers: string; // JSON string containing interval data
}

export interface LibraryContent {
  id: string;
  name: string;
  mediaType: string;
  channel: string;
  workoutType: string;
  category: string;
  level: string;
  duration: number;
  workoutId: string;
  videoId?: string;
  bannerImage?: string;
  posterImage?: string;
  defaultImage?: string;
  intensity?: string;
  tags?: string[];
  descriptions?: Array<{
    title: string;
    body: string;
  }>;
  metrics?: {
    tss?: number;
    intensityFactor?: number;
    ratings?: {
      nm: number;
      ac: number;
      map: number;
      ftp: number;
    };
  };
}

export interface LibraryResponse {
  data: {
    library: {
      content: LibraryContent[];
      sports: Array<{
        id: string;
        workoutType: string;
        name: string;
        description: string;
      }>;
      channels: Array<{
        id: string;
        name: string;
        description: string;
      }>;
    };
  };
}

export interface ScheduleWorkoutResponse {
  data: {
    addAgenda: {
      status: string;
      message: string | null;
      agendaId: string;
    };
  };
}

export interface MoveAgendaResponse {
  data: {
    moveAgenda: {
      status: string;
    };
  };
}

export interface DeleteAgendaResponse {
  data: {
    deleteAgenda: {
      status: string;
    };
  };
}

export interface FitnessTestResult {
  id: string;
  name: string;
  completedDate: string;
  durationSeconds: number;
  distanceKm: number;
  tss: number;
  intensityFactor: number;
  testResults?: {
    power5s: TestValue;
    power1m: TestValue;
    power5m: TestValue;
    power20m: TestValue;
    lactateThresholdHeartRate: number;
    riderType: RiderTypeInfo;
  };
}

export interface PowerBest {
  duration: number;
  value: number;
}

export interface FitnessTestDetails {
  id: string;
  name: string;
  completedDate: string;
  durationSeconds: number;
  distanceKm: number;
  tss: number;
  intensityFactor: number;
  notes: string;
  testResults: {
    power5s: TestValue;
    power1m: TestValue;
    power5m: TestValue;
    power20m: TestValue;
    lactateThresholdHeartRate: number;
    riderType: RiderTypeInfo;
  };
  profile: {
    ftp: number;
    map: number;
    ac: number;
    nm: number;
  };
  power: number[];
  cadence: number[];
  heartRate: number[];
  powerBests: PowerBest[];
  analysis: string;
}

export interface SearchActivitiesResponse {
  data: {
    searchActivities: {
      activities: FitnessTestResult[];
      total: number;
    };
  };
}

export interface GetActivityResponse {
  data: {
    getActivity: FitnessTestDetails;
  };
}
