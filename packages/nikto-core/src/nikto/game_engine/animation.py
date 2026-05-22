"""NIKTO Animation Engine — rigging, blending, motion warping, state machines."""

import math
import time
from typing import Optional

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class Bone:
    def __init__(self, name, length=20, angle=0.0, parent=None):
        self.name = name
        self.length = length
        self.angle = angle  # Local angle relative to parent
        self.world_angle = angle
        self.parent = parent
        self.children = []
        self.x = 0.0
        self.y = 0.0
        self.end_x = 0.0
        self.end_y = 0.0
        self.target_angle = angle
        self.ik_target = None
        self.color = (200, 200, 200)

    def add_child(self, bone):
        bone.parent = self
        self.children.append(bone)
        return bone

    def get_world_angle(self):
        if self.parent:
            return self.parent.get_world_angle() + self.angle
        return self.angle

    def solve_fk(self, origin_x=0, origin_y=0):
        """Forward kinematics: compute world positions."""
        self.world_angle = self.get_world_angle()
        if self.parent:
            self.x = self.parent.end_x
            self.y = self.parent.end_y
        else:
            self.x = origin_x
            self.y = origin_y
        self.end_x = self.x + math.cos(self.world_angle) * self.length
        self.end_y = self.y + math.sin(self.world_angle) * self.length
        self.angle += (self.target_angle - self.angle) * 0.1
        for child in self.children:
            child.solve_fk()

    def solve_ik_2bone(self, target_x, target_y, upper_len, lower_len):
        """2-bone IK solver (like arm/leg)."""
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > upper_len + lower_len:
            dist = upper_len + lower_len
        cos_angle = (dist*dist + upper_len*upper_len - lower_len*lower_len) / (2 * dist * upper_len)
        cos_angle = max(-1, min(1, cos_angle))
        base_angle = math.atan2(dy, dx)
        elbow_angle = math.acos(cos_angle)
        self.target_angle = base_angle + elbow_angle
        if self.children:
            child = self.children[0]
            child.target_angle = -elbow_angle * 2

    def render(self, surface, camera=None, show_joints=True, origin_x=0, origin_y=0):
        if not PYGAME_AVAILABLE:
            return
        sx, sy = origin_x, origin_y
        if camera:
            sx, sy = camera.world_to_screen(sx, sy)
        if self.parent:
            px, py = sx, sy
            if camera:
                px, py = camera.world_to_screen(self.parent.x, self.parent.y)
            pygame.draw.line(surface, self.color, 
                           (int(px), int(py)),
                           (int(self.x + px - self.parent.x), int(self.y + py - self.parent.y)), 3)
            if show_joints:
                pygame.draw.circle(surface, (255, 255, 255), (int(self.x + px - self.parent.x), int(self.y + py - self.parent.y)), 3)
        for child in self.children:
            child.render(surface, camera, show_joints, origin_x, origin_y)

    def to_dict(self):
        return {
            "name": self.name, "length": self.length, "angle": self.angle,
            "children": [c.to_dict() for c in self.children],
        }


class Skeleton:
    def __init__(self, name="Skeleton"):
        self.name = name
        self.root_bones = []
        self.all_bones = {}

    def add_root_bone(self, bone):
        self.root_bones.append(bone)
        self._index_bones(bone)
        return bone

    def _index_bones(self, bone):
        self.all_bones[bone.name] = bone
        for child in bone.children:
            self._index_bones(child)

    def get_bone(self, name):
        return self.all_bones.get(name)

    def solve_fk(self, origin_x=0, origin_y=0):
        for bone in self.root_bones:
            bone.solve_fk(origin_x, origin_y)

    def solve_ik(self, bone_name, target_x, target_y):
        bone = self.get_bone(bone_name)
        if bone and bone.parent and bone.children:
            bone.solve_ik_2bone(target_x, target_y, bone.length, bone.children[0].length)

    def render(self, surface, camera=None, origin_x=0, origin_y=0):
        for bone in self.root_bones:
            bone.render(surface, camera, True, origin_x, origin_y)

    @classmethod
    def create_humanoid(cls):
        skel = cls("Humanoid")
        spine = Bone("spine", 40, -math.pi/2)
        skel.add_root_bone(spine)
        head = Bone("head", 15, 0)
        spine.add_child(head)
        left_arm = Bone("left_arm", 30, -0.5)
        left_forearm = Bone("left_forearm", 25, -0.5)
        left_arm.add_child(left_forearm)
        spine.add_child(left_arm)
        right_arm = Bone("right_arm", 30, 0.5)
        right_forearm = Bone("right_forearm", 25, 0.5)
        right_arm.add_child(right_forearm)
        spine.add_child(right_arm)
        left_leg = Bone("left_leg", 35, 0.3)
        left_shin = Bone("left_shin", 35, 0)
        left_leg.add_child(left_shin)
        spine.add_child(left_leg)
        right_leg = Bone("right_leg", 35, -0.3)
        right_shin = Bone("right_shin", 35, 0)
        right_leg.add_child(right_shin)
        spine.add_child(right_leg)
        return skel


