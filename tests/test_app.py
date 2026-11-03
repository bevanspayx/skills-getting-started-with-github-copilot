import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_catalog(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Practice chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": [],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(activity_catalog):
    with TestClient(app_module.app, follow_redirects=False) as test_client:
        yield test_client


def test_root_redirects_to_app(client):
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog(client, activity_catalog):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activity_catalog


def test_signup_adds_participant(client, activity_catalog):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@mergington.edu for Chess Club"
    }
    assert activity_catalog["Chess Club"]["participants"] == [
        "student@mergington.edu"
    ]


def test_signup_rejects_duplicate_participant(client, activity_catalog):
    activity_catalog["Chess Club"]["participants"].append("student@mergington.edu")

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"
    assert activity_catalog["Chess Club"]["participants"] == [
        "student@mergington.edu"
    ]


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client, activity_catalog):
    activity_catalog["Chess Club"]["participants"].append(
        "student@mergington.edu"
    )

    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered student@mergington.edu from Chess Club"
    }
    assert activity_catalog["Chess Club"]["participants"] == []


def test_unregister_returns_not_found_for_missing_signup(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up"


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
