from uuid import uuid4


class MCPServerConfig:
    def __init__(self, host: str = "127.0.0.1", port: int = 4891, transport: str = "stdio"):
        self.host = host
        self.port = port
        self.transport = transport


class MCPServer:
    def __init__(self, name: str, config: MCPServerConfig = None):
        self.id = str(uuid4())[:12]
        self.name = name
        self.config = config or MCPServerConfig()
        self.running = False

    async def start(self) -> dict:
        self.running = True
        return {"success": True, "server": self.name, "status": "started", "transport": self.config.transport}

    async def stop(self) -> dict:
        self.running = False
        return {"success": True, "server": self.name, "status": "stopped"}

    async def status(self) -> dict:
        return {"id": self.id, "name": self.name, "running": self.running, "config": {"host": self.config.host, "port": self.config.port, "transport": self.config.transport}}
