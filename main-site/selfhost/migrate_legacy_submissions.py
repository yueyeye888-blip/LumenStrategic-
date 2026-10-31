"""Import the legacy submissions database into the current private database."""
import argparse
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import DB_PATH, SCHEMA

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
args = parser.parse_args()

namespace = uuid.UUID("8d26db44-6972-48bc-92ed-fbd50934044e")
inserted = 0
with sqlite3.connect(f"file:{args.source}?mode=ro", uri=True) as old, sqlite3.connect(DB_PATH) as new:
    new.execute(SCHEMA)
    rows = old.execute(
        "SELECT id,name,email,investor_type,interest,investment_size,needs,submit_time FROM submissions ORDER BY id"
    )
    for legacy_id, name, email, investor_type, topic, size, message, submitted in rows:
        record_id = str(uuid.uuid5(namespace, f"{legacy_id}|{submitted}|{email}"))
        try:
            created = datetime.fromisoformat(submitted).replace(tzinfo=timezone(timedelta(hours=8))).isoformat()
        except (ValueError, TypeError):
            created = submitted or datetime.now(timezone.utc).isoformat()
        before = new.total_changes
        new.execute(
            "INSERT OR IGNORE INTO applications VALUES (?,?,?,?,?,?,?,?,?)",
            (record_id, name or "", (email or "").lower(), investor_type or "", topic or "", size or "", message or "", "zh-Hans", created),
        )
        inserted += new.total_changes - before
print(f"legacy_inserted={inserted}")
