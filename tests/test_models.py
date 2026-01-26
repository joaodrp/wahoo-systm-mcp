"""Tests for Pydantic models."""

from wahoo_systm_mcp.client.models import (
    AddAgendaResponse,
    DeleteAgendaResponse,
    EnhancedRiderProfile,
    FitnessTestDetails,
    FitnessTestResult,
    GetUserPlansRangeResponse,
    GetWorkoutsResponse,
    HeartRateZone,
    LibraryContent,
    LibraryResponse,
    LoginResponse,
    MostRecentTestResponse,
    MoveAgendaResponse,
    PowerTestValue,
    RiderProfile,
    RiderTypeInfo,
    RiderWeaknessInfo,
    SearchActivitiesResponse,
    UserPlanItem,
    WorkoutDetails,
    WorkoutIntensity,
    WorkoutProspect,
)


class TestRiderProfile:
    """Tests for RiderProfile model."""

    def test_basic_profile(self) -> None:
        profile = RiderProfile(nm=800, ac=400, map=300, ftp=250)
        assert profile.nm == 800
        assert profile.ac == 400
        assert profile.map_ == 300
        assert profile.ftp == 250

    def test_alias_serialization(self) -> None:
        profile = RiderProfile(nm=800, ac=400, map=300, ftp=250)
        data = profile.model_dump(by_alias=True)
        assert data["map"] == 300
        assert "map_" not in data

    def test_from_api_response(self) -> None:
        """Test parsing from API response format."""
        api_data = {"nm": 850, "ac": 420, "map": 310, "ftp": 260}
        profile = RiderProfile.model_validate(api_data)
        assert profile.nm == 850
        assert profile.map_ == 310


class TestPowerTestValue:
    """Tests for PowerTestValue model."""

    def test_basic_value(self) -> None:
        value = PowerTestValue(status="ok", graphValue=85, value=800)
        assert value.status == "ok"
        assert value.graph_value == 85
        assert value.value == 800

    def test_alias_parsing(self) -> None:
        data = {"status": "ok", "graphValue": 90, "value": 750}
        value = PowerTestValue.model_validate(data)
        assert value.graph_value == 90


class TestRiderTypeInfo:
    """Tests for RiderTypeInfo model."""

    def test_basic_info(self) -> None:
        info = RiderTypeInfo(
            name="Attacker",
            description="Strong short efforts",
            icon="attacker.png",
        )
        assert info.name == "Attacker"
        assert info.description == "Strong short efforts"


class TestRiderWeaknessInfo:
    """Tests for RiderWeaknessInfo model."""

    def test_basic_info(self) -> None:
        info = RiderWeaknessInfo(
            name="Sprinter",
            description="Sprint focused",
            weaknessSummary="Low endurance",
            weaknessDescription="Struggles on long climbs",
            strengthName="Sprint",
            strengthDescription="Explosive power",
            strengthSummary="Great sprinter",
        )
        assert info.name == "Sprinter"
        assert info.weakness_summary == "Low endurance"
        assert info.strength_name == "Sprint"


class TestHeartRateZone:
    """Tests for HeartRateZone model."""

    def test_with_max(self) -> None:
        zone = HeartRateZone(zone=2, name="Endurance", min=120, max=140)
        assert zone.zone == 2
        assert zone.max == 140

    def test_without_max(self) -> None:
        zone = HeartRateZone(zone=5, name="VO2 Max", min=170, max=None)
        assert zone.max is None


