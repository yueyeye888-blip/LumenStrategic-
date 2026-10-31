"""Regression checks for submissions, authentication, dashboard, CSV and migration."""
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults

root = Path(__file__).parent
temporary = tempfile.TemporaryDirectory()
db_path = Path(temporary.name) / "applications.sqlite3"
os.environ.update({
    "LUMEN_DB_PATH": str(db_path),
    "LUMEN_PUBLIC_ORIGIN": "https://lumstrat.com",
    "LUMEN_ADMIN_USERNAME": "lumen-admin",
    "LUMEN_ADMIN_SECRET": "s" * 48,
})

import app

app.ADMIN_USERNAME = "lumen-admin"
app.ADMIN_SECRET = "s" * 48
app.ADMIN_PASSWORD_HASH = app.make_password_hash("correct horse battery staple", iterations=200_000)
with sqlite3.connect(db_path) as db:
    db.execute(
        "INSERT INTO administrators VALUES (?,?,?,?,?,?)",
        ("lumen-admin", app.ADMIN_PASSWORD_HASH, "superadmin", 1, "2026-10-31T00:00:00+00:00", "bootstrap"),
    )


def call(path, method="GET", body=b"", content_type="", cookie="", origin=""):
    environ = {}
    setup_testing_defaults(environ)
    environ.update({
        "PATH_INFO": path.split("?", 1)[0],
        "QUERY_STRING": path.split("?", 1)[1] if "?" in path else "",
        "REQUEST_METHOD": method,
        "CONTENT_LENGTH": str(len(body)) if body else "0",
        "CONTENT_TYPE": content_type,
        "wsgi.input": io.BytesIO(body),
        "REMOTE_ADDR": "127.0.0.1",
        "HTTP_COOKIE": cookie,
        "HTTP_ORIGIN": origin,
    })
    state = {}
    def start(status, headers):
        state["status"] = int(status.split()[0])
        state["headers"] = headers
    response = b"".join(app.application(environ, start))
    state["body"] = response
    return state


payload = {
    "id": str(uuid.uuid4()),
    "name": "<script>alert(1)</script>",
    "email": "private@example.com",
    "investorType": "机构投资人",
    "topic": "机构合作",
    "size": "S$500,000–1,000,000",
    "message": "长期合作需求",
    "language": "zh-Hans",
}
created = call(
    "/api/applications",
    "POST",
    json.dumps(payload).encode(),
    "application/json",
    origin="https://lumstrat.com",
)
assert created["status"] == 201, created
assert call("/api/applications")["status"] == 405
assert call("/admin")["status"] == 303

login = call("/admin/login")
assert login["status"] == 200
login_html = login["body"].decode()
csrf = re.search(r'name="csrf" value="([^"]+)"', login_html).group(1)
csrf_cookie = next(value for key, value in login["headers"] if key == "Set-Cookie").split(";", 1)[0]

wrong = call(
    "/admin/login",
    "POST",
    urlencode({"csrf": csrf, "username": "lumen-admin", "password": "wrong"}).encode(),
    "application/x-www-form-urlencoded",
    csrf_cookie,
    "https://lumstrat.com",
)
assert wrong["status"] == 401

logged_in = call(
    "/admin/login",
    "POST",
    urlencode({"csrf": csrf, "username": "lumen-admin", "password": "correct horse battery staple"}).encode(),
    "application/x-www-form-urlencoded",
    csrf_cookie,
)
assert logged_in["status"] == 303
session_cookie = next(value for key, value in logged_in["headers"] if key == "Set-Cookie" and value.startswith(app.SESSION_COOKIE)).split(";", 1)[0]
session_csrf = app.session_csrf({"HTTP_COOKIE": session_cookie})

dashboard = call("/admin", cookie=session_cookie)
assert dashboard["status"] == 200
dashboard_html = dashboard["body"].decode()
assert "private@example.com" in dashboard_html
assert "&lt;script&gt;alert(1)&lt;/script&gt;" in dashboard_html
assert "<script>alert(1)</script>" not in dashboard_html
assert any(key == "Content-Security-Policy" for key, _ in dashboard["headers"])

users = call("/admin/users", cookie=session_cookie)
assert users["status"] == 200 and "lumen-admin" in users["body"].decode()
created_admin = call(
    "/admin/users",
    "POST",
    urlencode({"csrf": session_csrf, "username": "analyst.one", "password": "secondary-admin-password"}).encode(),
    "application/x-www-form-urlencoded",
    session_cookie,
)
assert created_admin["status"] == 303
with sqlite3.connect(db_path) as db:
    account = db.execute("SELECT role,password_hash FROM administrators WHERE username='analyst.one'").fetchone()
assert account[0] == "admin" and "secondary-admin-password" not in account[1]

login2 = call("/admin/login")
csrf2 = re.search(r'name="csrf" value="([^"]+)"', login2["body"].decode()).group(1)
csrf_cookie2 = next(value for key, value in login2["headers"] if key == "Set-Cookie").split(";", 1)[0]
logged_in2 = call(
    "/admin/login",
    "POST",
    urlencode({"csrf": csrf2, "username": "analyst.one", "password": "secondary-admin-password"}).encode(),
    "application/x-www-form-urlencoded",
    csrf_cookie2,
)
admin_cookie = next(value for key, value in logged_in2["headers"] if key == "Set-Cookie" and value.startswith(app.SESSION_COOKIE)).split(";", 1)[0]
assert call("/admin", cookie=admin_cookie)["status"] == 200
assert call("/admin/users", cookie=admin_cookie)["status"] == 403

search = call("/admin?q=private%40example.com", cookie=session_cookie)
assert search["status"] == 200 and "private@example.com" in search["body"].decode()
export = call("/admin/export.csv", cookie=session_cookie)
assert export["status"] == 200 and b"private@example.com" in export["body"]

legacy = Path(temporary.name) / "legacy.db"
with sqlite3.connect(legacy) as db:
    db.execute("CREATE TABLE submissions (id INTEGER,name TEXT,email TEXT,investor_type TEXT,interest TEXT,investment_size TEXT,needs TEXT,submit_time TEXT)")
    db.execute("INSERT INTO submissions VALUES (1,'Legacy','legacy@example.com','个人合资格投资人','一级市场','S$200,000–500,000','Legacy need','2026-06-02 23:11:50')")
environment = dict(os.environ)
environment["LUMEN_DB_PATH"] = str(db_path)
result = subprocess.run(
    [sys.executable, str(root / "migrate_legacy_submissions.py"), str(legacy)],
    cwd=root,
    env=environment,
    text=True,
    capture_output=True,
    check=True,
)
assert "legacy_inserted=1" in result.stdout
with sqlite3.connect(db_path) as db:
    assert db.execute("SELECT count(*) FROM applications").fetchone()[0] == 2

print("admin_auth=ok roles=ok admin_creation=ok dashboard=ok csv=ok submission_api=ok legacy_migration=ok")
