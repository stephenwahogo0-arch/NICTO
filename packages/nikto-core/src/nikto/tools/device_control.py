"""Universal Device Control tools."""

from nikto.tools.base import Tool

_device_controller = None

def _set_device_controller(dc):
    global _device_controller
    _device_controller = dc

def _get_dc():
    global _device_controller
    if _device_controller is None:
        from nikto.devices.engine import DeviceController
        _device_controller = DeviceController()
    return _device_controller


async def tool_device_discover() -> str:
    dc = _get_dc()
    devices = await dc.discover()
    if not devices:
        return "No devices discovered on local network. Register devices manually with device_register."
    lines = [f"Discovered {len(devices)} devices:"]
    for d in devices:
        lines.append(f"  - {d['name']} ({d['type']}, {d['protocol']}, {d['address']}:{d['port']})")
    return "\n".join(lines)


async def tool_device_register(name: str, device_type: str = "custom", protocol: str = "shell", address: str = "", port: int = 0, config_json: str = "{}") -> str:
    dc = _get_dc()
    import json
    config = json.loads(config_json)
    result = dc.register_device(name, device_type, protocol, address, port, config)
    return f"Device '{name}' registered ({device_type}/{protocol}). Use device_command to control it."


async def tool_device_command(device: str, command: str, params_json: str = "{}", timeout: int = 30) -> str:
    dc = _get_dc()
    from nikto.devices.engine import DeviceCommand
    import json
    params = json.loads(params_json)
    cmd = DeviceCommand(device, command, params=params, timeout=timeout)
    result = await dc.execute(cmd)
    status = "SUCCESS" if result.success else "FAILED"
    output = result.output[:1000] if result.output else result.error[:1000]
    return f"[{status}] {device}: {command}\nOutput: {output}\nDuration: {result.duration_ms:.0f}ms"


async def tool_device_list() -> str:
    dc = _get_dc()
    devices = dc.list_devices()
    if not devices:
        return "No devices registered. Use device_discover or device_register."
    lines = [f"Registered devices ({len(devices)}):"]
    for d in devices:
        status = "connected" if d["connected"] else "disconnected"
        lines.append(f"  - {d['name']} ({d['type']}, {d['protocol']}, {d['address']}:{d['port']}) [{status}]")
    return "\n".join(lines)


async def tool_mobile_control(device: str, action: str, x: int = 0, y: int = 0, text: str = "") -> str:
    dc = _get_dc()
    actions_map = {
        "tap": lambda: dc.mobile_tap(device, x, y),
        "swipe": lambda: dc.mobile_swipe(device, x, y, x + 100, y),
        "type": lambda: dc.mobile_type(device, text),
        "screenshot": lambda: dc.mobile_screenshot(device),
    }
    if action not in actions_map:
        return f"Unknown action: {action}. Use: tap, swipe, type, screenshot"
    result = await actions_map[action]()
    return f"[MOBILE] {device}: {action} -> {result}"


async def tool_smart_home(device: str, entity: str, state: str) -> str:
    dc = _get_dc()
    result = await dc.smart_home_set(device, entity, state)
    return f"[SMART HOME] {device}: {entity} = {state} -> {'OK' if result.success else 'FAILED: ' + result.error}"


async def tool_robot_command(device: str, command: str, distance: int = 10) -> str:
    dc = _get_dc()
    result = await dc.robot_move(device, command, distance)
    return f"[ROBOT] {device}: {command} {distance} -> {'OK' if result.success else 'FAILED: ' + result.error}"


DeviceDiscoverTool = Tool(name="device_discover", description="Scan local network and ADB for available devices (phones, smart home, IoT, robots). Auto-discovers connected hardware.", parameters={"type": "object", "properties": {}}, async_function=tool_device_discover)
DeviceRegisterTool = Tool(name="device_register", description="Register a new device for NIKTO to control. Specify type (mobile, smart_home, robot, iot, custom), protocol (adb, mqtt, http, serial, ssh, shell), address, and port.", parameters={"type": "object", "properties": {
    "name": {"type": "string", "description": "Device name"},
    "device_type": {"type": "string", "enum": ["mobile", "smart_home", "robot", "iot", "computer", "custom"], "description": "Device category"},
    "protocol": {"type": "string", "enum": ["adb", "mqtt", "http", "serial", "ssh", "shell"], "description": "Communication protocol"},
    "address": {"type": "string", "description": "IP address or serial number"},
    "port": {"type": "integer", "description": "Port number"},
    "config_json": {"type": "string", "description": "Optional JSON config"},
}, "required": ["name", "device_type", "protocol"]}, async_function=tool_device_register)
DeviceCommandTool = Tool(name="device_command", description="Send a command to any registered device. Supports mobile (adb), smart home (MQTT/HTTP), robots (serial/SSH), and IoT devices.", parameters={"type": "object", "properties": {
    "device": {"type": "string", "description": "Device name from device_list"},
    "command": {"type": "string", "description": "Command to execute"},
    "params_json": {"type": "string", "description": "JSON parameters (method, body, topic, payload, args)"},
    "timeout": {"type": "integer", "description": "Command timeout in seconds"},
}, "required": ["device", "command"]}, async_function=tool_device_command)
DeviceListTool = Tool(name="device_list", description="List all registered devices and their connection status.", parameters={"type": "object", "properties": {}}, async_function=tool_device_list)
MobileControlTool = Tool(name="mobile_control", description="Control a connected mobile device: tap at coordinates, swipe across screen, type text, or take screenshot.", parameters={"type": "object", "properties": {
    "device": {"type": "string", "description": "Mobile device name"},
    "action": {"type": "string", "enum": ["tap", "swipe", "type", "screenshot"]},
    "x": {"type": "integer", "description": "X coordinate"},
    "y": {"type": "integer", "description": "Y coordinate"},
    "text": {"type": "string", "description": "Text to type"},
}, "required": ["device", "action"]}, async_function=tool_mobile_control)
SmartHomeTool = Tool(name="smart_home", description="Control smart home devices: set entities to states (on/off, temperature, brightness) via MQTT or HTTP.", parameters={"type": "object", "properties": {
    "device": {"type": "string", "description": "Smart home hub device name"},
    "entity": {"type": "string", "description": "Entity ID (e.g., light.living_room, thermostat.home)"},
    "state": {"type": "string", "description": "Target state (on, off, 75, etc.)"},
}, "required": ["device", "entity", "state"]}, async_function=tool_smart_home)
RobotControlTool = Tool(name="robot_control", description="Send movement commands to connected robots: FORWARD, BACKWARD, LEFT, RIGHT, STOP.", parameters={"type": "object", "properties": {
    "device": {"type": "string", "description": "Robot device name"},
    "command": {"type": "string", "enum": ["FORWARD", "BACKWARD", "LEFT", "RIGHT", "STOP"], "description": "Movement command"},
    "distance": {"type": "integer", "description": "Distance/step in units"},
}, "required": ["device", "command"]}, async_function=tool_robot_command)
