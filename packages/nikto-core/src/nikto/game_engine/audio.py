"""NIKTO Audio Engine — 3D positional audio, DSP effects, streaming, synthesis."""

import math
import struct
import random
from typing import Optional

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class AudioClip:
    def __init__(self, name, filepath=None, duration=0.0, sample_rate=44100):
        self.name = name
        self.filepath = filepath
        self.duration = duration
        self.sample_rate = sample_rate
        self._sound = None
        self._loaded = False

    def load(self):
        if not PYGAME_AVAILABLE:
            return
        if self._loaded:
            return
        if self.filepath:
            try:
                self._sound = pygame.mixer.Sound(self.filepath)
                self._loaded = True
            except Exception:
                self._sound = None


class AudioSource3D:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.velocity_x = 0
        self.velocity_y = 0
        self.velocity_z = 0
        self.clip = None
        self.volume = 1.0
        self.pitch = 1.0
        self.loop = False
        self.min_distance = 100.0
        self.max_distance = 500.0
        self.rolloff = 1.5
        self._channel = None
        self._playing = False
        self._paused = False

    def play(self):
        if not self.clip or not PYGAME_AVAILABLE:
            return
        self.clip.load()
        if self.clip._sound:
            self._channel = self.clip._sound.play(-1 if self.loop else 0)
            self._playing = True
            self._paused = False

    def stop(self):
        if self._channel:
            self._channel.stop()
        self._playing = False
        self._paused = False

    def pause(self):
        if self._channel:
            self._channel.pause()
            self._paused = True

    def resume(self):
        if self._channel and self._paused:
            self._channel.unpause()
            self._paused = False

    def update_3d(self, listener):
        """Update volume/pan based on listener position (3D audio)."""
        if not self._playing or not self._channel:
            return
        dx = self.x - listener.x
        dy = self.y - listener.y
        dz = self.z - listener.z
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        if distance < self.min_distance:
            vol = 1.0
        elif distance > self.max_distance:
            vol = 0.0
        else:
            vol = 1.0 - ((distance - self.min_distance) / (self.max_distance - self.min_distance)) ** self.rolloff
        pan = 0.0
        if distance > 0:
            pan = dx / distance * 0.5
            pan = max(-0.5, min(0.5, pan))
        self._channel.set_volume(vol * self.volume)
        # Doppler effect (pitch shift based on relative velocity)
        rvx = self.velocity_x - listener.velocity_x
        rvy = self.velocity_y - listener.velocity_y
        rel_speed = (dx * rvx + dy * rvy) / distance if distance > 0 else 0
        doppler = 1.0 + rel_speed / 34300.0  # speed of sound in px/s
        doppler = max(0.5, min(2.0, doppler))
        self._channel.set_volume(vol * self.volume)


class AudioListener:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.velocity_z = 0.0
        self.forward = (0, 0, -1)
        self.up = (0, 1, 0)


class AudioBus:
    def __init__(self, name, volume=1.0):
        self.name = name
        self.volume = volume
        self.effects = []
        self.sources = []

    def add_effect(self, effect):
        self.effects.append(effect)

    def add_source(self, source):
        self.sources.append(source)
        return source

    def process(self, samples):
        for effect in self.effects:
            samples = effect.process(samples)
        return samples


class AudioEffect:
    def process(self, samples):
        return samples


class LowPassFilter(AudioEffect):
    def __init__(self, cutoff=0.5):
        self.cutoff = cutoff
        self.prev_out = 0.0
        self.prev_in = 0.0

    def process(self, samples):
        result = []
        rc = 1.0 / (self.cutoff * 2 * math.pi)
        dt = 1.0 / 44100.0
        alpha = dt / (rc + dt)
        for s in samples:
            out = self.prev_out + alpha * (s - self.prev_out)
            self.prev_out = out
            result.append(out)
        return result


class HighPassFilter(AudioEffect):
    def __init__(self, cutoff=0.5):
        self.cutoff = cutoff
        self.prev_out = 0.0
        self.prev_in = 0.0

    def process(self, samples):
        result = []
        rc = 1.0 / (self.cutoff * 2 * math.pi)
        dt = 1.0 / 44100.0
        alpha = rc / (rc + dt)
        for s in samples:
            out = alpha * (self.prev_out + s - self.prev_in)
            self.prev_in = s
            self.prev_out = out
            result.append(out)
        return result


class ReverbEffect(AudioEffect):
    def __init__(self, decay=0.3, delay_samples=1000):
        self.decay = decay
        self.delay_samples = delay_samples
        self.buffer = [0.0] * delay_samples
        self.index = 0

    def process(self, samples):
        result = []
        for s in samples:
            delayed = self.buffer[self.index]
            out = s + delayed * self.decay
            self.buffer[self.index] = out
            self.index = (self.index + 1) % self.delay_samples
            result.append(out)
        return result


class ChorusEffect(AudioEffect):
    def __init__(self, rate=0.5, depth=0.002, mix=0.5):
        self.rate = rate
        self.depth = depth
        self.mix = mix
        self.phase = 0.0

    def process(self, samples):
        result = []
        for s in samples:
            self.phase += self.rate / 44100.0
            offset = int(math.sin(self.phase * 2 * math.pi) * self.depth * 44100)
            result.append(s * (1 - self.mix) + samples[max(0, len(result) - offset)] * self.mix if offset > 0 else s)
        return result


