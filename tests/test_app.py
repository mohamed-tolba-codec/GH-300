import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ACTIVITY_NAME = "Test Activity"
ACTIVITY_PATH = "Test%20Activity"
EXISTING_EMAIL = "existing@mergington.edu"


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch):
    # Arrange
    test_activities = {
        ACTIVITY_NAME: {
            "description": "A test activity",
            "schedule": "Mondays",
            "max_participants": 3,
            "participants": [EXISTING_EMAIL],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as client:
        yield client, test_activities


def test_get_activities_returns_data_without_caching(api_client):
    # Arrange
    client, test_activities = api_client

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == test_activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(api_client):
    # Arrange
    client, _ = api_client
    email = "new@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": email},
    )
    updated_activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {ACTIVITY_NAME}"
    }
    assert email in updated_activities[ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_participant(api_client):
    # Arrange
    client, _ = api_client

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": EXISTING_EMAIL},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_not_found_for_unknown_activity(api_client):
    # Arrange
    client, _ = api_client

    # Act
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "new@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(api_client):
    # Arrange
    client, _ = api_client

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": EXISTING_EMAIL},
    )
    updated_activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {EXISTING_EMAIL} from {ACTIVITY_NAME}"
    }
    assert EXISTING_EMAIL not in updated_activities[ACTIVITY_NAME]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(api_client):
    # Arrange
    client, _ = api_client

    # Act
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": EXISTING_EMAIL},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unregistered_participant(api_client):
    # Arrange
    client, _ = api_client

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": "not-registered@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"
