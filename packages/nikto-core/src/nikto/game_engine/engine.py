"""Nikto Game Engine — generates complete 3D games from text prompts using Godot."""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class GameGenre(str, Enum):
    RACING = "racing"
    FPS = "fps"
    BATTLE_ROYALE = "battle_royale"
    OPEN_WORLD = "open_world"
    PLATFORMER = "platformer"
    RPG = "rpg"
    STRATEGY = "strategy"
    SIMULATION = "simulation"
    PUZZLE = "puzzle"
    CUSTOM = "custom"


@dataclass
class GameAsset:
    name: str
    asset_type: str  # scene, script, texture, model, audio, font
    content: str = ""
    path: str = ""


@dataclass
class GameProject:
    title: str
    genre: GameGenre
    description: str = ""
    resolution: tuple = (1920, 1080)
    assets: list[GameAsset] = field(default_factory=list)
    output_dir: str = ""
    godot_version: str = "4.3"
    created_at: datetime = field(default_factory=datetime.now)
    project_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "genre": self.genre.value,
            "description": self.description[:100],
            "resolution": f"{self.resolution[0]}x{self.resolution[1]}",
            "assets": len(self.assets),
            "output_dir": self.output_dir,
            "godot_version": self.godot_version,
            "project_id": self.project_id,
        }


class SceneGenerator:
    """Generates Godot 3D scene files (.tscn) from game descriptions."""

    @staticmethod
    def generate_main_scene() -> str:
        return """[gd_scene load_steps=2 format=3 uid="uid://main"]

[ext_resource type="Script" path="res://main.gd" id="1"]

[node name="World" type="Node3D"]
script = ExtResource("1")

[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]
transform = Transform3D(1, 0, 0, 0, -0.5, 0.866, 0, 0.866, 0.5, 0, 10, 0)
shadow_enabled = true

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 5, 10)
current = true
"""

    @staticmethod
    def generate_3d_scene(genre: GameGenre) -> str:
        scenes = {
            GameGenre.RACING: """[gd_scene load_steps=2 format=3 uid="uid://racer"]

[node name="Track" type="Node3D"]

[node name="Ground" type="MeshInstance3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.5, 0)
mesh = SubResource(1)

[node name="PlayerCar" type="VehicleBody3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.5, 0)

[node name="CollisionShape3D" type="CollisionShape3D" parent="PlayerCar"]
shape = SubResource(2)

[node name="MeshInstance3D" type="MeshInstance3D" parent="PlayerCar"]
mesh = SubResource(3)
""",
            GameGenre.FPS: """[gd_scene load_steps=2 format=3 uid="uid://fps"]

[node name="Level" type="Node3D"]

[node name="WorldEnvironment" type="WorldEnvironment" parent="."]
environment = SubResource(1)

[node name="Player" type="CharacterBody3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0)

[node name="Camera3D" type="Camera3D" parent="Player"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.7, 0)
current = true

[node name="GunPivot" type="Node3D" parent="Player/Camera3D"]
""",
            GameGenre.BATTLE_ROYALE: """[gd_scene load_steps=2 format=3 uid="uid://br"]

[node name="Island" type="Node3D"]

[node name="Terrain" type="MeshInstance3D" parent="."]
mesh = SubResource(1)

[node name="Player" type="CharacterBody3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -50, 1, -50)

[node name="Camera3D" type="Camera3D" parent="Player"]
current = true
""",
        }
        return scenes.get(genre, SceneGenerator.generate_main_scene())

    @staticmethod
    def generate_subresources() -> str:
        return """[sub_resource type="BoxMesh" id=1]
size = Vector3(1000, 1, 1000)
material = SubResource(4)

[sub_resource type="BoxShape3D" id=2]
size = Vector3(2, 1, 4)

[sub_resource type="BoxMesh" id=3]
size = Vector3(2, 1, 4)

[sub_resource type="StandardMaterial3D" id=4]
albedo_color = Color(0.2, 0.6, 0.8)

[sub_resource type="Environment" id=5]
background_color = Color(0.3, 0.5, 0.8)
ambient_light_color = Color(0.2, 0.3, 0.5)
"""


