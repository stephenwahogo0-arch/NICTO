import os
import sys
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from typing import Optional


class UpdateInfo:
    def __init__(self, current_version: str, latest_version: str, update_available: bool, changelog: str):
        self.current_version = current_version
        self.latest_version = latest_version
        self.update_available = update_available
        self.changelog = changelog

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoAutoUpdater:
    REPO_URL = "https://github.com/stephenwahogo0-arch/NICTO"
    VERSION_FILE = os.path.join(os.path.expanduser("~"), ".nikto", "version.json")

    def __init__(self):
        self.current_version = self._get_current_version()
        os.makedirs(os.path.dirname(self.VERSION_FILE), exist_ok=True)

    def _get_current_version(self) -> str:
        if os.path.exists(self.VERSION_FILE):
            with open(self.VERSION_FILE) as f:
                return json.load(f).get("version", "2.0.0")
        return "2.0.0"

    async def check_for_updates(self) -> UpdateInfo:
        try:
            import requests
            resp = requests.get(f"{self.REPO_URL}/releases/latest", timeout=10, headers={"User-Agent": "NICTO/2.0"})
            data = resp.json()
            latest = data.get("tag_name", self.current_version).lstrip("v")
            changelog = data.get("body", "No changelog available")
            return UpdateInfo(self.current_version, latest, latest != self.current_version, changelog[:500])
        except Exception:
            return UpdateInfo(self.current_version, self.current_version, False, "Offline or GitHub unreachable")

    async def download_update(self, version: str) -> str:
        tmp_dir = tempfile.mkdtemp(prefix="nicto_update_")
        tmp_path = os.path.join(tmp_dir, f"nicto-{version}.zip")
        try:
            import requests
            url = f"{self.REPO_URL}/archive/refs/tags/v{version}.zip"
            resp = requests.get(url, timeout=60)
            with open(tmp_path, "wb") as f:
                f.write(resp.content)
            return tmp_path
        except Exception:
            return ""

    async def apply_update(self, package_path: str) -> bool:
        if not package_path or not os.path.exists(package_path):
            return False
        try:
            with open(self.VERSION_FILE, "w") as f:
                json.dump({"version": self._get_current_version(), "updated": datetime.now(timezone.utc).isoformat()}, f)
            return True
        except Exception:
            return False

    async def rollback(self) -> bool:
        old_version = "1.0.0"
        with open(self.VERSION_FILE, "w") as f:
            json.dump({"version": old_version, "rolled_back": datetime.now(timezone.utc).isoformat()}, f)
        self.current_version = old_version
        return True
