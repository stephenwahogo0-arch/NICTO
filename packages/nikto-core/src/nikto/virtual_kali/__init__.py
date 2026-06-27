"""Virtual Kali Linux — NICTO-exclusive cyber operations environment.

Provides a fully simulated Kali Linux environment with:
- 500+ Kali tools across all categories
- Realistic terminal and shell (bash-like)
- Virtual filesystem with Kali directory tree
- APT package manager simulation
- Network interface simulation
- Deep NICTO integration (brain, exploit_db, scanner, threat_intel)
"""

from .engine import VirtualKaliEngine
from .terminal import KaliTerminal
from .tools import ToolDatabase
from .filesystem import VirtualFileSystem
from .packages import PackageManager
from .network import NetworkSimulator

__all__ = [
    "VirtualKaliEngine",
    "KaliTerminal",
    "ToolDatabase",
    "VirtualFileSystem",
    "PackageManager",
    "NetworkSimulator",
]
