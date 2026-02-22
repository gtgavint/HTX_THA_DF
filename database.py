import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = "data.db" # Database file path

# Create the database
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            original_name TEXT,
            status TEXT,
            metadata TEXT,
            processed_at TEXT,
            error TEXT,
            duration REAL
        )''')

# Retrive all records from database
def get_all_records():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM images")
        rows = cursor.fetchall()

        results = []
        for row in rows:
            d = dict(row)
            try:
                d["metadata"] = json.loads(d["metadata"]) if d["metadata"] else {}
            except json.JSONDecodeError:
                d["metadata"] = {}
            results.append(d)

        return results

# Retrive specific record by id    
def get_record_by_id(id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM images WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            try:
                res["metadata"] = json.loads(res["metadata"]) if res["metadata"] else {}
            except json.JSONDecodeError:
                res["metadata"] = {}
            return res
        return None

# Save initial record when image is uploaded
def save_initial_record(id, name):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO images (id, original_name, status) VALUES (?, ?, ?)", 
                     (id, name, "processing"))

def update_record(id, status, metadata=None, error=None, duration=0):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE images SET status=?, metadata=?, error=?, processed_at=?, duration=? 
            WHERE id=?""", 
            (status, json.dumps(metadata) if metadata else "{}", error, 
             datetime.now(timezone.utc).isoformat() + "Z", duration, id))

def fetch_stats():
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM images").fetchone()[0]
        failed = conn.execute("SELECT COUNT(*) FROM images WHERE status='failed'").fetchone()[0]
        avg_time = conn.execute("SELECT AVG(duration) FROM images WHERE status='success'").fetchone()[0] or 0
        success_rate = f"{( (total-failed)/total * 100 if total > 0 else 0 ):.2f}%"
        return {
            "total": total, 
            "failed": failed, 
            "success_rate": success_rate, 
            "average_processing_time_seconds": round(avg_time, 2)
        }