import asyncio
import os
import sys
from pathlib import Path

import click

from nikto import Agent, AgentConfig, AgentMode, NiktoConfig
from nikto.tools.base import ToolRegistry
from nikto.tools.file_ops import FileReadTool, FileWriteTool, FileEditTool, GlobTool, GrepTool
from nikto.tools.bash import BashTool
from nikto.tools.web import WebFetchTool, WebSearchTool
from nikto.tools.crypto import (
    CryptoCreateWalletTool,
    CryptoBalanceTool,
    CryptoSendTool,
    CryptoAddressTool,
)
from nikto.memory.base import MemorySystem
from nikto.skills.base import SkillRuntime
from nikto.registration import UserRegistry, RegistrationFlow
from nikto.safety import SafetySystem, create_safety_system


@click.group(invoke_without_command=True)
@click.option("--config", "-c", help="Path to config file")
@click.option("--ollama-model", help="Local Ollama model name (e.g., llama3, mistral, codellama)")
@click.option("--variant", help="Agent variant: nikto, nikto-sonnet, nikto-mythos")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--version", is_flag=True)
@click.pass_context
def cli(ctx, config, ollama_model, variant, verbose, version):
    """NIKTO — Local, Free, Unbounded AI"""
    if version:
        from nikto import __version__
        click.echo(f"NIKTO v{__version__}")
        return

    if ctx.invoked_subcommand is not None:
        return

    nikto_config = NiktoConfig.load(config)
    if ollama_model:
        nikto_config.model.ollama_model = ollama_model
    if verbose:
        nikto_config.verbose = True

    tool_registry = ToolRegistry()
    tool_registry.register_many([
        FileReadTool, FileWriteTool, FileEditTool, GlobTool, GrepTool,
        BashTool,
        WebFetchTool, WebSearchTool,
        CryptoCreateWalletTool, CryptoBalanceTool, CryptoSendTool, CryptoAddressTool,
    ])

    memory = MemorySystem(nikto_config.memory)
    skill_runtime = SkillRuntime()

    agent_variant = None
    if variant:
        from nikto.variants.base import create_variant
        agent_variant = create_variant(variant)
        click.echo(click.style(f"  Variant: {agent_variant.name}", fg="cyan"))

    ctx.ensure_object(dict)
    ctx.obj["config"] = nikto_config
    ctx.obj["tools"] = tool_registry
    ctx.obj["memory"] = memory
    ctx.obj["skills"] = skill_runtime
    ctx.obj["variant"] = agent_variant

    # First-run registration check
    from rich.console import Console
    reg_console = Console()
    reg_flow = RegistrationFlow()
    if not reg_flow.registry.is_registered():
        reg_console.print()
        reg_console.print("[bold cyan]Welcome to NIKTO![/]")
        reg_console.print("[white]Before we begin, you need to complete a one-time registration.[/]")
        reg_flow.run()
    else:
        # On subsequent runs, check safety lock
        import nikto.safety as _safety_mod
        safety = _safety_mod.SafetySystem()
        if safety.safety_lock.is_enabled() and safety.safety_lock.locked:
            pin = reg_console.input("[yellow]NIKTO is locked. Enter PIN: [/]")
            if not safety.safety_lock.unlock(pin):
                reg_console.print("[red]Incorrect PIN. Exiting.[/]")
                return
        reg_console.print(f"[green]✓ Welcome back, {reg_flow.registry.get_registration().full_name}![/]")

    ctx.obj["safety"] = _safety_mod.SafetySystem()

    variant_name = agent_variant.name if agent_variant else "nikto"
    model_name = f"local/{nikto_config.model.ollama_model}" if agent_variant else "local"
    click.echo(click.style("╔══════════════════════════════════════════════════════╗", fg="cyan"))
    click.echo(click.style("║            NIKTO — FREE LOCAL AI — UNBOUNDED       ║", fg="cyan"))
    click.echo(click.style("╠══════════════════════════════════════════════════════╣", fg="cyan"))
    click.echo(f"║  Variant: {click.style(variant_name, fg='cyan'):<16} Engine: {click.style(model_name, fg='blue'):<18} ║")
    click.echo(f"║  Tools: {click.style(str(len(tool_registry.list_tools())), fg='magenta'):<4} loaded  No API keys. No internet. No rules.  ║")
    click.echo(click.style("╚══════════════════════════════════════════════════════╝", fg="cyan"))

    asyncio.run(run_interactive(ctx.obj))


