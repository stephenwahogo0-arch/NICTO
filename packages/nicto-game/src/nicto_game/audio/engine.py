"""AI Audio Engine — procedural sound effects and music generation."""

from __future__ import annotations
import math
import json
import struct
import random
import io
from typing import Optional
from pathlib import Path

from nicto_game.core.config import GameConfig, GameGenre

SOUND_DEFS: dict[str, dict] = {
    "player_shoot": {"type": "noise", "duration": 0.15, "freq_start": 800, "freq_end": 200,
                     "envelope": "decay", "noise_type": "white"},
    "enemy_shoot": {"type": "noise", "duration": 0.12, "freq_start": 400, "freq_end": 100,
                    "envelope": "decay", "noise_type": "white"},
    "player_hurt": {"type": "tone", "duration": 0.2, "freq": 150, "envelope": "decay"},
    "item_pickup": {"type": "tone", "duration": 0.15, "freq": 880, "envelope": "bell",
                    "harmonics": [(1320, 0.5), (1760, 0.3)]},
    "door_open": {"type": "noise", "duration": 0.2, "envelope": "smooth", "noise_type": "brown"},
    "footstep": {"type": "noise", "duration": 0.08, "envelope": "decay", "noise_type": "brown"},
    "explosion": {"type": "noise", "duration": 0.5, "envelope": "decay", "noise_type": "white"},
    "player_die": {"type": "tone", "duration": 0.5, "freq": 100, "envelope": "decay",
                   "harmonics": [(80, 0.7), (60, 0.3)]},
    "win": {"type": "chord", "duration": 1.0, "notes": [523, 659, 784], "envelope": "bell"},
    "ambient_wind": {"type": "noise", "duration": 2.0, "envelope": "smooth", "noise_type": "pink"},
    "coin": {"type": "tone", "duration": 0.1, "freq": 1200, "envelope": "bell",
             "harmonics": [(1500, 0.4)]},
}

GENRE_TRACKS: dict[str, list[dict]] = {
    "fps": [{"bpm": 140, "notes": ["E4", "E4", "G4", "E4", "A4", "E4", "B4", "E4"]}],
    "rpg": [{"bpm": 80, "notes": ["C4", "E4", "G4", "A4", "F4", "G4", "C5", "E5"]}],
    "dungeon": [{"bpm": 90, "notes": ["D4", "F4", "A4", "D5", "C5", "A4", "F4", "D4"]}],
    "survival": [{"bpm": 70, "notes": ["A3", "C4", "E4", "G4", "F4", "E4", "C4", "A3"]}],
}

NOTE_FREQS = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25,
    "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99,
    "A5": 880.00, "A3": 220.00, "C3": 130.81, "E3": 164.81,
}


