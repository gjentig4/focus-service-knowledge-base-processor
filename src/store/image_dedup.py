import os
import sqlite3


DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/image_dedup.db")


class ImageDedupStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS image_hashes (
                phash TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                alt_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def find_by_hash(self, phash: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM image_hashes WHERE phash = ?", (phash,)
        ).fetchone()
        return dict(row) if row else None

    def store(self, phash: str, url: str, alt_text: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO image_hashes (phash, url, alt_text) VALUES (?, ?, ?)",
            (phash, url, alt_text),
        )
        self.conn.commit()
