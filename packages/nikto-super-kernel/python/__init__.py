"""KYROS Super Kernel — Unified Rust backend with Python bridge."""

try:
    import nikto_super_kernel as _native
    HAS_NATIVE = True
except ImportError:
    HAS_NATIVE = False

from python.brain_core import SuperKernel

__all__ = ["SuperKernel", "HAS_NATIVE"]