class KeyFrame:
    def __init__(self, time, bone_name, angle, x=0, y=0):
        self.time = time
        self.bone_name = bone_name
        self.angle = angle
        self.x = x
        self.y = y


class AnimationClip:
    def __init__(self, name, duration=1.0, loop=True):
        self.name = name
        self.duration = duration
        self.loop = loop
        self.keyframes = []

    def add_keyframe(self, time, bone_name, angle, x=0, y=0):
        self.keyframes.append(KeyFrame(time, bone_name, angle, x, y))

    def sample(self, time, skeleton):
        if self.loop:
            time = time % self.duration
        else:
            time = min(time, self.duration)
        for bone_name in skeleton.all_bones:
            bone = skeleton.all_bones[bone_name]
            bone_kfs = [kf for kf in self.keyframes if kf.bone_name == bone_name]
            if not bone_kfs:
                continue
            before, after = None, None
            for kf in bone_kfs:
                if kf.time <= time:
                    before = kf
                if kf.time >= time and after is None:
                    after = kf
            if before and after and before != after:
                t = (time - before.time) / (after.time - before.time)
                bone.target_angle = before.angle + (after.angle - before.angle) * t
            elif before:
                bone.target_angle = before.angle

    @classmethod
    def create_walk_cycle(cls):
        anim = cls("Walk", 1.0, True)
        anim.add_keyframe(0.0, "left_leg", 0.5)
        anim.add_keyframe(0.25, "left_leg", -0.3)
        anim.add_keyframe(0.5, "left_leg", -0.5)
        anim.add_keyframe(0.75, "left_leg", 0.3)
        anim.add_keyframe(0.0, "right_leg", -0.5)
        anim.add_keyframe(0.25, "right_leg", 0.3)
        anim.add_keyframe(0.5, "right_leg", 0.5)
        anim.add_keyframe(0.75, "right_leg", -0.3)
        anim.add_keyframe(0.0, "left_arm", -0.3)
        anim.add_keyframe(0.5, "left_arm", 0.3)
        anim.add_keyframe(0.0, "right_arm", 0.3)
        anim.add_keyframe(0.5, "right_arm", -0.3)
        return anim

    @classmethod
    def create_idle_pose(cls):
        anim = cls("Idle", 2.0, True)
        for t in [0, 1.0, 2.0]:
            anim.add_keyframe(t, "spine", -math.pi/2 + math.sin(t * 2) * 0.02)
            anim.add_keyframe(t, "head", math.sin(t * 3) * 0.05)
        return anim

    @classmethod
    def create_jump_pose(cls):
        anim = cls("Jump", 0.5, False)
        anim.add_keyframe(0.0, "left_leg", 0.5)
        anim.add_keyframe(0.0, "right_leg", -0.5)
        anim.add_keyframe(0.0, "left_arm", -1.0)
        anim.add_keyframe(0.0, "right_arm", 1.0)
        anim.add_keyframe(0.25, "left_leg", -0.2)
        anim.add_keyframe(0.25, "right_leg", 0.2)
        return anim


