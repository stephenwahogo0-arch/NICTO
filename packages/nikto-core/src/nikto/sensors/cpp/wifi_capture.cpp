/**
 * Wi-Fi Signal Capture — C++ native backend for NIKTO Gesture Monitoring.
 *
 * Uses Windows Native WLAN API (wlanapi.dll) for high-speed, low-latency
 * Wi-Fi signal capture. Falls back to netsh subprocess if unavailable.
 *
 * Compile:
 *   cl /EHsc /Fe:wifi_capture.exe wifi_capture.cpp wlanapi.lib ole32.lib
 *
 * Usage:
 *   wifi_capture.exe scan           — one-shot BSSID scan
 *   wifi_capture.exe monitor <ms>   — continuous monitoring every <ms>
 *   wifi_capture.exe csi <seconds>  — pseudo-CSI capture (RSSI streaming)
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wlanapi.h>
#include <objbase.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <process.h>  // for _popen, _pclose

#pragma comment(lib, "wlanapi.lib")
#pragma comment(lib, "ole32.lib")

#define MAX_APS 256

typedef struct {
    double timestamp;
    double rssi;          // dBm
    int    channel;
    int    frequency_mhz; // 2400 or 5000
    char   ssid[64];
    char   bssid[20];
    int    signal_quality; // 0-100
} WifiSample;

typedef struct {
    WifiSample samples[MAX_APS];
    int count;
} WifiScanResult;

/* ── JSON output helpers ───────────────────────────────────────────── */

void print_json_sample(WifiSample *s) {
    printf("{\"ts\":%.3f,\"rssi\":%.1f,\"ch\":%d,\"freq\":%d,\"ssid\":\"%s\",\"bssid\":\"%s\",\"qual\":%d}",
           s->timestamp, s->rssi, s->channel, s->frequency_mhz,
           s->ssid, s->bssid, s->signal_quality);
}

void print_json_array(WifiScanResult *r) {
    printf("[");
    for (int i = 0; i < r->count; i++) {
        if (i > 0) printf(",");
        print_json_sample(&r->samples[i]);
    }
    printf("]\n");
}

/* ── WLAN API Scan ─────────────────────────────────────────────────── */

int wlan_scan(WifiScanResult *result) {
    HANDLE hClient = NULL;
    DWORD dwMaxClient = 2;
    DWORD dwCurVersion = 0;
    DWORD dwResult;
    PWLAN_INTERFACE_INFO_LIST pIfList = NULL;
    PWLAN_BSS_LIST pBssList = NULL;

    result->count = 0;

    dwResult = WlanOpenHandle(dwMaxClient, NULL, &dwCurVersion, &hClient);
    if (dwResult != ERROR_SUCCESS) {
        fprintf(stderr, "WlanOpenHandle failed: %lu\n", dwResult);
        return -1;
    }

    dwResult = WlanEnumInterfaces(hClient, NULL, &pIfList);
    if (dwResult != ERROR_SUCCESS) {
        fprintf(stderr, "WlanEnumInterfaces failed: %lu\n", dwResult);
        WlanCloseHandle(hClient, NULL);
        return -1;
    }

    if (pIfList->dwNumberOfItems == 0) {
        fprintf(stderr, "No wireless interfaces found\n");
        WlanFreeMemory(pIfList);
        WlanCloseHandle(hClient, NULL);
        return -1;
    }

    // Scan on first interface
    GUID guid = pIfList->InterfaceInfo[0].InterfaceGuid;

    dwResult = WlanScan(hClient, &guid, NULL, NULL, NULL);
    if (dwResult != ERROR_SUCCESS) {
        // Non-fatal — may have recent scan data
    }

    // Wait for scan to complete
    Sleep(2000);

    dwResult = WlanGetNetworkBssList(hClient, &guid, NULL, dot11_BSS_type_any, FALSE, NULL, &pBssList);
    if (dwResult != ERROR_SUCCESS) {
        fprintf(stderr, "WlanGetNetworkBssList failed: %lu\n", dwResult);
        WlanFreeMemory(pIfList);
        WlanCloseHandle(hClient, NULL);
        return -1;
    }

    double now = (double)GetTickCount64() / 1000.0;

    int count = (int)pBssList->dwNumberOfItems;
    if (count > MAX_APS) count = MAX_APS;

    for (int i = 0; i < count; i++) {
        PWLAN_BSS_ENTRY bss = &pBssList->wlanBssEntries[i];
        WifiSample *s = &result->samples[result->count];

        s->timestamp = now;
        s->rssi = (double)bss->lRssi;
        s->channel = (int)bss->ulChCenterFrequency / 1000;
        s->frequency_mhz = (bss->ulChCenterFrequency > 50000) ? 5000 : 2400;
        s->signal_quality = 50; // not available in this SDK version

        // BSSID formatting
        sprintf(s->bssid, "%02x:%02x:%02x:%02x:%02x:%02x",
                bss->dot11Bssid[0], bss->dot11Bssid[1],
                bss->dot11Bssid[2], bss->dot11Bssid[3],
                bss->dot11Bssid[4], bss->dot11Bssid[5]);

        // SSID (may be empty for hidden networks)
        int ssid_len = bss->dot11Ssid.uSSIDLength;
        if (ssid_len > 0 && ssid_len < 32) {
            memcpy(s->ssid, bss->dot11Ssid.ucSSID, ssid_len);
            s->ssid[ssid_len] = '\0';
        } else {
            strcpy(s->ssid, "(hidden)");
        }

        result->count++;
    }

    WlanFreeMemory(pBssList);
    WlanFreeMemory(pIfList);
    WlanCloseHandle(hClient, NULL);
    return result->count;
}

