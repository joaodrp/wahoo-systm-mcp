import { z } from 'zod';

// Base schemas
export const RatingsSchema = z.object({
  nm: z.number(),
  ac: z.number(),
  map: z.number(),
  ftp: z.number()
});

export const MetricsSchema = z.object({
  intensityFactor: z.number().optional(),
  tss: z.number().optional(),
  ratings: RatingsSchema.optional()
});

export const EquipmentSchema = z.object({
  name: z.string(),
  description: z.string(),
  thumbnail: z.string().optional()
});

export const DescriptionSchema = z.object({
  title: z.string(),
  body: z.string()
});

export const FeaturedRaceSchema = z.object({
  name: z.string(),
  thumbnail: z.string().optional(),
  darkBackgroundThumbnail: z.string().optional()
});

// Workout Details schema
export const WorkoutDetailsSchema = z.object({
  id: z.string(),
  sortOrder: z.number().nullable().optional(),
  sport: z.string(),
  stampImage: z.string().optional(),
  bannerImage: z.string().optional(),
  bestFor: z.string().nullable().optional(),
  equipment: z.array(EquipmentSchema).nullable().optional(),
  details: z.string(),
  shortDescription: z.string(),
  descriptions: z.array(DescriptionSchema).optional(),
  level: z.string().nullable().optional().transform(val => val || ''),
  durationSeconds: z.number(),
  name: z.string(),
  triggers: z.string().optional().transform(val => val || ''),
  featuredRaces: z.array(FeaturedRaceSchema).nullable().optional(),
  metrics: MetricsSchema.transform(m => ({
    intensityFactor: m.intensityFactor || 0,
    tss: m.tss || 0,
    ratings: m.ratings || { nm: 0, ac: 0, map: 0, ftp: 0 }
  })),
  brand: z.string().nullable().optional(),
  nonAppWorkout: z.boolean().optional(),
  notes: z.string().nullable().optional(),
  tags: z.array(z.string()).optional()
});

// Library Content schema
export const LibraryContentSchema = z.object({
  id: z.string(),
  name: z.string(),
  mediaType: z.string(),
  channel: z.string(),
  workoutType: z.string(),
  category: z.string(),
  level: z.string(),
  duration: z.number(),
  workoutId: z.string(),
  videoId: z.string().optional(),
  bannerImage: z.string().optional(),
  posterImage: z.string().optional(),
  defaultImage: z.string().optional(),
  intensity: z.string().optional(),
  tags: z.array(z.string()).optional(),
  descriptions: z.array(DescriptionSchema).optional(),
  metrics: MetricsSchema.optional()
});

// Channel schema
export const ChannelSchema = z.object({
  id: z.string(),
  name: z.string()
});

// Sport schema
export const SportSchema = z.object({
  id: z.string(),
  workoutType: z.string(),
  name: z.string(),
  description: z.string()
});

// Calendar workout schema
export const CalendarWorkoutSchema = z.object({
  id: z.string(),
  date: z.string(),
  workoutId: z.string().optional(),
  name: z.string().optional(),
  duration: z.number().optional(),
  status: z.string().optional(),
  type: z.string().optional()
});

// Rider profile schemas
export const PowerValueSchema = z.object({
  value: z.number(),
  graphValue: z.number()
});

export const RiderProfileSchema = z.object({
  nm: z.number(),
  ac: z.number(),
  map: z.number(),
  ftp: z.number(),
  power5s: PowerValueSchema,
  power1m: PowerValueSchema,
  power5m: PowerValueSchema,
  power20m: PowerValueSchema,
  lactateThresholdHeartRate: z.number(),
  riderType: z.object({
    name: z.string()
  }),
  startTime: z.string()
});

// Fitness test schemas
export const TestResultsSchema = z.object({
  power5s: PowerValueSchema,
  power1m: PowerValueSchema,
  power5m: PowerValueSchema,
  power20m: PowerValueSchema,
  lactateThresholdHeartRate: z.number(),
  riderType: z.object({
    name: z.string()
  })
});

export const FitnessTestSchema = z.object({
  id: z.string(),
  name: z.string(),
  completedDate: z.string(),
  durationSeconds: z.number(),
  distanceKm: z.number(),
  tss: z.number().optional(),
  intensityFactor: z.number().optional(),
  testResults: TestResultsSchema.nullable().optional()
});

// API Response schemas
export const WorkoutDetailsResponseSchema = z.object({
  data: z.object({
    workouts: z.array(WorkoutDetailsSchema)
  })
});

export const LibraryResponseSchema = z.object({
  data: z.object({
    library: z.object({
      content: z.array(LibraryContentSchema),
      sports: z.array(SportSchema),
      channels: z.array(ChannelSchema)
    })
  })
});

export const CalendarResponseSchema = z.object({
  data: z.object({
    calendar: z.array(CalendarWorkoutSchema)
  })
});

export const RiderProfileResponseSchema = z.object({
  data: z.object({
    profile: RiderProfileSchema.nullable()
  })
});

export const FitnessTestHistoryResponseSchema = z.object({
  data: z.object({
    fitnessTests: z.object({
      total: z.number(),
      activities: z.array(FitnessTestSchema)
    })
  })
});

export const GetWorkoutActivitiesResponseSchema = z.object({
  data: z.object({
    getWorkoutActivities: z.object({
      activities: z.array(FitnessTestSchema),
      count: z.number()
    })
  })
});

// Export types inferred from schemas
export type WorkoutDetails = z.infer<typeof WorkoutDetailsSchema>;
export type LibraryContent = z.infer<typeof LibraryContentSchema>;
export type CalendarWorkout = z.infer<typeof CalendarWorkoutSchema>;
export type RiderProfile = z.infer<typeof RiderProfileSchema>;
export type FitnessTest = z.infer<typeof FitnessTestSchema>;
