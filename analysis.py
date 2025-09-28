import cv2
import mediapipe as mp
import numpy as np
from collections import deque

# ------------------ Setup ------------------
mp_pose = mp.solutions.pose
LM = mp_pose.PoseLandmark

def to_xy(landmark):
    """
    Convert Mediapipe landmark object to (x, y) tuple.
    """
    return (landmark.x, landmark.y)

def angle_between(a, b, c):
    """
    Calculate angle ABC (in degrees) formed by three points.
    a, b, c are (x, y) coordinates.
    """
    ba = np.array([a[0] - b[0], a[1] - b[1]])
    bc = np.array([c[0] - b[0], c[1] - b[1]])
    cosang = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cosang = np.clip(cosang, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosang)))


# ------------------ Pose Check Functions ------------------
def is_hands_up(kp, thresh=0.08):
    """
    Check if both wrists are above their respective shoulders.
    """
    ls, rs = kp['LEFT_SHOULDER'][1], kp['RIGHT_SHOULDER'][1]
    lw, rw = kp['LEFT_WRIST'][1], kp['RIGHT_WRIST'][1]
    return (lw < ls - thresh) and (rw < rs - thresh)

def is_t_pose(kp, height_thresh=0.06, outward_thresh=0.05):
    """
    Check if arms are stretched out horizontally (like a T).
    """
    lw, rw = kp['LEFT_WRIST'], kp['RIGHT_WRIST']
    ls, rs = kp['LEFT_SHOULDER'], kp['RIGHT_SHOULDER']

    cond_height = abs(lw[1] - ls[1]) < height_thresh and abs(rw[1] - rs[1]) < height_thresh
    cond_outward = (lw[0] < ls[0] - outward_thresh) and (rw[0] > rs[0] + outward_thresh)
    return cond_height and cond_outward

def is_squat(kp, knee_angle_thresh=120, hip_drop_thresh=0.05):
    """
    Check if both knees are bent enough and hips are lowered.
    """
    left_knee = angle_between(kp['LEFT_HIP'], kp['LEFT_KNEE'], kp['LEFT_ANKLE'])
    right_knee = angle_between(kp['RIGHT_HIP'], kp['RIGHT_KNEE'], kp['RIGHT_ANKLE'])
    avg_knee = (left_knee + right_knee) / 2

    left_hip_drop = kp['LEFT_SHOULDER'][1] - kp['LEFT_HIP'][1]
    right_hip_drop = kp['RIGHT_SHOULDER'][1] - kp['RIGHT_HIP'][1]
    hip_drop_ok = (left_hip_drop > hip_drop_thresh) and (right_hip_drop > hip_drop_thresh)

    return avg_knee < knee_angle_thresh and hip_drop_ok

def is_one_hand_raised(kp):
    """
    Check if at least one hand is raised above the head.
    """
    lw, rw = kp['LEFT_WRIST'][1], kp['RIGHT_WRIST'][1]
    head_y = kp['NOSE'][1]
    return (lw < head_y) or (rw < head_y)

def is_jump(kp, prev_kp, jump_thresh=0.05):
    """
    Detect jumping by sudden upward movement of both ankles.
    """
    if prev_kp:
        left_ankle_delta = prev_kp['LEFT_ANKLE'][1] - kp['LEFT_ANKLE'][1]
        right_ankle_delta = prev_kp['RIGHT_ANKLE'][1] - kp['RIGHT_ANKLE'][1]
        return left_ankle_delta > jump_thresh and right_ankle_delta > jump_thresh
    return False

def is_rotation(kp, prev_kp, rot_thresh=0.05):
    """
    Detect body rotation by checking shoulder movement along x-axis.
    """
    if prev_kp:
        left_shoulder_delta = abs(prev_kp['LEFT_SHOULDER'][0] - kp['LEFT_SHOULDER'][0])
        right_shoulder_delta = abs(prev_kp['RIGHT_SHOULDER'][0] - kp['RIGHT_SHOULDER'][0])
        return (left_shoulder_delta + right_shoulder_delta) / 2 > rot_thresh
    return False

def is_leg_raise(kp, hip_thresh=0.1):
    """
    Check if either leg is lifted above hip level.
    """
    return (kp['LEFT_ANKLE'][1] < kp['LEFT_HIP'][1] - hip_thresh) or \
           (kp['RIGHT_ANKLE'][1] < kp['RIGHT_HIP'][1] - hip_thresh)

def is_crouch(kp, torso_thresh=0.05):
    """
    Detect crouching by checking if head is closer to shoulders.
    """
    nose = kp['NOSE'][1]
    shoulders = (kp['LEFT_SHOULDER'][1] + kp['RIGHT_SHOULDER'][1]) / 2
    return (nose - shoulders) > torso_thresh

def is_head_tilt(kp, tilt_thresh=0.05):
    """
    Check if head is tilted sideways compared to shoulder mid-point.
    """
    left_sh, right_sh = kp['LEFT_SHOULDER'][0], kp['RIGHT_SHOULDER'][0]
    mid = (left_sh + right_sh) / 2
    nose = kp['NOSE'][0]
    return abs(nose - mid) > tilt_thresh


