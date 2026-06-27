"""Virtual Kali Engine — Orchestrates the complete Kali simulation.

Main entry point for NICTO's exclusive Kali Linux environment.
Integrates filesystem, tools, terminal, packages, and network.
Provides NICTO brain integration and security module bridging.
"""

from __future__ import annotations
import os
import time
import json
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any, Callable

from .filesystem import VirtualFileSystem
from .tools import ToolDatabase, KaliTool, ToolCategory
from .terminal import KaliTerminal, CommandResult, CommandHistory
from .packages import PackageManager
from .network import NetworkSimulator


@dataclass
class KaliSession:
    start_time: float = 0.0
    commands_executed: int = 0
    last_command: str = ""
    environment: str = "kali"
    shell: str = "/bin/bash"
    user: str = "root"
    hostname: str = "nikto-kali"
    active: bool = False
    output_log: List[str] = field(default_factory=list)


class VirtualKaliEngine:
    """NICTO Virtual Kali Linux Engine.

    Full Kali Linux simulation with 500+ tools, APT, terminal,
    filesystem, and network. Designed for exclusive NICTO use.
    """

    def __init__(self):
        self.filesystem = VirtualFileSystem()
        self.tools = ToolDatabase()
        self.terminal = KaliTerminal(self.filesystem, self.tools)
        self.packages = PackageManager()
        self.network = NetworkSimulator()
        self.session = KaliSession()
        self._nikto_bridge: Optional[Any] = None
        self._exploit_db: Optional[Any] = None
        self._scanner: Optional[Any] = None
        self._threat_intel: Optional[Any] = None
        self._initialized = False
        self._register_all_packages()
        self._register_nicto_network_hosts()

    def _register_all_packages(self):
        for name, tool in self.tools.tools.items():
            self.packages.register(name, tool.version, tool.description)

    def _register_nicto_network_hosts(self):
        targets = [
            ("10.10.10.10", "dc01.nikto.lab", [53, 88, 135, 139, 389, 445, 3389]),
            ("10.10.10.20", "web01.nikto.lab", [22, 80, 443, 3306]),
            ("10.10.10.30", "db01.nikto.lab", [22, 3306, 5432]),
            ("10.10.10.50", "mail.nikto.lab", [25, 80, 110, 143, 443, 993]),
            ("192.168.1.50", "client-win10", [135, 139, 445, 3389]),
            ("192.168.1.60", "client-ubuntu", [22, 80, 3306]),
            ("10.0.0.1", "gateway", [22, 80, 443]),
            ("10.0.0.5", "dns-server", [53]),
            ("10.0.0.10", "nikto-engine", [22, 80, 443, 8080, 9090]),
        ]
        for ip, hostname, ports in targets:
            self.network.add_host(ip, hostname, ports)

    def initialize(self):
        if self._initialized:
            return
        self.session.start_time = time.time()
        self.session.active = True
        self.terminal.output_callback = self._log_output
        self._initialized = True

    def _log_output(self, output: str):
        self.session.output_log.append(output)
        if len(self.session.output_log) > 1000:
            self.session.output_log = self.session.output_log[-500:]

    def execute(self, command: str) -> CommandResult:
        if not self.session.active:
            return CommandResult(error="Session not active. Call initialize() first.", success=False)
        self.session.commands_executed += 1
        self.session.last_command = command
        result = self._preprocess_command(command)
        if result:
            return result
        result = self.terminal.execute(command)
        return result

    def _preprocess_command(self, command: str) -> Optional[CommandResult]:
        cmd = command.strip().split()[0] if command.strip() else ""
        if cmd in ("ifconfig", "ip"):
            iface = None
            parts = command.strip().split()
            if len(parts) > 1:
                iface = parts[-1]
            return CommandResult(output=self.network.ifconfig(iface))
        if cmd == "ping":
            args = command.strip().split()[1:]
            target = args[0] if args else "localhost"
            count = 4
            if "-c" in args:
                idx = args.index("-c")
                if idx + 1 < len(args):
                    count = int(args[idx + 1])
            return CommandResult(output=self.network.ping(target, count))
        if cmd == "traceroute":
            args = command.strip().split()[1:]
            target = args[0] if args else "localhost"
            return CommandResult(output=self.network.traceroute(target))
        if cmd == "netstat":
            return CommandResult(output=self.network.netstat())
        if cmd == "route":
            return CommandResult(output=self.network.route_table())
        if cmd == "arp":
            return CommandResult(output=self.network.arp_table())
        if cmd.startswith("apt-get"):
            return self._handle_apt(command)
        if cmd.startswith("apt"):
            return self._handle_apt(command)
        if cmd == "dpkg":
            return self._handle_dpkg(command)
        if cmd == "systemctl":
            return self._handle_systemctl(command)
        if cmd == "service":
            return self._handle_service(command)
        if cmd == "reboot":
            return CommandResult(output="System rebooting...\n")
        if cmd == "shutdown":
            return CommandResult(output="System is shutting down...\n")
        if cmd == "sudo":
            rest = " ".join(command.strip().split()[1:])
            return self.execute(rest)
        return None

    def _handle_apt(self, command: str) -> CommandResult:
        parts = command.strip().split()
        if "install" in parts:
            idx = parts.index("install")
            pkgs = parts[idx + 1:]
            output = ""
            for p in pkgs:
                output += self.packages.install(p)
            return CommandResult(output=output)
        elif "remove" in parts:
            idx = parts.index("remove")
            pkgs = parts[idx + 1:]
            output = ""
            for p in pkgs:
                output += self.packages.remove(p)
            return CommandResult(output=output)
        elif "purge" in parts:
            idx = parts.index("purge")
            pkgs = parts[idx + 1:]
            output = ""
            for p in pkgs:
                output += self.packages.remove(p, purge=True)
            return CommandResult(output=output)
        elif "update" in parts:
            return CommandResult(output=self.packages.update())
        elif "upgrade" in parts:
            return CommandResult(output=self.packages.upgrade())
        elif "search" in parts:
            idx = parts.index("search")
            query = " ".join(parts[idx + 1:]) if idx + 1 < len(parts) else ""
            return CommandResult(output=self.packages.search(query))
        elif "show" in parts:
            idx = parts.index("show")
            pkg = parts[idx + 1] if idx + 1 < len(parts) else ""
            return CommandResult(output=self.packages.show(pkg))
        elif "list" in parts:
            installed = "--installed" in parts
            pattern = ""
            for p in parts:
                if p and not p.startswith("-"):
                    pattern = p
            if installed:
                return CommandResult(output=self.packages.list_installed(pattern))
            return CommandResult(output=self.packages.list_installed())
        return CommandResult(output=f"apt: unknown command: {parts[1] if len(parts) > 1 else ''}")

    def _handle_dpkg(self, command: str) -> CommandResult:
        parts = command.strip().split()
        if "-l" in parts or "--list" in parts:
            pattern = parts[-1] if len(parts) > 2 and not parts[-1].startswith("-") else ""
            return CommandResult(output=self.packages.list_installed(pattern))
        if "-i" in parts or "--install" in parts:
            idx = parts.index("-i") if "-i" in parts else parts.index("--install")
            pkg = parts[idx + 1] if idx + 1 < len(parts) else ""
            name = pkg.replace(".deb", "").split("_")[0]
            return CommandResult(output=self.packages.install(name))
        if "-r" in parts or "--remove" in parts:
            idx = parts.index("-r") if "-r" in parts else parts.index("--remove")
            pkg = parts[idx + 1] if idx + 1 < len(parts) else ""
            return CommandResult(output=self.packages.remove(pkg))
        return CommandResult(output="dpkg: need an action option\n")

    def _handle_systemctl(self, command: str) -> CommandResult:
        parts = command.strip().split()
        if len(parts) >= 3:
            action = parts[1]
            service = parts[2]
            if action == "status":
                return CommandResult(
                    output=f"● {service}.service - {service} daemon\n"
                           f"     Loaded: loaded (/usr/lib/systemd/system/{service}.service; enabled)\n"
                           f"     Active: active (running) since {time.strftime('%a %Y-%m-%d %H:%M:%S')}\n"
                )
            elif action in ("start", "stop", "restart", "enable", "disable"):
                return CommandResult(output=f"Synchronizing state of {service}.service with SysV service script...\n")
        return CommandResult(output="systemctl: missing arguments\n")

    def _handle_service(self, command: str) -> CommandResult:
        parts = command.strip().split()
        if len(parts) >= 3:
            action = parts[1]
            service = parts[2]
            if action == "status":
                return CommandResult(
                    output=f"● {service} - {service} daemon\n"
                           f"     Active: active (running)\n"
                )
            elif action in ("start", "stop", "restart"):
                return CommandResult(output=f"[ ok ] {service} is {action}ing.\n")
        return CommandResult(output="Usage: service <option> <name>\n")

    def run_shell(self, input_fn: Callable[[], str], output_fn: Callable[[str], None]):
        """Run an interactive shell loop."""
        self.initialize()
        output_fn(f"\033[01;32mNICTO Virtual Kali Linux — Exclusive Operations Environment\033[0m\n")
        output_fn(f"Type 'nikto-help' for commands or 'help' for builtins.\n\n")
        while self.session.active:
            prompt = self.terminal.get_prompt()
            output_fn(prompt)
            try:
                cmd = input_fn()
            except (EOFError, KeyboardInterrupt):
                break
            if not cmd:
                continue
            result = self.execute(cmd)
            if result.output:
                output_fn(result.output)
            if not result.success and result.error:
                output_fn(result.error + "\n")

    def get_status(self) -> dict:
        uptime = time.time() - self.session.start_time if self.session.start_time else 0
        return {
            "initialized": self._initialized,
            "session_active": self.session.active,
            "uptime_seconds": round(uptime, 1),
            "commands_executed": self.session.commands_executed,
            "tools_available": len(self.tools.tools),
            "tools_integrated": len(self.tools.get_nicto_integrated()),
            "tool_categories": len(set(t.category.value for t in self.tools.tools.values())),
            "filesystem": self.filesystem.get_stats(),
            "packages": self.packages.get_stats(),
            "network": self.network.get_stats(),
            "user": self.session.user,
            "hostname": self.session.hostname,
        }

    def wire_nikto(self, brain=None, exploit_db=None, scanner=None, threat_intel=None):
        """Connect to NICTO brain and security modules."""
        self._nikto_bridge = brain
        self._exploit_db = exploit_db
        self._scanner = scanner
        self._threat_intel = threat_intel
        if exploit_db:
            self._integrate_exploit_db()
        if brain:
            self._integrate_brain()

    def _integrate_exploit_db(self):
        """Register NICTO exploit DB tools as NICTO-integrated."""
        if not self._exploit_db:
            return
        for tool_name, tool in self.tools.tools.items():
            if hasattr(self._exploit_db, 'search'):
                try:
                    results = self._exploit_db.search(tool_name)
                    if results:
                        tool.nicto_integrated = True
                except Exception:
                    pass

    def _integrate_brain(self):
        """Register virtual Kali with NICTO brain."""
        if not self._nikto_bridge:
            return
        try:
            if hasattr(self._nikto_bridge, 'register_subsystem'):
                self._nikto_bridge.register_subsystem("virtual_kali", self)
        except Exception:
            pass

    def export_state(self) -> dict:
        return {
            "session": {
                "start_time": self.session.start_time,
                "commands": self.session.commands_executed,
                "active": self.session.active,
            },
            "fs_size": self.filesystem.get_size("/"),
            "tools": self.tools.get_stats(),
            "network": self.network.get_stats(),
        }