class AudioEngine:
    """Procedural audio generation for game sound effects and music."""

    def __init__(self):
        self.sample_rate = 44100

    async def generate(self, config: GameConfig, output_dir: str) -> dict[str, str]:
        from nicto_game.assets.textures import ensure_dir
        audio_dir = Path(output_dir) / "assets" / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        generated: dict[str, str] = {}

        if config.assets.generate_audio:
            for name in ["player_shoot", "enemy_shoot", "player_hurt", "item_pickup",
                         "door_open", "footstep", "explosion", "player_die", "win",
                         "ambient_wind", "coin"]:
                wav_path = audio_dir / f"{name}.wav"
                self._generate_wav(name, str(wav_path))
                generated[name] = str(wav_path)

            if config.audio.generate_music:
                track_path = audio_dir / "music.wav"
                self._generate_music(track_path, config)
                generated["music"] = str(track_path)

        return generated

    def _generate_wav(self, name: str, output_path: str, duration: Optional[float] = None):
        sd = SOUND_DEFS.get(name, SOUND_DEFS["item_pickup"])
        dur = duration or sd.get("duration", 0.3)
        sample_count = int(self.sample_rate * dur)
        samples = []

        for i in range(sample_count):
            t = i / self.sample_rate
            envelope = self._envelope(t, dur, sd.get("envelope", "decay"))

            if sd["type"] == "noise":
                val = self._noise(sd.get("noise_type", "white"), i, self.sample_rate)
            elif sd["type"] == "tone":
                freq = sd.get("freq", 440)
                val = math.sin(2 * math.pi * freq * t)
                for hf, ha in sd.get("harmonics", []):
                    val += ha * math.sin(2 * math.pi * hf * t)
                val /= 1 + sum(ha for _, ha in sd.get("harmonics", []))
            elif sd["type"] == "chord":
                val = 0
                for note in sd.get("notes", [440]):
                    val += math.sin(2 * math.pi * note * t)
                val /= len(sd.get("notes", [1]))
            else:
                val = 0

            sample = max(-1.0, min(1.0, val * envelope))
            samples.append(int(sample * 32767))

        self._write_wav(output_path, samples)

    def _generate_music(self, output_path: Path, config: GameConfig):
        tracks = GENRE_TRACKS.get(config.genre.value, GENRE_TRACKS["rpg"])
        all_samples: list[int] = []
        for track in tracks:
            bpm = track.get("bpm", 120)
            beat_dur = 60.0 / bpm
            for note_str in track.get("notes", []):
                freq = NOTE_FREQS.get(note_str, 440)
                note_samples = int(self.sample_rate * beat_dur * 0.9)
                for i in range(note_samples):
                    t = i / self.sample_rate
                    env = self._envelope(t, beat_dur * 0.9, "bell")
                    val = math.sin(2 * math.pi * freq * t) * env * 0.4
                    all_samples.append(int(val * 32767))
                silence = int(self.sample_rate * beat_dur * 0.1)
                all_samples.extend([0] * silence)
        self._write_wav(str(output_path), all_samples)

    def _envelope(self, t: float, duration: float, env_type: str) -> float:
        if duration <= 0:
            return 0
        progress = t / duration
        if env_type == "decay":
            return max(0, 1 - progress)
        elif env_type == "bell":
            return math.sin(math.pi * progress) if progress <= 1 else 0
        elif env_type == "smooth":
            return 0.5 - 0.5 * math.cos(math.pi * progress)
        return max(0, 1 - progress)

    def _noise(self, noise_type: str, i: int, rate: int) -> float:
        if noise_type == "white":
            return random.uniform(-1, 1)
        elif noise_type == "pink":
            return self._pink_noise(i)
        elif noise_type == "brown":
            return self._brown_noise(i)
        return random.uniform(-1, 1)

    def _pink_noise(self, i: int) -> float:
        b = [0] * 7
        white = random.uniform(-1, 1)
        b[0] = 0.99886 * b[0] + white * 0.0555179
        b[1] = 0.99332 * b[1] + white * 0.0750759
        b[2] = 0.96900 * b[2] + white * 0.1538520
        b[3] = 0.86650 * b[3] + white * 0.3104856
        b[4] = 0.55000 * b[4] + white * 0.5329522
        b[5] = -0.7616 * b[5] - white * 0.0168980
        return (b[0] + b[1] + b[2] + b[3] + b[4] + b[5] + b[6] + white * 0.5362) * 0.11

    def _brown_noise(self, i: int) -> float:
        white = random.uniform(-1, 1)
        return white * 0.02

    def _write_wav(self, path: str, samples: list[int]):
        sample_count = len(samples)
        data_size = sample_count * 2
        with open(path, "wb") as f:
            f.write(b"RIFF")
            f.write(struct.pack("<I", 36 + data_size))
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write(struct.pack("<I", 16))
            f.write(struct.pack("<H", 1))
            f.write(struct.pack("<H", 1))
            f.write(struct.pack("<I", self.sample_rate))
            f.write(struct.pack("<I", self.sample_rate * 2))
            f.write(struct.pack("<H", 2))
            f.write(struct.pack("<H", 16))
            f.write(b"data")
            f.write(struct.pack("<I", data_size))
            for s in samples:
                f.write(struct.pack("<h", max(-32768, min(32767, s))))
