"""``.aim-use/summaries.db`` の SQLite CRUD。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS file_summaries (
    file_path     TEXT PRIMARY KEY,
    content_hash  TEXT NOT NULL,
    summary       TEXT NOT NULL,
    model         TEXT NOT NULL,
    generated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skip_records (
    file_path    TEXT PRIMARY KEY,
    reason       TEXT NOT NULL,
    detail       TEXT,
    recorded_at  TEXT NOT NULL
);
"""


class SummaryDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "SummaryDB":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # --- file_summaries ---

    def get_content_hash(self, file_path: str) -> str | None:
        row = self.conn.execute(
            "SELECT content_hash FROM file_summaries WHERE file_path = ?", (file_path,)
        ).fetchone()
        return row["content_hash"] if row else None

    def upsert_summary(
        self, file_path: str, content_hash: str, summary: str, model: str, generated_at: str
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO file_summaries (file_path, content_hash, summary, model, generated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                content_hash = excluded.content_hash,
                summary = excluded.summary,
                model = excluded.model,
                generated_at = excluded.generated_at
            """,
            (file_path, content_hash, summary, model, generated_at),
        )
        self.conn.execute("DELETE FROM skip_records WHERE file_path = ?", (file_path,))
        self.conn.commit()

    def delete_summary(self, file_path: str) -> None:
        self.conn.execute("DELETE FROM file_summaries WHERE file_path = ?", (file_path,))
        self.conn.commit()

    # --- skip_records ---

    def record_skip(
        self, file_path: str, reason: str, detail: str | None, recorded_at: str
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO skip_records (file_path, reason, detail, recorded_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                reason = excluded.reason,
                detail = excluded.detail,
                recorded_at = excluded.recorded_at
            """,
            (file_path, reason, detail, recorded_at),
        )
        self.conn.commit()

    def delete_skip_record(self, file_path: str) -> None:
        self.conn.execute("DELETE FROM skip_records WHERE file_path = ?", (file_path,))
        self.conn.commit()

    # --- orphan cleanup ---

    def all_known_file_paths(self) -> set[str]:
        rows = self.conn.execute("SELECT file_path FROM file_summaries").fetchall()
        rows += self.conn.execute("SELECT file_path FROM skip_records").fetchall()
        return {row["file_path"] for row in rows}

    def delete_file(self, file_path: str) -> None:
        self.conn.execute("DELETE FROM file_summaries WHERE file_path = ?", (file_path,))
        self.conn.execute("DELETE FROM skip_records WHERE file_path = ?", (file_path,))
        self.conn.commit()

    # --- get ---

    def get_all_summaries(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM file_summaries ORDER BY file_path").fetchall()

    def get_summaries_under(self, prefix: str) -> list[sqlite3.Row]:
        rows = self.conn.execute(
            "SELECT * FROM file_summaries WHERE file_path = ? OR file_path LIKE ? ESCAPE '\\' ORDER BY file_path",
            (prefix, _like_prefix(prefix)),
        ).fetchall()
        return rows


def _like_prefix(prefix: str) -> str:
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"{escaped}/%"