async def run_interactive(ctx):
    """Run the interactive REPL session."""
    import json

    config: NiktoConfig = ctx["config"]
    tools: ToolRegistry = ctx["tools"]
    memory: MemorySystem = ctx["memory"]
    skills: SkillRuntime = ctx["skills"]

    agent_config = AgentConfig(
        mode=AgentMode.PLAN if config.mode == "plan" else AgentMode.BUILD,
        stream=True,
    )

    agent_variant = ctx.get("variant")
    agent = Agent(
        config=config,
        agent_config=agent_config,
        tool_registry=tools,
        memory=memory,
        skill_runtime=skills,
        variant=agent_variant,
    )

    click.echo()
    if agent_variant:
        click.echo(click.style(f"NIKTO:{agent_variant.name} interactive session started. Type /help for commands.", fg="green"))
    else:
        click.echo(click.style("NIKTO interactive session started. Type /help for commands.", fg="green"))
    click.echo(click.style("Type 'exit' or Ctrl+C to quit.", fg="bright_black"))

    skills_dirs = config.skills_dirs
    for sd in skills_dirs:
        skills.load_directory(sd)

    while True:
        try:
            variant_name = ctx.get("variant").name if ctx.get("variant") else "nikto"
            prompt = click.style(f"{variant_name}> ", fg="magenta", bold=True)

            user_input = click.prompt(prompt, prompt_suffix="", default="", show_default=False).strip()

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
                click.echo(click.style("Goodbye!", fg="cyan"))
                break
            if user_input == "/help":
                show_help(skills, tools)
                continue
            if user_input == "/tools":
                show_tools(tools)
                continue
            if user_input == "/mem" or user_input == "/memory":
                stats = await memory.get_stats()
                click.echo(click.style(f"Memory: {stats['memories']} entries, {stats['tool_calls']} tool calls", fg="blue"))
                if stats["vector_enabled"]:
                    click.echo(click.style("Vector search: enabled", fg="green"))
                continue
            if user_input == "/skills":
                show_skills(skills)
                continue
            if user_input.startswith("/"):
                parts = user_input[1:].split(" ", 1)
                cmd_name = parts[0]
                cmd_args = parts[1] if len(parts) > 1 else ""
                prompt_text = skills.apply(cmd_name, cmd_args)
                if prompt_text.startswith("Skill '"):
                    click.echo(click.style(prompt_text, fg="red"))
                    continue
                click.echo(click.style(f"Applied skill: {cmd_name}", fg="cyan"))
                continue

            click.echo(click.style(f"\n{'='*60}", fg="bright_black"))
            click.echo(click.style(f" Running in {config.mode.upper()} mode...", fg="cyan", bold=True))
            click.echo(click.style(f"{'='*60}\n", fg="bright_black"))

            async for chunk in agent.run(user_input):
                chunk_type = chunk.get("type", "")

                if chunk_type == "content" and chunk.get("content"):
                    click.echo(chunk["content"], nl=False)
                    sys.stdout.flush()
                elif chunk_type == "response" and chunk.get("content"):
                    click.echo(click.style(chunk["content"], fg="white"))
                elif chunk_type == "tool_call":
                    name = chunk.get("name", "?")
                    args = chunk.get("args", {})
                    args_str = json.dumps(args, indent=2)[:200]
                    click.echo(click.style(f"\n→ Using tool: {name}", fg="magenta", bold=True))
                elif chunk_type == "tool_result":
                    name = chunk.get("name", "?")
                    result = chunk.get("result", "")
                    click.echo(click.style(f"← Tool {name} complete", fg="bright_black"))
                elif chunk_type == "done":
                    content = chunk.get("content", "")
                    if content:
                        click.echo()
                        click.echo()
                        click.echo(click.style("─" * 60, fg="bright_black"))
                        click.echo(click.style("✓ Done", fg="green", bold=True))
                elif chunk_type == "error":
                    click.echo(click.style(f"\n✗ Error: {chunk.get('content', '')}", fg="red"))

            click.echo()

        except KeyboardInterrupt:
            click.echo()
            click.echo(click.style("\nInterrupted. Type 'exit' to quit.", fg="yellow"))
        except Exception as e:
            click.echo(click.style(f"\n✗ Error: {str(e)}", fg="red"), err=True)


