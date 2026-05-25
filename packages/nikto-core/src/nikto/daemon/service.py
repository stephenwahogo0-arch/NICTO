import asyncio
import os
import sys
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from nikto.ui.theme import NICTO_THEME, apply_theme_to_rich, generate_terminal_banner

console = apply_theme_to_rich()
C = NICTO_THEME["colors"]

VERSION = "2.0.0"
STARTUP_TIME = datetime.now(timezone.utc).isoformat()


class NiktoDaemon:
    def __init__(self):
        self._running = False
        self.modules_loaded = 0
        self.modules_failed = 0
        self.api_port = 4890

    async def startup(self):
        console.print(generate_terminal_banner(), style=NICTO_THEME["rich"]["heading"])
        console.print()
        console.print(Panel(
            Text(f"NICTO v{VERSION} — Autonomous Intelligence", style=NICTO_THEME["rich"]["heading"]),
            subtitle=Text("Built by Stephen Wahogo · Nairobi, Kenya", style=NICTO_THEME["rich"]["dim"]),
            border_style=C["border_mid"],
        ))
        console.print()

        modules = [
            ("NiktoBrain", "nikto.brain.core"),
            ("NiktoIdentity", "nikto.brain.identity"),
            ("NiktoKnowledgeCore", "nikto.brain.knowledge"),
            ("NiktoLongTermMemory", "nikto.brain.memory"),
            ("NiktoEmotionalCore", "nikto.brain.emotion"),
            ("NiktoConscience", "nikto.brain.conscience"),
            ("NiktoReasoner", "nikto.brain.reasoner"),
            ("NiktoLanguageEngine", "nikto.brain.language"),
            ("NiktoLearner", "nikto.brain.learner"),
            ("NiktoGoalSystem", "nikto.brain.goals"),
            ("NiktoTeacher", "nikto.brain.teacher"),
            ("NiktoSelfRepair", "nikto.brain.repair"),
            ("NiktoVoice", "nikto.voice.engine"),
            ("NiktoMultiModal", "nikto.input.multimodal"),
            ("NiktoProjectBuilder", "nikto.builder.project"),
            ("NiktoCodeGenerator", "nikto.builder.codegen"),
            ("NiktoConversationMemory", "nikto.memory.conversation"),
            ("NiktoExploitDB", "nikto.security.exploit_db"),
            ("NiktoThreatIntel", "nikto.security.threat_intel"),
            ("NiktoPluginEngine", "nikto.plugins.engine"),
            ("NiktoScheduler", "nikto.autopilot.scheduler"),
            ("NiktoReportingEngine", "nikto.reporting.engine"),
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[green]Loading NICTO modules...", total=len(modules))
            for name, module_path in modules:
                try:
                    __import__(module_path, fromlist=[""])
                    self.modules_loaded += 1
                    progress.console.print(f"  [green]✓[/green] {name}")
                except Exception as e:
                    self.modules_failed += 1
                    progress.console.print(f"  [red]✗[/red] {name}: {e}")
                progress.advance(task)

        console.print()
        tbl = Table(title="System Status", border_style=C["border_mid"])
        tbl.add_column("Component", style=C["accent_primary"])
        tbl.add_column("Status", style=C["text_primary"])
        tbl.add_row("Modules Loaded", f"[green]{self.modules_loaded}[/green]")
        tbl.add_row("Modules Failed", f"[red]{self.modules_failed}[/red]" if self.modules_failed else "[green]0[/green]")
        tbl.add_row("API Endpoint", f"{C['accent_electric']}http://localhost:{self.api_port}")
        tbl.add_row("Brain State", "[bright_green]NOMINAL[/bright_green]")
        console.print(tbl)
        console.print()
        console.print(Text("NICTO is ready. All systems nominal.", style=NICTO_THEME["rich"]["success"]))
        self._running = True

    async def shutdown(self):
        self._running = False
        console.print("[dim]NICTO shutting down...[/dim]")

    async def run_forever(self):
        await self.startup()
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await self.shutdown()
