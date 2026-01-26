"""GraphQL queries and mutations for the Wahoo SYSTM API."""

LOGIN_MUTATION = """
mutation LoginUser($username: String!, $password: String!, $appInformation: AppInformation!) {
  loginUser(username: $username, password: $password, appInformation: $appInformation) {
    status
    message
    token
    user {
      id
    }
  }
}
"""

IMPERSONATE_MUTATION = """
mutation Impersonate($appInformation: AppInformation!, $sessionToken: String!) {
  impersonateUser(appInformation: $appInformation, sessionToken: $sessionToken) {
    status
    message
    user {
      profiles {
        riderProfile {
          nm
          ac
          map
          ftp
          lthr
          cadenceThreshold
        }
      }
    }
    token
  }
}
"""

MOST_RECENT_TEST_QUERY = """
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
"""

GET_USER_PLANS_RANGE_QUERY = """
query GetUserPlansRange(
  $startDate: Date,
  $endDate: Date,
  $queryParams: QueryParams,
  $timezone: TimeZone
) {
  userPlan(
    startDate: $startDate,
    endDate: $endDate,
    queryParams: $queryParams,
    timezone: $timezone
  ) {
    day
    plannedDate
    rank
    agendaId
    status
    type
    appliedTimeZone
    wahooWorkoutId
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
      fourDPWorkoutGraph {
        time
        value
        type
      }
    }
    plan {
      id
      name
      color
      description
      category
      grouping
      level
      type
    }
    linkData {
      name
      date
      activityId
      durationSeconds
      style
      deleted
    }
  }
}
"""

GET_WORKOUTS_QUERY = """
query GetWorkoutCollection($ids: [ID], $queryParams: QueryParams) {
  workouts(ids: $ids, queryParams: $queryParams) {
    id
    name
    sport
    shortDescription
    details
    level
    durationSeconds
    equipment {
      name
      description
      thumbnail
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
    graphTriggers {
      time
      value
      type
    }
  }
}
"""

LIBRARY_QUERY = """
query Library($locale: Locale!, $queryParams: QueryParams, $appInformation: AppInformation!) {
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
"""

ADD_AGENDA_MUTATION = """
mutation AddAgenda($contentId: ID!, $date: Date!, $timeZone: TimeZone!) {
  addAgenda(contentId: $contentId, date: $date, timeZone: $timeZone) {
    status
    message
    agendaId
  }
}
"""

MOVE_AGENDA_MUTATION = """
mutation MoveAgenda($agendaId: ID!, $date: Date!, $timeZone: TimeZone!) {
  moveAgenda(agendaId: $agendaId, date: $date, timeZone: $timeZone) {
    status
  }
}
"""

DELETE_AGENDA_MUTATION = """
mutation DeleteAgenda($agendaId: ID!) {
  deleteAgenda(agendaId: $agendaId) {
    status
  }
}
"""

GET_WORKOUT_ACTIVITIES_QUERY = """
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
      workoutId
      contentId
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
          description
          icon
        }
      }
    }
    count
  }
}
"""

SEARCH_ACTIVITIES_QUERY = """
query SearchActivities(
  $search: ActivitySearch!,
  $page: PageInformation!,
  $appInfo: AppInformation!,
  $includeGraphs: Boolean
) {
  searchActivities(
    searchParams: $search,
    pageInformation: $page,
    appInformation: $appInfo,
    includeGraphs: $includeGraphs
  ) {
    activities {
      id
      name
      completedDate
      durationSeconds
      distanceKm
      tss
      intensityFactor
      analysis
      workoutId
      contentId
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
          description
          icon
        }
      }
    }
    count
  }
}
"""

GET_ACTIVITY_QUERY = """
query GetActivity($activityId: ID!) {
  activity(id: $activityId) {
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
        description
        icon
      }
    }
    profile {
      nm
      ac
      map
      ftp
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
"""

__all__ = [
    "LOGIN_MUTATION",
    "IMPERSONATE_MUTATION",
    "MOST_RECENT_TEST_QUERY",
    "GET_USER_PLANS_RANGE_QUERY",
    "GET_WORKOUTS_QUERY",
    "LIBRARY_QUERY",
    "ADD_AGENDA_MUTATION",
    "MOVE_AGENDA_MUTATION",
    "DELETE_AGENDA_MUTATION",
    "GET_WORKOUT_ACTIVITIES_QUERY",
    "SEARCH_ACTIVITIES_QUERY",
    "GET_ACTIVITY_QUERY",
]