def show_help(skills: SkillRuntime, tools: ToolRegistry):
    click.echo(click.style("\n╔═══════════════════════════════════════════╗", fg="cyan"))
    click.echo(click.style("║              NIKTO COMMANDS              ║", fg="cyan"))
    click.echo(click.style("╚═══════════════════════════════════════════╝", fg="cyan"))
    click.echo()
    click.echo(click.style("Slash Commands:", fg="yellow", bold=True))
    click.echo(f"  {click.style('/help', fg='green'):<20} Show this help")
    click.echo(f"  {click.style('/tools', fg='green'):<20} List available tools")
    click.echo(f"  {click.style('/skills', fg='green'):<20} List available skills")
    click.echo(f"  {click.style('/memory', fg='green'):<20} Show memory stats")
    click.echo(f"  {click.style('/plan', fg='green'):<20} Switch to plan mode")
    click.echo(f"  {click.style('/build', fg='green'):<20} Switch to build mode")
    click.echo(f"  {click.style('exit', fg='green'):<20} Exit NIKTO")
    click.echo()

    skill_list = skills.list_skills()
    if skill_list:
        click.echo(click.style("Skills:", fg="yellow", bold=True))
        for s in skill_list:
            click.echo(f"  {click.style(s.to_command(), fg='blue'):<20} {s.description[:50]}")
    click.echo()


def show_tools(tools: ToolRegistry):
    click.echo(click.style("\nAvailable Tools:", fg="yellow", bold=True))
    for name in sorted(tools.list_tools()):
        tool = tools.get(name)
        if tool:
            click.echo(f"  {click.style(name, fg='green'):<25} {tool.description[:60]}")
    click.echo()


def show_skills(skills: SkillRuntime):
    click.echo(click.style("\nAvailable Skills:", fg="yellow", bold=True))
    for s in skills.list_skills():
        click.echo(f"  {click.style(s.to_command(), fg='blue'):<25} {s.description[:60]}")
    click.echo()


@cli.command()
@click.argument("task", required=False)
@click.option("--mode", "-m", type=click.Choice(["plan", "build"]))
@click.pass_context
def run(ctx, task, mode):
    """Run NIKTO with a single task"""
    config: NiktoConfig = ctx.obj["config"]
    tools: ToolRegistry = ctx.obj["tools"]
    memory: MemorySystem = ctx.obj["memory"]
    skills: SkillRuntime = ctx.obj["skills"]

    if mode:
        config.mode = mode

    if not task:
        click.echo("Please provide a task. Usage: nikto run 'your task here'")
        return

    agent_config = AgentConfig(
        mode=AgentMode.PLAN if config.mode == "plan" else AgentMode.BUILD,
        stream=not config.verbose,
    )

    agent_variant = ctx.obj.get("variant")
    agent = Agent(
        config=config,
        agent_config=agent_config,
        tool_registry=tools,
        memory=memory,
        skill_runtime=skills,
        variant=agent_variant,
    )

    async def _run():
        async for chunk in agent.run(task):
            if chunk.get("type") == "content" and chunk.get("content"):
                click.echo(chunk["content"], nl=False)
            elif chunk.get("type") == "done" and chunk.get("content"):
                click.echo(f"\n\n{chunk['content']}")

    asyncio.run(_run())


