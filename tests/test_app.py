"""
Tests for the Mergington High School Activities API.
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_participants():
    """Restore participants lists to their original state after every test."""
    original = {name: copy.deepcopy(data["participants"]) for name, data in activities.items()}
    yield
    for name, participants in original.items():
        activities[name]["participants"] = participants


client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_get_activities_structure():
    response = client.get("/activities")
    data = response.json()
    for name, details in data.items():
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_activity_not_found():
    response = client.post(
        "/activities/Nonexistent%20Club/signup",
        params={"email": "anyone@mergington.edu"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_duplicate_registration():
    email = "duplicate@mergington.edu"
    client.post("/activities/Chess%20Club/signup", params={"email": email})
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success():
    # Use a participant that exists in the seed data
    email = "michael@mergington.edu"
    assert email in activities["Chess Club"]["participants"]
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )
    assert response.status_code == 200
    assert email in response.json()["message"]
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_activity_not_found():
    response = client.delete(
        "/activities/Nonexistent%20Club/signup",
        params={"email": "anyone@mergington.edu"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unregister_participant_not_signed_up():
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "ghost@mergington.edu"},
    )
    assert response.status_code == 404
    assert "not signed up" in response.json()["detail"].lower()


def test_signup_then_unregister():
    email = "roundtrip@mergington.edu"
    signup = client.post("/activities/Chess%20Club/signup", params={"email": email})
    assert signup.status_code == 200

    unregister = client.delete("/activities/Chess%20Club/signup", params={"email": email})
    assert unregister.status_code == 200
    assert email not in activities["Chess Club"]["participants"]
