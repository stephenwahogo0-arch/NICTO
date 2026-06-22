import json
import os
import time
import copy
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Snapshot:
    id: str
    label: str
    timestamp: float
    data: Dict = field(default_factory=dict)


class RollbackManager:
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".nicto", "neural", "snapshots")
        os.makedirs(self.storage_dir, exist_ok=True)
        self._snapshots: Dict[str, Snapshot] = {}

    def create_snapshot(self, label: str, data: Dict = None) -> str:
        snap_id = f"snap_{int(time.time() * 1000)}_{len(self._snapshots)}"
        snapshot = Snapshot(
            id=snap_id,
            label=label,
            timestamp=time.time(),
            data=copy.deepcopy(data) if data else {},
        )
        self._snapshots[snap_id] = snapshot
        self._save_to_disk(snap_id, snapshot)
        return snap_id

    def restore(self, snapshot_id: str) -> Optional[Dict]:
        if snapshot_id in self._snapshots:
            return copy.deepcopy(self._snapshots[snapshot_id].data)
        disk = self._load_from_disk(snapshot_id)
        if disk:
            self._snapshots[snapshot_id] = disk
            return copy.deepcopy(disk.data)
        return None

    def delete_snapshot(self, snapshot_id: str) -> bool:
        if snapshot_id in self._snapshots:
            del self._snapshots[snapshot_id]
        path = os.path.join(self.storage_dir, f"{snapshot_id}.json")
        if os.path.exists(path):
            os.remove(path)
            return True
        return snapshot_id in self._snapshots

    def list_snapshots(self, label_filter: str = None) -> list:
        snaps = list(self._snapshots.values())
        if label_filter:
            snaps = [s for s in snaps if label_filter in s.label]
        return [{"id": s.id, "label": s.label, "timestamp": s.timestamp} for s in snaps]

    def _save_to_disk(self, snap_id: str, snapshot: Snapshot):
        path = os.path.join(self.storage_dir, f"{snap_id}.json")
        with open(path, "w") as f:
            json.dump({"id": snapshot.id, "label": snapshot.label, "timestamp": snapshot.timestamp}, f)

    def _load_from_disk(self, snap_id: str) -> Optional[Snapshot]:
        path = os.path.join(self.storage_dir, f"{snap_id}.json")
        if not os.path.exists(path):
            return None
        with open(path) as f:
            data = json.load(f)
        return Snapshot(**data)