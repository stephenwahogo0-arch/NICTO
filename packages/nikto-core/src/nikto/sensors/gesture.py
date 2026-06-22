"""
Gesture / Wi-Fi Sensing Module for NIKTO.

Provides RSSI-based signal sensing without simulated data.
On Windows: uses a C++ binary via subprocess.
On Linux: reads ``/proc/net/wireless``.
On macOS: uses the ``airport`` CLI tool.
Raises ``RuntimeError`` if Wi-Fi sensing is not available on the platform.
"""

import os
import platform
import re
import subprocess
from typing import Optional


class GestureSensor:
    """Real Wi-Fi signal sensor — no simulated data."""

    def __init__(self) -> None:
        self._system = platform.system().lower()

    def get_rssi(self, interface: Optional[str] = None) -> float:
        """Return the current RSSI value in dBm.

        Raises ``RuntimeError`` if the platform is unsupported or the
        required tool is unavailable.
        """
        if self._system == "windows":
            return self._get_windows_rssi(interface)
        elif self._system == "linux":
            return self._get_linux_rssi(interface)
        elif self._system == "darwin":
            return self._get_macos_rssi()
        raise RuntimeError(f"Wi-Fi sensing not available on {self._system}")

    def _get_windows_rssi(self, interface: Optional[str] = None) -> float:
        # Try to use a bundled C++ binary; fall back to netsh
        binary = os.path.join(os.path.dirname(__file__), "..", "bin", "wifi_sensor.exe")
        if os.path.isfile(binary):
            try:
                result = subprocess.run([binary], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return float(result.stdout.strip())
            except (subprocess.TimeoutExpired, ValueError, OSError):
                pass
        # netsh fallback
        try:
            out = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=5,
            )
            for line in out.stdout.splitlines():
                line = line.strip()
                if "Signal" in line and "%" in line:
                    pct = int(re.search(r"(\d+)%", line).group(1))
                    # Convert percentage to RSSI (approx)
                    return float(-100 + pct * 0.5)
            raise RuntimeError("No Wi-Fi interface found on Windows")
        except Exception as e:
            raise RuntimeError(f"Wi-Fi sensing not available on this platform: {e}") from e

    def _get_linux_rssi(self, interface: Optional[str] = None) -> float:
        iface = interface or "wlan0"
        proc_path = "/proc/net/wireless"
        if os.path.exists(proc_path):
            with open(proc_path, "r") as f:
                for line in f:
                    if iface in line:
                        parts = line.strip().split()
                        # Format: Inter-| sta-|   Quality        |   Discarded packets...
                        # wlan0: 0000   54.  -60.  -256   0
                        if len(parts) >= 4:
                            try:
                                return float(parts[3].rstrip("."))
                            except ValueError:
                                pass
        # Try iwconfig
        try:
            out = subprocess.run(
                ["iwconfig", iface],
                capture_output=True, text=True, timeout=5,
            )
            for line in out.stdout.splitlines():
                if "Signal level" in line:
                    m = re.search(r"Signal level[=:](-?\d+)", line)
                    if m:
                        return float(m.group(1))
            raise RuntimeError(f"No Wi-Fi signal found on {iface}")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Wi-Fi sensing not available on this platform: {e}") from e

    def _get_macos_rssi(self) -> float:
        airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        if not os.path.isfile(airport):
            raise RuntimeError("airport CLI not found. Wi-Fi sensing not available on macOS.")
        try:
            out = subprocess.run([airport, "-I"], capture_output=True, text=True, timeout=5)
            for line in out.stdout.splitlines():
                line = line.strip()
                if "agrCtlRSSI" in line:
                    return float(line.split(":")[-1].strip())
            raise RuntimeError("No RSSI information from airport")
        except (subprocess.TimeoutExpired, ValueError) as e:
            raise RuntimeError(f"Wi-Fi sensing failed: {e}") from e
