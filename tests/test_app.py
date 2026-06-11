"""
Backend tests for Mergington High School Activities API

Tests follow the AAA pattern:
- Arrange: Set up test data and fixtures
- Act: Execute the API call
- Assert: Verify the response
"""

import pytest
from httpx import AsyncClient
from src.app import app


@pytest.fixture
async def client():
    """Fixture providing an async HTTP client for testing the FastAPI app"""
    async with AsyncClient(app=app, base_url="http://test") as async_client:
        yield async_client


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    @pytest.mark.asyncio
    async def test_get_activities_returns_all_activities(self, client):
        """Verify that GET /activities returns all available activities"""
        # Arrange
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Training",
            "Swim Club",
            "Art Studio",
            "Drama Club",
            "Debate Team",
            "Science Olympiad",
        ]

        # Act
        response = await client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        for activity_name in expected_activities:
            assert activity_name in data
            assert "description" in data[activity_name]
            assert "schedule" in data[activity_name]
            assert "max_participants" in data[activity_name]
            assert "participants" in data[activity_name]
            assert isinstance(data[activity_name]["participants"], list)

    @pytest.mark.asyncio
    async def test_get_activities_participants_list_contains_emails(self, client):
        """Verify that participants list contains email strings"""
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = await client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        participants = data[activity_name]["participants"]
        assert len(participants) > 0
        for participant in participants:
            assert isinstance(participant, str)
            assert "@" in participant


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    @pytest.mark.asyncio
    async def test_signup_for_activity_adds_participant(self, client):
        """Verify that signup adds a new participant to an activity"""
        # Arrange
        activity_name = "Chess Club"
        test_email = "newstudent@mergington.edu"

        # Act
        response = await client.post(
            f"/activities/{activity_name}/signup?email={test_email}",
            params={"email": test_email},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert test_email in data["message"]

        # Verify participant was added by fetching activities
        activities_response = await client.get("/activities")
        activities_data = activities_response.json()
        assert test_email in activities_data[activity_name]["participants"]

    @pytest.mark.asyncio
    async def test_signup_duplicate_participant_returns_error(self, client):
        """Verify that signing up the same student twice returns an error"""
        # Arrange
        activity_name = "Chess Club"
        duplicate_email = "michael@mergington.edu"  # Already signed up

        # Act
        response = await client.post(
            f"/activities/{activity_name}/signup?email={duplicate_email}",
            params={"email": duplicate_email},
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_signup_for_nonexistent_activity_returns_404(self, client):
        """Verify that signing up for a non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Club"
        test_email = "student@mergington.edu"

        # Act
        response = await client.post(
            f"/activities/{activity_name}/signup?email={test_email}",
            params={"email": test_email},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    @pytest.mark.asyncio
    async def test_remove_participant_unregisters_student(self, client):
        """Verify that removing a participant unregisters them from the activity"""
        # Arrange
        activity_name = "Chess Club"
        test_email = "removestudent@mergington.edu"

        # First, sign up the student
        await client.post(
            f"/activities/{activity_name}/signup?email={test_email}",
            params={"email": test_email},
        )

        # Act
        response = await client.delete(
            f"/activities/{activity_name}/participants?email={test_email}",
            params={"email": test_email},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert test_email in data["message"]

        # Verify participant was removed by fetching activities
        activities_response = await client.get("/activities")
        activities_data = activities_response.json()
        assert test_email not in activities_data[activity_name]["participants"]

    @pytest.mark.asyncio
    async def test_remove_nonexistent_participant_returns_404(self, client):
        """Verify that removing a non-existent participant returns 404"""
        # Arrange
        activity_name = "Chess Club"
        nonexistent_email = "nosuchstudent@mergington.edu"

        # Act
        response = await client.delete(
            f"/activities/{activity_name}/participants?email={nonexistent_email}",
            params={"email": nonexistent_email},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_remove_participant_from_nonexistent_activity_returns_404(self, client):
        """Verify that removing a participant from non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Club"
        test_email = "student@mergington.edu"

        # Act
        response = await client.delete(
            f"/activities/{activity_name}/participants?email={test_email}",
            params={"email": test_email},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestWorkflow:
    """Integration tests for common workflows"""

    @pytest.mark.asyncio
    async def test_complete_signup_and_removal_workflow(self, client):
        """Verify a complete workflow: signup, verify, remove"""
        # Arrange
        activity_name = "Programming Class"
        workflow_email = "workflowstudent@mergington.edu"

        # Act 1: Get initial participant count
        initial_response = await client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        # Act 2: Sign up
        signup_response = await client.post(
            f"/activities/{activity_name}/signup?email={workflow_email}",
            params={"email": workflow_email},
        )

        # Assert signup success
        assert signup_response.status_code == 200

        # Act 3: Verify participant was added
        check_response = await client.get("/activities")
        updated_count = len(check_response.json()[activity_name]["participants"])

        # Assert participant count increased
        assert updated_count == initial_count + 1
        assert workflow_email in check_response.json()[activity_name]["participants"]

        # Act 4: Remove participant
        remove_response = await client.delete(
            f"/activities/{activity_name}/participants?email={workflow_email}",
            params={"email": workflow_email},
        )

        # Assert removal success
        assert remove_response.status_code == 200

        # Act 5: Verify participant was removed
        final_response = await client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])

        # Assert participant count returned to original
        assert final_count == initial_count
        assert workflow_email not in final_response.json()[activity_name]["participants"]
