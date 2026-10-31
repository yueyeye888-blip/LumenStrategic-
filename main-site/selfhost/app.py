"""Self-hosted application receiver and private administration console."""
import base64
import csv
import hashlib
import hmac
import html
import io
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlencode

DB_PATH = Path(os.environ.get("LUMEN_DB_PATH", str(Path(__file__).parent / "data/applications.sqlite3")))
PUBLIC_ORIGIN = os.environ.get("LUMEN_PUBLIC_ORIGIN", "").rstrip("/")
ADMIN_USERNAME = os.environ.get("LUMEN_ADMIN_USERNAME", "")
ADMIN_PASSWORD_HASH = os.environ.get("LUMEN_ADMIN_PASSWORD_HASH", "")
ADMIN_SECRET = os.environ.get("LUMEN_ADMIN_SECRET", "")
SESSION_COOKIE = "lumen_admin_session"
CSRF_COOKIE = "lumen_admin_csrf"
SESSION_SECONDS = 8 * 60 * 60
LOGIN_WINDOW = 15 * 60
LOGIN_LIMIT = 8
SCHEMA = """CREATE TABLE IF NOT EXISTS applications (
 id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 email TEXT NOT NULL,
 investor_type TEXT NOT NULL,
 topic TEXT NOT NULL,
 investment_size TEXT NOT NULL,
 message TEXT NOT NULL,
 language TEXT NOT NULL,
 created_at TEXT NOT NULL
)"""
ADMIN_SCHEMA = """CREATE TABLE IF NOT EXISTS administrators (
 username TEXT PRIMARY KEY,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('superadmin','admin')),
 active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL,
 created_by TEXT NOT NULL
)"""
LOGIN_ATTEMPTS = {}


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute(SCHEMA)
        db.execute(ADMIN_SCHEMA)
        if ADMIN_USERNAME and ADMIN_PASSWORD_HASH:
            db.execute(
                "INSERT OR IGNORE INTO administrators VALUES (?,?,?,?,?,?)",
                (ADMIN_USERNAME, ADMIN_PASSWORD_HASH, "superadmin", 1, datetime.now(timezone.utc).isoformat(), "bootstrap"),
            )
    os.chmod(DB_PATH, 0o600)


init_db()


def make_password_hash(password, iterations=600_000):
    salt = secrets.token_bytes(18)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.urlsafe_b64encode(salt).decode().rstrip("="),
        base64.urlsafe_b64encode(digest).decode().rstrip("="),
    )


def verify_password(password, encoded):
    try:
        algorithm, raw_iterations, raw_salt, raw_digest = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(raw_iterations)
        if not 200_000 <= iterations <= 2_000_000:
            return False
        salt = base64.urlsafe_b64decode(raw_salt + "=" * (-len(raw_salt) % 4))
        expected = base64.urlsafe_b64decode(raw_digest + "=" * (-len(raw_digest) % 4))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _status_text(code):
    return {
        200: "OK", 201: "Created", 303: "See Other", 400: "Bad Request",
        401: "Unauthorized", 403: "Forbidden", 404: "Not Found",
        405: "Method Not Allowed", 413: "Payload Too Large",
        415: "Unsupported Media Type", 429: "Too Many Requests",
        503: "Service Unavailable",
    }[code]


def respond(start_response, code, body=b"", content_type="text/plain; charset=utf-8", headers=None):
    if isinstance(body, str):
        body = body.encode("utf-8")
    output_headers = [
        ("Content-Type", content_type),
        ("Cache-Control", "no-store"),
        ("Content-Length", str(len(body))),
        ("X-Content-Type-Options", "nosniff"),
        ("Referrer-Policy", "no-referrer"),
    ]
    output_headers.extend(headers or [])
    start_response(f"{code} {_status_text(code)}", output_headers)
    return [body]


def json_reply(start_response, code, ok=False):
    return respond(start_response, code, json.dumps({"ok": ok}).encode(), "application/json")


def admin_reply(start_response, code, body, headers=None):
    security = [
        ("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"),
        ("X-Frame-Options", "DENY"),
        ("Permissions-Policy", "camera=(), microphone=(), geolocation=()"),
    ]
    security.extend(headers or [])
    return respond(start_response, code, body, "text/html; charset=utf-8", security)