class ScriptGenerator:
    """Generates Godot GDScript files for game logic."""

    @staticmethod
    def generate_main_script(genre: GameGenre, title: str) -> str:
        scripts = {
            GameGenre.RACING: """extends Node3D

var speed = 0.0
var max_speed = 100.0
var acceleration = 5.0
var steering = 0.0

func _ready():
    Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
    $PlayerCar/EngineSound.play()

func _process(delta):
    var steer = 0
    if Input.is_action_pressed("ui_left"): steer = -1
    if Input.is_action_pressed("ui_right"): steer = 1
    steering = lerp(steering, steer * 0.5, delta * 5)
    $PlayerCar.steering = steering

    var throttle = 0
    if Input.is_action_pressed("ui_up"): throttle = 1
    if Input.is_action_pressed("ui_down"): throttle = -1
    speed += throttle * acceleration * delta
    speed = clamp(speed, -max_speed * 0.3, max_speed)
    $PlayerCar.engine_force = speed

func _physics_process(delta):
    $Camera3D.position = $PlayerCar.position + Vector3(0, 5, -8)
    $Camera3D.look_at($PlayerCar.position)
""",
            GameGenre.FPS: """extends Node3D

var mouse_sensitivity = 0.002
var movement_speed = 5.0
var jump_velocity = 4.5
var gravity = 9.8
var velocity = Vector3.ZERO
var health = 100
var ammo = 30

func _ready():
    Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _input(event):
    if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
        $Player/Camera3D.rotation.x -= event.relative.y * mouse_sensitivity
        $Player/Camera3D.rotation.x = clamp($Player/Camera3D.rotation.x, -1.5, 1.5)
        rotation.y -= event.relative.x * mouse_sensitivity

func _process(delta):
    if Input.is_action_just_pressed("ui_cancel"):
        Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE if Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED else Input.MOUSE_MODE_CAPTURED)
    if Input.is_action_just_pressed("ui_accept"):
        shoot()

func shoot():
    var space_state = get_world_3d().direct_space_state
    var cam = $Player/Camera3D
    var from = cam.global_position
    var to = from - cam.global_transform.basis.z * 100
    var query = PhysicsRayQueryParameters3D.create(from, to)
    var hit = space_state.intersect_ray(query)
    if hit:
        $HitEffect.position = hit.position
        $HitEffect.emitting = true

func _physics_process(delta):
    var input = Vector3.ZERO
    if Input.is_action_pressed("ui_up"): input.z -= 1
    if Input.is_action_pressed("ui_down"): input.z += 1
    if Input.is_action_pressed("ui_left"): input.x -= 1
    if Input.is_action_pressed("ui_right"): input.x += 1
    input = input.normalized()
    velocity.x = input.x * movement_speed
    velocity.z = input.z * movement_speed
    velocity = $Player.transform.basis * velocity
    velocity.y -= gravity * delta
    if Input.is_action_just_pressed("ui_select") and $Player.is_on_floor():
        velocity.y = jump_velocity
    $Player.velocity = velocity
    $Player.move_and_slide()
""",
            GameGenre.BATTLE_ROYALE: """extends Node3D

var players = {}
var zone_radius = 100.0
var zone_position = Vector3.ZERO
var zone_shrinking = false
var game_time = 0.0
var loot_items = []

func _ready():
    spawn_loot()
    spawn_players()
    $ZoneTimer.start()

func _process(delta):
    game_time += delta
    if game_time > 30 and not zone_shrinking:
        shrink_zone()

func spawn_loot():
    var locations = [Vector3(10, 0, 10), Vector3(-10, 0, 10), Vector3(10, 0, -10), Vector3(-10, 0, -10)]
    for loc in locations:
        var chest = MeshInstance3D.new()
        chest.mesh = BoxMesh.new()
        chest.position = loc
        add_child(chest)

func spawn_players():
    var spawns = [Vector3(-40, 0, -40), Vector3(40, 0, 40), Vector3(-40, 0, 40), Vector3(40, 0, -40)]

func shrink_zone():
    zone_shrinking = true
    var tween = create_tween()
    tween.tween_property(self, "zone_radius", 20.0, 60.0)
""",
        }
        return scripts.get(genre, """extends Node3D

func _ready():
    $DirectionalLight3D.shadow_enabled = true
    print("Game started: """ + title + """")

func _process(delta):
    if Input.is_action_just_pressed("ui_cancel"):
        get_tree().quit()
""")

    @staticmethod
    def generate_input_map() -> str:
        return """[remap]

path="res://inputmap.gd"

[input]
ui_up={
"deadzone": 0.5,
"events": [{"type": 7, "keycode": 87}, {"type": 7, "keycode": 79}]
}
ui_down={
"deadzone": 0.5,
"events": [{"type": 7, "keycode": 83}, {"type": 7, "keycode": 75}]
}
ui_left={
"deadzone": 0.5,
"events": [{"type": 7, "keycode": 65}, {"type": 7, "keycode": 81}]
}
ui_right={
"deadzone": 0.5,
"events": [{"type": 7, "keycode": 68}, {"type": 7, "keycode": 69}]
}
ui_accept={
"deadzone": 0.5,
"events": [{"type": 7, "keycode": 32}]
}
ui_cancel={
"deadzone": 0.5,
"events": [{"type": 7, "keycode": 4194305}]
}
ui_select={
"deadzone": 0.5,
"events": [{"type": 7, "keycode": 32}]
}
"""


