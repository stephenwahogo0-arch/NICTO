#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "nikto-core", "src"))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from nikto.ui.theme import NICTO_THEME, apply_theme_to_rich

console = apply_theme_to_rich()


@click.group()
def cli():
    pass


@cli.command()
@click.argument("message", nargs=-1)
def chat(message):
    """Interactive chat with NICTO brain"""
    msg = " ".join(message) if message else ""
    from nikto import NiktoBrain
    async def _run():
        brain = NiktoBrain()
        await brain.awaken(restore=True)
        if msg:
            result = brain.process(msg)
            console.print(f"[bright_green]NICTO:[/bright_green] {result['response']}")
        else:
            console.print("[bright_green]Entering interactive chat mode. Type 'exit' to quit.[/bright_green]")
            while True:
                try:
                    user = input(f"{NICTO_THEME['rich']['prompt']}> ")
                except (EOFError, KeyboardInterrupt):
                    break
                if user.lower() in ("exit", "quit"):
                    break
                result = brain.process(user)
                console.print(f"[bright_green]NICTO:[/bright_green] {result['response']}")
        await brain.sleep()
    asyncio.run(_run())


@cli.command()
def voice():
    """Voice chat mode with NICTO"""
    from nikto import NiktoBrain, NiktoVoice
    async def _run():
        brain = NiktoBrain()
        await brain.awaken(restore=True)
        voice = NiktoVoice()
        console.print("[bright_green]Starting voice chat. Say 'exit' to quit.[/bright_green]")
        while True:
            text = await voice.listen()
            if not text or text.startswith("[Voice"):
                continue
            console.print(f"[dim]You said:[/dim] {text}")
            if text.lower() in ("exit", "quit", "stop"):
                break
            result = brain.process(text)
            response = result['response']
            console.print(f"[bright_green]NICTO:[/bright_green] {response}")
            await voice.speak(response)
        await brain.sleep()
    asyncio.run(_run())


@cli.command()
@click.argument("topic")
def learn(topic):
    """Teach NICTO a new topic"""
    from nikto import NiktoBrain
    async def _run():
        brain = NiktoBrain()
        await brain.awaken(restore=True)
        result = await brain.teacher.learn_topic(topic)
        console.print(f"[green]Learned:[/green] {topic}")
        console.print(f"Lessons: {result.lessons_count}, Gaps filled: {result.gaps_filled}")
        await brain.sleep()
    asyncio.run(_run())


@cli.command()
@click.argument("description", nargs=-1)
@click.option("--output", "-o", default=".")
def build(description, output):
    """Build a project from description"""
    from nikto import NiktoProjectBuilder
    desc = " ".join(description)
    async def _run():
        builder = NiktoProjectBuilder()
        result = await builder.build_from_description(desc, output)
        for f in result.files_created:
            console.print(f"[green]Created:[/green] {f}")
    asyncio.run(_run())


@cli.command()
@click.argument("target")
def scan(target):
    """Run security scan on target"""
    from nikto import NiktoExploitDB
    db = NiktoExploitDB()
    console.print(f"[bright_green]NICTO Security Scan:[/bright_green] {target}")
    console.print(f"Available reverse shells: {', '.join(db.list_shell_types())}")
    console.print(f"XSS payloads: {len(db.XSS_PAYLOADS)}")
    console.print(f"SQLi payloads: {sum(len(v) for v in db.SQL_PAYLOADS.values())}")
    for cat, payloads in db.SQL_PAYLOADS.items():
        console.print(f"  [dim]{cat}[/dim]: {payloads[0]}")


@cli.command()
def exploit():
    """Browse exploit database"""
    from nikto import NiktoExploitDB
    db = NiktoExploitDB()
    table = Table(title="NICTO Exploit Database", border_style=NICTO_THEME["colors"]["border_mid"])
    table.add_column("Category", style=NICTO_THEME["colors"]["accent_primary"])
    table.add_column("Count", style=NICTO_THEME["colors"]["text_primary"])
    for cat in db.list_categories():
        count = len(db.get_payload_by_category(cat))
        table.add_row(cat, str(count))
    console.print(table)


@cli.command()
def dashboard():
    """Open Textual TUI dashboard"""
    from nikto.ui.dashboard import run_dashboard
    run_dashboard()


