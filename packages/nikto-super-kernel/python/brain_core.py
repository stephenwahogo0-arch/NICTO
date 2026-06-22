"""KYROS Super Kernel — Pythonic wrapper around native 8-sector cdylib."""

import os

try:
    import nikto_super_kernel as _native
    HAS_NATIVE = True
except ImportError:
    HAS_NATIVE = False


class SuperKernel:
    """High-performance unified kernel — 8 sectors in one native module.

    Sectors:
      1. Boot – kernel init, health checks, resource discovery
      2. Brain – neural memory, knowledge recall, context graph
      3. Physics – rigid-body N-body simulation + collision
      4. Predictive – code analysis, Monte Carlo market sim, diagnostic archival
      5. Financial – time series, risk gate, order execution, backtest
      6. Swarm – distributed agent orchestration, heartbeat tracking
      7. Sync – MPMC channels, hsync publish/subscribe (FFI)
      8. WebForge – template rendering, static site generation

    Gracefully degrades if the compiled .pyd is absent.
    """

    def __init__(self, gravity: float = 9.81, fill_latency_ms: int = 50):
        if not HAS_NATIVE:
            raise RuntimeError(
                "nikto_super_kernel native module not found. "
                "Run `cargo build --release` in packages/nikto-super-kernel "
                "and copy the .pyd to this directory."
            )
        self._kernel = _native.SuperKernel(gravity, fill_latency_ms)

    # ── Boot ──────────────────────────────────────────────────────────

    def boot_register(self, name: str, version: str) -> None:
        """Register a module for boot tracking."""
        self._kernel.boot_register(name, version)

    def boot_load(self, name: str) -> str:
        """Load a registered module and return status string."""
        return self._kernel.boot_load(name)

    def boot_health(self) -> str:
        """Return one-line health summary."""
        return self._kernel.boot_health()

    def boot_resource_report(self) -> str:
        """Return multi-line resource and module status report."""
        return self._kernel.boot_resource_report()

    # ── Neural ────────────────────────────────────────────────────────

    def neural_ingest(self, topic: str, content: str) -> None:
        """Store a knowledge record under the given topic."""
        self._kernel.neural_ingest(topic, content)

    def neural_recall(self, query: str, top_k: int = 5) -> list[str]:
        """Retrieve top-k knowledge records most relevant to query."""
        return list(self._kernel.neural_recall(query, top_k))

    def neural_count(self) -> int:
        """Total number of stored knowledge records."""
        return self._kernel.neural_count()

    # ── Physics ───────────────────────────────────────────────────────

    def physics_add_body(self, x: float, y: float, z: float,
                         mass: float, radius: float) -> None:
        """Add a rigid body at the given position."""
        self._kernel.physics_add_body(x, y, z, mass, radius)

    def physics_step(self, dt: float = 0.016) -> None:
        """Advance physics simulation by dt seconds (default ~60 FPS)."""
        self._kernel.physics_step(dt)

    def physics_body_count(self) -> int:
        """Number of rigid bodies in the simulation."""
        return self._kernel.physics_body_count()

    # ── Predictive: Code Analyzer ─────────────────────────────────────

    def code_analyze_project(self, project_path: str) -> "_native.DiagnosticReport":
        """Scan a project directory for code vulnerabilities."""
        path = os.path.abspath(project_path)
        return self._kernel.code_analyze_project(path)

    def code_vulnerability_count(self) -> int:
        """Return the number of vulnerability patterns the analyzer knows."""
        return self._kernel.code_vulnerability_count()

    # ── Predictive: Market Engine ─────────────────────────────────────

    def market_predict(self, candles: list, horizon_days: int = 30):
        """Run Monte Carlo simulation over OHLCV data.

        Parameters
        ----------
        candles : list of _native.MarketOHLCV
        horizon_days : int

        Returns
        -------
        _native.PredictionMatrix
        """
        return self._kernel.market_predict(candles, horizon_days)

    # ── Predictive: Diagnostic Archive ────────────────────────────────

    def archive_write_diag(self, report: "_native.DiagnosticReport") -> str:
        """Persist a diagnostic report to disk."""
        return self._kernel.archive_write_diag(report)

    def archive_read_diag(self, index: int) -> "_native.DiagnosticReport":
        """Read a diagnostic report by archive index."""
        return self._kernel.archive_read_diag(index)

    # ── Financial: Time Series ────────────────────────────────────────

    def finance_analyze(self, ohlcv: list):
        """Compute indicators (SMA, EMA, Bollinger, ATR, regression)."""
        return self._kernel.finance_analyze(ohlcv)

    # ── Financial: Order Executor ─────────────────────────────────────

    def finance_submit(self, proposal: "_native.TradeProposal",
                       equity: float, daily_pnl: float,
                       daily_loss_limit: float, max_drawdown_pct: float):
        """Submit a trade proposal through the risk gate."""
        return self._kernel.finance_submit(
            proposal, equity, daily_pnl, daily_loss_limit, max_drawdown_pct
        )

    def finance_fill_next(self):
        """Simulate filling the oldest pending order."""
        return self._kernel.finance_fill_next()

    # ── Swarm ─────────────────────────────────────────────────────────

    def swarm_register_agent(self, agent_id: str, role: str) -> None:
        """Register an agent in the swarm."""
        self._kernel.swarm_register_agent(agent_id, role)

    def swarm_dispatch(self, target: str, command: str,
                       payload: bytes | bytearray) -> int:
        """Dispatch a task to the target agent. Returns task ID."""
        return self._kernel.swarm_dispatch(target, command, bytes(payload))

    def swarm_heartbeat(self, agent_id: str) -> None:
        """Record a heartbeat from the given agent."""
        self._kernel.swarm_heartbeat(agent_id)

    def swarm_status(self) -> str:
        """Return multi-line swarm status report."""
        return self._kernel.swarm_status()

    # ── WebForge ──────────────────────────────────────────────────────

    def webforge_add_template(self, name: str, content: str) -> None:
        """Register a template by name."""
        self._kernel.webforge_add_template(name, content)

    def webforge_add_site(self, name: str, domain: str,
                          template: str, output_dir: str,
                          variables: dict[str, str] | None = None) -> None:
        """Register a site configuration."""
        self._kernel.webforge_add_site(
            name, domain, template, output_dir, variables or {}
        )

    def webforge_render(self, site_name: str) -> str:
        """Render a site's template with its variables."""
        return self._kernel.webforge_render(site_name)

    # ── Status ────────────────────────────────────────────────────────

    def status(self) -> str:
        """Return one-line kernel status string."""
        return self._kernel.status()

    def __repr__(self) -> str:
        try:
            return f"<SuperKernel {self.status()}>"
        except Exception:
            return f"<SuperKernel (uninitialized)>"
