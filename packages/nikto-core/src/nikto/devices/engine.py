from enum import Enum
from uuid import uuid4
from datetime import datetime


class DeviceType(Enum):
    SERVER = "server"
    WORKSTATION = "workstation"
    MOBILE = "mobile"
    IOT = "iot"
    ROBOT = "robot"
    EMBEDDED = "embedded"


class DeviceConnection:
    def __init__(self, protocol: str, address: str, port: int = 0):
        self.protocol = protocol
        self.address = address
        self.port = port


class DeviceCommand:
    def __init__(self, command: str, params: dict = None):
        self.command = command
        self.params = params or {}


class CommandResult:
    def __init__(self, success: bool, output: str = "", error: str = ""):
        self.success = success
        self.output = output
        self.error = error


class DeviceController:
    def __init__(self):
        self._devices = {}

    def register_device(self, name: str, device_type: DeviceType, connection: DeviceConnection = None) -> dict:
        device_id = str(uuid4())[:12]
        self._devices[device_id] = {"id": device_id, "name": name, "type": device_type.value, "connection": {"protocol": connection.protocol if connection else "unknown", "address": connection.address if connection else "unknown"}, "registered_at": datetime.now().isoformat()}
        return self._devices[device_id]

    def list_devices(self) -> list[dict]:
        return list(self._devices.values())

    def execute(self, device_id: str, command: DeviceCommand) -> CommandResult:
        if device_id not in self._devices:
            return CommandResult(False, error="Device not found")
        return CommandResult(True, output=f"Executed {command.command} on {device_id}")
