import pytest
from fastapi.testclient import TestClient


class TestActivitiesAPI:
    """Test cases for the Activities API"""

    def test_get_activities(self, client: TestClient):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

        # Check that each activity has the required fields
        for activity_name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_get_root_redirect(self, client: TestClient):
        """Test root endpoint redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]

    def test_signup_successful(self, client: TestClient):
        """Test successful signup for an activity"""
        # First get activities to find one with available spots
        response = client.get("/activities")
        activities = response.json()

        # Find an activity that has available spots
        activity_name = None
        for name, details in activities.items():
            if len(details["participants"]) < details["max_participants"]:
                activity_name = name
                break

        assert activity_name is not None, "No activity with available spots found"

        # Test signup
        email = "test@example.com"
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

        # Verify the participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_activity_not_found(self, client: TestClient):
        """Test signup for non-existent activity"""
        response = client.post("/activities/NonExistentActivity/signup?email=test@example.com")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_already_registered(self, client: TestClient):
        """Test signup when student is already registered"""
        # First signup
        response = client.post("/activities/Basketball/signup?email=duplicate@example.com")
        assert response.status_code == 200

        # Try to signup again
        response = client.post("/activities/Basketball/signup?email=duplicate@example.com")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]

    def test_signup_activity_full(self, client: TestClient):
        """Test signup when activity is full"""
        # Find an activity and fill it up
        response = client.get("/activities")
        activities = response.json()

        # Find an activity with few spots
        activity_name = None
        for name, details in activities.items():
            if details["max_participants"] - len(details["participants"]) <= 2:
                activity_name = name
                break

        if activity_name:
            # Fill up the activity
            spots_left = activities[activity_name]["max_participants"] - len(activities[activity_name]["participants"])
            for i in range(spots_left):
                email = f"fillup{i}@example.com"
                response = client.post(f"/activities/{activity_name}/signup?email={email}")
                assert response.status_code == 200

            # Try to signup one more time
            response = client.post(f"/activities/{activity_name}/signup?email=overflow@example.com")
            assert response.status_code == 400

            data = response.json()
            assert "detail" in data
            assert "full" in data["detail"]

    def test_unregister_successful(self, client: TestClient):
        """Test successful unregister from an activity"""
        # First signup a participant
        email = "unregister@example.com"
        response = client.post(f"/activities/Tennis/signup?email={email}")
        assert response.status_code == 200

        # Verify they are signed up
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Tennis"]["participants"]

        # Now unregister
        response = client.delete(f"/activities/Tennis/unregister?email={email}")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Tennis" in data["message"]

        # Verify they are removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Tennis"]["participants"]

    def test_unregister_activity_not_found(self, client: TestClient):
        """Test unregister from non-existent activity"""
        response = client.delete("/activities/NonExistentActivity/unregister?email=test@example.com")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_unregister_not_signed_up(self, client: TestClient):
        """Test unregister when student is not signed up"""
        response = client.delete("/activities/Basketball/unregister?email=notsignedup@example.com")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"]