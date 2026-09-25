"""Small durable local store; production deployments can replace this boundary."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from sre_agent.models.domain import Incident


class IncidentStore:
    def __init__(self, database_url: str = ".local/remediation.db") -> None:
        self.path = Path(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS incidents (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL)"
        )
        self.connection.execute("CREATE INDEX IF NOT EXISTS incidents_fingerprint ON incidents(fingerprint)")
        self.connection.commit()

    def save(self, incident: Incident) -> None:
        self.connection.execute(
            "INSERT INTO incidents(id, fingerprint, status, payload) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET status=excluded.status, payload=excluded.payload",
            (incident.id, incident.fingerprint, incident.status, incident.model_dump_json()),
        )
        self.connection.commit()

    def get(self, incident_id: str) -> Incident | None:
        row = self.connection.execute("SELECT payload FROM incidents WHERE id=?", (incident_id,)).fetchone()
        return Incident.model_validate_json(row[0]) if row else None

    def active_by_fingerprint(self, fingerprint: str) -> Incident | None:
        row = self.connection.execute(
            "SELECT payload FROM incidents WHERE fingerprint=? AND status NOT IN ('RESOLVED','FAILED','ESCALATED') ORDER BY rowid DESC LIMIT 1",
            (fingerprint,),
        ).fetchone()
        return Incident.model_validate_json(row[0]) if row else None

    def list(self) -> list[Incident]:
        return [Incident.model_validate_json(row[0]) for row in self.connection.execute("SELECT payload FROM incidents ORDER BY rowid")]