class DelayEffect(AudioEffect):
    def __init__(self, delay_ms=200, feedback=0.3, mix=0.3):
        self.delay_samples = int(44100 * delay_ms / 1000)
        self.feedback = feedback
        self.mix = mix
        self.buffer = [0.0] * self.delay_samples
        self.index = 0

    def process(self, samples):
        result = []
        for s in samples:
            delayed = self.buffer[self.index]
            out = s * (1 - self.mix) + delayed * self.mix
            self.buffer[self.index] = s + delayed * self.feedback
            self.index = (self.index + 1) % self.delay_samples
            result.append(out)
        return result


class AudioMixer:
    def __init__(self, sample_rate=44100, channels=2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.buses = {
            "master": AudioBus("master"),
            "music": AudioBus("music", 0.8),
            "sfx": AudioBus("sfx", 1.0),
            "voice": AudioBus("voice", 1.0),
            "ambient": AudioBus("ambient", 0.5),
        }
        self.listener = AudioListener()
        self._master_volume = 1.0

    def get_bus(self, name):
        return self.buses.get(name, self.buses["master"])

    def play_on_bus(self, bus_name, clip, x=0, y=0, z=0, loop=False, volume=1.0):
        bus = self.get_bus(bus_name)
        source = AudioSource3D(x, y, z)
        source.clip = clip
        source.loop = loop
        source.volume = volume
        bus.add_source(source)
        source.play()
        return source

    def update(self):
        for bus in self.buses.values():
            for source in bus.sources:
                source.update_3d(self.listener)
                if not source._playing:
                    bus.sources.remove(source)

    def set_master_volume(self, vol):
        self._master_volume = max(0, min(1, vol))


class Synthesizer:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.phase = 0.0

    def generate_tone(self, frequency, duration, waveform="sine", amplitude=0.5):
        samples = int(self.sample_rate * duration)
        result = []
        for i in range(samples):
            t = i / self.sample_rate
            self.phase += frequency / self.sample_rate
            if waveform == "sine":
                val = math.sin(2 * math.pi * self.phase)
            elif waveform == "square":
                val = 1.0 if self.phase % 1.0 < 0.5 else -1.0
            elif waveform == "sawtooth":
                val = 2.0 * (self.phase % 1.0) - 1.0
            elif waveform == "triangle":
                p = self.phase % 1.0
                val = 4.0 * abs(p - 0.5) - 1.0
            elif waveform == "noise":
                val = random.uniform(-1, 1)
            else:
                val = math.sin(2 * math.pi * self.phase)
            envelope = math.exp(-3.0 * t / duration) if duration > 0 else 1.0
            val *= amplitude * envelope
            val = max(-1, min(1, val))
            result.append(val)
        return result

    def generate_chord(self, frequencies, duration, waveform="sine", amplitude=0.3):
        chords = [self.generate_tone(f, duration, waveform, amplitude / len(frequencies)) for f in frequencies]
        return [sum(s) for s in zip(*chords)]

    def generate_drum(self, duration=0.1, amplitude=0.8):
        samples = int(self.sample_rate * duration)
        result = []
        for i in range(samples):
            t = i / self.sample_rate
            noise = random.uniform(-1, 1)
            envelope = math.exp(-20.0 * t)
            val = noise * amplitude * envelope
            result.append(val)
        return result

    def generate_piano(self, frequency, duration, amplitude=0.5):
        samples = int(self.sample_rate * duration)
        result = []
        for i in range(samples):
            t = i / self.sample_rate
            self.phase += frequency / self.sample_rate
            fundamental = math.sin(2 * math.pi * self.phase)
            harmonics = (
                math.sin(2 * math.pi * self.phase * 2) * 0.5 +
                math.sin(2 * math.pi * self.phase * 3) * 0.25 +
                math.sin(2 * math.pi * self.phase * 4) * 0.125 +
                math.sin(2 * math.pi * self.phase * 5) * 0.0625
            )
            val = (fundamental + harmonics) * amplitude
            envelope = math.exp(-5.0 * t)
            val *= envelope
            result.append(val)
        return result

    def save_wav(self, samples, filepath):
        """Save generated samples to a WAV file."""
        try:
            import wave
            with wave.open(filepath, "w") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(self.sample_rate)
                data = b"".join(struct.pack("<h", int(s * 32767)) for s in samples)
                wav.writeframes(data)
        except ImportError:
            pass


class AudioManager:
    def __init__(self):
        self.mixer = AudioMixer()
        self.synth = Synthesizer()
        self.clips = {}
        self.music_volume = 0.5
        self.sfx_volume = 1.0

    def load_clip(self, name, filepath):
        clip = AudioClip(name, filepath)
        clip.load()
        self.clips[name] = clip
        return clip

    def create_clip(self, name, samples, sample_rate=44100):
        clip = AudioClip(name, duration=len(samples) / sample_rate, sample_rate=sample_rate)
        self.clips[name] = clip
        return clip

    def play_music(self, name, loop=True):
        clip = self.clips.get(name)
        if clip:
            return self.mixer.play_on_bus("music", clip, loop=loop, volume=self.music_volume)
        return None

    def play_sfx(self, name, x=0, y=0, z=0):
        clip = self.clips.get(name)
        if clip:
            return self.mixer.play_on_bus("sfx", clip, x=x, y=y, z=z, volume=self.sfx_volume)
        return None

    def play_ambient(self, name, loop=True):
        clip = self.clips.get(name)
        if clip:
            return self.mixer.play_on_bus("ambient", clip, loop=loop, volume=0.5)
        return None

    def set_music_volume(self, vol):
        self.music_volume = max(0, min(1, vol))

    def set_sfx_volume(self, vol):
        self.sfx_volume = max(0, min(1, vol))

    def update(self):
        self.mixer.update()