@cli.command()
def status():
    """Show system status"""
    from nikto import NiktoBrain
    async def _run():
        brain = NiktoBrain()
        await brain.awaken(restore=True)
        s = brain.get_status()
        i = brain.introspect()
        table = Table(title="NICTO System Status", border_style=NICTO_THEME["colors"]["border_mid"])
        table.add_column("Metric", style=NICTO_THEME["colors"]["accent_primary"])
        table.add_column("Value", style=NICTO_THEME["colors"]["text_primary"])
        table.add_row("Name", s['name'])
        table.add_row("Awake", str(s['awake']))
        table.add_row("Cycle", str(s['cycle']))
        table.add_row("Mood", s['mood'])
        table.add_row("Thoughts", str(s['thoughts']))
        table.add_row("Memories", str(s['memories']))
        table.add_row("Goals", str(s['goals']))
        table.add_row("Facts", str(i['knowledge']['facts']))
        table.add_row("Lessons", str(i['learning']['lessons']))
        console.print(table)
        await brain.sleep()
    asyncio.run(_run())


@cli.command()
def repair():
    """Run self-repair check"""
    from nikto import NiktoSelfRepair
    async def _run():
        repair = NiktoSelfRepair()
        report = await repair.health_check_all()
        table = Table(title="Self-Repair Health Check", border_style=NICTO_THEME["colors"]["border_mid"])
        table.add_column("Module", style=NICTO_THEME["colors"]["accent_primary"])
        table.add_column("Status", style=NICTO_THEME["colors"]["text_primary"])
        for mod, result in report.modules.items():
            status_style = "green" if result['status'] == "PASS" else "red"
            table.add_row(mod, f"[{status_style}]{result['status']}[/{status_style}]")
        console.print(table)
    asyncio.run(_run())


@cli.command()
def update():
    """Check for NICTO updates"""
    from nikto import NiktoAutoUpdater
    async def _run():
        updater = NiktoAutoUpdater()
        info = await updater.check_for_updates()
        console.print(f"[bright_green]Current version:[/bright_green] {info.current_version}")
        console.print(f"[bright_green]Latest version:[/bright_green] {info.latest_version}")
        if info.update_available:
            console.print("[bright_green]Update available![/bright_green]")
            console.print(info.changelog[:200])
        else:
            console.print("[green]NICTO is up to date.[/green]")
    asyncio.run(_run())


@cli.command()
@click.argument("title", nargs=-1)
def report(title):
    """Generate a report"""
    from nikto import NiktoReportingEngine
    title_str = " ".join(title) if title else "Security Report"
    async def _run():
        engine = NiktoReportingEngine()
        r = await engine.generate_pentest_report([], "example.com")
        console.print(f"[green]Report generated:[/green] {r.title}")
        console.print(f"Findings: {len(r.findings)}")
        console.print(f"Summary: {r.summary}")
    asyncio.run(_run())


@cli.command()
def skills():
    """List all 80 NICTO skills"""
    from nikto.skills.production import register_production_skills
    from nikto.skills.base import SkillRuntime
    
    runtime = SkillRuntime()
    skills_list = register_production_skills(runtime)
    
    table = Table(title="NICTO Skills (80 total)", border_style=NICTO_THEME["colors"]["border_mid"])
    table.add_column("#", style=NICTO_THEME["colors"]["text_muted"])
    table.add_column("Name", style=NICTO_THEME["colors"]["accent_primary"])
    table.add_column("Description", style=NICTO_THEME["colors"]["text_primary"])
    for i, s in enumerate(skills_list, 1):
        desc = s.get("description", "")[:60]
        table.add_row(str(i), s.get("name", ""), desc)
    console.print(table)


@cli.command()
def knowledge():
    """Browse knowledge base"""
    from nikto.knowledge.loader import COLLECTION_METADATA
    table = Table(title="NICTO Knowledge Base", border_style=NICTO_THEME["colors"]["border_mid"])
    table.add_column("Collection", style=NICTO_THEME["colors"]["accent_primary"])
    table.add_column("Description", style=NICTO_THEME["colors"]["text_primary"])
    for name, meta in COLLECTION_METADATA.items():
        table.add_row(name, meta.get("description", ""))
    console.print(table)


@cli.command()
def daemon():
    """Start NICTO daemon"""
    from nikto.daemon.service import NiktoDaemon
    async def _run():
        daemon = NiktoDaemon()
        await daemon.run_forever()
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[dim]NICTO daemon stopped.[/dim]")