class TestEnhancedRiderProfile:
    """Tests for EnhancedRiderProfile model."""

    def test_full_profile(self) -> None:
        data = {
            "nm": 800,
            "ac": 400,
            "map": 300,
            "ftp": 250,
            "power5s": {"status": "ok", "graphValue": 85, "value": 800},
            "power1m": {"status": "ok", "graphValue": 80, "value": 400},
            "power5m": {"status": "ok", "graphValue": 75, "value": 300},
            "power20m": {"status": "ok", "graphValue": 70, "value": 250},
            "lactateThresholdHeartRate": 165,
            "heartRateZones": [
                {"zone": 1, "name": "Recovery", "min": 100, "max": 120},
                {"zone": 2, "name": "Endurance", "min": 120, "max": 140},
            ],
            "riderType": {
                "name": "Attacker",
                "description": "Strong attacks",
                "icon": "attacker.png",
            },
            "riderWeakness": {
                "name": "Sprinter",
                "description": "Sprint focused",
                "weaknessSummary": "Low endurance",
                "weaknessDescription": "Struggles on long climbs",
                "strengthName": "Sprint",
                "strengthDescription": "Explosive power",
                "strengthSummary": "Great sprinter",
            },
            "fitnessTestRidden": True,
            "startTime": "2024-01-01T10:00:00Z",
            "endTime": "2024-01-01T11:00:00Z",
        }
        profile = EnhancedRiderProfile.model_validate(data)
        assert profile.nm == 800
        assert profile.power_5s.value == 800
        assert profile.lactate_threshold_heart_rate == 165
        assert len(profile.heart_rate_zones) == 2
        assert profile.rider_type.name == "Attacker"
        assert profile.fitness_test_ridden is True


class TestWorkoutIntensity:
    """Tests for WorkoutIntensity model."""

    def test_basic_intensity(self) -> None:
        intensity = WorkoutIntensity(master=3, nm=4, ac=3, map=2, ftp=3)
        assert intensity.master == 3
        assert intensity.map_ == 2


class TestWorkoutProspect:
    """Tests for WorkoutProspect model."""

    def test_basic_prospect(self) -> None:
        data = {
            "type": "workout",
            "name": "Nine Hammers",
            "compatibility": "full",
            "description": "A classic",
            "style": "endurance",
            "intensity": {"master": 4, "nm": 3, "ac": 4, "map": 4, "ftp": 3},
            "plannedDuration": 3600,
            "durationType": "fixed",
            "contentId": "abc123",
            "workoutId": "xyz789",
        }
        prospect = WorkoutProspect.model_validate(data)
        assert prospect.name == "Nine Hammers"
        assert prospect.planned_duration == 3600
        intensity = prospect.intensity
        assert intensity is not None
        assert intensity.map_ == 4

    def test_with_notes(self) -> None:
        data = {
            "type": "workout",
            "name": "Test",
            "compatibility": "full",
            "description": "Desc",
            "style": "endurance",
            "intensity": {"master": 1, "nm": 1, "ac": 1, "map": 1, "ftp": 1},
            "plannedDuration": 1800,
            "durationType": "fixed",
            "contentId": "abc",
            "workoutId": "xyz",
            "notes": "Take it easy",
        }
        prospect = WorkoutProspect.model_validate(data)
        assert prospect.notes == "Take it easy"


class TestUserPlanItem:
    """Tests for UserPlanItem model."""

    def test_basic_item(self) -> None:
        data = {
            "day": 1,
            "plannedDate": "2024-01-15",
            "rank": 1,
            "agendaId": "agenda123",
            "status": "scheduled",
            "type": "workout",
            "prospects": [
                {
                    "type": "workout",
                    "name": "Test Workout",
                    "compatibility": "full",
                    "description": "A test",
                    "style": "endurance",
                    "intensity": {"master": 2, "nm": 2, "ac": 2, "map": 2, "ftp": 2},
                    "plannedDuration": 1800,
                    "durationType": "fixed",
                    "contentId": "content1",
                    "workoutId": "workout1",
                }
            ],
            "plan": {
                "id": "plan1",
                "name": "Base Training",
                "color": "#FF0000",
                "description": "Base building",
                "category": "endurance",
            },
        }
        item = UserPlanItem.model_validate(data)
        assert item.day == 1
        assert item.planned_date == "2024-01-15"
        assert item.agenda_id == "agenda123"
        prospects = item.prospects
        assert prospects is not None
        assert len(prospects) == 1
        plan = item.plan
        assert plan is not None
        assert plan.name == "Base Training"


