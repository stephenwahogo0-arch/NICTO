import ast
import inspect
import json
import pkgutil
import sys
from pathlib import Path
from typing import Any, Optional

from nikto.capabilities.manifest import CapabilityManifest, FeatureCapability


class CapabilityScanner:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.data_dir / "capability_manifest.json"

    def scan_module(self, module_name: str) -> list[FeatureCapability]:
        features = []
        try:
            __import__(module_name)
            module = sys.modules[module_name]
        except Exception:
            return features

        for name, obj in inspect.getmembers(module):
            if not inspect.isclass(obj):
                continue
            if name.startswith("_"):
                continue
            if name in ("BaseModel",):
                continue

            try:
                source_file = inspect.getfile(obj)
            except Exception:
                continue

            if not source_file.startswith(str(Path(__file__).resolve().parent.parent)):
                continue

            try:
                source = inspect.getsource(obj)
            except Exception:
                source = ""

            doc = (obj.__doc__ or "").strip()
            methods = [
                m for m in dir(obj)
                if callable(getattr(obj, m, None))
                and not m.startswith("_")
            ]

            features.append(FeatureCapability(
                name=name,
                module=module_name,
                doc=doc[:500] if doc else "",
                methods=methods,
                source_preview=source[:300] if source else "",
                summary=getattr(obj, "summary", None),
            ))

        return features

    def scan_all_nikto_modules(self) -> list[FeatureCapability]:
        modules_to_scan = [
            "nikto.advanced_evolution.bio_medical",
            "nikto.advanced_evolution.consciousness",
            "nikto.advanced_evolution.physics_reality",
            "nikto.advanced_evolution.communication",
            "nikto.advanced_evolution.global_cosmic",
            "nikto.advanced_evolution.breakthrough",
            "nikto.memory",
            "nikto.security",
            "nikto.autopilot",
            "nikto.devices",
            "nikto.game_engine",
            "nikto.evolution",
            "nikto.dream",
            "nikto.mesh",
            "nikto.tools",
            "nikto.skills",
            "nikto.mcp",
            "nikto.cua",
            "nikto.earn",
        ]

        all_features = []
        for mod in modules_to_scan:
            try:
                features = self.scan_module(mod)
                all_features.extend(features)
            except Exception:
                pass

        return all_features

    def generate_manifest(self) -> CapabilityManifest:
        features = self.scan_all_nikto_modules()
        manifest = CapabilityManifest(features=features)
        return manifest

    def save_manifest(self, manifest: CapabilityManifest):
        data = manifest.to_dict()
        self.manifest_path.write_text(json.dumps(data, indent=2))
        return self.manifest_path

    def load_manifest(self) -> Optional[CapabilityManifest]:
        if not self.manifest_path.exists():
            return None
        try:
            data = json.loads(self.manifest_path.read_text())
            return CapabilityManifest.from_dict(data)
        except Exception:
            return None