class AnimationState:
    def __init__(self, name):
        self.name = name
        self.clip = None
        self.blend_time = 0.2
        self.next_state = None
        self.transitions = []

    def add_transition(self, to_state, condition_func):
        self.transitions.append((to_state, condition_func))

    def update(self, dt):
        if self.clip:
            self.clip.sample(time.time(), None)


class AnimationStateMachine:
    def __init__(self):
        self.states = {}
        self.current_state = None
        self.previous_state = None
        self.blend_weight = 1.0
        self.time = 0.0

    def add_state(self, state):
        self.states[state.name] = state
        return state

    def transition_to(self, name):
        if name in self.states:
            self.previous_state = self.current_state
            self.current_state = self.states[name]
            self.blend_weight = 0.0

    def update(self, dt, context=None):
        self.time += dt
        if self.current_state:
            for to_state, condition in self.current_state.transitions:
                if condition(context):
                    self.transition_to(to_state)
                    break
            self.blend_weight = min(1.0, self.blend_weight + dt / (self.current_state.blend_time or 0.2))
            self.current_state.clip.sample(self.time, context.get("skeleton") if context else None)

    def blend(self, skeleton):
        if self.previous_state and self.blend_weight < 1.0:
            self.previous_state.clip.sample(self.time, skeleton)


class MotionWarper:
    def __init__(self):
        self.target_positions = []
        self.current_position = (0, 0)
        self.warp_speed = 5.0

    def set_target(self, x, y):
        self.target_positions.append((x, y))
        if len(self.target_positions) > 10:
            self.target_positions.pop(0)

    def warp_animation(self, skeleton, target_x, target_y):
        """Warp skeleton animation to match target position."""
        root = skeleton.root_bones[0] if skeleton.root_bones else None
        if root:
            dx = target_x - root.x
            dy = target_y - root.y
            root.angle = math.atan2(dy, dx) - math.pi / 2


class AnimationController2:
    def __init__(self):
        self.skeleton = None
        self.clips = {}
        self.current_clip = None
        self.current_time = 0.0
        self.speed = 1.0
        self.blend = 0.0
        self.blend_speed = 5.0
        self.next_clip = None

    def set_skeleton(self, skeleton):
        self.skeleton = skeleton

    def add_clip(self, clip):
        self.clips[clip.name] = clip

    def play(self, name):
        if name in self.clips and name != self.current_clip:
            if self.current_clip:
                self.next_clip = self.clips[name]
            else:
                self.current_clip = self.clips[name]
                self.current_time = 0.0

    def update(self, dt):
        self.current_time += dt * self.speed
        if self.current_clip:
            self.current_clip.sample(self.current_time, self.skeleton)
        if self.next_clip:
            self.blend = min(1.0, self.blend + dt * self.blend_speed)
            self.next_clip.sample(self.current_time, self.skeleton)
            if self.blend >= 1.0:
                self.current_clip = self.next_clip
                self.next_clip = None
                self.blend = 0.0
        if self.skeleton:
            self.skeleton.solve_fk()


class SpriteSheetAnimator:
    def __init__(self):
        self.animations = {}
        self.current_anim = None
        self.frame = 0
        self.timer = 0.0
        self.fps = 12

    def add_animation(self, name, frames, fps=12, loop=True, flip_h=False):
        self.animations[name] = {"frames": frames, "fps": fps, "loop": loop, "flip_h": flip_h, "frame_count": len(frames)}

    def play(self, name):
        if name in self.animations and name != self.current_anim:
            self.current_anim = name
            self.frame = 0
            self.timer = 0.0

    def update(self, dt):
        if not self.current_anim:
            return
        anim = self.animations[self.current_anim]
        self.timer += dt
        if self.timer >= 1.0 / anim["fps"]:
            self.timer -= 1.0 / anim["fps"]
            self.frame += 1
            if self.frame >= anim["frame_count"]:
                if anim["loop"]:
                    self.frame = 0
                else:
                    self.frame = anim["frame_count"] - 1

    def get_frame(self):
        if not self.current_anim:
            return None
        anim = self.animations[self.current_anim]
        if self.frame < len(anim["frames"]):
            return anim["frames"][self.frame]
        return None