class TestWorkoutDetails:
    """Tests for WorkoutDetails model."""

    def test_basic_details(self) -> None:
        data = {
            "id": "workout1",
            "name": "Nine Hammers",
            "sport": "cycling",
            "shortDescription": "A classic Sufferfest workout",
            "details": "Full details here",
            "level": "advanced",
            "durationSeconds": 3600,
            "equipment": [{"name": "Trainer", "description": "Smart trainer"}],
            "metrics": {
                "intensityFactor": 0.85,
                "tss": 95,
                "ratings": {"nm": 3, "ac": 4, "map": 4, "ftp": 3},
            },
            "graphTriggers": [{"time": 0, "value": 50, "type": "power"}],
        }
        details = WorkoutDetails.model_validate(data)
        assert details.name == "Nine Hammers"
        assert details.duration_seconds == 3600
        metrics = details.metrics
        assert metrics is not None
        assert metrics.tss == 95
        ratings = metrics.ratings
        assert ratings is not None
        assert ratings.map_ == 4
        assert details.graph_triggers is not None

    def test_graph_triggers(self) -> None:
        """Test that graph triggers are parsed."""
        data = {
            "id": "workout1",
            "name": "Test",
            "sport": "cycling",
            "shortDescription": "Test",
            "details": "Test",
            "level": "intermediate",
            "durationSeconds": 1800,
            "equipment": [],
            "metrics": {
                "intensityFactor": 0.75,
                "tss": 50,
                "ratings": {"nm": 2, "ac": 2, "map": 2, "ftp": 2},
            },
            "graphTriggers": [{"time": 0, "value": 100, "type": "power"}],
        }
        details = WorkoutDetails.model_validate(data)
        assert details.graph_triggers is not None
        assert details.graph_triggers[0].type == "power"


class TestLibraryContent:
    """Tests for LibraryContent model."""

    def test_minimal_content(self) -> None:
        data = {
            "id": "content1",
            "name": "Nine Hammers",
            "mediaType": "video",
            "channel": "Sufferfest",
            "workoutType": "cycling",
            "category": "threshold",
            "level": "advanced",
            "duration": 3600,
            "workoutId": "workout1",
        }
        content = LibraryContent.model_validate(data)
        assert content.name == "Nine Hammers"
        assert content.workout_type == "cycling"
        assert content.video_id is None
        assert content.metrics is None

    def test_full_content(self) -> None:
        data = {
            "id": "content1",
            "name": "Nine Hammers",
            "mediaType": "video",
            "channel": "Sufferfest",
            "workoutType": "cycling",
            "category": "threshold",
            "level": "advanced",
            "duration": 3600,
            "workoutId": "workout1",
            "videoId": "video123",
            "intensity": "High",
            "tags": ["classic", "indoor"],
            "metrics": {
                "tss": 95,
                "intensityFactor": 0.85,
                "ratings": {"nm": 3, "ac": 4, "map": 4, "ftp": 3},
            },
        }
        content = LibraryContent.model_validate(data)
        assert content.video_id == "video123"
        assert content.intensity == "High"
        assert content.tags == ["classic", "indoor"]
        assert content.metrics is not None
        assert content.metrics.tss == 95