/* ── netsh fallback ────────────────────────────────────────────────── */

int netsh_scan(WifiScanResult *result) {
    result->count = 0;
    FILE *fp = _popen("netsh wlan show networks mode=Bssid", "r");
    if (!fp) return -1;

    char line[256];
    char current_ssid[64] = "";
    char current_bssid[20] = "";
    int current_signal = 0;
    double now = (double)GetTickCount64() / 1000.0;

    while (fgets(line, sizeof(line), fp)) {
        // Strip newline
        size_t len = strlen(line);
        if (len > 0 && line[len-1] == '\n') line[len-1] = '\0';

        if (strstr(line, "SSID")) {
            char *colon = strchr(line, ':');
            if (colon) {
                strncpy(current_ssid, colon + 2, sizeof(current_ssid) - 1);
                // Trim leading spaces
                char *p = current_ssid;
                while (*p == ' ') p++;
                if (p != current_ssid) memmove(current_ssid, p, strlen(p) + 1);
            }
        }
        if (strstr(line, "BSSID")) {
            char *colon = strchr(line, ':');
            if (colon) {
                strncpy(current_bssid, colon + 2, sizeof(current_bssid) - 1);
                char *p = current_bssid;
                while (*p == ' ') p++;
                if (p != current_bssid) memmove(current_bssid, p, strlen(p) + 1);
            }
        }
        if (strstr(line, "Signal") && strstr(line, "%")) {
            char *colon = strchr(line, ':');
            if (colon) {
                current_signal = atoi(colon + 1);
            }
        }
        if (strstr(line, "Radio type") || strstr(line, "Channel")) {
            if (result->count >= MAX_APS) continue;
            WifiSample *s = &result->samples[result->count];
            s->timestamp = now;
            s->rssi = (current_signal / 2.0) - 100.0;
            s->signal_quality = current_signal;
            strncpy(s->ssid, current_ssid, sizeof(s->ssid) - 1);
            strncpy(s->bssid, current_bssid, sizeof(s->bssid) - 1);
            s->channel = 6;
            s->frequency_mhz = 2400;
            result->count++;
        }
    }
    _pclose(fp);
    return result->count;
}

/* ── Signal Processing (MATLAB-grade) ──────────────────────────────── */

typedef struct {
    double mean;
    double variance;
    double stddev;
    double min;
    double max;
    double slope;
    double entropy;
} SignalFeatures;

double compute_entropy(double *vals, int n, int bins) {
    if (n < 2) return 0.0;
    double mn = vals[0], mx = vals[0];
    for (int i = 1; i < n; i++) {
        if (vals[i] < mn) mn = vals[i];
        if (vals[i] > mx) mx = vals[i];
    }
    if (mx - mn < 0.001) return 0.0;

    int *hist = (int *)calloc(bins, sizeof(int));
    if (!hist) return 0.0;

    for (int i = 0; i < n; i++) {
        int idx = (int)((vals[i] - mn) / (mx - mn) * bins);
        if (idx >= bins) idx = bins - 1;
        if (idx < 0) idx = 0;
        hist[idx]++;
    }

    double ent = 0.0;
    for (int i = 0; i < bins; i++) {
        if (hist[i] > 0) {
            double p = (double)hist[i] / n;
            ent -= p * log2(p);
        }
    }
    free(hist);
    return ent / log2(bins);
}

SignalFeatures compute_features(double *rssi_vals, int n) {
    SignalFeatures f = {0};
    if (n < 2) return f;

    double sum = 0.0, sum2 = 0.0;
    f.min = rssi_vals[0];
    f.max = rssi_vals[0];
    for (int i = 0; i < n; i++) {
        sum += rssi_vals[i];
        sum2 += rssi_vals[i] * rssi_vals[i];
        if (rssi_vals[i] < f.min) f.min = rssi_vals[i];
        if (rssi_vals[i] > f.max) f.max = rssi_vals[i];
    }
    f.mean = sum / n;
    f.variance = (sum2 / n) - (f.mean * f.mean);
    f.stddev = sqrt(f.variance);
    f.slope = (rssi_vals[n-1] - rssi_vals[0]) / (n > 1 ? n : 1);
    f.entropy = compute_entropy(rssi_vals, n, 10);
    return f;
}

