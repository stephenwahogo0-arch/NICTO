"""Autopilot control tools — start, stop, monitor, and manage the autopilot."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from nikto.tools.base import Tool

_autopilot_instance = None
logger = logging.getLogger(__name__)


def _set_autopilot(instance):
    global _autopilot_instance
    _autopilot_instance = instance


def _get_ap():
    return _autopilot_instance


async def tool_autopilot_start(interval_seconds: int = 60) -> str:
    from nikto.autopilot.engine import AutopilotEngine, AutopilotConfig
    from nikto.autopilot.tasks import DEFAULT_AUTOPILOT_TASKS

    ap = _get_ap()
    if ap is None:
        ap = AutopilotEngine(AutopilotConfig(interval_seconds=interval_seconds))
        _set_autopilot(ap)

    if ap.status.value == "running":
        return "Autopilot is already running."

    for task in DEFAULT_AUTOPILOT_TASKS:
        ap.register_task(task)

    await ap.start()
    return f"Autopilot started with {len(DEFAULT_AUTOPILOT_TASKS)} background tasks (interval={interval_seconds}s)"


async def tool_autopilot_stop() -> str:
    ap = _get_ap()
    if ap is None or ap.status.value == "stopped":
        return "Autopilot is not running."
    await ap.stop()
    total = ap.total_earnings
    return f"Autopilot stopped. Total earnings this session: ${total:.2f}"


async def tool_autopilot_status() -> str:
    ap = _get_ap()
    if ap is None:
        return "Autopilot has not been started yet."
    report = ap.status_report()
    lines = [
        f"Autopilot Status: {report['status']}",
        f"Session:         {report['session_id'][:8]}...",
        f"Uptime:          {report['uptime_seconds']:.0f}s",
        f"Total Earnings:  ${report['total_earnings']:.2f}",
        f"Tasks Completed: {report['tasks_completed']} ({report['tasks_succeeded']} ok, {report['tasks_failed']} failed)",
        f"Active Tasks:    {report['active_tasks']}",
        f"Connections:     {report['connections']}",
        f"Wallets:         {len(report['wallets'])}",
    ]
    return "\n".join(lines)


async def tool_autopilot_report() -> str:
    ap = _get_ap()
    if ap is None:
        return "Autopilot has not been started yet."
    return json.dumps(ap.status_report(), indent=2)


async def tool_autopilot_connect(email: str = "", password: str = "", smtp_host: str = "smtp.gmail.com") -> str:
    ap = _get_ap()
    if ap is None:
        from nikto.autopilot.engine import AutopilotEngine
        ap = AutopilotEngine()
        _set_autopilot(ap)
    await ap.connections.auto_discover()
    if email and password:
        ok = await ap.connections.connect_email(email, password, smtp_host)
        if ok:
            return f"Connected to email: {email}"
        return f"Failed to connect to email: {email}"
    total = ap.connections.count()
    details = ap.connections.list_all()
    return f"Auto-discovered {total} connections:\n" + "\n".join(f"  - {c['name']} ({c['type']}, {'connected' if c['connected'] else 'disconnected'})" for c in details)


async def tool_autopilot_earnings() -> str:
    ap = _get_ap()
    if ap is None:
        return "No autopilot earnings data available."
    summary = ap.finance.summary()
    lines = [
        f"Total Earnings:    ${summary['total_earnings_usd']:.2f} USD",
        f"Transactions:      {summary['transaction_count']}",
        f"Payment Methods:   {', '.join(summary['payment_methods'])}",
        "",
        "Recent Transactions:",
    ]
    for t in summary.get("recent", []):
        lines.append(f"  [{t['timestamp'][:19]}] {t['source']}: ${t['amount_usd']:.2f} — {t['status']}")
    return "\n".join(lines)


AutopilotStartTool = Tool(
    name="autopilot_start",
    description="Start the Nikto Autopilot background engine. Runs autonomous profit-generating tasks on a scheduled interval. Tasks include crypto market monitoring, freelance scanning, data processing, and market analysis.",
    parameters={
        "type": "object",
        "properties": {
            "interval_seconds": {"type": "integer", "description": "Interval between task cycles in seconds (default 60)"},
        },
    },
    async_function=tool_autopilot_start,
)

AutopilotStopTool = Tool(
    name="autopilot_stop",
    description="Stop the Nikto Autopilot engine. Completes current tasks and reports total earnings for the session.",
    parameters={"type": "object", "properties": {}},
    async_function=tool_autopilot_stop,
)

AutopilotStatusTool = Tool(
    name="autopilot_status",
    description="Get the current status of the Nikto Autopilot. Shows running state, earnings, tasks completed, connections, and wallet summaries.",
    parameters={"type": "object", "properties": {}},
    async_function=tool_autopilot_status,
)

AutopilotReportTool = Tool(
    name="autopilot_report",
    description="Get a detailed JSON report of all autopilot activity including task history, earnings breakdown, connection status, and wallet data.",
    parameters={"type": "object", "properties": {}},
    async_function=tool_autopilot_report,
)

AutopilotConnectTool = Tool(
    name="autopilot_connect",
    description="Auto-discover and connect to all available connections (file system, git, workspaces, email). Optionally connect a specific email account.",
    parameters={
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "Email address to connect"},
            "password": {"type": "string", "description": "Email password"},
            "smtp_host": {"type": "string", "description": "SMTP server hostname"},
        },
    },
    async_function=tool_autopilot_connect,
)

AutopilotEarningsTool = Tool(
    name="autopilot_earnings",
    description="View all autopilot earnings. Shows total earnings, transaction history, connected payment methods, and recent profit-generating activity.",
    parameters={"type": "object", "properties": {}},
    async_function=tool_autopilot_earnings,
)
