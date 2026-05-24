from uuid import uuid4
from nikto.tools.base import Tool

_autopilot_engine = None

def _set_autopilot(engine):
    global _autopilot_engine
    _autopilot_engine = engine


class AutopilotStartTool(Tool):
    name = "autopilot_start"
    description = "Start the autopilot engine"

    async def execute(self, **kwargs) -> dict:
        if _autopilot_engine:
            return _autopilot_engine.start()
        return {"success": False, "error": "Autopilot engine not configured"}


class AutopilotStopTool(Tool):
    name = "autopilot_stop"
    description = "Stop the autopilot engine"

    async def execute(self, **kwargs) -> dict:
        if _autopilot_engine:
            return _autopilot_engine.stop()
        return {"success": False, "error": "Autopilot engine not configured"}


class AutopilotStatusTool(Tool):
    name = "autopilot_status"
    description = "Get autopilot engine status"

    async def execute(self, **kwargs) -> dict:
        if _autopilot_engine:
            return _autopilot_engine.status_report()
        return {"success": False, "error": "Autopilot engine not configured"}


class AutopilotReportTool(Tool):
    name = "autopilot_report"
    description = "Get autopilot earnings report"

    async def execute(self, **kwargs) -> dict:
        if _autopilot_engine:
            return _autopilot_engine.status_report()
        return {"success": False, "error": "Autopilot engine not configured"}


class AutopilotConnectTool(Tool):
    name = "autopilot_connect"
    description = "Connect to a remote service via autopilot"

    async def execute(self, name: str, conn_type: str, **kwargs) -> dict:
        from nikto.autopilot.connections import ConnectionManager, ConnectionType
        mgr = ConnectionManager()
        try:
            ct = ConnectionType(conn_type)
        except ValueError:
            ct = ConnectionType.API
        return mgr.add(name, ct)


class AutopilotEarningsTool(Tool):
    name = "autopilot_earnings"
    description = "Get autopilot total earnings"

    async def execute(self, **kwargs) -> dict:
        from nikto.autopilot.finance import FinanceManager
        fm = FinanceManager()
        return {"success": True, "total_earnings": fm.total_earnings()}


async def tool_autopilot_start() -> dict:
    t = AutopilotStartTool()
    return await t.execute()


async def tool_autopilot_stop() -> dict:
    t = AutopilotStopTool()
    return await t.execute()


async def tool_autopilot_status() -> dict:
    t = AutopilotStatusTool()
    return await t.execute()


async def tool_autopilot_report() -> dict:
    t = AutopilotReportTool()
    return await t.execute()


async def tool_autopilot_connect(name: str, conn_type: str) -> dict:
    t = AutopilotConnectTool()
    return await t.execute(name=name, conn_type=conn_type)


async def tool_autopilot_earnings() -> dict:
    t = AutopilotEarningsTool()
    return await t.execute()
