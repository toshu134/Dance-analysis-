import io
import pytest
from app import app
import os 


@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app"""
    app.testing = True
    with app.test_client() as client:
        yield client


def test_home_endpoint(client):
    """Test the home (/) endpoint"""
    response = client.get("/")

    # Check response status
    assert response.status_code == 200

    # Verify expected content in response
    assert b"Dance Analysis Server" in response.data


def test_upload_endpoint_with_real_file(client):
    """Test /upload endpoint with a real video file"""

    video_path = os.path.join("Dataset", "sample_dance.mp4")
    with open(video_path, "rb") as f:
        response = client.post(
            "/upload",
            content_type="multipart/form-data",
            data={"video": (f, "sample_dance.mp4")}
        )

    # Check response status
    assert response.status_code == 200

    json_data = response.get_json()
    assert "results" in json_data

    results = json_data["results"]

    # Top-level keys
    expected_keys = {"video", "total_frames", "poses_detected"}
    assert set(results.keys()) == expected_keys

    # Check poses_detected dictionary
    expected_poses = [
        "hands_up", "t_pose", "squat", "one_hand_raised",
        "standing_still", "jump", "rotation",
        "leg_raise", "step_forward", "crouch", "head_tilt"
    ]
    assert set(results["poses_detected"].keys()) == set(expected_poses)

    # Each pose count should be an integer
    for count in results["poses_detected"].values():
        assert isinstance(count, int)