@cli.command()
@click.argument("mode", default="directive")
@click.argument("prompt", nargs=-1, default="explore consciousness")
def dream(mode, prompt):
    """Use Dream Steerer to augment thinking"""
    from nikto import NiktoDreamSteerer
    prompt_str = " ".join(prompt)
    d = NiktoDreamSteerer()
    result = d.steer(prompt_str, mode)
    console.print(f"[bright_green]Dream Mode:[/bright_green] {result['mode']}")
    console.print(f"[green]Patterns:[/green] {', '.join(result['patterns_applied'])}")
    console.print(f"[green]Coherence:[/green] {result['coherence']}")
    console.print(f"[cyan]Output:[/cyan] {result['output']}")
    table = Table(title="Available Dream Patterns", border_style=NICTO_THEME["colors"]["border_mid"])
    table.add_column("Name", style=NICTO_THEME["colors"]["accent_primary"])
    table.add_column("Mode", style=NICTO_THEME["colors"]["text_muted"])
    table.add_column("Strength", style=NICTO_THEME["colors"]["text_primary"])
    for pat in d.list_patterns()[:10]:
        table.add_row(pat["name"], pat["mode"], str(pat["strength"]))
    console.print(table)


@cli.command()
@click.argument("claim", nargs=-1)
def truth(claim):
    """Check truth score of a claim"""
    from nikto import NiktoTruthEngine
    claim_str = " ".join(claim)
    eng = NiktoTruthEngine()
    result = eng.compute_truth_score(claim_str, "deep")
    console.print(f"[bright_green]Truth Analysis:[/bright_green]")
    table = Table(border_style=NICTO_THEME["colors"]["border_mid"])
    table.add_column("Metric", style=NICTO_THEME["colors"]["accent_primary"])
    table.add_column("Value", style=NICTO_THEME["colors"]["text_primary"])
    table.add_row("Claim", claim_str[:80])
    table.add_row("Score", str(result["truth_score"]))
    table.add_row("Status", result["status"])
    table.add_row("Level", result["verification_level"])
    console.print(table)


@cli.command()
@click.argument("input_text", nargs=-1)
def swarm(input_text):
    """Query the agent swarm"""
    from nikto import NiktoSwarmEngine, NiktoBrain
    from nikto import NiktoReasoner, NiktoLongTermMemory
    text = " ".join(input_text) if input_text else "analyze system health"

    async def _run():
        brain = NiktoBrain()
        await brain.awaken(restore=True)
        swarm_eng = NiktoSwarmEngine()
        swarm_eng.register_agent("reasoner", "reasoning", ["analysis", "logic", "deduction"])
        swarm_eng.register_agent("memory", "memory", ["recall", "storage", "search"])
        swarm_eng.register_agent("knowledge", "knowledge", ["facts", "concepts", "query"])

        result = swarm_eng.swarm_query(text, ["analysis"])
        console.print(f"[bright_green]Swarm Result:[/bright_green]")
        console.print(f"Strategy: {result['strategy']}")
        console.print(f"Agents: {result['agents_involved']}")
        leader = result.get("leader", {})
        if leader:
            console.print(f"Leader: {leader.get('name', 'N/A')}")
        for r in result.get("individual_results", []):
            console.print(f"  [dim]{r['agent']}:[/dim] {r['response'][:60]}")
        await brain.sleep()
    asyncio.run(_run())


@cli.command()
@click.argument("metric_name", default=None, required=False)
def perf(metric_name):
    """Show performance metrics"""
    from nikto import NiktoPerformanceGraph
    pg = NiktoPerformanceGraph()
    if metric_name:
        m = pg.get_metric(metric_name)
        if m:
            console.print(f"[bright_green]Metric: {metric_name}[/bright_green]")
            for k, v in m.items():
                console.print(f"  [dim]{k}:[/dim] {v}")
        else:
            console.print(f"[yellow]No data for metric '{metric_name}'[/yellow]")
    else:
        report = pg.summary_report()
        console.print(f"[bright_green]Performance Summary[/bright_green]")
        console.print(f"Metrics tracked: {report['total_metrics']}")
        console.print(f"Regressions: {report['regressions_detected']}")
        for cat, count in report.get("categories", {}).items():
            console.print(f"  [dim]{cat}:[/dim] {count}")
        console.print(f"\n[green]Sparklines:[/green]")
        console.print(pg.sparkline_report())


