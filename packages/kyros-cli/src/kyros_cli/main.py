import click


@click.group()
def cli():
    """KYROS — Modular AI Agent Framework"""


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=4890, help="Port to bind")
def daemon(host, port):
    """Start the KYROS daemon"""
    click.echo(f"KYROS daemon starting on {host}:{port}")


@cli.command()
@click.argument("message")
@click.option("--provider", default="local", help="LLM provider")
def chat(message, provider):
    """Chat with KYROS"""
    click.echo(f"[{provider}] {message}")


@cli.command()
@click.argument("target")
@click.option("--ports", default="1-1000", help="Port range")
def scan(target, ports):
    """Run a security scan on a target"""
    click.echo(f"Scanning {target} ports {ports}")


@cli.command()
def status():
    """Get KYROS system status"""
    click.echo("KYROS status: running")


if __name__ == "__main__":
    cli()
