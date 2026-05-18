import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: snapshot original in-memory state before each test
    original = copy.deepcopy(activities)
    yield
    # Restore original state after each test to prevent cross-test pollution
    activities.clear()
    activities.update(original)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects():
    # Arrange
    # (no setup required)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (301, 302, 307, 308)
    assert "/static/index.html" in response.headers["location"]


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200():
    # Arrange
    # (no setup required)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200


def test_get_activities_structure():
    # Arrange
    required_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")
    data = response.json()

    # Assert
    assert isinstance(data, dict)
    assert len(data) > 0
    for activity in data.values():
        assert required_fields.issubset(activity.keys())


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent_signup@test.com"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]


def test_signup_activity_not_found():
    # Arrange
    activity_name = "Unknown Activity"
    email = "student_notfound@test.com"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404


def test_signup_already_registered():
    # Arrange
    activity_name = "Chess Club"
    email = "duplicate_signup@test.com"
    client.post(f"/activities/{activity_name}/signup?email={email}")

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400


def test_signup_activity_full():
    # Arrange
    activity_name = "Chess Club"
    max_participants = activities[activity_name]["max_participants"]
    activities[activity_name]["participants"] = [
        f"filler{i}@test.com" for i in range(max_participants)
    ]

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email=overflow@test.com")

    # Assert
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

def test_unregister_success():
    # Arrange
    activity_name = "Chess Club"
    email = "unregister_me@test.com"
    client.post(f"/activities/{activity_name}/signup?email={email}")

    # Act
    response = client.post(f"/activities/{activity_name}/unregister?email={email}")

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]


def test_unregister_activity_not_found():
    # Arrange
    activity_name = "Unknown Activity"
    email = "student_unregister_notfound@test.com"

    # Act
    response = client.post(f"/activities/{activity_name}/unregister?email={email}")

    # Assert
    assert response.status_code == 404


def test_unregister_not_registered():
    # Arrange
    activity_name = "Chess Club"
    email = "not_registered@test.com"

    # Act
    response = client.post(f"/activities/{activity_name}/unregister?email={email}")

    # Assert
    assert response.status_code == 400
