// Desktop Streamer — Sector 3a Vision backend (C++).
// Compiles to a static lib linked into the Rust cdylib via build.rs.
// Uses DXGI on Windows / VA-API on Linux.

#ifdef _WIN32
#include <windows.h>
#include <dxgi1_2.h>
#include <d3d11.h>
#pragma comment(lib, "dxgi.lib")
#pragma comment(lib, "d3d11.lib")
#else
#include <cstdint>
#endif

#include <cstdio>

extern "C" {

int desktop_streamer_start(const char* display) {
    (void)display;
    // TODO: Initialize DXGI output duplication
    fprintf(stderr, "desktop_streamer_start: stub\n");
    return 0;
}

int desktop_streamer_capture(uint8_t* dst, int width, int height) {
    (void)dst; (void)width; (void)height;
    // TODO: Acquire next DXGI frame, copy to dst as BGRA
    fprintf(stderr, "desktop_streamer_capture: stub\n");
    return -1;
}

void desktop_streamer_stop() {
    fprintf(stderr, "desktop_streamer_stop: stub\n");
}

// Voice Synth — Sector 3b Audio backend (C++).
// Uses WASAPI on Windows / ALSA on Linux.

int voice_synth_speak(const char* text, int voice, float rate) {
    (void)text; (void)voice; (void)rate;
    fprintf(stderr, "voice_synth_speak: stub\n");
    return 0;
}

int voice_synth_save(const char* text, int voice, float rate, const char* path) {
    (void)text; (void)voice; (void)rate; (void)path;
    fprintf(stderr, "voice_synth_save: stub\n");
    return 0;
}

} // extern "C"