@cli.command()
@click.argument("action", type=click.Choice(["start", "stop", "status", "run"]))
@click.argument("task_name", nargs=-1, default=None)
def autopilot(action, task_name):
    """Control the autopilot system"""
    from nikto import NiktoAutopilot
    ap = NiktoAutopilot()

    async def _run():
        if action == "status":
            stats = ap.get_stats()
            table = Table(title="Autopilot Status", border_style=NICTO_THEME["colors"]["border_mid"])
            table.add_column("Metric", style=NICTO_THEME["colors"]["accent_primary"])
            table.add_column("Value", style=NICTO_THEME["colors"]["text_primary"])
            for k, v in stats.items():
                table.add_row(k.replace("_", " ").title(), str(v))
            console.print(table)
        elif action == "run":
            name = " ".join(task_name) if task_name else None
            if name:
                for tid, t in ap.tasks.items():
                    if t.name == name:
                        result = await ap.run_task(tid)
                        console.print(f"[green]Ran:[/green] {name} -> {'OK' if result['success'] else 'FAIL'}")
                        break
                else:
                    console.print(f"[yellow]No task named '{name}'[/yellow]")
                    ap.add_task("health_check", "echo NICTO autopilot check OK", "manual")
                    result = await ap.run_task(list(ap.tasks.keys())[0])
                    console.print(f"[green]Ran health check:[/green] {result.get('output', '')[:100]}")
            else:
                results = await ap.run_all_tasks("manual")
                for r in results:
                    console.print(f"  {r['task_name']}: {'OK' if r['success'] else 'FAIL'}")
        else:
            console.print(f"[yellow]Autopilot {action} (simulated)[/yellow]")
    asyncio.run(_run())


@cli.command()
@click.argument("command_type", type=click.Choice(["scan", "orchestrate", "list"]))
@click.argument("target", nargs=-1, default=None)
def command(command_type, target):
    """Run orchestrator workflows or security scans"""
    target_str = " ".join(target) if target else "localhost"
    if command_type == "scan":
        from nikto import NiktoScanner
        scanner = NiktoScanner()
        result = scanner.quick_scan(target_str) if target_str != "localhost" else scanner.quick_scan("127.0.0.1")
        report = scanner.assess_risk(result)
        table = Table(title=f"Security Scan: {target_str}", border_style=NICTO_THEME["colors"]["border_mid"])
        table.add_column("Property", style=NICTO_THEME["colors"]["accent_primary"])
        table.add_column("Value", style=NICTO_THEME["colors"]["text_primary"])
        for k, v in result.items():
            if k != "results":
                table.add_row(k.replace("_", " ").title(), str(v))
        console.print(table)
        risk_table = Table(title="Risk Assessment", border_style=NICTO_THEME["colors"]["border_mid"])
        risk_table.add_column("Factor", style=NICTO_THEME["colors"]["accent_primary"])
        risk_table.add_column("Value", style=NICTO_THEME["colors"]["text_primary"])
        for k, v in report.items():
            risk_table.add_row(k.replace("_", " ").title(), str(v))
        console.print(risk_table)
    elif command_type == "orchestrate":
        from nikto import NiktoOrchestrator
        orch = NiktoOrchestrator()
        wid = orch.create_workflow("quick_analysis", "Analyze and respond to input")
        orch.add_step(wid, "process_input", "reasoner", params={"action": "think",
            "kwargs": {"prompt": target_str, "style": "analytical"}})
        orch.add_step(wid, "check_facts", "truth_engine", params={"action": "compute_truth_score",
            "kwargs": {"claim": target_str}}, depends_on=[])
        result = orch.execute_workflow(wid)
        console.print(f"[bright_green]Orchestrator:[/bright_green] {result['workflow_name']}")
        console.print(f"Status: {result['status']}, Steps: {result['completed_steps']}/{result['total_steps']}")
        for step in result.get("steps", []):
            status_style = "green" if step["status"] == "completed" else "red"
            console.print(f"  [{status_style}]{step['name']}[/{status_style}]: {step['status']}")
    elif command_type == "list":
        from nikto import NiktoOrchestrator
        orch = NiktoOrchestrator()
        wfs = orch.list_workflows()
        console.print(f"[bright_green]Workflows:[/bright_green] {len(wfs)}")
        for wf in wfs:
            console.print(f"  [dim]{wf['name']}[/dim] ({wf['status']})")


