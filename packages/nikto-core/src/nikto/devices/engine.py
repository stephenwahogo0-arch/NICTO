"""Universal Device Control — the single protocol to rule all devices."""

import asyncio
import json
import logging
import socket
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    MOBILE = "mobile"
    SMART_HOME = "smart_home"
    ROBOT = "robot"
    IOT = "iot"
    COMPUTER = "computer"
    WEARABLE = "wearable"
    VEHICLE = "vehicle"
    CUSTOM = "custom"


@dataclass
class DeviceConnection:
    device_type: DeviceType
    name: str
    protocol: str  # adb, mqtt, http, serial, ssh, bluetooth, custom
    address: str = ""
    port: int = 0
    config: dict = field(default_factory=dict)
    connected: bool = False
    last_seen: Optional[datetime] = None


@dataclass
class DeviceCommand:
    device: str
    command: str
    params: dict = field(default_factory=dict)
    timeout: int = 30


@dataclass
class CommandResult:
    success: bool
    output: str = ""
    error: str = ""
    duration_ms: float = 0.0


class DeviceDiscovery:
    """Discovers devices on the local network and system."""

    @staticmethod
    async def discover_all() -> list[DeviceConnection]:
        devices = []
        adb = await DeviceDiscovery._scan_adb()
        devices.extend(adb)
        network = await DeviceDiscovery._scan_network()
        devices.extend(network)
        logger.info(f"Device discovery found {len(devices)} devices")
        return devices

    @staticmethod
    async def _scan_adb() -> list[DeviceConnection]:
        devices = []
        try:
            result = subprocess.run(
                ["adb", "devices"], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split("\n")[1:]:
                line = line.strip()
                if line and "device" in line and "offline" not in line:
                    serial = line.split("\t")[0]
                    devices.append(DeviceConnection(
                        device_type=DeviceType.MOBILE,
                        name=f"android_{serial[:8]}",
                        protocol="adb",
                        address=serial,
                        connected=True,
                        last_seen=datetime.now(),
                    ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return devices

    @staticmethod
    async def _scan_network() -> list[DeviceConnection]:
        """Scan local network for common IoT/smart home ports."""
        devices = []
        targets = [
            ("192.168.1.1", 80, DeviceType.IOT),
            ("192.168.1.1", 8123, DeviceType.SMART_HOME),  # Home Assistant
            ("192.168.1.1", 1883, DeviceType.IOT),          # MQTT
        ]
        base = "192.168.1."
        for i in range(1, 20):
            ip = f"{base}{i}"
            for port, dtype in [(80, DeviceType.IOT), (8123, DeviceType.SMART_HOME), (1883, DeviceType.IOT)]:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)
                    result = s.connect_ex((ip, port))
                    s.close()
                    if result == 0:
                        devices.append(DeviceConnection(
                            device_type=dtype,
                            name=f"device_{ip}_{port}",
                            protocol="tcp",
                            address=ip,
                            port=port,
                            connected=False,
                        ))
                except Exception:
                    pass
        return devices


class DeviceController:
    """Universal controller for any device type."""

    def __init__(self):
        self.devices: dict[str, DeviceConnection] = {}
        self._adb_available = False
        self._check_adb()

    def _check_adb(self):
        try:
            subprocess.run(["adb", "version"], capture_output=True, timeout=3)
            self._adb_available = True
        except Exception:
            self._adb_available = False

    async def discover(self) -> list[dict]:
        found = await DeviceDiscovery.discover_all()
        for d in found:
            self.devices[d.name] = d
        return [self._conn_to_dict(d) for d in found]

    def register_device(self, name: str, device_type: str, protocol: str, address: str = "", port: int = 0, config: dict = None):
        conn = DeviceConnection(
            device_type=DeviceType(device_type) if device_type in [e.value for e in DeviceType] else DeviceType.CUSTOM,
            name=name,
            protocol=protocol,
            address=address,
            port=port,
            config=config or {},
            connected=False,
        )
        self.devices[name] = conn
        return {"success": True, "device": name}

    async def execute(self, command: DeviceCommand) -> CommandResult:
        import time
        start = time.time()
        device = self.devices.get(command.device)
        if not device:
            return CommandResult(False, error=f"Device '{command.device}' not found")

        try:
            if device.protocol == "adb":
                result = await self._exec_adb(device, command)
            elif device.protocol == "mqtt":
                result = await self._exec_mqtt(device, command)
            elif device.protocol == "http":
                result = await self._exec_http(device, command)
            elif device.protocol == "serial":
                result = await self._exec_serial(device, command)
            elif device.protocol == "ssh":
                result = await self._exec_ssh(device, command)
            elif device.protocol == "shell":
                result = await self._exec_shell(device, command)
            else:
                result = CommandResult(False, error=f"Unsupported protocol: {device.protocol}")
        except Exception as e:
            result = CommandResult(False, error=str(e))

        result.duration_ms = (time.time() - start) * 1000
        device.last_seen = datetime.now()
        return result

    async def _exec_adb(self, device: DeviceConnection, command: DeviceCommand) -> CommandResult:
        if not self._adb_available:
            return CommandResult(False, error="ADB not available")
        cmd = command.command
        args = command.params.get("args", "")
        full = ["adb", "-s", device.address, "shell", cmd]
        if args:
            full.append(args)
        try:
            result = subprocess.run(full, capture_output=True, text=True, timeout=command.timeout)
            return CommandResult(result.returncode == 0, output=result.stdout, error=result.stderr)
        except subprocess.TimeoutExpired:
            return CommandResult(False, error="ADB command timed out")

    async def _exec_mqtt(self, device: DeviceConnection, command: DeviceCommand) -> CommandResult:
        topic = command.params.get("topic", "nikto/command")
        payload = command.params.get("payload", command.command)
        try:
            result = subprocess.run(
                ["mosquitto_pub", "-h", device.address, "-p", str(device.port), "-t", topic, "-m", payload],
                capture_output=True, text=True, timeout=10
            )
            return CommandResult(result.returncode == 0, output=f"MQTT published to {topic}", error=result.stderr)
        except FileNotFoundError:
            return CommandResult(False, error="mosquitto_pub not installed")

    async def _exec_http(self, device: DeviceConnection, command: DeviceCommand) -> CommandResult:
        import httpx
        method = command.params.get("method", "GET").upper()
        url = f"http://{device.address}:{device.port}{command.command}"
        try:
            async with httpx.AsyncClient(timeout=command.timeout) as client:
                if method == "GET":
                    resp = await client.get(url, params=command.params.get("query", {}))
                elif method == "POST":
                    resp = await client.post(url, json=command.params.get("body", {}))
                else:
                    resp = await client.request(method, url)
                return CommandResult(resp.is_success, output=resp.text[:2000], error="" if resp.is_success else f"HTTP {resp.status_code}")
        except Exception as e:
            return CommandResult(False, error=str(e))

    async def _exec_serial(self, device: DeviceConnection, command: DeviceCommand) -> CommandResult:
        try:
            import serial
            ser = serial.Serial(device.address, baudrate=device.port or 9600, timeout=command.timeout)
            ser.write(command.command.encode())
            import time
            time.sleep(0.1)
            output = ser.read(1024).decode(errors="replace")
            ser.close()
            return CommandResult(True, output=output)
        except ImportError:
            return CommandResult(False, error="pyserial not installed")
        except Exception as e:
            return CommandResult(False, error=str(e))

    async def _exec_ssh(self, device: DeviceConnection, command: DeviceCommand) -> CommandResult:
        try:
            import asyncssh
            async with asyncssh.connect(device.address, port=device.port or 22, known_hosts=None) as conn:
                result = await conn.run(command.command, timeout=command.timeout)
                return CommandResult(result.returncode == 0, output=result.stdout, error=result.stderr)
        except ImportError:
            return CommandResult(False, error="asyncssh not installed")
        except Exception as e:
            return CommandResult(False, error=str(e))

    async def _exec_shell(self, device: DeviceConnection, command: DeviceCommand) -> CommandResult:
        try:
            result = subprocess.run(command.command, shell=True, capture_output=True, text=True, timeout=command.timeout)
            return CommandResult(result.returncode == 0, output=result.stdout, error=result.stderr)
        except subprocess.TimeoutExpired:
            return CommandResult(False, error="Command timed out")
        except Exception as e:
            return CommandResult(False, error=str(e))

    async def mobile_tap(self, device_name: str, x: int, y: int) -> CommandResult:
        return await self.execute(DeviceCommand(device_name, f"input tap {x} {y}"))

    async def mobile_swipe(self, device_name: str, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> CommandResult:
        return await self.execute(DeviceCommand(device_name, f"input swipe {x1} {y1} {x2} {y2} {duration}"))

    async def mobile_type(self, device_name: str, text: str) -> CommandResult:
        return await self.execute(DeviceCommand(device_name, f"input text '{text}'"))

    async def mobile_screenshot(self, device_name: str) -> str:
        tmp = tempfile.gettempdir()
        out = f"{tmp}/nikto_screen.png"
        r1 = subprocess.run(["adb", "-s", self.devices[device_name].address, "shell", "screencap", "-p", "/sdcard/screen.png"], capture_output=True, timeout=10)
        r2 = subprocess.run(["adb", "-s", self.devices[device_name].address, "pull", "/sdcard/screen.png", out], capture_output=True, timeout=10)
        if r1.returncode == 0 and r2.returncode == 0:
            return f"Screenshot saved to {out}"
        return "Screenshot failed"

    async def smart_home_set(self, device_name: str, entity: str, state: str) -> CommandResult:
        return await self.execute(DeviceCommand(device_name, f"set {entity} {state}", params={"topic": f"home/{entity}/set", "payload": state}))

    async def robot_move(self, device_name: str, direction: str, distance: int = 10) -> CommandResult:
        return await self.execute(DeviceCommand(device_name, f"MOVE {direction.upper()} {distance}"))

    def list_devices(self) -> list[dict]:
        return [self._conn_to_dict(d) for d in self.devices.values()]

    def _conn_to_dict(self, conn: DeviceConnection) -> dict:
        return {
            "name": conn.name,
            "type": conn.device_type.value,
            "protocol": conn.protocol,
            "address": conn.address,
            "port": conn.port,
            "connected": conn.connected,
            "last_seen": conn.last_seen.isoformat() if conn.last_seen else None,
        }
