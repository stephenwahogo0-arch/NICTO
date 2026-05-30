"""NICTO CLI — doctor, init, run, benchmark, consent commands."""
from __future__ import annotations
import sys
import os
import json
from datetime import datetime
try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

app = typer.Typer(name="nicto", help="NICTO AI Agent System CLI")
console = Console() if HAS_RICH else None

VERSION = "2.1.0"


def _print(text: str):
    if console:
        console.print(text)
    else:
        # Handle encoding for Windows console
        try:
            print(text)
        except UnicodeEncodeError:
            # Replace problematic characters with ASCII equivalents
            cleaned = text.replace('✓', '[OK]').replace('✗', '[FAIL]').replace('─', '[GPU]').replace('?', '[UNKNOWN]')
            print(cleaned)


@app.command()
def version():
    """Show NICTO version."""
    _print(f"[bold green]NICTO[/bold green] v{VERSION}" if console else f"NICTO v{VERSION}")


@app.command()
def doctor():
    """Validate installation and suggest fixes."""
    results = []

    # Python version
    py_ok = sys.version_info >= (3, 10)
    results.append(("Python >=3.10", "✓" if py_ok else "✗",
                    f"{sys.version}" if py_ok else f"Need >=3.10, have {sys.version}"))

    # Core imports
    for mod, name in [("torch", "PyTorch"), ("transformers", "Transformers"),
                      ("fastapi", "FastAPI"), ("rich", "Rich")]:
        try:
            __import__(mod)
            results.append((name, "✓", "installed"))
        except ImportError:
            results.append((name, "✗", f"pip install {mod}"))

    # GPU check
    try:
        import torch
        gpu = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu else "NONE"
        results.append(("GPU", "✓" if gpu else "─", gpu_name if gpu else "CPU only"))
    except Exception:
        results.append(("GPU", "?", "not checked"))

    # Disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free / 1e9
        results.append(("Disk space", "✓" if free_gb > 5 else "✗", f"{free_gb:.1f}GB free"))
    except Exception:
        results.append(("Disk space", "?", "not checked"))

    if HAS_RICH:
        table = Table(title="NICTO Doctor Report", box=box.ROUNDED)
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Detail")
        for name, status, detail in results:
            color = "green" if status == "✓" else "red" if status == "✗" else "yellow"
            table.add_row(name, f"[{color}]{status}[/{color}]", detail)
        console.print(table)
    else:
        print(f"\nNICTO Doctor v{VERSION}")
        print(f"{'='*50}")
        for name, status, detail in results:
            print(f"  [{status}] {name}: {detail}")

    # Summary
    failures = sum(1 for _, s, _ in results if s == "✗")
    if failures:
        print(f"\n  {failures} issues found. Run suggested pip commands.")
    else:
        _print("\n[bold green]All systems nominal![/bold green]" if console else "\nAll systems nominal!")
    return results


@app.command()
def init():
    """Initialize NICTO working directory."""
    os.makedirs(".nicto", exist_ok=True)
    os.makedirs(".nicto/data", exist_ok=True)
    os.makedirs(".nicto/logs", exist_ok=True)
    config = {
        "version": VERSION,
        "created": datetime.utcnow().isoformat(),
        "brains": ["primary", "ethical"],
        "policy_level": "strict",
        "sandbox": True,
    }
    with open(".nicto/config.json", "w") as f:
        json.dump(config, f, indent=2)
    _print("[green]✓[/green] NICTO initialized in .nicto/" if console else "NICTO initialized in .nicto/")


@app.command()
def run(prompt: str = typer.Argument(None, help="Query to process"),
        domain: str = "general"):
    """Process a query through the NICTO agent."""
    from ..core.agent import Agent

    agent = Agent()
    if prompt:
        result = agent.process(prompt, domain=domain)
        output = result.content if hasattr(result, 'content') else str(result)
        if console:
            console.print(Panel(output, title="NICTO Response", border_style="green"))
        else:
            print(f"NICTO: {output}")
    else:
        _print("[bold]NICTO Interactive Mode[/bold]" if console else "NICTO Interactive Mode")
        while True:
            try:
                q = input("\nYou: ").strip()
                if q.lower() in ("exit", "quit"):
                    break
                if q:
                    result = agent.process(q, domain=domain)
                    output = result.content if hasattr(result, 'content') else str(result)
                    print(f"\nNICTO: {output}\n")
            except (KeyboardInterrupt, EOFError):
                break


@app.command()
def consent(action: str = typer.Argument(..., help="grant | revoke | list"),
            rule: str = typer.Argument("", help="Rule ID")):
    """Manage ethical consent for policy rules."""
    from ..brains.ethical import EthicalBrain
    brain = EthicalBrain()
    if action == "grant" and rule:
        brain.consent_store.grant(rule)
        _print(f"[green]✓[/green] Consent granted for rule: {rule}" if console else f"Consent granted: {rule}")
    elif action == "revoke" and rule:
        brain.consent_store.revoke(rule)
        _print(f"[yellow]✗[/yellow] Consent revoked for rule: {rule}" if console else f"Consent revoked: {rule}")
    elif action == "list":
        rules = [r.id for r in brain.rules if r.requires_consent]
        _print("Rules requiring consent: " + ", ".join(rules) if rules else "No consent-required rules.")
    else:
        _print("[red]Usage:[/red] nicto consent grant|revoke|list [rule_id]" if console else "Usage: nicto consent grant|revoke|list [rule_id]")


def main():
    app()


if __name__ == "__main__":
    main()