class ProjectGenerator:
    """Generates complete Godot project structure."""

    @staticmethod
    def generate_project(project: GameProject) -> str:
        output_dir = Path(project.output_dir) / project.project_id
        output_dir.mkdir(parents=True, exist_ok=True)

        ProjectGenerator._write_project_file(output_dir, project)
        ProjectGenerator._write_main_tscn(output_dir, project)
        ProjectGenerator._write_main_gd(output_dir, project)
        ProjectGenerator._write_input_map(output_dir)

        logger.info(f"Game project generated at {output_dir}")
        return str(output_dir)

    @staticmethod
    def _write_project_file(output_dir: Path, project: GameProject):
        content = f"""; Nikto Game Engine — {project.title}
; Genre: {project.genre.value}
; Generated: {project.created_at.isoformat()}
; Game Engine AI: NIKTO

config_version=5

[application]
config/name="{project.title}"
config/description="{project.description}"
run/main_scene="res://main.tscn"
config/icon="res://icon.svg"

[display]
window/size/viewport_width={project.resolution[0]}
window/size/viewport_height={project.resolution[1]}
window/size/mode=0
window/size/resizable=true

[rendering]
renderer/rendering_method="forward_plus"
environment/defaults/default_clear_color=Color(0.3, 0.5, 0.8, 1)
"""
        (output_dir / "project.godot").write_text(content)

    @staticmethod
    def _write_main_tscn(output_dir: Path, project: GameProject):
        scene = SceneGenerator.generate_main_scene()
        scene_3d = SceneGenerator.generate_3d_scene(project.genre)
        sub = SceneGenerator.generate_subresources()
        (output_dir / "main.tscn").write_text(scene + "\n" + sub)
        (output_dir / "world.tscn").write_text(scene_3d + "\n" + sub)
        # Create icon
        (output_dir / "icon.svg").write_text("""<svg width="128" height="128"><rect width="128" height="128" fill="#1a1a2e"/><text x="64" y="72" text-anchor="middle" fill="#00ffff" font-size="28" font-family="monospace">N</text></svg>""")

    @staticmethod
    def _write_main_gd(output_dir: Path, project: GameProject):
        script = ScriptGenerator.generate_main_script(project.genre, project.title)
        (output_dir / "main.gd").write_text(script)

    @staticmethod
    def _write_input_map(output_dir: Path):
        (output_dir / "inputmap.gd").write_text(ScriptGenerator.generate_input_map())


