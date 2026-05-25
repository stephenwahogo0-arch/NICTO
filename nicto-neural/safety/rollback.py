"""State snapshot and rollback system."""

import copy
import json
from datetime import datetime


class RollbackManager:
    """State snapshot and restore for safe experimentation."""

    MAX_SNAPSHOTS = 50

    def __init__(self):
        self._snapshots: list[dict] = []
        self._current_state: dict = {}

    def snapshot(self, state: dict, label: str = "") -> str:
        """Take a snapshot of the current state."""
        snapshot_id = f"snap_{len(self._snapshots):04d}"
        self._snapshots.append({
            "id": snapshot_id,
            "label": label or snapshot_id,
            "state": copy.deepcopy(state),
            "timestamp": datetime.utcnow().isoformat(),
        })

        if len(self._snapshots) > self.MAX_SNAPSHOTS:
            self._snapshots = self._snapshots[-self.MAX_SNAPSHOTS:]

        self._current_state = copy.deepcopy(state)
        return snapshot_id

    def restore(self, snapshot_id: str) -> dict:
        """Restore state from a snapshot."""
        for snap in reversed(self._snapshots):
            if snap["id"] == snapshot_id:
                self._current_state = copy.deepcopy(snap["state"])
                return self._current_state
        raise ValueError(f"Snapshot '{snapshot_id}' not found")

    def restore_latest(self) -> dict:
        if not self._snapshots:
            return {}
        latest = self._snapshots[-1]
        self._current_state = copy.deepcopy(latest["state"])
        return self._current_state

    def list_snapshots(self) -> list[dict]:
        return [
            {"id": s["id"], "label": s["label"], "timestamp": s["timestamp"]}
            for s in self._snapshots
        ]

    def diff(self, id_a: str, id_b: str) -> dict:
        """Compare two snapshots."""
        snap_a = snap_b = None
        for s in self._snapshots:
            if s["id"] == id_a:
                snap_a = s["state"]
            if s["id"] == id_b:
                snap_b = s["state"]

        if snap_a is None or snap_b is None:
            return {"error": "snapshot not found"}

        keys_a = set(snap_a.keys()) if isinstance(snap_a, dict) else set()
        keys_b = set(snap_b.keys()) if isinstance(snap_b, dict) else set()

        return {
            "added": list(keys_b - keys_a),
            "removed": list(keys_a - keys_b),
            "common": list(keys_a & keys_b),
        }