# ------------------ Walking Detector ------------------
class WalkingDetector:
    """
    Detects walking by checking alternating ankle motion over frames.
    Uses a buffer of recent movements to confirm walking.
    """
    def __init__(self, buffer_size=30, x_thresh=0.02, min_alt_steps=3):
        self.left_rel = deque(maxlen=buffer_size)
        self.right_rel = deque(maxlen=buffer_size)
        self.events = deque(maxlen=buffer_size)
        self.frame_idx = 0
        self.x_thresh = x_thresh
        self.min_alt_steps = min_alt_steps

    def update(self, kp):
        """
        Update detector with new frame keypoints.
        Returns True if walking detected in this frame.
        """
        self.frame_idx += 1
        lx, _ = kp['LEFT_ANKLE']
        rx, _ = kp['RIGHT_ANKLE']
        lhx, _ = kp['LEFT_HIP']
        rhx, _ = kp['RIGHT_HIP']

        # Relative ankle position w.r.t hips
        self.left_rel.append(lx - lhx)
        self.right_rel.append(rx - rhx)

        if len(self.left_rel) < 2:
            return False

        # Detect step events (change in relative x position)
        if abs(self.left_rel[-1] - self.left_rel[-2]) > self.x_thresh:
            self.events.append(('L', self.frame_idx))
        if abs(self.right_rel[-1] - self.right_rel[-2]) > self.x_thresh:
            self.events.append(('R', self.frame_idx))

        return self.is_walking()

    def is_walking(self):
        """
        Walking is confirmed if enough alternating steps are seen recently.
        """
        if len(self.events) < self.min_alt_steps:
            return False
        last_steps = [e[0] for e in list(self.events)[-self.min_alt_steps:]]
        return all(last_steps[i] != last_steps[i+1] for i in range(len(last_steps) - 1))


# ------------------ Main Video Analysis ------------------
def analyze_video(video_path,
                  hands_thresh=0.08, t_height=0.06, t_outward=0.05,
                  knee_thresh=140, standing_thresh=0.02,
                  jump_thresh=0.05, rot_thresh=0.05):
    """
    Analyze a video and count how many frames contain certain poses.
    Returns a summary dictionary.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": f"Cannot open video: {video_path}"}

    # Pose frame counts
    pose_counts = {
        "hands_up": 0, "t_pose": 0, "squat": 0,
        "one_hand_raised": 0, "standing_still": 0,
        "jump": 0, "rotation": 0,
        "leg_raise": 0, "walking": 0, "crouch": 0, "head_tilt": 0
    }

    total_frames = 0
    prev_landmarks = None
    walk_detector = WalkingDetector(buffer_size=30, x_thresh=0.02, min_alt_steps=3)

    # Run Mediapipe pose tracking
    with mp_pose.Pose(min_detection_confidence=0.5,
                      min_tracking_confidence=0.5) as pose:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            total_frames += 1

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            if result.pose_landmarks:
                lm = result.pose_landmarks.landmark
                kp = {}
                # Store only the key landmarks needed
                for name in ['LEFT_SHOULDER','RIGHT_SHOULDER','LEFT_ELBOW','RIGHT_ELBOW',
                             'LEFT_WRIST','RIGHT_WRIST','LEFT_HIP','RIGHT_HIP',
                             'LEFT_KNEE','RIGHT_KNEE','LEFT_ANKLE','RIGHT_ANKLE','NOSE']:
                    idx = getattr(LM, name).value
                    kp[name] = to_xy(lm[idx])

                # Pose detections
                if is_hands_up(kp, hands_thresh): pose_counts['hands_up'] += 1
                if is_t_pose(kp, t_height, t_outward): pose_counts['t_pose'] += 1
                if is_squat(kp, knee_thresh): pose_counts['squat'] += 1
                if is_one_hand_raised(kp): pose_counts['one_hand_raised'] += 1
                if is_jump(kp, prev_landmarks, jump_thresh): pose_counts['jump'] += 1
                if is_rotation(kp, prev_landmarks, rot_thresh): pose_counts['rotation'] += 1
                if is_leg_raise(kp): pose_counts['leg_raise'] += 1
                if is_crouch(kp): pose_counts['crouch'] += 1
                if is_head_tilt(kp): pose_counts['head_tilt'] += 1

                # Standing still detection (very little movement between frames)
                if prev_landmarks:
                    movement = sum([np.linalg.norm(np.array(kp[k]) - np.array(prev_landmarks[k])) for k in kp])
                    if movement < standing_thresh:
                        pose_counts['standing_still'] += 1

                # Walking detection
                if walk_detector.update(kp):
                    pose_counts['walking'] += 1

                prev_landmarks = kp

    cap.release()

    # Final summary
    summary = {
        "video": video_path,
        "total_frames": total_frames,
        "poses_detected": pose_counts
    }
    return summary
