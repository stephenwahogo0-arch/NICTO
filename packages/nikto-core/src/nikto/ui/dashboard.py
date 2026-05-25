import asyncio
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, ProgressBar, RichLog, Label
from textual.reactive import reactive
from nikto.ui.theme import NICTO_THEME

C = NICTO_THEME["colors"]
T = NICTO_THEME["textual"]


class StatusPanel(Static):
    def compose(self):
        yield Label("BRAIN STATUS", classes="panel-title")
        yield DataTable(classes="status-table")

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Component", "Status", "Confidence")
        table.add_rows([
            ("Identity", "ONLINE", "1.00"),
            ("Knowledge Core", "ONLINE", "0.92"),
            ("Memory", "ONLINE", "0.88"),
            ("Reasoner", "ONLINE", "0.95"),
            ("Emotion", "ONLINE", "0.76"),
            ("Conscience", "ACTIVE", "0.90"),
            ("Learner", "ACTIVE", "0.84"),
            ("Language", "READY", "0.91"),
        ])


class MemoryPanel(Static):
    def compose(self):
        yield Label("MEMORY STATS", classes="panel-title")
        yield DataTable(classes="memory-table")

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Type", "Count", "Usage")
        table.add_rows([
            ("Episodic", "1,247", "62%"),
            ("Semantic", "3,891", "78%"),
            ("Procedural", "534", "43%"),
            ("Working", "12", "24%"),
        ])


class TaskPanel(Static):
    def compose(self):
        yield Label("ACTIVE TASKS", classes="panel-title")
        yield DataTable(classes="task-table")

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Task", "Progress", "Priority")
        table.add_rows([
            ("Knowledge Consolidation", "78%", "HIGH"),
            ("Learning Review", "45%", "MEDIUM"),
            ("Memory Cleanup", "0%", "LOW"),
            ("Threat Intel Update", "100%", "DONE"),
        ])


class MetricsPanel(Static):
    def compose(self):
        yield Label("SYSTEM METRICS", classes="panel-title")
        with Horizontal():
            yield Label("CPU:")
            yield ProgressBar(total=100, show_eta=False, classes="metric-bar")
        with Horizontal():
            yield Label("RAM:")
            yield ProgressBar(total=100, show_eta=False, classes="metric-bar")
        with Horizontal():
            yield Label("DISK:")
            yield ProgressBar(total=100, show_eta=False, classes="metric-bar")
        with Horizontal():
            yield Label("TOKENS:")
            yield Static("1,024 / 4,096", classes="metric-text")

    def on_mount(self):
        self.set_interval(5, self._update_metrics)

    def _update_metrics(self):
        import random
        bars = self.query(ProgressBar)
        for bar in bars:
            bar.progress = random.randint(20, 80)


class KnowledgePanel(Static):
    def compose(self):
        yield Label("KNOWLEDGE BASE", classes="panel-title")
        yield DataTable(classes="knowledge-table")

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Collection", "Entries")
        table.add_rows([
            ("CVEs", "50"),
            ("Pentest Playbooks", "30"),
            ("Programming Languages", "60"),
            ("Framework Patterns", "40"),
            ("Cloud Patterns", "25"),
            ("AI Patterns", "25"),
        ])


class NiktoDashboard(App):
    CSS = f"""
    Screen {{
        background: {C["bg_primary"]};
    }}
    Header {{
        background: {C["bg_secondary"]};
        color: {C["accent_primary"]};
    }}
    Footer {{
        background: {C["bg_secondary"]};
        color: {C["text_secondary"]};
    }}
    .panel-title {{
        color: {C["accent_primary"]};
        text-style: bold;
        padding: 0 1;
    }}
    StatusPanel, MemoryPanel, TaskPanel, MetricsPanel, KnowledgePanel {{
        border: solid {C["border_mid"]};
        background: {C["bg_panel"]};
        margin: 1;
        height: auto;
    }}
    DataTable {{
        background: {C["bg_card"]};
        color: {C["text_primary"]};
    }}
    DataTable > .datatable--header {{
        background: {C["bg_secondary"]};
        color: {C["accent_primary"]};
    }}
    ProgressBar {{
        width: 20;
    }}
    ProgressBar > .bar {{
        color: {C["accent_primary"]};
        background: {C["bg_card"]};
    }}
    .metric-text {{
        color: {C["text_primary"]};
    }}
    #main-container {{
        layout: grid;
        grid-size: 2 3;
        grid-gutter: 1;
        padding: 1;
    }}
    """

    def compose(self):
        yield Header(show_clock=True)
        yield Footer()
        with Container(id="main-container"):
            yield StatusPanel()
            yield MemoryPanel()
            yield TaskPanel()
            yield MetricsPanel()
            yield KnowledgePanel()
            yield RichLog(highlight=True, markup=True, classes="log-panel")

    def on_mount(self):
        log = self.query_one(RichLog)
        log.write("[bright_green]NICTO v2.0 Dashboard Online[/bright_green]")
        log.write("[dim]System ready. All modules nominal.[/dim]")
        self.set_interval(10, self._add_log_entry)

    def _add_log_entry(self):
        import random
        log = self.query_one(RichLog)
        entries = [
            "[dim green]Memory consolidation cycle complete[/dim green]",
            "[green]Knowledge base updated[/green]",
            "[bright_green]Self-health check: ALL PASS[/bright_green]",
            "[dim]Learning review queued[/dim]",
        ]
        log.write(random.choice(entries))


def run_dashboard():
    app = NiktoDashboard()
    app.run()
