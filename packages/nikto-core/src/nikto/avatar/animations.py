"""Avatar animation system — movement paths, expression transitions, talking animations."""
import math
import random
import time
from enum import Enum


class AnimationType(Enum):
    IDLE = "idle"
    TALKING = "talking"
    THINKING = "thinking"
    WORKING = "working"
    WALKING = "walking"
    POINTING = "pointing"
    GREETING = "greeting"
    LISTENING = "listening"
    CELEBRATING = "celebrating"
    TYPING = "typing"


class Expression(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SURPRISED = "surprised"
    FOCUSED = "focused"
    THINKING = "thinking"
    LISTENING = "listening"


MOUTH_SHAPES = {
    "idle": [("-", 1)],
    "talking_a": [("O", 3), ("o", 2), ("_", 1)],
    "talking_e": [("_", 2), ("o", 2), ("O", 2)],
    "talking_i": [("|", 3), ("_", 2)],
    "talking_o": [("O", 4), ("o", 2)],
    "talking_u": [("o", 3), ("_", 3)],
}


class AnimationFrame:
    def __init__(self, pose="idle", expression="neutral", duration=0.5, position=None):
        self.pose = pose
        self.expression = expression
        self.duration = duration
        self.position = position or (0, 0)

    def to_dict(self):
        return {
            "pose": self.pose,
            "expression": self.expression,
            "duration": self.duration,
            "position": self.position,
        }


ANIMATIONS = {
    AnimationType.IDLE: [
        AnimationFrame("idle", "neutral", 2.0),
        AnimationFrame("idle", "neutral", 0.3, (2, 0)),
        AnimationFrame("idle", "neutral", 1.0),
    ],
    AnimationType.TALKING: [
        AnimationFrame("idle", "happy", 0.15),
        AnimationFrame("idle", "neutral", 0.15),
        AnimationFrame("idle", "surprised", 0.15),
        AnimationFrame("idle", "neutral", 0.15),
    ],
    AnimationType.THINKING: [
        AnimationFrame("idle", "focused", 1.0),
        AnimationFrame("idle", "thinking", 1.5),
        AnimationFrame("idle", "neutral", 0.5),
    ],
    AnimationType.WORKING: [
        AnimationFrame("working", "focused", 1.5),
        AnimationFrame("working", "neutral", 0.5),
        AnimationFrame("working", "focused", 1.5),
    ],
    AnimationType.WALKING: [
        AnimationFrame("walking", "neutral", 0.3, (10, 0)),
        AnimationFrame("walking", "neutral", 0.3, (-5, 0)),
        AnimationFrame("walking", "neutral", 0.3, (10, 0)),
    ],
    AnimationType.POINTING: [
        AnimationFrame("pointing", "focused", 1.0),
        AnimationFrame("pointing", "neutral", 0.5),
    ],
    AnimationType.GREETING: [
        AnimationFrame("idle", "happy", 0.3),
        AnimationFrame("pointing", "happy", 0.5),
        AnimationFrame("idle", "happy", 0.3),
    ],
    AnimationType.LISTENING: [
        AnimationFrame("idle", "listening", 1.0),
        AnimationFrame("idle", "neutral", 0.3),
        AnimationFrame("idle", "listening", 1.0),
    ],
    AnimationType.CELEBRATING: [
        AnimationFrame("idle", "happy", 0.2),
        AnimationFrame("pointing", "happy", 0.2),
        AnimationFrame("idle", "surprised", 0.2),
        AnimationFrame("pointing", "happy", 0.2),
    ],
    AnimationType.TYPING: [
        AnimationFrame("working", "focused", 0.1),
        AnimationFrame("working", "neutral", 0.1),
    ],
}


class AnimationPlayer:
    def __init__(self):
        self.current_anim = AnimationType.IDLE
        self.frame_index = 0
        self.frame_time = 0.0
        self.looping = True
        self.start_time = time.time()

    def play(self, anim_type: AnimationType, loop=True):
        if anim_type != self.current_anim:
            self.current_anim = anim_type
            self.frame_index = 0
            self.frame_time = 0.0
            self.looping = loop
            self.start_time = time.time()

    def get_current_frame(self) -> AnimationFrame:
        frames = ANIMATIONS.get(self.current_anim, ANIMATIONS[AnimationType.IDLE])
        if not frames:
            return AnimationFrame()
        idx = min(self.frame_index, len(frames) - 1)
        return frames[idx]

    def update(self, dt: float):
        frames = ANIMATIONS.get(self.current_anim, ANIMATIONS[AnimationType.IDLE])
        if not frames:
            return
        self.frame_time += dt
        current = frames[self.frame_index]
        if self.frame_time >= current.duration:
            self.frame_time = 0
            self.frame_index += 1
            if self.frame_index >= len(frames):
                if self.looping:
                    self.frame_index = 0
                else:
                    self.frame_index = len(frames) - 1

    def get_pose_and_expression(self):
        frame = self.get_current_frame()
        return frame.pose, frame.expression, frame.position

    def set_speed(self, multiplier: float):
        for anim_list in ANIMATIONS.values():
            for frame in anim_list:
                frame.duration *= multiplier


def smooth_move(current_pos, target_pos, speed=5.0):
    dx = target_pos[0] - current_pos[0]
    dy = target_pos[1] - current_pos[1]
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 1:
        return target_pos
    step = min(speed, dist)
    ratio = step / dist
    return (current_pos[0] + dx * ratio, current_pos[1] + dy * ratio)