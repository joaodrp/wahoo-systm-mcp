# Wahoo SYSTM GraphQL (Observed Spec)

This document captures the Wahoo SYSTM GraphQL contract as observed from the
web app (`systm.wahoofitness.com`) on **January 25, 2026**. This is not an
official API spec and may change at any time.

## Base URL

- `https://api.thesufferfest.com/graphql`

## Auth

- Authenticate with the `loginUser` mutation.
- Subsequent requests include `Authorization: Bearer <token>`.

## App Information

Most queries include an `appInformation` input with the following fields:

- `platform`: `"web"`
- `version`: e.g. `"7.101.1-web.3480-7-g4802ce80"`
- `installId`: observed on login; appears optional for other queries

## Key Operations (Observed)

### Login

```graphql
mutation LoginUser($username: String!, $password: String!, $appInformation: AppInformation!) {
  loginUser(username: $username, password: $password, appInformation: $appInformation) {
    status
    message
    token
    user { id }
  }
}
```

Notes:
- `status` has been observed as `"Success"` (capital S).

### Library

```graphql
query Library($locale: Locale!, $queryParams: QueryParams, $appInformation: AppInformation!) {
  library(locale: $locale, queryParams: $queryParams, appInformation: $appInformation) {
    content { ... }
    sports { id workoutType name description }
    channels { id name description }
  }
}
```

Notes:
- `locale` is required (web uses `"en"`).
- `content.metrics.ratings` and `content.metrics.intensityFactor` can be `null`.
- The web app also calls `cmsContent`, `equipment`, and `GetFavorites` around library navigation.

### Workout Details

```graphql
query GetWorkoutCollection($ids: [ID], $queryParams: QueryParams) {
  workouts(ids: $ids, queryParams: $queryParams) {
    id
    name
    sport
    shortDescription
    details
    level
    durationSeconds
    equipment { name description thumbnail }
    metrics { intensityFactor tss ratings { nm ac map ftp } }
    graphTriggers { time value type }
  }
}
```

Notes:
- `graphTriggers` replaces older `triggers` field.
- The older `getWorkouts(input: ...)` query used by the JS client is no longer
  used by the web app.

### Calendar / Plans

```graphql
query GetUserPlansRange($startDate: Date, $endDate: Date, $queryParams: QueryParams, $timezone: TimeZone) {
  userPlan(startDate: $startDate, endDate: $endDate, queryParams: $queryParams, timezone: $timezone) {
    day
    plannedDate
    agendaId
    status
    type
    appliedTimeZone
    wahooWorkoutId
    completionData { name date activityId durationSeconds style deleted }
    prospects {
      type
      name
      intensity { master nm ac map ftp }
      trainerSetting { mode level }
      metrics { ratings { nm ac map ftp } }
      contentId
      workoutId
      fourDPWorkoutGraph { time value type }
    }
    plan { id name color description category grouping level type }
    linkData { name date activityId durationSeconds style deleted }
  }
}
```

Notes:
- The web app uses `queryParams: { limit: 1000 }`.
- This replaces the older `getUserPlansRange(input: ...)` operation.

### Activity Search (History)

```graphql
query SearchActivities($search: ActivitySearch!, $page: PageInformation!, $appInfo: AppInformation!, $includeGraphs: Boolean) {
  searchActivities(searchParams: $search, pageInformation: $page, appInformation: $appInfo, includeGraphs: $includeGraphs) {
    activities { id name completedDate durationSeconds distanceKm tss intensityFactor analysis workoutId contentId ... }
    count
  }
}
```

Notes:
- The web app uses `sortDirection: "Descending"` and `sortKey: "date"`.
- The response includes `count` (not `total`).
- `analysis` can be `null`.

### Activity Detail

```graphql
query GetActivity($activityId: ID!) {
  activity(id: $activityId) { ... }
}
```

Notes:
- The older `getActivity(input: ...)` operation is no longer used by the web app.

### Mutations (Calendar)

Observed mutations used by the web app:

```graphql
mutation AddAgenda($contentId: ID!, $date: Date!, $timeZone: TimeZone) {
  addAgenda(contentId: $contentId, date: $date, timeZone: $timeZone) { status message agendaId }
}

mutation MoveAgenda($agendaId: ID!, $date: Date!, $timeZone: TimeZone) {
  moveAgenda(agendaId: $agendaId, date: $date, timeZone: $timeZone) { status }
}

mutation DeleteAgenda($agendaId: ID!) {
  deleteAgenda(agendaId: $agendaId) { status }
}
```

## Contract Changes vs Legacy JS Client

The following legacy operations/fields appear to be deprecated in favor of the
current web app contract:

- `getUserPlansRange(input: ...)` → **replaced by** `userPlan(startDate, endDate, queryParams, timezone)`
- `getWorkouts(input: ...)` → **replaced by** `workouts(ids, queryParams)`
- `getActivity(input: ...)` → **replaced by** `activity(id)`
- `searchActivities(input: ...)` → **replaced by** `searchActivities(searchParams, pageInformation, appInformation, includeGraphs)`
- `searchActivities.total` → **replaced by** `searchActivities.count`
- `workouts.triggers` → **replaced by** `workouts.graphTriggers`

## Notes on Nullability

Based on live traffic and direct probes:

- `content.metrics` may be present but `metrics.ratings` and `metrics.intensityFactor` can be `null`.
- `activity.analysis` can be `null`.