class TestFitnessTestResult:
    """Tests for FitnessTestResult model."""

    def test_without_results(self) -> None:
        data = {
            "id": "test1",
            "name": "Full Frontal",
            "completedDate": "2024-01-10T10:00:00Z",
            "durationSeconds": 4200,
            "distanceKm": 35.5,
            "tss": 110,
            "intensityFactor": 0.92,
        }
        result = FitnessTestResult.model_validate(data)
        assert result.name == "Full Frontal"
        assert result.test_results is None

    def test_with_results(self) -> None:
        data = {
            "id": "test1",
            "name": "Full Frontal",
            "completedDate": "2024-01-10T10:00:00Z",
            "durationSeconds": 4200,
            "distanceKm": 35.5,
            "tss": 110,
            "intensityFactor": 0.92,
            "testResults": {
                "power5s": {"status": "ok", "graphValue": 85, "value": 850},
                "power1m": {"status": "ok", "graphValue": 80, "value": 420},
                "power5m": {"status": "ok", "graphValue": 75, "value": 310},
                "power20m": {"status": "ok", "graphValue": 70, "value": 260},
                "lactateThresholdHeartRate": 168,
                "riderType": {
                    "name": "Attacker",
                    "description": "Strong",
                    "icon": "attacker.png",
                },
            },
        }
        result = FitnessTestResult.model_validate(data)
        assert result.test_results is not None
        assert result.test_results.power_5s.value == 850


class TestFitnessTestDetails:
    """Tests for FitnessTestDetails model."""

    def test_full_details(self) -> None:
        data = {
            "id": "test1",
            "name": "Full Frontal",
            "completedDate": "2024-01-10T10:00:00Z",
            "durationSeconds": 4200,
            "distanceKm": 35.5,
            "tss": 110,
            "intensityFactor": 0.92,
            "notes": "Felt strong",
            "testResults": {
                "power5s": {"status": "ok", "graphValue": 85, "value": 850},
                "power1m": {"status": "ok", "graphValue": 80, "value": 420},
                "power5m": {"status": "ok", "graphValue": 75, "value": 310},
                "power20m": {"status": "ok", "graphValue": 70, "value": 260},
                "lactateThresholdHeartRate": 168,
                "riderType": {
                    "name": "Attacker",
                    "description": "Strong",
                    "icon": "attacker.png",
                },
            },
            "profile": {"nm": 850, "ac": 420, "map": 310, "ftp": 260},
            "power": [100, 150, 200],
            "cadence": [80, 85, 90],
            "heartRate": [120, 140, 160],
            "powerBests": [
                {"duration": 5, "value": 850},
                {"duration": 60, "value": 420},
            ],
            "analysis": "Great test performance",
        }
        details = FitnessTestDetails.model_validate(data)
        assert details.notes == "Felt strong"
        profile = details.profile
        assert profile is not None
        assert profile.map_ == 310
        power = details.power
        assert power is not None
        assert len(power) == 3
        power_bests = details.power_bests
        assert power_bests is not None
        assert len(power_bests) == 2
        assert power_bests[0].value == 850


