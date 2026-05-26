from uuid import uuid4


class DaemonConfig:
    def __init__(self, host: str = "0.0.0.0", port: int = 4890, workers: int = 4):
        self.host = host
        self.port = port
        self.workers = workers


class KyrosDaemon:
    def __init__(self, config: DaemonConfig = None):
        self.config = config or DaemonConfig()
        self.daemon_id = str(uuid4())[:12]
        self.running = False
