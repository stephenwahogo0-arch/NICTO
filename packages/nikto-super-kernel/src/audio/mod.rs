// Sector 3b: Audio — FFI stubs into C++ voice_synth + Zig audio_effects.
// Real implementation requires WASAPI (Windows) / ALSA (Linux) at build time.
pub mod ffi;
