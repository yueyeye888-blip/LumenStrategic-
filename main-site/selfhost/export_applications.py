"""Run only on the server; no public download endpoint."""
import csv, sqlite3, sys
from app import DB_PATH
with sqlite3.connect(DB_PATH) as db:
 cursor=db.execute('SELECT * FROM applications ORDER BY created_at DESC')
 writer=csv.writer(sys.stdout)
 writer.writerow([col[0] for col in cursor.description])
 for row in cursor:
  writer.writerow([("'"+value if isinstance(value,str) and value[:1] in ('=','+','-','@') else value) for value in row])