/* ── Movement Classification ───────────────────────────────────────── */

const char* classify_movement(double variance, double entropy) {
    if (variance < 0.05 && entropy < 0.2) return "stationary";
    if (variance < 0.3)                   return "walking";
    if (variance < 0.8)                   return "exercising";
    return "running";
}

const char* detect_gesture(double variance, double slope, double duration) {
    if (variance > 0.7 && duration < 0.2)          return "tap";
    if (variance > 0.5 && slope > 2.0)              return "swipe_right";
    if (variance > 0.5 && slope < -2.0)             return "swipe_left";
    if (variance > 0.3 && duration > 0.3 && duration < 1.0)
        return slope > 0 ? "push" : "pull";
    if (variance > 0.4 && duration > 0.5 && duration < 2.0)
        return slope > 0 ? "circle_cw" : "circle_ccw";
    if (variance > 0.3 && duration > 0.3)            return "wave";
    return "unknown";
}

/* ── Main CLI ──────────────────────────────────────────────────────── */

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: wifi_capture scan|monitor <ms>|csi <sec>\n");
        return 1;
    }

    const char *cmd = argv[1];

    if (strcmp(cmd, "scan") == 0) {
        WifiScanResult result;
        int n;

        // Try WLAN API first
        n = wlan_scan(&result);
        if (n <= 0) {
            n = netsh_scan(&result);
        }

        if (n > 0) {
            print_json_array(&result);
        } else {
            printf("[]\n");
        }
        return 0;
    }

    if (strcmp(cmd, "monitor") == 0) {
        int interval_ms = (argc > 2) ? atoi(argv[2]) : 1000;
        if (interval_ms < 50) interval_ms = 50;

        // Rolling window for signal processing
        #define WINDOW_SIZE 100
        double rssi_window[WINDOW_SIZE];
        int window_count = 0;

        while (1) {
            WifiScanResult result;
            int n = wlan_scan(&result);
            if (n <= 0) n = netsh_scan(&result);

            if (n > 0) {
                // Find best RSSI
                double best_rssi = -100.0;
                for (int i = 0; i < n; i++) {
                    if (result.samples[i].rssi > best_rssi)
                        best_rssi = result.samples[i].rssi;
                }

                // Rolling window
                if (window_count < WINDOW_SIZE) {
                    rssi_window[window_count++] = best_rssi;
                } else {
                    memmove(rssi_window, rssi_window + 1, (WINDOW_SIZE - 1) * sizeof(double));
                    rssi_window[WINDOW_SIZE - 1] = best_rssi;
                }

                // Compute features
                SignalFeatures feat = compute_features(rssi_window, window_count);
                const char *movement = classify_movement(feat.variance, feat.entropy);
                const char *gesture = detect_gesture(feat.variance, feat.slope, interval_ms / 1000.0);

                // JSON output
                printf("{\"ts\":%.3f,\"rssi\":%.1f,\"var\":%.4f,\"ent\":%.4f,"
                       "\"mov\":\"%s\",\"gest\":\"%s\",\"slp\":%.4f}\n",
                       (double)GetTickCount64() / 1000.0,
                       best_rssi, feat.variance, feat.entropy,
                       movement, gesture, feat.slope);
                fflush(stdout);
            }

            Sleep(interval_ms);
        }
    }

    if (strcmp(cmd, "csi") == 0) {
        int duration_sec = (argc > 2) ? atoi(argv[2]) : 10;
        int samples = duration_sec * 10; // 10 Hz
        int interval_ms = 100;

        printf("{\"capture\":\"csi\",\"duration\":%d,\"samples\":%d,\"data\":[\n", duration_sec, samples);
        for (int i = 0; i < samples; i++) {
            if (i > 0) printf(",\n");

            WifiScanResult result;
            int n = wlan_scan(&result);
            if (n <= 0) n = netsh_scan(&result);

            double best_rssi = -100.0;
            for (int j = 0; j < n && j < MAX_APS; j++) {
                if (result.samples[j].rssi > best_rssi)
                    best_rssi = result.samples[j].rssi;
            }

            printf("{\"i\":%d,\"ts\":%.3f,\"rssi\":%.1f,\"aps\":%d}",
                   i, (double)GetTickCount64() / 1000.0, best_rssi, n);
            Sleep(interval_ms);
        }
        printf("\n]}\n");
        return 0;
    }

    fprintf(stderr, "Unknown command: %s\n", cmd);
    return 1;
}