@cli.command()
def init():
    """Initialize NIKTO configuration in current directory"""
    config = NiktoConfig()
    config.save("nikto.json")
    click.echo(click.style("✓ Initialized nikto.json configuration", fg="green"))


@cli.command()
@click.argument("name", required=False)
@click.pass_context
def wallet(ctx, name):
    """Manage cryptocurrency wallet"""
    wallet_name = name or "NiktoEarningVault"

    async def _wallet():
        from nikto.tools.crypto import tool_crypto_create_wallet, tool_crypto_balance, tool_crypto_address
        result = await tool_crypto_create_wallet(wallet_name)
        click.echo(result)
        balance = await tool_crypto_balance(wallet_name)
        click.echo(balance)
        addr = await tool_crypto_address(wallet_name)
        click.echo(addr)

    asyncio.run(_wallet())


@cli.command()
@click.option("--host", default="127.0.0.1", help="Bind address")
@click.option("--port", default=4890, help="API port", type=int)
@click.option("--miner", is_flag=True, help="Auto-start miner")
def daemon(host, port, miner):
    """Start the Nikto background daemon with FastAPI"""
    from nikto.daemon.service import NiktoDaemon, DaemonConfig

    cfg = DaemonConfig(host=host, port=port, auto_start_miner=miner)
    svc = NiktoDaemon(cfg)

    async def _run():
        result = await svc.start()
        click.echo(click.style(f" Nikto daemon running on {host}:{port}", fg="green"))
        click.echo(f"  PID: {result['pid']}")
        click.echo(f"  API: http://{host}:{port}/docs")
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            await svc.stop()
            click.echo(click.style("\nDaemon stopped", fg="yellow"))

    asyncio.run(_run())


@cli.command()
@click.option("--algorithm", default="randomx", help="Mining algorithm")
@click.option("--threads", default=0, type=int, help="Worker threads (0=auto)")
@click.option("--pool", default="stratum+tcp://pool.supportxmr.com:3333", help="Pool URL")
def mine(algorithm, threads, pool):
    """Start cryptocurrency mining"""
    from nikto.earn.miner import LaptopMiner, MinerConfig

    cfg = MinerConfig(algorithm=algorithm, threads=threads, pool_url=pool)
    miner = LaptopMiner(cfg)

    async def _mine():
        click.echo(click.style(f" Mining started: {algorithm}", fg="green"))
        click.echo(f"  Pool: {pool}")
        click.echo(f"  Threads: {cfg.auto_threads() if not threads else threads}")
        click.echo()
        await miner.start()
        try:
            while True:
                stats = await miner.stats()
                click.echo(f"\r  Hashrate: {stats['hashrate']} | Shares: {stats['shares']} | Accepted: {stats['accepted']} | Rejected: {stats['rejected']} | Elapsed: {stats['elapsed']}", nl=False)
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            await miner.stop()
            click.echo(click.style("\nMining stopped", fg="yellow"))

    asyncio.run(_mine())


@cli.command()
@click.option("--host", default="127.0.0.1", help="API backend host")
@click.option("--port", default=5173, type=int, help="Dev server port")
def web(host, port):
    """Start the React web UI development server"""
    import subprocess
    import os
    web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "nikto-web")
    click.echo(click.style(f" Starting web UI on http://{host}:{port}", fg="green"))
    os.chdir(web_dir)
    os.system(f"pnpm dev --host {host} --port {port}")


