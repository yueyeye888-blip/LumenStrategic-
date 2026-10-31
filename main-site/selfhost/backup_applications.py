"""Create a consistent private SQLite backup and remove backups older than 30 days."""
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from app import DB_PATH

BACKUP_DIR = Path(os.environ.get("LUMEN_BACKUP_DIR", "/var/backups/lumen"))
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
os.chmod(BACKUP_DIR, 0o700)
destination = BACKUP_DIR / f"applications-{datetime.now(timezone.utc):%Y-%m-%d}.sqlite3"
temporary = destination.with_suffix(".tmp")

with sqlite3.connect(DB_PATH) as source, sqlite3.connect(temporary) as target:
    source.backup(target)
os.chmod(temporary, 0o600)
temporary.replace(destination)

cutoff = time.time() - 30 * 24 * 60 * 60
for backup in BACKUP_DIR.glob("applications-*.sqlite3"):
    if backup.stat().st_mtime < cutoff:
        backup.unlink()

print(destination)
