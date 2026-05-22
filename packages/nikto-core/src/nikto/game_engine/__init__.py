"""NIKTO Game Engine — complete real-time game engine with ECS, rendering, physics, audio, AI, VFX, animation."""

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from .core import (
    Transform, SpriteRenderer, PhysicsBody, BoxCollider, CircleCollider,
    Camera, AudioSource, ParticleSystem, TextLabel, Button, Light,
    AnimationController, GameObject, GameScene, NIKTOCoreEngine,
)
from .renderer import (
    RenderLayer, ShadowCaster, Material, PostProcessor, DecalRenderer, SkyboxRenderer,
)
from .physics import (
    Vec2, RigidBody, Joint, DistanceJoint, SpringJoint, HingeJoint,
    PhysicsMaterial, SoftBody, DestructionSystem, PhysicsWorld,
)
from .audio import (
    AudioClip, AudioSource3D, AudioListener, AudioBus, AudioEffect,
    LowPassFilter, HighPassFilter, ReverbEffect, ChorusEffect, DelayEffect,
    AudioMixer, Synthesizer, AudioManager,
)
from .ai import (
    BTNode, BTAction, BTCondition, BTSequence, BTSelector, BTInverter,
    BTSucceeder, BTRepeater, BTParallel, BehaviourTree, StateMachine,
    UtilityConsideration, UtilityAction, UtilityAI,
    NavNode, NavGrid, AIController,
)
from .vfx import (
    Particle, EmitterModule, Emitter, VFXPresets, VFXSystem,
)
from .animation import (
    Bone, Skeleton, KeyFrame, AnimationClip, AnimationState,
    AnimationStateMachine, MotionWarper, AnimationController2, SpriteSheetAnimator,
)
from .visual_script import (
    Node, NodeGraph, BlueprintManager,
)

__all__ = [
    "Transform", "SpriteRenderer", "PhysicsBody", "BoxCollider", "CircleCollider",
    "Camera", "AudioSource", "ParticleSystem", "TextLabel", "Button", "Light",
    "AnimationController", "GameObject", "GameScene", "NIKTOCoreEngine",
    "RenderLayer", "ShadowCaster", "Material", "PostProcessor", "DecalRenderer", "SkyboxRenderer",
    "Vec2", "RigidBody", "Joint", "DistanceJoint", "SpringJoint", "HingeJoint",
    "PhysicsMaterial", "SoftBody", "DestructionSystem", "PhysicsWorld",
    "AudioClip", "AudioSource3D", "AudioListener", "AudioBus", "AudioEffect",
    "LowPassFilter", "HighPassFilter", "ReverbEffect", "ChorusEffect", "DelayEffect",
    "AudioMixer", "Synthesizer", "AudioManager",
    "BTNode", "BTAction", "BTCondition", "BTSequence", "BTSelector", "BTInverter",
    "BTSucceeder", "BTRepeater", "BTParallel", "BehaviourTree", "StateMachine",
    "UtilityConsideration", "UtilityAction", "UtilityAI",
    "NavNode", "NavGrid", "AIController",
    "Particle", "EmitterModule", "Emitter", "VFXPresets", "VFXSystem",
    "Bone", "Skeleton", "KeyFrame", "AnimationClip", "AnimationState",
    "AnimationStateMachine", "MotionWarper", "AnimationController2", "SpriteSheetAnimator",
    "Node", "NodeGraph", "BlueprintManager",
]
