from .base import MemoryStore, MemoryEntry
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import os


class GoalMemory(MemoryStore):
    def __init__(self, store_name: str = "goals", base_path: Optional[str] = None):
        super().__init__(store_name, base_path)

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                goal_id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'pending',
                progress REAL DEFAULT 0.0,
                subgoals TEXT DEFAULT '[]',
                parent_goal TEXT DEFAULT '',
                deadline REAL DEFAULT 0.0,
                created_at REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_goals_status
            ON goals(status)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_goals_priority
            ON goals(priority)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_goals_parent
            ON goals(parent_goal)
        """)
        self._conn.commit()

    def create_goal(
        self,
        description: str,
        priority: int = 5,
        subgoals: Optional[List[str]] = None,
        parent_goal: Optional[str] = None,
        deadline: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        goal_id = f"goal_{int(time.time() * 1e6)}"
        ts = time.time()
        self._conn.execute(
            """
            INSERT INTO goals
            (goal_id, description, priority, status, progress, subgoals, parent_goal, deadline, created_at, metadata)
            VALUES (?, ?, ?, 'pending', 0.0, ?, ?, ?, ?, ?)
            """,
            (
                goal_id,
                description,
                min(max(priority, 0), 10),
                json.dumps(subgoals or []),
                parent_goal or "",
                deadline or 0.0,
                ts,
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()
        return goal_id

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        md = metadata or {}
        if isinstance(value, dict):
            desc = value.get("description", str(value))
            priority = value.get("priority", md.get("priority", 5))
            subgoals = value.get("subgoals", md.get("subgoals"))
            parent = value.get("parent_goal", md.get("parent_goal"))
            deadline = value.get("deadline", md.get("deadline"))
        else:
            desc = str(value)
            priority = md.get("priority", 5)
            subgoals = md.get("subgoals")
            parent = md.get("parent_goal")
            deadline = md.get("deadline")
        return self.create_goal(
            description=desc,
            priority=priority,
            subgoals=subgoals,
            parent_goal=parent,
            deadline=deadline,
            metadata=md,
        )

    def update_progress(self, goal_id: str, progress: float) -> None:
        progress = min(max(progress, 0.0), 1.0)
        status = "completed" if progress >= 1.0 else "active" if progress > 0 else "pending"
        self._conn.execute(
            "UPDATE goals SET progress = ?, status = ? WHERE goal_id = ?",
            (progress, status, goal_id),
        )
        self._conn.commit()

    def complete_goal(self, goal_id: str) -> None:
        self._conn.execute(
            "UPDATE goals SET progress = 1.0, status = 'completed' WHERE goal_id = ?",
            (goal_id,),
        )
        self._conn.commit()

    def active_goals(self) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT goal_id, description, priority, status, progress, subgoals, parent_goal, deadline, created_at, metadata FROM goals WHERE status IN ('pending', 'active') ORDER BY priority DESC, created_at ASC"
        ).fetchall()
        return [
            {
                "goal_id": r[0],
                "description": r[1],
                "priority": r[2],
                "status": r[3],
                "progress": r[4],
                "subgoals": json.loads(r[5]) if r[5] else [],
                "parent_goal": r[6],
                "deadline": r[7],
                "created_at": r[8],
                "metadata": json.loads(r[9]) if r[9] else {},
            }
            for r in rows
        ]

    def subgoal_tree(self, goal_id: str) -> Dict:
        row = self._conn.execute(
            "SELECT goal_id, description, priority, status, progress, subgoals, parent_goal, deadline, created_at, metadata FROM goals WHERE goal_id = ?",
            (goal_id,),
        ).fetchone()
        if not row:
            return {}
        result = {
            "goal_id": row[0],
            "description": row[1],
            "priority": row[2],
            "status": row[3],
            "progress": row[4],
            "subgoals": [],
            "parent_goal": row[6],
            "deadline": row[7],
            "created_at": row[8],
            "metadata": json.loads(row[9]) if row[9] else {},
        }
        sub_ids = json.loads(row[5]) if row[5] else []
        for sid in sub_ids:
            child = self.subgoal_tree(sid)
            if child:
                result["subgoals"].append(child)
        if row[6]:
            parent = self._conn.execute(
                "SELECT goal_id, description FROM goals WHERE goal_id = ?",
                (row[6],),
            ).fetchone()
            if parent:
                result["parent"] = {"goal_id": parent[0], "description": parent[1]}
        return result

    def query(self, query_text: str = "", limit: int = 10) -> List[Dict]:
        like = f"%{query_text}%"
        rows = self._conn.execute(
            "SELECT goal_id, description, priority, status, progress, subgoals, parent_goal, deadline, created_at, metadata FROM goals WHERE description LIKE ? OR goal_id = ? ORDER BY priority DESC LIMIT ?",
            (like, query_text, limit),
        ).fetchall()
        return [
            {
                "goal_id": r[0],
                "description": r[1],
                "priority": r[2],
                "status": r[3],
                "progress": r[4],
                "subgoals": json.loads(r[5]) if r[5] else [],
                "parent_goal": r[6],
                "deadline": r[7],
                "created_at": r[8],
                "metadata": json.loads(r[9]) if r[9] else {},
            }
            for r in rows
        ]

    def recall(self, key: str) -> Optional[Any]:
        row = self._conn.execute(
            "SELECT goal_id, description, priority, status, progress, subgoals, parent_goal, deadline, created_at, metadata FROM goals WHERE goal_id = ?",
            (key,),
        ).fetchone()
        if row:
            return {
                "goal_id": row[0],
                "description": row[1],
                "priority": row[2],
                "status": row[3],
                "progress": row[4],
                "subgoals": json.loads(row[5]) if row[5] else [],
                "parent_goal": row[6],
                "deadline": row[7],
                "created_at": row[8],
                "metadata": json.loads(row[9]) if row[9] else {},
            }
        return None

    def forget(self, key: str) -> bool:
        c = self._conn.execute("DELETE FROM goals WHERE goal_id = ?", (key,))
        self._conn.commit()
        return c.rowcount > 0

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM goals").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM goals")
        self._conn.commit()
