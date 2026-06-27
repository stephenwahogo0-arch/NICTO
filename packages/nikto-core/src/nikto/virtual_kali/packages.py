"""APT Package Manager — Simulated Kali package management.

Simulates APT/Dpkg with package installation, removal, updates.
All 500+ tools are 'pre-installed' for NICTO's environment.
"""

from __future__ import annotations
import time
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class KaliPackage:
    name: str
    version: str = "1.0.0-kali1"
    description: str = ""
    section: str = "main"
    installed: bool = True
    size_kb: int = 1024
    dependencies: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.name)


class PackageManager:
    """Simulated APT/Dpkg package manager for Kali.

    All tools come pre-installed. This provides:
    - apt-get install/remove/update/upgrade
    - dpkg -i/-l/-r
    - apt-cache search/show
    - Repository simulation
    """

    REPOSITORIES = {
        "kali-rolling": "http://http.kali.org/kali kali-rolling main contrib non-free",
        "kali-last-snapshot": "http://http.kali.org/kali kali-last-snapshot main contrib non-free",
        "kali-dev": "http://http.kali.org/kali kali-dev main contrib non-free",
        "nicto-repo": "http://repo.nikto.ai/kali nicto main",
    }

    def __init__(self):
        self.packages: Dict[str, KaliPackage] = {}
        self.repos = dict(self.REPOSITORIES)
        self._updates_available = 0
        self._last_update = 0.0

    def register(self, name: str, version: str = "1.0.0-kali1",
                 description: str = "", section: str = "main"):
        if name not in self.packages:
            self.packages[name] = KaliPackage(
                name=name, version=version, description=description,
                section=section, installed=True
            )

    def install(self, package_name: str) -> str:
        pkg = self.packages.get(package_name)
        if not pkg:
            return (f"Reading package lists... Done\n"
                    f"Building dependency tree... Done\n"
                    f"Package '{package_name}' is not available, but is referred to by another package.\n"
                    f"E: Unable to locate package {package_name}\n")
        if pkg.installed:
            return (f"Reading package lists... Done\n"
                    f"Building dependency tree... Done\n"
                    f"Package '{package_name}' is already installed.\n")
        deps = [d for d in pkg.dependencies if d in self.packages and not self.packages[d].installed]
        dep_lines = "\n".join(f"  {d}" for d in deps)
        pkg.installed = True
        for d in deps:
            self.packages[d].installed = True
        return (f"Reading package lists... Done\n"
                f"Building dependency tree... Done\n"
                f"Reading state information... Done\n"
                f"The following NEW packages will be installed:\n"
                f"  {package_name}{' ' + dep_lines if dep_lines else ''}\n"
                f"0 upgraded, {1 + len(deps)} newly installed, 0 to remove and {self._updates_available} not upgraded.\n"
                f"Need to get {pkg.size_kb} kB of archives.\n"
                f"After this operation, {pkg.size_kb * 2} kB of additional disk space will be used.\n"
                f"Get:1 http://http.kali.org/kali {package_name} [{pkg.size_kb} kB]\n"
                f"Fetched {pkg.size_kb} kB in 0.1s (1000 kB/s)\n"
                f"Selecting previously unselected package {package_name}.\n"
                f"(Reading database ... 450000 files and directories currently installed.)\n"
                f"Preparing to unpack .../{package_name}_{pkg.version}_amd64.deb ...\n"
                f"Unpacking {package_name} ({pkg.version}) ...\n"
                f"Setting up {package_name} ({pkg.version}) ...\n"
                f"Processing triggers for libc-bin (2.37-2) ...\n")

    def remove(self, package_name: str, purge: bool = False) -> str:
        pkg = self.packages.get(package_name)
        if not pkg or not pkg.installed:
            return (f"E: Unable to locate package {package_name}\n")
        pkg.installed = False
        action = "purged" if purge else "removed"
        return (f"Reading package lists... Done\n"
                f"Building dependency tree... Done\n"
                f"The following packages will be REMOVED:\n"
                f"  {package_name}\n"
                f"0 upgraded, 0 newly installed, 1 to remove and {self._updates_available} not upgraded.\n"
                f"After this operation, {pkg.size_kb} kB disk space will be freed.\n"
                f"(Reading database ... 450001 files and directories currently installed.)\n"
                f"Removing {package_name} ({pkg.version}) ...\n"
                f"Processing triggers for libc-bin (2.37-2) ...\n"
                f"({action})\n")

    def update(self) -> str:
        self._last_update = time.time()
        hits = random.randint(300, 500)
        self._updates_available = random.randint(0, 15)
        return (f"Hit:1 http://http.kali.org/kali kali-rolling InRelease\n"
                f"Hit:2 http://http.kali.org/kali kali-rolling/main amd64 Packages\n"
                f"Hit:3 http://http.kali.org/kali kali-rolling/contrib amd64 Packages\n"
                f"Hit:4 http://http.kali.org/kali kali-rolling/non-free amd64 Packages\n"
                f"Hit:5 http://repo.nikto.ai/kali nicto InRelease\n"
                f"Reading package lists... Done\n"
                f"Fetched 42.5 MB in 2.3s (18.5 MB/s)\n"
                f"{self._updates_available} packages can be upgraded. Run 'apt list --upgradable' to see them.\n")

    def upgrade(self) -> str:
        if self._updates_available == 0:
            return ("Reading package lists... Done\n"
                    "Building dependency tree... Done\n"
                    "0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.\n")
        result = (f"Reading package lists... Done\n"
                  f"Building dependency tree... Done\n"
                  f"Calculating upgrade... Done\n"
                  f"The following packages will be upgraded:\n")
        upgraded = 0
        for name, pkg in self.packages.items():
            if pkg.installed and upgraded < self._updates_available:
                result += f"  {name}\n"
                upgraded += 1
        dl_size = upgraded * 2048
        result += (f"{upgraded} upgraded, 0 newly installed, 0 to remove.\n"
                   f"Need to get {dl_size} kB of archives.\n"
                   f"After this operation, 4096 kB of additional disk space will be used.\n"
                   f"Do you want to continue? [Y/n] y\n"
                   f"Get:1 http://http.kali.org/kali ...\n"
                   f"Fetched {dl_size} kB in 1.2s (1000 kB/s)\n"
                   f"(Reading database ... 450000 files and directories currently installed.)\n")
        for name in list(self.packages.keys())[:upgraded]:
            result += f"Unpacking {name} ...\n"
        result += f"Setting up ...\nProcessing triggers for libc-bin (2.37-2) ...\n"
        self._updates_available = 0
        return result

    def search(self, query: str) -> str:
        q = query.lower()
        matches = [p for p in self.packages.values() if q in p.name.lower() or q in p.description.lower()]
        if not matches:
            return f"Sorting... Full Text Search... 0 results for '{query}'\n"
        result = f"Sorting... Full Text Search... {len(matches)} results for '{query}'\n"
        for p in sorted(matches, key=lambda x: x.name)[:30]:
            status = "i" if p.installed else " "
            result += f"{status} {p.name:<30} {p.version:<20} {p.section}\n"
        return result

    def show(self, package_name: str) -> str:
        pkg = self.packages.get(package_name)
        if not pkg:
            return f"Package '{package_name}' not found.\n"
        return (f"Package: {pkg.name}\n"
                f"Version: {pkg.version}\n"
                f"Section: {pkg.section}\n"
                f"Installed-Size: {pkg.size_kb}\n"
                f"Description: {pkg.description}\n"
                f"Homepage: https://tools.kali.org/\n"
                f"Priority: optional\n"
                f"Status: {'install ok installed' if pkg.installed else 'deinstall ok config-files'}\n")

    def list_installed(self, pattern: str = "") -> str:
        result = "Desired=Unknown/Install/Remove/Purge/Hold\n| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend\n|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)\n||/ Name                          Version                  Architecture Description\n+++-============================-========================-============-====================================\n"
        for p in sorted(self.packages.values(), key=lambda x: x.name):
            if p.installed and (not pattern or pattern in p.name):
                result += f"ii  {p.name:<30} {p.version:<25} amd64       {p.description[:40]}\n"
        return result

    def get_stats(self) -> dict:
        installed = sum(1 for p in self.packages.values() if p.installed)
        return {
            "packages": len(self.packages),
            "installed": installed,
            "repos": len(self.repos),
            "updates_available": self._updates_available,
            "last_update": self._last_update,
        }