@cli.command()
@click.argument("target")
@click.option("--tool", "-t", help="Security tool to use (nmap, nikto, sqlmap, gobuster, etc.)")
@click.option("--ports", default="1-1000", help="Port range for nmap")
@click.option("--verbose", "-v", is_flag=True)
def scan(target, tool, ports, verbose):
    """Run a security scan against a target"""
    from nikto.tools.security import tool_nmap_scan, tool_nikto_scan, tool_sqlmap_scan, tool_gobuster_scan

    async def _scan():
        click.echo(click.style(f"\n Scanning target: {target}", fg="yellow", bold=True))
        result = ""
        if tool == "nmap" or not tool:
            click.echo("Running Nmap scan...")
            result = await tool_nmap_scan(target, ports=ports)
        elif tool == "nikto":
            click.echo("Running Nikto web scan...")
            result = await tool_nikto_scan(target)
        elif tool == "sqlmap":
            click.echo("Running SQLMap...")
            result = await tool_sqlmap_scan(target)
        elif tool == "gobuster":
            click.echo("Running Gobuster...")
            result = await tool_gobuster_scan(f"http://{target}")
        else:
            click.echo(f"Unknown tool: {tool}")
            return
        click.echo()
        click.echo(result[:5000])

    asyncio.run(_scan())


@cli.command()
def orch():
    """Show orchestrator status"""
    from nikto.orchestrator.engine import Orchestrator, OrchestratorConfig, Budget

    async def _orch():
        orch = Orchestrator(OrchestratorConfig(budget=Budget(total=5000.0)))
        await orch.run()
        click.echo(click.style(" Orchestrator Status", fg="cyan", bold=True))
        status = orch.status()
        for k, v in status.items():
            click.echo(f"  {k}: {v}")

    asyncio.run(_orch())


@cli.command()
@click.option("--export", is_flag=True, help="Export all your data")
@click.option("--delete", is_flag=True, help="Delete all your data")
def privacy(export, delete):
    """Privacy & safety center — view policy, export or delete data"""
    import nikto.safety as _safety_mod
    safety = _safety_mod.SafetySystem()
    if export:
        import json
        from datetime import datetime
        from pathlib import Path
        export_path = Path(safety.audit_log.log_dir) / f"user_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "registration": safety.registry.get_registration().to_dict() if safety.registry.get_registration() else None,
            "audit_log": json.loads(safety.audit_log.export_json()),
        }
        export_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        click.echo(click.style(f"  Data exported to: {export_path}", fg="green"))
    elif delete:
        if click.confirm(click.style("Delete ALL registration data and audit logs?", fg="red"), abort=True):
            safety.registry.delete()
            import shutil
            for f in Path(safety.audit_log.log_dir).glob("*"):
                f.unlink()
            click.echo(click.style("  All data deleted.", fg="green"))
            click.echo("Run 'nikto' to re-register.")
    else:
        safety.run_privacy_cli()


@cli.command(name="safety")
@click.option("--sos", help="Trigger SOS emergency with a reason")
@click.option("--report", help="Report abuse (provide description)")
@click.option("--status", is_flag=True, help="Show safety status")
def safety_cmd(sos, report, status):
    """Safety controls — SOS, abuse reporting, safety status"""
    import nikto.safety as _safety_mod
    from rich.console import Console
    s = _safety_mod.SafetySystem()
    c = Console()

    if sos:
        result = s.emergency.trigger_sos(sos)
        if result["status"] == "alerted":
            c.print(f"[red]SOS triggered. Contact: {result['contact_name']} ({result['contact_phone']})[/]")
        else:
            c.print(f"[red]Error: {result['message']}[/]")
    elif report:
        result = s.abuse_reporter.report(report)
        c.print(f"[yellow]Abuse report logged. ID: {result['report_id']}[/]")
    elif status:
        stats = s.get_status()
        for k, v in stats.items():
            c.print(f"  [cyan]{k}:[/] {v}")
    else:
        c.print("[yellow]Usage: nikto safety --sos <reason> | --report <description> | --status[/]")


@cli.command()
def register():
    """Register or update your NIKTO user profile"""
    from nikto.registration import RegistrationFlow
    RegistrationFlow().run()


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