class GameEngine:
    """Main game engine interface — generate, manage, and export games."""

    def __init__(self, output_base: str = ""):
        self.output_base = Path(output_base or Path(tempfile.gettempdir()) / "nikto_games")
        self.output_base.mkdir(parents=True, exist_ok=True)
        self.projects: dict[str, GameProject] = {}

    async def generate_game(self, prompt: str, title: str = "", genre: str = "", resolution: str = "1920x1080") -> dict:
        detected_genre = self._detect_genre(prompt)
        if genre and genre in [g.value for g in GameGenre]:
            detected_genre = GameGenre(genre)
        title = title or self._generate_title(prompt, detected_genre)
        w, h = [int(x) for x in resolution.split("x")] if "x" in resolution else (1920, 1080)

        project = GameProject(
            title=title,
            genre=detected_genre,
            description=prompt[:500],
            resolution=(w, h),
            output_dir=str(self.output_base),
        )

        output_path = ProjectGenerator.generate_project(project)
        project.output_dir = output_path
        self.projects[project.project_id] = project

        return {
            "success": True,
            "project_id": project.project_id,
            "title": title,
            "genre": detected_genre.value,
            "output_path": output_path,
            "resolution": f"{w}x{h}",
            "assets_count": len(project.assets),
            "prompt": prompt[:200],
            "message": f"Game '{title}' generated at {output_path}. Open with Godot {project.godot_version}.",
        }

    async def export_game(self, project_id: str, export_format: str = "windows") -> dict:
        project = self.projects.get(project_id)
        if not project:
            return {"success": False, "error": f"Project {project_id} not found"}
        return {
            "success": True,
            "message": f"Project '{project.title}' ready for export to {export_format}. Use Godot headless to build.",
            "project_path": project.output_dir,
        }

    async def list_games(self) -> list[dict]:
        return [p.to_dict() for p in self.projects.values()]

    def _detect_genre(self, prompt: str) -> GameGenre:
        p = prompt.lower()
        if any(w in p for w in ["race", "racing", "car", "drive", "speed", "track", "formula"]):
            return GameGenre.RACING
        if any(w in p for w in ["fps", "shoot", "gun", "battle", "war", "soldier", "call of duty", "combat"]):
            return GameGenre.FPS
        if any(w in p for w in ["battle royale", "fortnite", "last standing", "100 players"]):
            return GameGenre.BATTLE_ROYALE
        if any(w in p for w in ["open world", "explore", "adventure", "rpg"]):
            return GameGenre.OPEN_WORLD
        if any(w in p for w in ["platform", "jump", "mario", "2d"]):
            return GameGenre.PLATFORMER
        if any(w in p for w in ["simulation", "sim", "city", "build", "tycoon"]):
            return GameGenre.SIMULATION
        if any(w in p for w in ["puzzle", "match", "solve", "brain"]):
            return GameGenre.PUZZLE
        if any(w in p for w in ["strategy", "rts", "tower", "defense", "chess"]):
            return GameGenre.STRATEGY
        return GameGenre.CUSTOM

    def _generate_title(self, prompt: str, genre: GameGenre) -> str:
        words = [w.capitalize() for w in prompt.split()[:3] if len(w) > 2]
        prefix = {
            GameGenre.RACING: "Turbo",
            GameGenre.FPS: "Steel",
            GameGenre.BATTLE_ROYALE: "Apex",
            GameGenre.OPEN_WORLD: "Vast",
            GameGenre.SIMULATION: "Ultimate",
        }.get(genre, "Neon")
        suffix = {
            GameGenre.RACING: "Rivals",
            GameGenre.FPS: "Fire",
            GameGenre.BATTLE_ROYALE: "Storm",
            GameGenre.OPEN_WORLD: "Frontier",
            GameGenre.SIMULATION: "Tycoon",
        }.get(genre, "Quest")
        base = " ".join(words[:2]) if words else f"{prefix} {suffix}"
        return f"{prefix} {base} {suffix}"[:64]
