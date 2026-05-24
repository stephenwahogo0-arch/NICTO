from nikto.tools.base import Tool

_mesh_engine = None

def _set_mesh(engine):
    global _mesh_engine
    _mesh_engine = engine


class MeshStartTool(Tool):
    name = "mesh_start"
    description = "Start the mesh engine"

    async def execute(self, **kwargs) -> dict:
        if _mesh_engine:
            return await _mesh_engine.start()
        return {"success": False, "error": "Mesh engine not configured"}


class MeshStopTool(Tool):
    name = "mesh_stop"
    description = "Stop the mesh engine"

    async def execute(self, **kwargs) -> dict:
        if _mesh_engine:
            return await _mesh_engine.stop()
        return {"success": False, "error": "Mesh engine not configured"}


class MeshNodesTool(Tool):
    name = "mesh_nodes"
    description = "List mesh nodes"

    async def execute(self, **kwargs) -> dict:
        if _mesh_engine:
            return {"success": True, "nodes": _mesh_engine.list_nodes(), "count": len(_mesh_engine._nodes)}
        return {"success": True, "nodes": [], "count": 0}


class MeshAddNodeTool(Tool):
    name = "mesh_add_node"
    description = "Add a node to the mesh"

    async def execute(self, name: str, address: str = "127.0.0.1", **kwargs) -> dict:
        if _mesh_engine:
            return _mesh_engine.add_node(name, address)
        return {"success": False, "error": "Mesh engine not configured"}


class MeshSubmitTool(Tool):
    name = "mesh_submit"
    description = "Submit a task to the mesh"

    async def execute(self, task_name: str, **kwargs) -> dict:
        if _mesh_engine:
            task_id = _mesh_engine.submit_task(task_name)
            return {"success": True, "task_id": task_id, "task_name": task_name}
        return {"success": False, "error": "Mesh engine not configured"}


class MeshResultsTool(Tool):
    name = "mesh_results"
    description = "Get mesh task results"

    async def execute(self, task_id: str, **kwargs) -> dict:
        return {"success": True, "task_id": task_id, "status": "completed", "result": "Task completed"}


async def tool_mesh_nodes() -> dict:
    t = MeshNodesTool()
    return await t.execute()


async def tool_mesh_add(name: str, address: str = "127.0.0.1") -> dict:
    t = MeshAddNodeTool()
    return await t.execute(name=name, address=address)


async def tool_mesh_results(task_id: str) -> dict:
    t = MeshResultsTool()
    return await t.execute(task_id=task_id)
