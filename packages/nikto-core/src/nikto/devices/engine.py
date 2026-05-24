"""Real device controller — discovers and interacts with actual system devices."""
import os
import platform
import subprocess
import sys
from enum import Enum
from typing import Optional


class DeviceType(Enum):
    SYSTEM = "system"
    CPU = "cpu"
    STORAGE = "storage"
    MEMORY = "memory"
    NETWORK = "network"


class DeviceConnection:
    def __init__(self, device_id: str, protocol: str = "local"):
        self.device_id = device_id
        self.protocol = protocol
        self.connected = False


class DeviceCommand:
    def __init__(self, command: str, args: list = None, timeout: int = 30):
        self.command = command
        self.args = args or []
        self.timeout = timeout


class CommandResult:
    def __init__(self, success: bool, output: str = "", error: str = ""):
        self.success = success
        self.output = output
        self.error = error


class DeviceDiscovery:
    def __init__(self):
        self.devices = {}

    def scan(self) -> list:
        result = []
        result.append({"type": DeviceType.SYSTEM, "name": platform.node(), "os": platform.system(), "arch": platform.machine()})
        result.append({"type": DeviceType.CPU, "name": platform.processor() or "Unknown", "cores": os.cpu_count() or 1})
        result.append({"type": DeviceType.NETWORK, "hostname": platform.node()})
        try:
            import psutil
            disk = psutil.disk_usage("/")
            result.append({"type": DeviceType.STORAGE, "total_gb": round(disk.total / 1e9, 1), "free_gb": round(disk.free / 1e9, 1)})
            result.append({"type": DeviceType.MEMORY, "total_gb": round(psutil.virtual_memory().total / 1e9, 1)})
        except ImportError:
            pass
        return result


class DeviceController:
    def __init__(self):
        self.devices = {}

    def discover(self) -> list:
        self.devices = {}
        # System device
        self.devices["system"] = {"type": "system", "name": platform.node(), "os": platform.system(), "arch": platform.machine()}
        # CPU
        self.devices["cpu"] = {"type": "cpu", "name": platform.processor() or "Unknown", "cores": os.cpu_count() or 1}
        # Disk
        try:
            import psutil
            disk = psutil.disk_usage("/")
            self.devices["disk"] = {"type": "storage", "total_gb": round(disk.total / 1e9, 1), "free_gb": round(disk.free / 1e9, 1)}
            self.devices["memory"] = {"type": "memory", "total_gb": round(psutil.virtual_memory().total / 1e9, 1)}
        except ImportError:
            self.devices["disk"] = {"type": "storage", "note": "Install psutil for details"}
        # Network
        self.devices["network"] = {"type": "network", "hostname": platform.node()}
        return list(self.devices.values())

    def get_devices(self) -> list:
        if not self.devices:
            self.discover()
        return list(self.devices.values())
