import os
import pytest
from analysis import analyze_video

SAMPLE_VIDEO = os.path.join("Dataset", "sample_dance.mp4")

def test_analyze_video_runs_on_sample():
    """Basic run: ensure analyze_video returns a dictionary with expected keys"""
    result = analyze_video(SAMPLE_VIDEO)
    
    assert isinstance(result, dict)
    assert "video" in result
    assert "total_frames" in result
    assert "poses_detected" in result
    assert isinstance(result["poses_detected"], dict)

def test_analyze_video_output_format():
    """Check output format and pose counts types"""
    result = analyze_video(SAMPLE_VIDEO)

    # Top-level keys
    expected_keys = {"video", "total_frames", "poses_detected"}
    assert set(result.keys()) == expected_keys

    # Types
    assert isinstance(result["video"], str)
    assert isinstance(result["total_frames"], int)
    assert isinstance(result["poses_detected"], dict)

    # Expected poses
    expected_poses = [
        "hands_up", "t_pose", "squat", "one_hand_raised",
        "standing_still", "jump", "rotation",
        "leg_raise", "step_forward", "crouch", "head_tilt"
    ]
    assert set(result["poses_detected"].keys()) == set(expected_poses)

    # Each pose count should be integer
    for pose in expected_poses:
        assert isinstance(result["poses_detected"][pose], int)

def test_analyze_video_invalid_file():
    """Should return an error dictionary if video file does not exist"""
    result = analyze_video("Dataset/non_existent.mp4")
    assert "error" in result
    assert isinstance(result["error"], str)
