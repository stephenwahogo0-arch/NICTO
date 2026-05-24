"""NIKTO Super Kernel — Main runner: boot, train, serve."""

import sys
import time

from python.brain_core import SuperKernel, HAS_NATIVE


def banner():
    print("=" * 60)
    print("  NIKTO Super Kernel v1.0")
    print("  8 sectors — 10 languages — One unified runtime")
    print("=" * 60)


def main():
    if not HAS_NATIVE:
        print("[ERROR] nikto_super_kernel native module not found.")
        print("  Build it with:")
        print("    cd packages/nikto-super-kernel")
        print("    cargo build --release")
        print("    copy target/release/nikto_super_kernel.pyd to python/")
        sys.exit(1)

    banner()

    kernel = SuperKernel(gravity=9.81, fill_latency_ms=50)

    # ── Sector 1: Boot ──
    kernel.boot_register("predictive", "1.0.0")
    kernel.boot_register("finance", "1.0.0")
    kernel.boot_register("swarm", "1.0.0")
    kernel.boot_register("webforge", "1.0.0")
    for m in ["predictive", "finance", "swarm", "webforge"]:
        print(f"  {kernel.boot_load(m)}")
    print(f"  Health: {kernel.boot_health()}")

    # ── Sector 2: Neural ──
    kernel.neural_ingest("architecture", "NIKTO uses 8 sectors in a unified kernel")
    kernel.neural_ingest("performance", "Native Rust cdylib with zero-copy C-ABI")
    print(f"  Neural: {kernel.neural_count()} records ingested")
    results = kernel.neural_recall("kernel design", top_k=2)
    for r in results:
        print(f"    Recall: {r}")

    # ── Sector 3: Physics ──
    kernel.physics_add_body(0, 0, 0, 1e10, 1)
    kernel.physics_add_body(10, 0, 0, 1, 0.5)
    kernel.physics_add_body(-10, 0, 0, 1, 0.5)
    for _ in range(100):
        kernel.physics_step(0.016)
    print(f"  Physics: {kernel.physics_body_count()} bodies, 100 steps")

    # ── Sector 4: Predictive ──
    vuln_count = kernel.code_vulnerability_count()
    print(f"  Code Analyzer: {vuln_count} vulnerability patterns")

    # ── Sector 6: Swarm ──
    kernel.swarm_register_agent("worker-a", "compute")
    kernel.swarm_register_agent("worker-b", "storage")
    kernel.swarm_dispatch("worker-a", "scan", b'{"target": "/tmp"}')
    kernel.swarm_heartbeat("worker-a")
    kernel.swarm_heartbeat("worker-b")
    print(f"  Swarm: {kernel.swarm_status()}")

    # ── WebForge ──
    kernel.webforge_add_template(
        "landing",
        "<html><body><h1>{{title}}</h1><p>{{message}}</p></body></html>"
    )
    kernel.webforge_add_site(
        "mysite", "example.com", "landing", "./output",
        {"title": "NIKTO", "message": "Super Kernel ready"}
    )
    html = kernel.webforge_render("mysite")
    print(f"  WebForge: rendered {len(html)} bytes")

    # ── Final status ──
    print()
    print(f"  {kernel.status()}")
    print()
    print("NIKTO Super Kernel operational.")


if __name__ == "__main__":
    main()
