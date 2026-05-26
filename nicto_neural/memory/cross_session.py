import sqlite3
import json
import datetime
from pathlib import Path
from typing import Optional


class CrossSessionMemory:
    MAX_CONTEXT_TOKENS = 1_000_000
    COMPRESSION_RATIO = 0.3

    def __init__(self, db_path="~/.nicto/cross_session.db"):
        path = Path(db_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._init_schema()
        self._session_count = self._get_session_count()

    def _init_schema(self):
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT,
                ended_at TEXT,
                interactions INTEGER DEFAULT 0,
                domains_covered TEXT DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS long_term_facts (
                id TEXT PRIMARY KEY,
                fact TEXT NOT NULL,
                domain TEXT,
                confidence REAL DEFAULT 0.8,
                times_recalled INTEGER DEFAULT 0,
                first_seen TEXT,
                last_recalled TEXT,
                source_session INTEGER
            );
            CREATE TABLE IF NOT EXISTS user_models (
                user_id TEXT PRIMARY KEY,
                expertise_json TEXT DEFAULT '{}',
                preferences_json TEXT DEFAULT '{}',
                interaction_count INTEGER DEFAULT 0,
                first_seen TEXT,
                last_seen TEXT,
                projects_json TEXT DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS insight_chain (
                id TEXT PRIMARY KEY,
                insight TEXT,
                connected_to TEXT DEFAULT '[]',
                domain TEXT,
                strength REAL DEFAULT 0.5,
                created_at TEXT
            );
        """)
        self._db.commit()

    def _get_session_count(self):
        row = self._db.execute("SELECT COUNT(*) FROM sessions").fetchone()
        return row[0] if row else 0

    def start_session(self):
        now = datetime.datetime.utcnow().isoformat()
        cursor = self._db.execute(
            "INSERT INTO sessions (started_at) VALUES (?)", (now,)
        )
        self._db.commit()
        self._session_count += 1
        return cursor.lastrowid

    def end_session(self, session_id, interactions, domains):
        now = datetime.datetime.utcnow().isoformat()
        self._db.execute(
            "UPDATE sessions SET ended_at=?, interactions=?, domains_covered=? WHERE id=?",
            (now, interactions, json.dumps(domains), session_id)
        )
        self._db.commit()

    def store_fact(self, fact_id, fact, domain, confidence, session_id):
        now = datetime.datetime.utcnow().isoformat()
        self._db.execute(
            "INSERT OR REPLACE INTO long_term_facts "
            "(id, fact, domain, confidence, first_seen, last_recalled, source_session) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (fact_id, fact, domain, confidence, now, now, session_id)
        )
        self._db.commit()

    def recall_facts(self, query=None, domain=None, limit=20, min_confidence=0.6):
        if domain:
            cursor = self._db.execute(
                "SELECT id, fact, domain, confidence, times_recalled "
                "FROM long_term_facts WHERE domain=? AND confidence>=? "
                "ORDER BY times_recalled DESC, confidence DESC LIMIT ?",
                (domain, min_confidence, limit)
            )
        else:
            cursor = self._db.execute(
                "SELECT id, fact, domain, confidence, times_recalled "
                "FROM long_term_facts WHERE confidence>=? "
                "ORDER BY confidence DESC LIMIT ?",
                (min_confidence, limit)
            )
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0], "fact": row[1], "domain": row[2],
                "confidence": row[3], "times_recalled": row[4],
            })
            self._db.execute(
                "UPDATE long_term_facts SET times_recalled=times_recalled+1 WHERE id=?",
                (row[0],)
            )
        self._db.commit()
        return results

    def update_user_model(self, user_id, domain, expertise_level, project=None):
        now = datetime.datetime.utcnow().isoformat()
        existing = self._db.execute(
            "SELECT expertise_json, projects_json, interaction_count FROM user_models WHERE user_id=?",
            (user_id,)
        ).fetchone()
        if existing:
            expertise = json.loads(existing[0])
            projects = json.loads(existing[1])
            count = existing[2]
        else:
            expertise = {}
            projects = []
            count = 0
        if domain in expertise:
            expertise[domain] = expertise[domain] * 0.8 + expertise_level * 0.2
        else:
            expertise[domain] = expertise_level
        if project and project not in projects:
            projects.append(project)
        self._db.execute(
            "INSERT OR REPLACE INTO user_models "
            "(user_id, expertise_json, projects_json, interaction_count, first_seen, last_seen) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, json.dumps(expertise), json.dumps(projects), count + 1, now, now)
        )
        self._db.commit()

    def get_user_model(self, user_id):
        row = self._db.execute(
            "SELECT expertise_json, projects_json, interaction_count, first_seen, last_seen "
            "FROM user_models WHERE user_id=?", (user_id,)
        ).fetchone()
        if not row:
            return {"user_id": user_id, "known": False}
        return {
            "user_id": user_id,
            "expertise": json.loads(row[0]),
            "projects": json.loads(row[1]),
            "interactions": row[2],
            "first_seen": row[3],
            "last_seen": row[4],
            "known": True,
        }

    def store_insight(self, insight_id, insight, domain, connected_to=None, strength=0.5):
        now = datetime.datetime.utcnow().isoformat()
        self._db.execute(
            "INSERT OR REPLACE INTO insight_chain "
            "(id, insight, domain, connected_to, strength, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (insight_id, insight, domain, json.dumps(connected_to or []), strength, now)
        )
        self._db.commit()

    def get_stats(self):
        facts = self._db.execute("SELECT COUNT(*) FROM long_term_facts").fetchone()[0]
        users = self._db.execute("SELECT COUNT(*) FROM user_models").fetchone()[0]
        insights = self._db.execute("SELECT COUNT(*) FROM insight_chain").fetchone()[0]
        return {
            "total_sessions": self._session_count,
            "long_term_facts": facts,
            "user_models": users,
            "insight_chain_length": insights,
            "growing": True,
        }
