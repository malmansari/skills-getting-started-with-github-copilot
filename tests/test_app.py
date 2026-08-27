from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)
initial_activities = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(deepcopy(initial_activities))
    yield
    activities.clear()
    activities.update(deepcopy(initial_activities))


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data():
    # Arrange
    expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == expected_participants


def test_signup_adds_participant():
    # Arrange
    activity_name = "Basketball Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{quote(activity_name)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_unknown_activity():
    # Arrange
    activity_name = "Robotics Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{quote(activity_name)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    original_participants = activities[activity_name]["participants"].copy()

    # Act
    response = client.post(f"/activities/{quote(activity_name)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up for this activity"}
    assert activities[activity_name]["participants"] == original_participants


def test_signup_requires_email():
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{quote(activity_name)}/signup")

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]


def test_remove_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_rejects_unknown_activity():
    # Arrange
    activity_name = "Robotics Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_rejects_unregistered_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}