@cli.command()
@click.argument("action", type=click.Choice(["start", "stop", "status", "report"]))
def pro(action):
    """Control Autopilot Pro"""
    from nikto import NiktoBrain, NiktoAutopilotPro
    async def _run():
        brain = NiktoBrain()
        await brain.awaken(restore=True)
        pro = brain.autopilot_pro
        if action == "start":
            await pro.start()
            console.print("[bright_green]Autopilot Pro started[/bright_green]")
        elif action == "stop":
            report = await pro.stop()
            console.print(f"[yellow]Stopped. Uptime: {report.uptime_seconds}s, Value: {report.total_value_generated} {report.currency}[/yellow]")
        elif action == "status":
            s = pro.get_status()
            table = Table(title="Autopilot Pro Status", border_style=NICTO_THEME["colors"]["border_mid"])
            table.add_column("Metric", style=NICTO_THEME["colors"]["accent_primary"])
            table.add_column("Value", style=NICTO_THEME["colors"]["text_primary"])
            for k, v in s.items():
                table.add_row(k.replace("_", " ").title(), str(v))
            console.print(table)
        elif action == "report":
            report = await pro.generate_full_report()
            table = Table(title="Autopilot Pro Report", border_style=NICTO_THEME["colors"]["border_mid"])
            table.add_column("Metric", style=NICTO_THEME["colors"]["accent_primary"])
            table.add_column("Value", style=NICTO_THEME["colors"]["text_primary"])
            for k, v in report.to_dict().items():
                table.add_row(k.replace("_", " ").title(), str(v))
            console.print(table)
        await brain.sleep()
    asyncio.run(_run())


@cli.command()
@click.argument("model_name", default=None, required=False)
@click.option("--skills", "-s", default=None, help="Comma-separated skill list")
def business(model_name, skills):
    """Zero-capital business engine"""
    from nikto import NiktoBrain, NiktoZeroCapitalEngine
    async def _run():
        brain = NiktoBrain()
        await brain.awaken(restore=True)
        bc = brain.zero_capital
        if model_name:
            user_skills = skills.split(",") if skills else ["python", "security"]
            plan = await bc.start_business(model_name, user_skills)
            console.print(f"[bright_green]Business Plan: {plan.model_name}[/bright_green]")
            console.print(f"[green]Capital:[/green] KES {plan.capital_required}")
            console.print(f"[green]Time to revenue:[/green] {plan.time_to_first_revenue}")
            console.print(f"[green]Monthly potential:[/green] {plan.monthly_potential}")
            console.print("\n[green]Steps:[/green]")
            for s in plan.steps:
                console.print(f"  {s}")
            console.print("\n[green]First Week Actions:[/green]")
            for a in plan.first_week_actions:
                console.print(f"  - {a}")
            console.print("\n[green]Projections:[/green]")
            for month, data in plan.projections.items():
                console.print(f"  {month}: KES {data['revenue_kes']} revenue, KES {data['profit_kes']} profit")
        else:
            models = await bc.list_models()
            table = Table(title="Zero-Capital Business Models", border_style=NICTO_THEME["colors"]["border_mid"])
            table.add_column("Model", style=NICTO_THEME["colors"]["accent_primary"])
            table.add_column("Capital", style=NICTO_THEME["colors"]["text_muted"])
            table.add_column("Time to Revenue", style=NICTO_THEME["colors"]["text_primary"])
            table.add_column("Monthly Potential", style=NICTO_THEME["colors"]["text_primary"])
            for m in models:
                table.add_row(m["name"], str(m["capital"]), m["time_to_revenue"], m["monthly_potential"])
            console.print(table)
        await brain.sleep()
    asyncio.run(_run())


