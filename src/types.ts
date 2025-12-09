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
  nm: number;  // Neuromuscular Power
  ac: number;  // Anaerobic Capacity
  map: number; // Maximal Aerobic Power
  ftp: number; // Functional Threshold Power
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
