import json
import time
from pathlib import Path
from typing import Any, Optional

from nikto.capabilities.scanner import CapabilityScanner
from nikto.knowledge.engine import KnowledgeEngine


class TrainingEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.scanner = CapabilityScanner(data_dir=data_dir)
        self.knowledge = KnowledgeEngine(data_dir=data_dir)
        self.report_path = self.data_dir / "training_report.json"

    def train_full(self) -> dict:
        manifest = self.scanner.generate_manifest()
        self.knowledge.ingest_manifest(manifest)
        report = self._generate_report(manifest)
        self.report_path.write_text(json.dumps(report, indent=2))
        return report

    def _generate_report(self, manifest) -> dict:
        cats = manifest.categories()
        kb_summary = self.knowledge.summary()
        features_by_cat = {}
        for cat in sorted(cats.keys()):
            features = manifest.get_by_category(cat)
            features_by_cat[cat] = [
                {"name": f.name, "module": f.module, "doc_preview": f.doc[:150]}
                for f in features
            ]

        return {
            "trained_at": time.time(),
            "total_features": manifest.total_features,
            "vector_enabled": kb_summary["vector_enabled"],
            "categories": cats,
            "knowledge_path": str(self.knowledge.kb_path),
            "features_by_category": features_by_cat,
        }

    def train_on_task(self, task: str) -> dict:
        context = self.knowledge.build_context_block(task)
        return {
            "task": task,
            "relevant_features": context,
            "knowledge_loaded": self.knowledge.total_features(),
        }

    def get_status(self) -> dict:
        return {
            "trained": self.knowledge.total_features() > 0,
            "total_features": self.knowledge.total_features(),
            "vector_enabled": self.knowledge.summary()["vector_enabled"],
            "categories": self.knowledge.summary()["categories"],
            "report_exists": self.report_path.exists(),
        }