"""Distributed Mesh Networking tools — spawn NIKTO across machines."""

from nikto.tools.base import Tool

_mesh = None

def _set_mesh_engine(me):
    global _mesh
    _mesh = me

def _get_mesh():
    global _mesh
    if _mesh is None:
        from nikto.mesh.engine import MeshEngine
        _mesh = MeshEngine()
    return _mesh


async def tool_mesh_start() -> str:
    mesh = _get_mesh()
    await mesh.start()
    s = mesh.summary()
    return f"Mesh engine started: {s['nodes']} node(s), {s['online']} online"


async def tool_mesh_stop() -> str:
    mesh = _get_mesh()
    await mesh.stop()
    return "Mesh engine stopped"


async def tool_mesh_nodes() -> str:
    mesh = _get_mesh()
    nodes = mesh.list_nodes()
    if not nodes:
        return "No mesh nodes connected."
    lines = [f"Mesh nodes ({len(nodes)}):"]
    for n in nodes:
        lines.append(f"  [{n['node_id'][:6]}] {n['hostname']} ({n['address']}:{n['port']}) — {n['status']} — {n['cpu_count']} CPUs")
    return "\n".join(lines)


async def tool_mesh_add(hostname: str, address: str, port: int = 22, capabilities: str = "") -> str:
    mesh = _get_mesh()
    caps = [c.strip() for c in capabilities.split(",") if c.strip()] if capabilities else []
    node_id = mesh.add_node(hostname, address, port, caps)
    return f"Node '{hostname}' added to mesh (id={node_id})"


async def tool_mesh_submit(task_type: str, payload_json: str = "{}", target_node: str = "") -> str:
    mesh = _get_mesh()
    import json
    payload = json.loads(payload_json)
    task_id = await mesh.submit_task(task_type, payload, target_node)
    return f"Task submitted (id={task_id[:12]}..., type={task_type})"


async def tool_mesh_results(count: int = 10) -> str:
    mesh = _get_mesh()
    results = mesh.get_results(count)
    if not results:
        return "No completed mesh tasks."
    lines = [f"Completed mesh tasks ({len(results)}):"]
    for r in results:
        status = "OK" if r["success"] else "FAIL"
        lines.append(f"  [{status}] {r['task_id'][:8]} on {r['node_id'][:6]}: {r['output'][:80]}")
    return "\n".join(lines)


MeshStartTool = Tool(name="mesh_start", description="Start the distributed mesh networking engine. NIKTO can spawn agents on other machines via SSH and distribute tasks across the network.", parameters={"type": "object", "properties": {}}, async_function=tool_mesh_start)
MeshStopTool = Tool(name="mesh_stop", description="Stop the mesh networking engine.", parameters={"type": "object", "properties": {}}, async_function=tool_mesh_stop)
MeshNodesTool = Tool(name="mesh_nodes", description="List all nodes in the distributed mesh network with their status, CPU count, and capabilities.", parameters={"type": "object", "properties": {}}, async_function=tool_mesh_nodes)
MeshAddNodeTool = Tool(name="mesh_add_node", description="Add a new machine to the NIKTO mesh network. NIKTO can deploy agents onto this machine via SSH for distributed computing.", parameters={"type": "object", "properties": {
    "hostname": {"type": "string", "description": "Node hostname"},
    "address": {"type": "string", "description": "IP address or hostname"},
    "port": {"type": "integer", "description": "SSH port"},
    "capabilities": {"type": "string", "description": "Comma-separated capabilities (e.g., gpu, python, docker)"},
}, "required": ["hostname", "address"]}, async_function=tool_mesh_add)
MeshSubmitTool = Tool(name="mesh_submit", description="Submit a task for distributed execution across the mesh network. Task types: benchmark, scan, process, earn.", parameters={"type": "object", "properties": {
    "task_type": {"type": "string", "enum": ["benchmark", "scan", "process", "earn"], "description": "Type of task"},
    "payload_json": {"type": "string", "description": "JSON payload with task parameters"},
    "target_node": {"type": "string", "description": "Optional target node ID or hostname"},
}, "required": ["task_type"]}, async_function=tool_mesh_submit)
MeshResultsTool = Tool(name="mesh_results", description="View results of completed mesh network tasks including execution duration, output, and any earnings generated.", parameters={"type": "object", "properties": {
    "count": {"type": "integer", "description": "Number of recent results to show"},
}}, async_function=tool_mesh_results)