def redirect(start_response, location, headers=None):
    extra = [("Location", location)]
    extra.extend(headers or [])
    return respond(start_response, 303, b"", headers=extra)


def read_body(environ, maximum=20_000):
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        return None
    if not 0 < length <= maximum:
        return None
    return environ["wsgi.input"].read(length)


def cookies(environ):
    jar = SimpleCookie()
    try:
        jar.load(environ.get("HTTP_COOKIE", ""))
    except Exception:
        return {}
    return {key: morsel.value for key, morsel in jar.items()}


def cookie_header(name, value, max_age=None):
    parts = [f"{name}={value}", "Path=/admin", "Secure", "HttpOnly", "SameSite=Strict"]
    if max_age is not None:
        parts.append(f"Max-Age={max_age}")
    return "; ".join(parts)


def _signed_session(username):
    payload = json.dumps({"u": username, "exp": int(time.time()) + SESSION_SECONDS}, separators=(",", ":")).encode()
    encoded = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    signature = hmac.new(ADMIN_SECRET.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def _session_user(environ):
    if not ADMIN_SECRET:
        return None
    value = cookies(environ).get(SESSION_COOKIE, "")
    try:
        encoded, signature = value.rsplit(".", 1)
        expected = hmac.new(ADMIN_SECRET.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        if payload.get("exp", 0) < int(time.time()):
            return None
        username = payload.get("u", "")
        with sqlite3.connect(DB_PATH) as db:
            row = db.execute(
                "SELECT username,role FROM administrators WHERE username=? AND active=1",
                (username,),
            ).fetchone()
        return {"username": row[0], "role": row[1]} if row else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def admin_configured():
    if len(ADMIN_SECRET) < 32:
        return False
    with sqlite3.connect(DB_PATH) as db:
        return bool(db.execute("SELECT 1 FROM administrators WHERE active=1 LIMIT 1").fetchone())


def session_csrf(environ):
    value = cookies(environ).get(SESSION_COOKIE, "")
    return hmac.new(ADMIN_SECRET.encode(), ("csrf:" + value).encode(), hashlib.sha256).hexdigest()


def valid_session_csrf(environ, value):
    return bool(value) and hmac.compare_digest(value, session_csrf(environ))


def login_limited(address):
    now = time.time()
    recent = [stamp for stamp in LOGIN_ATTEMPTS.get(address, []) if stamp > now - LOGIN_WINDOW]
    LOGIN_ATTEMPTS[address] = recent
    return len(recent) >= LOGIN_LIMIT


def record_failed_login(address):
    LOGIN_ATTEMPTS.setdefault(address, []).append(time.time())


BASE_CSS = """
:root{--gold:#ad8e56;--gold-dark:#876c3b;--ink:#202522;--muted:#747671;--paper:#faf9f6;--line:#e6e2da;--green:#1f5544;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei','Segoe UI',sans-serif;color:var(--ink);background:var(--paper)}*{box-sizing:border-box}body{margin:0;background:linear-gradient(140deg,#faf9f6 0%,#f4f5f2 100%);min-height:100vh}a{color:inherit}button,input{font:inherit}button{cursor:pointer}.shell{width:min(1180px,calc(100% - 40px));margin:auto}.top{background:#fff;border-bottom:1px solid var(--line)}.topin{min-height:88px;display:flex;align-items:center;justify-content:space-between;gap:24px}.brand{display:flex;align-items:center;gap:15px;text-decoration:none}.brand img{width:178px;height:54px;object-fit:contain}.tag{font-size:11px;letter-spacing:1.4px;color:var(--gold-dark);border-left:1px solid #d9c8a8;padding-left:15px}.actions{display:flex;align-items:center;gap:12px}.actions form{margin:0}.button{border:1px solid var(--gold);background:var(--gold);color:#fff;padding:11px 17px;min-height:44px;text-decoration:none;display:inline-flex;align-items:center;justify-content:center}.button:hover{background:var(--gold-dark)}.button.secondary{background:#fff;color:var(--gold-dark)}.button.ghost{background:transparent;color:#555;border-color:#d7d5ce}.main{padding:42px 0 70px}.eyebrow{font:13px Georgia,serif;color:var(--gold-dark);letter-spacing:1.8px;text-transform:uppercase}.title{font:500 clamp(31px,4vw,48px)/1.14 Georgia,'Noto Serif SC','Songti SC',serif;margin:9px 0 11px}.lead{color:var(--muted);line-height:1.8;margin:0}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:30px 0}.stat{background:#fff;border:1px solid var(--line);padding:22px}.stat span{color:var(--muted);font-size:12px}.stat strong{font:500 34px Georgia,serif;display:block;margin-top:8px;color:var(--green)}.toolbar{display:flex;justify-content:space-between;align-items:end;gap:18px;margin:30px 0 16px}.search{display:flex;gap:9px;flex:1;max-width:650px}.search input,.field input{width:100%;min-height:46px;border:1px solid #d9d8d1;background:#fff;padding:11px 13px;border-radius:0;color:var(--ink)}.search input:focus,.field input:focus{outline:2px solid var(--gold);outline-offset:2px}.records{display:grid;gap:12px}.record{background:#fff;border:1px solid var(--line);display:grid;grid-template-columns:1.1fr 1.2fr 1fr 1fr 1fr;gap:16px;padding:19px 21px}.record.head{background:#f0ede5;color:#777266;font-size:11px;letter-spacing:.5px;text-transform:uppercase;padding-block:12px}.cell{min-width:0;overflow-wrap:anywhere}.cell small{display:block;color:var(--muted);margin-top:6px}.message{grid-column:1/-1;background:#faf9f6;border-left:2px solid var(--gold);padding:12px 14px;line-height:1.7;white-space:pre-wrap;color:#525850}.empty{background:#fff;border:1px solid var(--line);padding:60px 30px;text-align:center;color:var(--muted)}.pager{display:flex;justify-content:flex-end;align-items:center;gap:10px;margin-top:18px}.pager span{color:var(--muted);font-size:13px}.loginwrap{min-height:100vh;display:grid;place-items:center;padding:24px}.login{width:min(470px,100%);background:#fff;border:1px solid var(--line);padding:38px}.login .brand{margin-bottom:30px}.field{display:grid;gap:7px;margin:18px 0}.field label{font-size:13px;color:#62665f}.login .button{width:100%;margin-top:10px}.error,.success{padding:11px 13px;line-height:1.6}.error{background:#fff2ef;border-left:3px solid #b94b3d;color:#8b3328}.success{background:#edf6f1;border-left:3px solid var(--green);color:var(--green)}.privacy{font-size:11px;color:#8a8b86;line-height:1.7;margin-top:18px}.footer{border-top:1px solid var(--line);padding:22px 0;color:#8a8983;font-size:11px}.nowrap{white-space:nowrap}.admin-grid{display:grid;grid-template-columns:minmax(300px,.8fr) minmax(420px,1.2fr);gap:22px;margin-top:30px}.panel{background:#fff;border:1px solid var(--line);padding:25px}.panel h2{font:500 25px Georgia,'Songti SC',serif;margin:0 0 8px}.panel-note{color:var(--muted);font-size:13px;line-height:1.7}.admin-list{display:grid;margin-top:20px}.admin-row{display:grid;grid-template-columns:1fr auto;gap:14px;padding:15px 0;border-top:1px solid var(--line)}.admin-row small{display:block;color:var(--muted);margin-top:5px}.role{align-self:center;color:var(--gold-dark);font-size:12px;letter-spacing:.5px}.account{color:var(--muted);font-size:12px;margin-top:12px}@media(max-width:800px){.shell{width:min(100% - 28px,1180px)}.topin{min-height:76px}.brand img{width:145px}.tag{display:none}.main{padding-top:28px}.stats{grid-template-columns:1fr}.toolbar{align-items:stretch;flex-direction:column}.search{max-width:none;width:100%}.record.head{display:none}.record{grid-template-columns:1fr 1fr;padding:17px}.cell:before{content:attr(data-label);display:block;color:#9a927f;font-size:10px;letter-spacing:.4px;margin-bottom:5px}.message{grid-column:1/-1}.actions .home{display:none}.admin-grid{grid-template-columns:1fr}.actions{flex-wrap:wrap;justify-content:flex-end}}@media(max-width:480px){.record{grid-template-columns:1fr}.message{grid-column:auto}.search{display:grid}.login{padding:28px 22px}.title{font-size:32px}.actions{gap:6px}.button{padding:10px 12px}.topin{align-items:flex-start;padding:12px 0}.topin .brand{margin-top:5px}.actions{max-width:170px}}
"""


def layout(content, title="申请管理", actions=""):
    return f"""<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="noindex,nofollow"><title>{html.escape(title)} | LUMEN</title><style>{BASE_CSS}</style></head><body><header class="top"><div class="shell topin"><a class="brand" href="/admin"><img src="/assets/lumen-horizontal.png?v=1" alt="LUMEN Strategic Capital"><span class="tag">PRIVATE ADMINISTRATION</span></a><div class="actions">{actions}</div></div></header>{content}<footer class="footer"><div class="shell">LUMEN Strategic Capital PTE. LTD. · Private administration console</div></footer></body></html>"""


def login_page(csrf, error=""):
    alert = f'<p class="error" role="alert">{html.escape(error)}</p>' if error else ""
    return f"""<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="noindex,nofollow"><title>管理后台登录 | LUMEN</title><style>{BASE_CSS}</style></head><body><main class="loginwrap"><section class="login"><a class="brand" href="/"><img src="/assets/lumen-horizontal.png?v=1" alt="LUMEN Strategic Capital"></a><p class="eyebrow">Private administration</p><h1 class="title">管理后台</h1><p class="lead">登录后查看合作申请与联系资料。</p>{alert}<form action="/admin/login" method="post"><input type="hidden" name="csrf" value="{html.escape(csrf)}"><div class="field"><label for="username">管理员账号</label><input id="username" name="username" autocomplete="username" required maxlength="80"></div><div class="field"><label for="password">密码</label><input id="password" name="password" type="password" autocomplete="current-password" required maxlength="200"></div><button class="button" type="submit">安全登录</button></form><p class="privacy">本页面仅供授权人员使用。登录会话最长持续8小时；用户资料不得向无关人员披露。</p></section></main></body></html>"""


def format_time(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone(timedelta(hours=8)))
        return parsed.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return value


def fetch_dashboard(query, page, page_size=50):
    page = max(1, page)
    terms = []
    params = []
    if query:
        pattern = f"%{query}%"
        terms.append("(name LIKE ? OR email LIKE ? OR investor_type LIKE ? OR topic LIKE ? OR investment_size LIKE ? OR message LIKE ?)")
        params.extend([pattern] * 6)
    where = " WHERE " + " AND ".join(terms) if terms else ""
    with sqlite3.connect(DB_PATH) as db:
        total = db.execute("SELECT count(*) FROM applications" + where, params).fetchone()[0]
        rows = db.execute(
            "SELECT id,name,email,investor_type,topic,investment_size,message,language,created_at FROM applications"
            + where + " ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [page_size, (page - 1) * page_size],
        ).fetchall()
        all_total = db.execute("SELECT count(*) FROM applications").fetchone()[0]
        singapore = timezone(timedelta(hours=8))
        today = datetime.now(singapore).date().isoformat()
        today_total = db.execute("SELECT count(*) FROM applications WHERE date(created_at,'+8 hours')=?", (today,)).fetchone()[0]
        latest = db.execute("SELECT max(created_at) FROM applications").fetchone()[0]
    return rows, total, all_total, today_total, latest


def dashboard_page(query, page, user, csrf):
    rows, filtered, total, today, latest = fetch_dashboard(query, page)
    manage = '<a class="button secondary" href="/admin/users">管理员</a>' if user["role"] == "superadmin" else ""
    actions = f"""{manage}<a class="button secondary" href="/admin/export.csv{('?'+urlencode({'q':query})) if query else ''}">导出 CSV</a><a class="button ghost home" href="/">返回官网</a><form action="/admin/logout" method="post"><input type="hidden" name="csrf" value="{csrf}"><button class="button ghost" type="submit">退出</button></form>"""
    record_html = []
    for _, name, email, investor_type, topic, size, message, language, created_at in rows:
        lang = {"zh-Hans": "简中", "zh-Hant": "繁中", "en": "English"}.get(language, language)
        record_html.append(f"""<article class="record"><div class="cell" data-label="姓名 / 机构"><strong>{html.escape(name)}</strong><small>{html.escape(lang)}</small></div><div class="cell" data-label="邮箱"><a href="mailto:{html.escape(email, quote=True)}">{html.escape(email)}</a></div><div class="cell" data-label="投资人类型">{html.escape(investor_type)}</div><div class="cell" data-label="关注方向">{html.escape(topic)}</div><div class="cell nowrap" data-label="提交时间">{html.escape(format_time(created_at))}<small>{html.escape(size)}</small></div><div class="message">{html.escape(message)}</div></article>""")
    records = "".join(record_html) if record_html else '<div class="empty">暂无符合条件的申请记录</div>'
    pages = max(1, (filtered + 49) // 50)
    pager = []
    if page > 1:
        pager.append(f'<a class="button secondary" href="/admin?{urlencode({"q": query, "page": page - 1})}">上一页</a>')
    pager.append(f"<span>第 {page} / {pages} 页 · {filtered} 条</span>")
    if page < pages:
        pager.append(f'<a class="button secondary" href="/admin?{urlencode({"q": query, "page": page + 1})}">下一页</a>')
    latest_text = format_time(latest) if latest else "暂无"
    content = f"""<main class="shell main"><p class="eyebrow">Cooperation applications</p><h1 class="title">合作申请管理</h1><p class="lead">集中查看网站访客提交的联系信息、投资偏好与合作诉求。</p><p class="account">当前账号：{html.escape(user['username'])} · {'超级管理员' if user['role'] == 'superadmin' else '管理员'}</p><section class="stats" aria-label="申请概览"><div class="stat"><span>全部申请</span><strong>{total}</strong></div><div class="stat"><span>今日新增</span><strong>{today}</strong></div><div class="stat"><span>最近提交</span><strong style="font-size:22px">{html.escape(latest_text)}</strong></div></section><div class="toolbar"><form class="search" action="/admin" method="get"><input name="q" value="{html.escape(query, quote=True)}" placeholder="搜索姓名、邮箱、类型、方向或留言" aria-label="搜索申请"><button class="button" type="submit">搜索</button>{'<a class="button ghost" href="/admin">清除</a>' if query else ''}</form></div><div class="record head" aria-hidden="true"><div>姓名 / 机构</div><div>邮箱</div><div>投资人类型</div><div>关注方向</div><div>提交时间 / 规模</div></div><section class="records">{records}</section><nav class="pager" aria-label="分页">{''.join(pager)}</nav></main>"""
    return layout(content, actions=actions)


def administrators_page(user, csrf, notice="", error=""):
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            "SELECT username,role,created_at,created_by FROM administrators WHERE active=1 ORDER BY role DESC,created_at"
        ).fetchall()
    items = "".join(
        f'<div class="admin-row"><div><strong>{html.escape(username)}</strong><small>创建时间：{html.escape(format_time(created_at))} · 创建人：{html.escape(created_by)}</small></div><span class="role">{"超级管理员" if role == "superadmin" else "管理员"}</span></div>'
        for username, role, created_at, created_by in rows
    )
    alert = f'<p class="success" role="status">{html.escape(notice)}</p>' if notice else ""
    alert += f'<p class="error" role="alert">{html.escape(error)}</p>' if error else ""
    actions = f"""<a class="button secondary" href="/admin">返回申请</a><form action="/admin/logout" method="post"><input type="hidden" name="csrf" value="{csrf}"><button class="button ghost" type="submit">退出</button></form>"""
    content = f"""<main class="shell main"><p class="eyebrow">Access administration</p><h1 class="title">管理员管理</h1><p class="lead">只有超级管理员可以新增后台账号。新管理员可查看、搜索及导出申请记录，但不能管理其他账号。</p><div class="admin-grid"><section class="panel"><h2>新增管理员</h2><p class="panel-note">用户名支持字母、数字、点、下划线和连字符；密码至少 10 位。</p>{alert}<form action="/admin/users" method="post"><input type="hidden" name="csrf" value="{csrf}"><div class="field"><label for="new_username">用户名</label><input id="new_username" name="username" autocomplete="off" required minlength="3" maxlength="32" pattern="[A-Za-z0-9._-]+"></div><div class="field"><label for="new_password">初始密码</label><input id="new_password" name="password" type="password" autocomplete="new-password" required minlength="10" maxlength="200"></div><button class="button" type="submit">创建管理员</button></form></section><section class="panel"><h2>现有管理员</h2><p class="panel-note">当前共有 {len(rows)} 个启用账号。</p><div class="admin-list">{items}</div></section></div></main>"""
    return layout(content, "管理员管理", actions)


def export_csv(query):
    terms = ""
    params = []
    if query:
        terms = " WHERE name LIKE ? OR email LIKE ? OR investor_type LIKE ? OR topic LIKE ? OR investment_size LIKE ? OR message LIKE ?"
        params = [f"%{query}%"] * 6
    with sqlite3.connect(DB_PATH) as db:
        cursor = db.execute(
            "SELECT name,email,investor_type,topic,investment_size,message,language,created_at FROM applications"
            + terms + " ORDER BY created_at DESC",
            params,
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["姓名 / 机构", "邮箱", "投资人类型", "关注方向", "预计投资规模", "投资周期与合作诉求", "语言", "提交时间"])
        for row in cursor:
            writer.writerow([("'" + value if isinstance(value, str) and value[:1] in ("=", "+", "-", "@") else value) for value in row])
    return "\ufeff" + output.getvalue()


def handle_submission(environ, start_response):
    if environ.get("REQUEST_METHOD") != "POST":
        return json_reply(start_response, 405)
    origin = environ.get("HTTP_ORIGIN")
    if origin and PUBLIC_ORIGIN and origin != PUBLIC_ORIGIN:
        return json_reply(start_response, 403)
    if not environ.get("CONTENT_TYPE", "").startswith("application/json"):
        return json_reply(start_response, 415)
    raw = read_body(environ)
    if raw is None or len(raw) > 12_000:
        return json_reply(start_response, 413)
    try:
        values = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return json_reply(start_response, 400)
    limits = {"id": 36, "name": 120, "email": 200, "investorType": 150, "topic": 150, "size": 100, "message": 1500, "language": 10}
    if not isinstance(values, dict) or any(not isinstance(values.get(key), str) or len(values[key]) > limit for key, limit in limits.items()):
        return json_reply(start_response, 400)
    values = {key: values[key].strip() for key in limits}
    try:
        valid_id = bool(re.fullmatch(r"[0-9a-fA-F-]{36}", values["id"])) and uuid.UUID(values["id"]).version == 4
    except ValueError:
        valid_id = False
    if not valid_id or not values["name"] or not values["message"] or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", values["email"]) or values["language"] not in ("zh-Hans", "zh-Hant", "en"):
        return json_reply(start_response, 400)
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT id FROM applications WHERE id=?", (values["id"],)).fetchone():
                return json_reply(start_response, 200, True)
            since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            email_value = values["email"].lower()
            count = db.execute("SELECT count(*) FROM applications WHERE email=? AND created_at>?", (email_value, since)).fetchone()[0]
            if count >= 5:
                return json_reply(start_response, 429)
            db.execute(
                "INSERT INTO applications VALUES (?,?,?,?,?,?,?,?,?)",
                (values["id"], values["name"], email_value, values["investorType"], values["topic"], values["size"], values["message"], values["language"], datetime.now(timezone.utc).isoformat()),
            )
        return json_reply(start_response, 201, True)
    except sqlite3.Error:
        return json_reply(start_response, 503)


def handle_admin(environ, start_response):
    path = environ.get("PATH_INFO", "")
    method = environ.get("REQUEST_METHOD", "GET")
    if not admin_configured():
        return admin_reply(start_response, 503, layout('<main class="shell main"><h1 class="title">管理后台尚未配置</h1></main>', "尚未配置"))
    if path == "/admin/login":
        if method == "GET":
            if _session_user(environ):
                return redirect(start_response, "/admin")
            token = secrets.token_urlsafe(24)
            return admin_reply(start_response, 200, login_page(token), [("Set-Cookie", cookie_header(CSRF_COOKIE, token, 900))])
        if method != "POST":
            return admin_reply(start_response, 405, "Method not allowed")
        raw = read_body(environ, 8_192)
        if raw is None:
            return admin_reply(start_response, 403, "Forbidden")
        form = parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True)
        csrf = form.get("csrf", [""])[0]
        if not csrf or not hmac.compare_digest(csrf, cookies(environ).get(CSRF_COOKIE, "")):
            return admin_reply(start_response, 403, "Forbidden")
        address = environ.get("HTTP_X_REAL_IP") or environ.get("REMOTE_ADDR", "unknown")
        if login_limited(address):
            return admin_reply(start_response, 429, login_page(csrf, "登录尝试过多，请稍后再试。"))
        username = form.get("username", [""])[0].strip()
        password = form.get("password", [""])[0]
        with sqlite3.connect(DB_PATH) as db:
            account = db.execute(
                "SELECT password_hash FROM administrators WHERE username=? AND active=1",
                (username,),
            ).fetchone()
        if not account or not verify_password(password, account[0]):
            record_failed_login(address)
            time.sleep(0.3)
            return admin_reply(start_response, 401, login_page(csrf, "账号或密码不正确。"))
        LOGIN_ATTEMPTS.pop(address, None)
        return redirect(
            start_response,
            "/admin",
            [
                ("Set-Cookie", cookie_header(SESSION_COOKIE, _signed_session(username), SESSION_SECONDS)),
                ("Set-Cookie", cookie_header(CSRF_COOKIE, "", 0)),
            ],
        )
    user = _session_user(environ)
    if not user:
        return redirect(start_response, "/admin/login")
    if path == "/admin/logout":
        raw = read_body(environ, 8_192) if method == "POST" else None
        form = parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True) if raw else {}
        if method != "POST" or not valid_session_csrf(environ, form.get("csrf", [""])[0]):
            return admin_reply(start_response, 403, "Forbidden")
        return redirect(start_response, "/admin/login", [("Set-Cookie", cookie_header(SESSION_COOKIE, "", 0))])
    csrf = session_csrf(environ)
    if path in ("/admin/users", "/admin/users/"):
        if user["role"] != "superadmin":
            return admin_reply(start_response, 403, layout('<main class="shell main"><h1 class="title">无权访问</h1><p class="lead">只有超级管理员可以管理账号。</p></main>', "无权访问"))
        if method == "GET":
            params = parse_qs(environ.get("QUERY_STRING", ""))
            notice = "管理员账号已创建。" if params.get("created") == ["1"] else ""
            return admin_reply(start_response, 200, administrators_page(user, csrf, notice=notice))
        if method != "POST":
            return admin_reply(start_response, 403, "Forbidden")
        raw = read_body(environ, 8_192)
        form = parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True) if raw else {}
        if not valid_session_csrf(environ, form.get("csrf", [""])[0]):
            return admin_reply(start_response, 403, "Forbidden")
        username = form.get("username", [""])[0].strip()
        password = form.get("password", [""])[0]
        if not re.fullmatch(r"[A-Za-z0-9._-]{3,32}", username):
            return admin_reply(start_response, 400, administrators_page(user, csrf, error="用户名格式不正确。"))
        if len(password) < 10 or len(password) > 200:
            return admin_reply(start_response, 400, administrators_page(user, csrf, error="密码至少需要 10 位。"))
        try:
            with sqlite3.connect(DB_PATH) as db:
                db.execute(
                    "INSERT INTO administrators VALUES (?,?,?,?,?,?)",
                    (username, make_password_hash(password), "admin", 1, datetime.now(timezone.utc).isoformat(), user["username"]),
                )
        except sqlite3.IntegrityError:
            return admin_reply(start_response, 400, administrators_page(user, csrf, error="该用户名已经存在。"))
        return redirect(start_response, "/admin/users?created=1")
    if path == "/admin/export.csv":
        if method != "GET":
            return admin_reply(start_response, 405, "Method not allowed")
        query = parse_qs(environ.get("QUERY_STRING", "")).get("q", [""])[0].strip()[:200]
        data = export_csv(query).encode("utf-8")
        return respond(
            start_response,
            200,
            data,
            "text/csv; charset=utf-8",
            [("Content-Disposition", 'attachment; filename="lumen-applications.csv"'), ("X-Frame-Options", "DENY")],
        )
    if path not in ("/admin", "/admin/") or method != "GET":
        return admin_reply(start_response, 404, "Not found")
    params = parse_qs(environ.get("QUERY_STRING", ""))
    query = params.get("q", [""])[0].strip()[:200]
    try:
        page = max(1, min(10_000, int(params.get("page", ["1"])[0])))
    except ValueError:
        page = 1
    return admin_reply(start_response, 200, dashboard_page(query, page, user, csrf))


def application(environ, start_response):
    path = environ.get("PATH_INFO", "")
    if path == "/api/applications":
        return handle_submission(environ, start_response)
    if path == "/admin" or path.startswith("/admin/"):
        return handle_admin(environ, start_response)
    return json_reply(start_response, 404)


if __name__ == "__main__":
    print("Application database initialized.")