class TestGraphQLResponses:
    """Tests for GraphQL response wrapper models."""

    def test_login_response(self) -> None:
        data = {
            "loginUser": {
                "status": "success",
                "message": "Logged in",
                "token": "abc123",
                "user": {"id": "user1", "profiles": {}},
            }
        }
        response = LoginResponse.model_validate(data)
        assert response.login_user.token == "abc123"

    def test_most_recent_test_response(self) -> None:
        data = {
            "mostRecentTest": {
                "status": "success",
                "message": None,
                "fitnessTestRidden": True,
                "riderType": {"name": "Attacker", "description": "Strong", "icon": "a.png"},
                "riderWeakness": {
                    "name": "Sprinter",
                    "description": "Sprint focused",
                    "weaknessSummary": "Low endurance",
                    "weaknessDescription": "Struggles",
                    "strengthName": "Sprint",
                    "strengthDescription": "Power",
                    "strengthSummary": "Great",
                },
                "power5s": {"status": "ok", "graphValue": 85, "value": 850},
                "power1m": {"status": "ok", "graphValue": 80, "value": 420},
                "power5m": {"status": "ok", "graphValue": 75, "value": 310},
                "power20m": {"status": "ok", "graphValue": 70, "value": 260},
                "lactateThresholdHeartRate": 168,
                "startTime": "2024-01-01T10:00:00Z",
                "endTime": "2024-01-01T11:00:00Z",
            }
        }
        response = MostRecentTestResponse.model_validate(data)
        assert response.most_recent_test.fitness_test_ridden is True
        assert response.most_recent_test.power_5s.value == 850

    def test_library_response(self) -> None:
        data = {
            "library": {
                "content": [
                    {
                        "id": "c1",
                        "name": "Workout 1",
                        "mediaType": "video",
                        "channel": "Sufferfest",
                        "workoutType": "cycling",
                        "category": "threshold",
                        "level": "advanced",
                        "duration": 3600,
                        "workoutId": "w1",
                    }
                ],
                "sports": [
                    {
                        "id": "s1",
                        "workoutType": "cycling",
                        "name": "Cycling",
                        "description": "Bike workouts",
                    }
                ],
                "channels": [{"id": "ch1", "name": "Sufferfest", "description": "Classic"}],
            }
        }
        response = LibraryResponse.model_validate(data)
        assert len(response.library.content) == 1
        assert response.library.content[0].name == "Workout 1"

    def test_add_agenda_response(self) -> None:
        data = {"addAgenda": {"status": "success", "message": None, "agendaId": "agenda1"}}
        response = AddAgendaResponse.model_validate(data)
        assert response.add_agenda.agenda_id == "agenda1"

    def test_move_agenda_response(self) -> None:
        data = {"moveAgenda": {"status": "success"}}
        response = MoveAgendaResponse.model_validate(data)
        assert response.move_agenda.status == "success"

    def test_delete_agenda_response(self) -> None:
        data = {"deleteAgenda": {"status": "success"}}
        response = DeleteAgendaResponse.model_validate(data)
        assert response.delete_agenda.status == "success"

    def test_search_activities_response(self) -> None:
        data = {
            "searchActivities": {
                "activities": [
                    {
                        "id": "a1",
                        "name": "Full Frontal",
                        "completedDate": "2024-01-10T10:00:00Z",
                        "durationSeconds": 4200,
                        "distanceKm": 35.5,
                        "tss": 110,
                        "intensityFactor": 0.92,
                    }
                ],
                "count": 1,
            }
        }
        response = SearchActivitiesResponse.model_validate(data)
        assert response.search_activities.count == 1
        assert response.search_activities.activities[0].name == "Full Frontal"

    def test_get_user_plans_range_response(self) -> None:
        data = {
            "userPlan": [
                {
                    "day": 1,
                    "plannedDate": "2024-01-15",
                    "rank": 1,
                    "agendaId": "agenda1",
                    "status": "scheduled",
                    "type": "workout",
                    "prospects": [],
                    "plan": {
                        "id": "plan1",
                        "name": "Base",
                        "color": "#FF0000",
                        "description": "Base plan",
                        "category": "endurance",
                    },
                }
            ]
        }
        response = GetUserPlansRangeResponse.model_validate(data)
        assert len(response.user_plan) == 1
        assert response.user_plan[0].agenda_id == "agenda1"

    def test_get_workouts_response(self) -> None:
        data = {
            "workouts": [
                {
                    "id": "w1",
                    "name": "Nine Hammers",
                    "sport": "cycling",
                    "shortDescription": "Classic",
                    "details": "Full details",
                    "level": "advanced",
                    "durationSeconds": 3600,
                    "equipment": [],
                    "metrics": {
                        "intensityFactor": 0.85,
                        "tss": 95,
                        "ratings": {"nm": 3, "ac": 4, "map": 4, "ftp": 3},
                    },
                    "graphTriggers": [{"time": 0, "value": 50, "type": "power"}],
                }
            ]
        }
        response = GetWorkoutsResponse.model_validate(data)
        assert len(response.workouts) == 1
        assert response.workouts[0].name == "Nine Hammers"