@cli.command()
@click.argument("action", type=click.Choice(["open", "close", "analyze", "report"]))
@click.argument("target", nargs=-1, default=None)
def eagle(action, target):
    """Eagle Eye observation and analysis"""
    from nikto import NiktoBrain
    target_str = " ".join(target) if target else "localhost"
    async def _run():
        brain = NiktoBrain()
        await brain.awaken(restore=True)
        ee = brain.eagle_eye
        if action == "open":
            await ee.open()
            console.print(f"[bright_green]Eagle Eye is now watching[/bright_green]")
        elif action == "close":
            report = await ee.close()
            console.print(f"[yellow]Eagle Eye stopped.[/yellow] Observations: {report.total_observations}, Alerts: {report.total_alerts}")
        elif action == "analyze":
            analysis = await ee.analyze_target(target_str)
            table = Table(title=f"Eagle Eye Analysis: {target_str}", border_style=NICTO_THEME["colors"]["border_mid"])
            table.add_column("Layer", style=NICTO_THEME["colors"]["accent_primary"])
            table.add_column("Result", style=NICTO_THEME["colors"]["text_primary"])
            table.add_row("Target Type", str(analysis.surface_findings.get("target_type", "unknown")))
            table.add_row("Alert Level", analysis.alert_level)
            table.add_row("Confidence", str(analysis.confidence))
            table.add_row("Patterns Found", str(len(analysis.patterns_found)))
            table.add_row("Anomalies", str(len(analysis.anomalies_detected)))
            table.add_row("Opportunities", str(len(analysis.opportunities_identified)))
            console.print(table)
        elif action == "report":
            report = await ee.generate_report()
            table = Table(title="Eagle Eye Report", border_style=NICTO_THEME["colors"]["border_mid"])
            table.add_column("Metric", style=NICTO_THEME["colors"]["accent_primary"])
            table.add_column("Value", style=NICTO_THEME["colors"]["text_primary"])
            for k, v in report.to_dict().items():
                table.add_row(k.replace("_", " ").title(), str(v))
            console.print(table)
        await brain.sleep()
    asyncio.run(_run())


@cli.command()
@click.argument("question", nargs=-1)
@click.option("--timeframe", "-t", default="30_day", help="Prediction timeframe: 7_day, 30_day, 90_day, 1_year")
@click.option("--verify", "-v", default=None, help="Verify a prediction by ID with actual outcome")
@click.option("--accuracy", "-a", is_flag=True, help="Show prediction accuracy report")
def predict(question, timeframe, verify, accuracy):
    """Make or verify predictions"""
    from nikto import NiktoBrain
    async def _run():
        brain = NiktoBrain()
        await brain.awaken(restore=True)
        fe = brain.future_engine
        if accuracy:
            report = await fe.get_accuracy_report()
            table = Table(title="Prediction Accuracy Report", border_style=NICTO_THEME["colors"]["border_mid"])
            table.add_column("Metric", style=NICTO_THEME["colors"]["accent_primary"])
            table.add_column("Value", style=NICTO_THEME["colors"]["text_primary"])
            table.add_row("Total Predictions", str(report["total_predictions_verified"]))
            table.add_row("Average Accuracy", f"{report['average_accuracy']:.2%}")
            console.print(table)
        elif verify:
            result = await fe.verify_prediction(verify, "verified outcome")
            console.print(f"[bright_green]Verification:[/bright_green] ID={verify}")
            console.print(f"Correct: {result.was_correct}, Accuracy: {result.accuracy_score:.2%}")
        else:
            q = " ".join(question) if question else "Will AI surpass human intelligence by 2030?"
            prediction = await fe.predict(q, timeframe)
            console.print(f"[bright_green]Prediction:[/bright_green] {q[:80]}")
            console.print(f"[green]Most Likely:[/green] {prediction.most_likely_outcome}")
            console.print(f"[green]Probability:[/green] {prediction.probability:.1%}")
            console.print(f"[green]Confidence:[/green] {prediction.confidence:.1%}")
            console.print(f"[green]Timeframe:[/green] {prediction.timeframe}")
            console.print(f"[green]Domain:[/green] {prediction.domain}")
            console.print(f"\n[green]Alternative Scenarios:[/green]")
            for s in prediction.alternative_scenarios:
                console.print(f"  {s.name}: {s.outcome[:60]} ({s.probability:.0%})")
            console.print(f"\n[green]Signals to Watch:[/green]")
            for sig in prediction.signals_to_watch:
                console.print(f"  - {sig}")
            console.print(f"\n[green]Methodology Used:[/green] {', '.join(prediction.methodology)}")
            console.print(f"\n[dim]Prediction ID: {prediction.id} (save this for verification)[/dim]")
        await brain.sleep()
    asyncio.run(_run())


if __name__ == "__main__":
    cli()
