"""Durable local Sachet prototype. Run: uvicorn app.main:app --host 127.0.0.1."""
import hashlib
import asyncio
import hmac
import json
import os
import re
import secrets
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4
import httpx
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from .database import db, postgres_enabled
from .accounts import authenticate
from .engine import assess, fingerprint, minimize
from .payments import parse_payment
from .providers import configuration, propose, ProviderFailure

def now():
    return datetime.now(timezone.utc).isoformat()

def uid(prefix):
    return prefix + "_" + uuid4().hex

def dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

def demo_mode():
    return os.getenv("VERCEL") != "1" and os.getenv("DEMO_MODE", "false").lower() == "true"

def init_db():
    with db(write=True) as c:
        schema = """
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, owner TEXT, role TEXT, expires_at TEXT);
        CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, owner TEXT, revision INTEGER, data TEXT, create_key TEXT, UNIQUE(owner,create_key));
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases(id) ON DELETE CASCADE, revision INTEGER, idem TEXT, data TEXT, UNIQUE(case_id,idem));
        CREATE TABLE IF NOT EXISTS assessments(id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases(id) ON DELETE CASCADE, revision INTEGER, stale INTEGER DEFAULT 0, data TEXT);
        CREATE TABLE IF NOT EXISTS alerts(id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases(id) ON DELETE CASCADE, concern_id TEXT, fingerprint TEXT, data TEXT, UNIQUE(case_id,concern_id));
        CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY, data TEXT);
        CREATE TABLE IF NOT EXISTS contributions(id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases(id) ON DELETE CASCADE, candidate_id TEXT REFERENCES candidates(id), data TEXT);
        CREATE TABLE IF NOT EXISTS bundles(id TEXT PRIMARY KEY, active INTEGER DEFAULT 0, data TEXT);
        CREATE TABLE IF NOT EXISTS payments(id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases(id) ON DELETE CASCADE, data TEXT);
        CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases(id) ON DELETE CASCADE, data TEXT);
        CREATE TABLE IF NOT EXISTS order_attempts(request_key TEXT PRIMARY KEY, case_id TEXT REFERENCES cases(id) ON DELETE CASCADE, payment_id TEXT, status TEXT, order_id TEXT);
        CREATE TABLE IF NOT EXISTS gateway_events(id TEXT PRIMARY KEY, order_id TEXT REFERENCES orders(id) ON DELETE CASCADE, digest TEXT);
        CREATE TABLE IF NOT EXISTS provider_calls(id TEXT PRIMARY KEY, provider TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY, action TEXT, target TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL, disabled INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS login_attempts(id TEXT PRIMARY KEY, subject TEXT NOT NULL, client TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS schema_versions(version INTEGER PRIMARY KEY);
        CREATE INDEX IF NOT EXISTS login_subject_time ON login_attempts(subject,created_at);
        CREATE INDEX IF NOT EXISTS login_client_time ON login_attempts(client,created_at);
        """
        if postgres_enabled():
            # Explicit insertion order replaces SQLite's implicit rowid.
            for table in ("cases", "assessments", "alerts", "candidates", "bundles"):
                schema = re.sub(r"(CREATE TABLE IF NOT EXISTS " + table + r"\(.*)(\);)", r"\1, rowid BIGSERIAL\2", schema)
        c.executescript(schema)
        c.execute("INSERT INTO schema_versions(version) VALUES(1) ON CONFLICT(version) DO NOTHING")
        baseline = {"id": "baseline-v1", "title": "English pattern baseline", "patterns": [], "status": "active", "evaluation": None, "created_at": now(), "limitations": ["Limited deterministic rules; no independently measured detection claim."]}
        c.execute("INSERT INTO bundles(id,active,data) VALUES(?,1,?) ON CONFLICT(id) DO NOTHING", (baseline["id"], dump(baseline)))

def audit(c, action, target):
    c.execute("INSERT INTO audit(id,action,target,created_at) VALUES(?,?,?,?)", (uid("audit"), action, target, now()))

def active_bundle(c):
    return json.loads(c.execute("SELECT data FROM bundles WHERE active=1").fetchone()[0])

def withdraw_candidate_source(c, candidate_id):
    """Invalidate every descendant update, and retain only remaining consented summaries."""
    remaining = [json.loads(r[0]) for r in c.execute("SELECT data FROM contributions WHERE candidate_id=?", (candidate_id,))]
    if remaining:
        row = c.execute("SELECT data FROM candidates WHERE id=?", (candidate_id,)).fetchone()
        candidate = json.loads(row[0])
        tags = sorted({tag for item in remaining for tag in item["preview"]["workflow_tags"]})
        candidate.update(workflow_tags=tags, report_count=len(remaining), status="needs_evidence", reviews=[],
                         title=" / ".join(tag.replace("_", " ") for tag in tags) or "Unresolved workflow",
                         evidence=[e for item in remaining for e in item["preview"]["evidence"]],
                         workflow_narrative="\n\n".join(item["preview"].get("workflow_narrative", "") for item in remaining if item["preview"].get("workflow_narrative")),
                         nearest_pattern=tags[0] if tags else None)
        c.execute("UPDATE candidates SET data=? WHERE id=?", (dump(candidate), candidate_id))
    else:
        c.execute("DELETE FROM candidates WHERE id=?", (candidate_id,))
    bundles = [dict(json.loads(r["data"]), id=r["id"]) for r in c.execute("SELECT id,data FROM bundles WHERE id!='baseline-v1'").fetchall()]
    invalid = {b["id"] for b in bundles if b.get("candidate_id") == candidate_id}
    while True:
        descendants = {b["id"] for b in bundles if b.get("parent_id") in invalid}
        if descendants <= invalid:
            break
        invalid |= descendants
    for bundle_id in invalid:
        c.execute("DELETE FROM bundles WHERE id=?", (bundle_id,))
        audit(c, "bundle_withdrawn_source_deleted", bundle_id)
    if not c.execute("SELECT 1 FROM bundles WHERE active=1").fetchone():
        c.execute("UPDATE bundles SET active=1 WHERE id='baseline-v1'")

def remove_case(c, case_id):
    candidate_ids = {r[0] for r in c.execute("SELECT candidate_id FROM contributions WHERE case_id=?", (case_id,))}
    c.execute("DELETE FROM cases WHERE id=?", (case_id,))
    for candidate_id in candidate_ids:
        withdraw_candidate_source(c, candidate_id)
    audit(c, "case_deleted", case_id)

def expire():
    with db(write=True) as c:
        for row in c.execute("SELECT id,data FROM cases").fetchall():
            if json.loads(row["data"])["retention_until"] <= now():
                remove_case(c, row["id"])
        for row in c.execute("SELECT id,data FROM candidates").fetchall():
            if json.loads(row["data"]).get("expires_at", "9999") <= now():
                c.execute("DELETE FROM contributions WHERE candidate_id=?", (row["id"],))
                withdraw_candidate_source(c, row["id"])
        c.execute("DELETE FROM login_attempts WHERE created_at<?", ((datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),))
        c.execute("DELETE FROM sessions WHERE expires_at<?", (now(),))
        c.execute("DELETE FROM provider_calls WHERE created_at<?", ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),))
        c.execute("DELETE FROM audit WHERE created_at<?", ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),))

async def retention_loop():
    while True:
        await asyncio.sleep(60)
        await asyncio.to_thread(expire)

@asynccontextmanager
async def lifespan(app):
    hosted = os.getenv("VERCEL") == "1"
    if hosted:
        if not postgres_enabled():
            raise RuntimeError("Set DATABASE_URL before deploying to Vercel.")
        if os.getenv("DEMO_MODE", "false").lower() == "true":
            raise RuntimeError("DEMO_MODE must be false on Vercel.")
        if len(os.getenv("CRON_SECRET", "")) < 32:
            raise RuntimeError("Set a random CRON_SECRET of at least 32 characters.")
    if postgres_enabled():
        with db() as c:
            if not c.execute("SELECT version FROM schema_versions WHERE version=1").fetchone():
                raise RuntimeError("Run python -m app.manage migrate before starting the API.")
    else:
        init_db()
    retention_task = None
    if not hosted:
        expire()
        retention_task = asyncio.create_task(retention_loop())
    try:
        yield
    finally:
        if retention_task:
            retention_task.cancel()
            with suppress(asyncio.CancelledError):
                await retention_task

app = FastAPI(title="Sachet", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[s.strip() for s in os.getenv("SACHET_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173").split(",")], allow_credentials=False, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Authorization", "Content-Type"])
security = HTTPBearer(auto_error=False)

@app.middleware("http")
async def limits(request: Request, call_next):
    from fastapi.responses import JSONResponse
    try:
        content_length = int(request.headers.get("content-length", "0") or 0)
    except ValueError:
        return JSONResponse({"detail": "Invalid Content-Length."}, status_code=400)
    if content_length < 0 or content_length > 100000:
        return JSONResponse({"detail": "Request too large."}, status_code=413)
    if request.method in {"POST", "PUT", "PATCH"}:
        chunks, size = [], 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > 100000:
                return JSONResponse({"detail": "Request too large."}, status_code=413)
            chunks.append(chunk)
        request._body = b"".join(chunks)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response

def auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(401, "Authentication required.")
    hashed = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    with db() as c:
        row = c.execute("SELECT * FROM sessions WHERE token_hash=? AND expires_at>?", (hashed, now())).fetchone()
    if not row:
        raise HTTPException(401, "Session is missing or expired.")
    if not demo_mode():
        with db() as c:
            account = c.execute("SELECT role,disabled FROM accounts WHERE id=?", (row["owner"],)).fetchone()
        if not account or account["disabled"] or account["role"] != row["role"]:
            raise HTTPException(401, "Session is missing or expired.")
    return dict(row)

def require(user, roles):
    if user["role"] not in roles:
        raise HTTPException(403, "This role cannot perform that action.")

def owned(c, case_id, user):
    row = c.execute("SELECT * FROM cases WHERE id=? AND owner=?", (case_id, user["owner"])).fetchone()
    if not row:
        raise HTTPException(404, "Case not found.")
    case = json.loads(row["data"])
    case["revision"] = row["revision"]
    if case["retention_until"] <= now():
        raise HTTPException(410, "Case retention has expired.")
    return case

def source_events(c, case_id):
    events = [json.loads(r[0]) for r in c.execute("SELECT data FROM events WHERE case_id=? ORDER BY revision", (case_id,))]
    superseded = {e.get("supersedes_id") for e in events}
    for event in events:
        event["active"] = event["id"] not in superseded
    return events

def detail(c, case_id, user):
    case = owned(c, case_id, user)
    case["events"] = source_events(c, case_id)
    rows = c.execute("SELECT data,stale FROM assessments WHERE case_id=? ORDER BY rowid DESC", (case_id,)).fetchall()
    history = [dict(json.loads(r[0]), stale=bool(r[1])) for r in rows]
    case["assessment"] = next((a for a in history if a["case_revision"] == case["revision"] and not a["stale"]), None)
    case["history"] = history
    case["assessments"] = history
    case["alerts"] = [json.loads(r[0]) for r in c.execute("SELECT data FROM alerts WHERE case_id=? ORDER BY rowid DESC", (case_id,))]
    case["contributions"] = [json.loads(r[0]) for r in c.execute("SELECT data FROM contributions WHERE case_id=?", (case_id,))]
    return case

class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")

class SessionBody(Body):
    role: Literal["user", "analyst", "admin"] = "user"

@app.post("/v1/sessions")
def session(body: SessionBody):
    if not demo_mode():
        raise HTTPException(403, "Demo sessions are disabled. Sign in with your account.")
    token = secrets.token_urlsafe(40)
    with db(write=True) as c:
        c.execute("INSERT INTO sessions(token_hash,owner,role,expires_at) VALUES(?,?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), uid("user"), body.role, (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()))
    return {"token": token, "role": body.role, "demo": True}

class LoginBody(Body):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)

@app.post("/v1/auth/login")
def login(body: LoginBody, request: Request):
    client = request.headers.get("x-real-ip", "unknown") if os.getenv("VERCEL") == "1" else (request.client.host if request.client else "unknown")
    return authenticate(body.username, body.password, client)

@app.get("/v1/sessions/current")
def current_session(user=Depends(auth)):
    return {"role": user["role"], "demo": demo_mode(), "expires_at": user["expires_at"]}

@app.get("/internal/cron/expire")
def scheduled_expiry(credentials: HTTPAuthorizationCredentials = Depends(security)):
    secret = os.getenv("CRON_SECRET", "")
    if not secret or not credentials or not hmac.compare_digest(credentials.credentials.encode(), secret.encode()):
        raise HTTPException(401, "Unauthorized cleanup request.")
    expire()
    return {"ok": True}

@app.delete("/v1/sessions/current")
def revoke(user=Depends(auth)):
    with db(write=True) as c:
        c.execute("DELETE FROM sessions WHERE token_hash=?", (user["token_hash"],))
    return {"revoked": True}

@app.get("/health")
@app.get("/v1/health")
def health():
    with db() as c:
        bundle = active_bundle(c)
    return {"status": "ok", "demo_mode": demo_mode(), "engine": "local_rules", "active_bundle": bundle["id"], "capabilities": {"local_rules": True, "cloud": {p: configuration(p) for p in ["groq", "gemini"]}, "private_cloud": False, "payment_test": {"configured": gateway_configured()}, "live_handoff": False, "storage": "postgresql" if postgres_enabled() else "sqlite", "discovery": "reviewed_workflow_tags"}, "limitations": ["Local rules are a limited baseline with no measured real-world detection claim.", "Cloud account eligibility and model quality require validation.", "Demo role creation is restricted to local development; deployed accounts are operator-provisioned."]}

class CaseBody(Body):
    title: str = Field(default="New interaction", min_length=1, max_length=120)
    goal: str = Field(default="", max_length=1000)
    data_class: Literal["synthetic", "public", "private", "consented", "synthetic_demo"] = "private"
    mode: Literal["local", "cloud"] = "local"
    provider: Literal["groq", "gemini"] | None = None
    idempotency_key: str | None = Field(default=None, max_length=100)

@app.post("/v1/cases")
def create_case(body: CaseBody, user=Depends(auth)):
    require(user, {"user"})
    if body.mode == "cloud" and body.data_class not in {"synthetic", "synthetic_demo", "public"}:
        raise HTTPException(403, "Private financial content cannot use the configured free cloud route. Select local assessment.")
    case = {"id": uid("case"), **body.model_dump(exclude={"idempotency_key"}), "revision": 0, "created_at": now(), "updated_at": now(), "retention_until": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(), "language": "en"}
    if body.mode == "cloud" and not body.provider:
        raise HTTPException(422, "Select a cloud provider explicitly.")
    with db(write=True) as c:
        if body.idempotency_key:
            old = c.execute("SELECT id,data FROM cases WHERE owner=? AND create_key=?", (user["owner"], body.idempotency_key)).fetchone()
            if old:
                previous = json.loads(old["data"])
                if any(previous[k] != v for k, v in body.model_dump(exclude={"idempotency_key"}).items()):
                    raise HTTPException(409, "Idempotency key was already used for another case request.")
                return detail(c, old["id"], user)
        c.execute("INSERT INTO cases(id,owner,revision,data,create_key) VALUES(?,?,?,?,?)", (case["id"], user["owner"], 0, dump(case), body.idempotency_key))
        return detail(c, case["id"], user)

@app.get("/v1/cases")
def list_cases(user=Depends(auth)):
    require(user, {"user"})
    expire()
    with db() as c:
        ids = [r[0] for r in c.execute("SELECT id FROM cases WHERE owner=? ORDER BY rowid DESC LIMIT 100", (user["owner"],))]
        return {"cases": [detail(c, case_id, user) for case_id in ids]}

@app.get("/v1/cases/{case_id}")
def get_case(case_id: str, user=Depends(auth)):
    with db() as c:
        return detail(c, case_id, user)

@app.get("/v1/cases/{case_id}/assessments")
def get_assessments(case_id: str, user=Depends(auth)):
    with db() as c:
        return {"assessments": detail(c, case_id, user)["history"]}

class EventBody(Body):
    text: str = Field(min_length=1, max_length=16000)
    source_type: Literal["text", "share", "notification", "ocr", "answer", "user_shared_text"] = "text"
    idempotency_key: str = Field(min_length=1, max_length=100)
    source_event_id: str | None = Field(default=None, max_length=150)
    observed_at: str | None = Field(default=None, max_length=80)
    provenance: dict = Field(default_factory=dict)

class CorrectionBody(Body):
    event_id: str
    text: str = Field(min_length=1, max_length=16000)
    reason: str = Field(default="User correction", max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=100)

class AnswerBody(Body):
    text: str = Field(min_length=1, max_length=16000)
    idempotency_key: str = Field(min_length=1, max_length=100)

def ingest(case_id, body, user, supersedes=None, reason=None):
    with db(write=True) as c:
        case = owned(c, case_id, user)
        old = c.execute("SELECT data FROM events WHERE case_id=? AND idem=?", (case_id, body.idempotency_key)).fetchone()
        if old:
            event = json.loads(old[0])
            if event["text"] != body.text or event["source_type"] != body.source_type or (supersedes and event.get("supersedes_id") != supersedes):
                raise HTTPException(409, "Idempotency key was already used for different content.")
            return False
        events = source_events(c, case_id)
        if len(events) >= 120:
            raise HTTPException(422, "This case has reached the prototype's 120-event limit.")
        if supersedes and not any(e["id"] == supersedes and e["active"] for e in events):
            raise HTTPException(409, "Only the current version of an event can be corrected.")
        if body.source_type == "notification" and body.source_event_id and not supersedes:
            supersedes = next((e["id"] for e in reversed(events) if e.get("source_event_id") == body.source_event_id and e["source_type"] == "notification" and e["active"]), None)
        revision = case["revision"] + 1
        event = {"id": uid("evt"), "case_id": case_id, "revision": revision, "text": body.text, "source_type": body.source_type, "source_event_id": body.source_event_id, "received_at": now(), "observed_at": body.observed_at, "provenance": body.provenance, "supersedes_id": supersedes, "correction_reason": reason, "ordering_confidence": "user_supplied" if body.observed_at else "receipt_order_only", "active": True}
        case.update(revision=revision, updated_at=now())
        c.execute("INSERT INTO events(id,case_id,revision,idem,data) VALUES(?,?,?,?,?)", (event["id"], case_id, revision, body.idempotency_key, dump(event)))
        c.execute("UPDATE cases SET revision=?,data=? WHERE id=?", (revision, dump(case), case_id))
    return True

def process(case_id):
    with db() as c:
        row = c.execute("SELECT data,revision FROM cases WHERE id=?", (case_id,)).fetchone()
        if not row:
            return
        case, revision = json.loads(row[0]), row[1]
        events = [e for e in source_events(c, case_id) if e["active"]]
        bundle = active_bundle(c)
    if case["mode"] == "cloud":
        provider = case["provider"]
        try:
            if case["data_class"] not in {"synthetic", "synthetic_demo", "public"}:
                raise ProviderFailure("private_data_route_disabled")
            with db(write=True) as c:
                day = datetime.now(timezone.utc).date().isoformat()
                count = c.execute("SELECT COUNT(*) FROM provider_calls WHERE created_at>=?", (day,)).fetchone()[0]
                if count >= int(os.getenv("SACHET_CLOUD_DAILY_REQUEST_LIMIT", "40")):
                    raise ProviderFailure("local_daily_budget_exhausted")
                c.execute("INSERT INTO provider_calls(id,provider,created_at) VALUES(?,?,?)", (uid("call"), provider, now()))
            result = propose(provider, events, revision, bundle)
        except ProviderFailure as e:
            result = {"case_revision": revision, "bundle_version": bundle["id"], "engine": provider, "processing_status": "unavailable", "evidence_sufficiency": "unresolved", "response": "explain", "headline": "Assessment unavailable", "summary": "The selected cloud route did not produce a usable assessment.", "failure_category": e.category, "concerns": [], "relations": [], "clarification": None, "next_action": "Review the supplied material and verify financial requests independently. Retry when the selected provider is available.", "limitations": ["No successful new detection result is available.", "There was no silent fallback to a different provider or a safety decision."], "change_summary": "Processing failed; existing source material remains available."}
    else:
        result = assess(events, revision, bundle)
    result["id"] = uid("assessment")
    result["created_at"] = now()
    with db(write=True) as c:
        row = c.execute("SELECT revision FROM cases WHERE id=?", (case_id,)).fetchone()
        if not row:
            return
        stale = row[0] != revision
        previous = c.execute("SELECT data FROM assessments WHERE case_id=? AND stale=0 ORDER BY rowid DESC LIMIT 1", (case_id,)).fetchone()
        if previous:
            last = json.loads(previous[0])
            old_ids = {x["id"] for x in last["concerns"]}
            new_ids = {x["id"] for x in result["concerns"]}
            result["change_summary"] = "Supported concerns changed after this update." if old_ids != new_ids else "The same concern types remain; evidence has been refreshed." if new_ids else "The updated material does not establish a specific concern under this assessment method."
        c.execute("INSERT INTO assessments(id,case_id,revision,stale,data) VALUES(?,?,?,?,?)", (result["id"], case_id, revision, int(stale), dump(result)))
        if stale:
            return
        active_ids = set()
        if result["processing_status"] != "unavailable":
            for concern in result["concerns"]:
                active_ids.add(concern["id"])
                fp = fingerprint(concern)
                old = c.execute("SELECT id,fingerprint,data FROM alerts WHERE case_id=? AND concern_id=?", (case_id, concern["id"])).fetchone()
                if old:
                    alert = json.loads(old["data"])
                    changed = old["fingerprint"] != fp or not alert.get("active", True)
                    alert.update(revision=revision, active=True, updated_at=now(), description=concern["description"], quietly_updated=not changed)
                    if changed:
                        alert.update(acknowledged=False, notification_count=alert.get("notification_count", 1) + 1)
                    c.execute("UPDATE alerts SET fingerprint=?,data=? WHERE id=?", (fp, dump(alert), old["id"]))
                else:
                    alert = {"id": uid("alert"), "concern_id": concern["id"], "revision": revision, "description": concern["description"], "acknowledged": False, "active": True, "created_at": now(), "updated_at": now(), "notification_count": 1, "quietly_updated": False}
                    c.execute("INSERT INTO alerts(id,case_id,concern_id,fingerprint,data) VALUES(?,?,?,?,?)", (alert["id"], case_id, concern["id"], fp, dump(alert)))
            for old in c.execute("SELECT id,concern_id,data FROM alerts WHERE case_id=?", (case_id,)).fetchall():
                if old["concern_id"] not in active_ids:
                    alert = json.loads(old["data"])
                    alert.update(active=False, resolved_at=now())
                    c.execute("UPDATE alerts SET data=? WHERE id=?", (dump(alert), old["id"]))

@app.post("/v1/cases/{case_id}/events")
def add_event(case_id: str, body: EventBody, user=Depends(auth)):
    changed = ingest(case_id, body, user)
    with db() as c:
        missing = detail(c, case_id, user)["assessment"] is None
    if changed or missing:
        process(case_id)
    with db() as c:
        return detail(c, case_id, user)

@app.post("/v1/cases/{case_id}/corrections")
def correct(case_id: str, body: CorrectionBody, user=Depends(auth)):
    with db() as c:
        owned(c, case_id, user)
        row = c.execute("SELECT data FROM events WHERE id=? AND case_id=?", (body.event_id, case_id)).fetchone()
        if not row:
            raise HTTPException(404, "Event not found.")
        original = json.loads(row[0])
    event = EventBody(text=body.text, source_type=original["source_type"], source_event_id=original.get("source_event_id"), idempotency_key=body.idempotency_key or uid("correction"), provenance={"kind": "user_correction"})
    changed = ingest(case_id, event, user, body.event_id, body.reason)
    with db() as c:
        missing = detail(c, case_id, user)["assessment"] is None
    if changed or missing:
        process(case_id)
    with db() as c:
        return detail(c, case_id, user)

@app.post("/v1/cases/{case_id}/answers")
def answer(case_id: str, body: AnswerBody, user=Depends(auth)):
    return add_event(case_id, EventBody(text=body.text, source_type="answer", idempotency_key=body.idempotency_key), user)

@app.post("/v1/cases/{case_id}/reassess")
def reassess(case_id: str, user=Depends(auth)):
    with db() as c:
        owned(c, case_id, user)
    process(case_id)
    with db() as c:
        return detail(c, case_id, user)

@app.post("/v1/cases/{case_id}/alerts/{alert_id}/acknowledge")
def acknowledge(case_id: str, alert_id: str, user=Depends(auth)):
    with db(write=True) as c:
        owned(c, case_id, user)
        row = c.execute("SELECT data FROM alerts WHERE id=? AND case_id=?", (alert_id, case_id)).fetchone()
        if not row:
            raise HTTPException(404, "Alert not found.")
        alert = json.loads(row[0])
        alert["acknowledged"] = True
        c.execute("UPDATE alerts SET data=? WHERE id=?", (dump(alert), alert_id))
    return alert

@app.delete("/v1/cases/{case_id}")
def delete_case(case_id: str, user=Depends(auth)):
    with db(write=True) as c:
        owned(c, case_id, user)
        remove_case(c, case_id)
    return {"deleted": True, "limitations": "Local active database content removed. External provider retention and any independently created backups are outside this deletion."}

class ContributionBody(Body):
    consent: bool
    narrative: str = Field(default="", max_length=2000)
    preview_digest: str | None = Field(default=None, min_length=64, max_length=64)

class ContributionPreviewBody(Body):
    narrative: str = Field(default="", max_length=2000)

def contribution_preview(case, narrative=""):
    assessment = case.get("assessment") or {"concerns": []}
    concerns = assessment["concerns"]
    tags = sorted({c["id"] for c in concerns})
    note = minimize(narrative.strip())
    result = {"title": " / ".join(t.replace("_", " ") for t in tags) if tags else "Unresolved workflow", "workflow_tags": tags, "summary": "User-contributed workflow description and detected categories for review." if note else "Detected action categories from one separately consented case.", "workflow_narrative": note, "narrative_provenance": "user_written_unverified" if note else "not_supplied", "evidence": [{"concern_id": c["id"], "description": c["description"], "source_event_count": len({e["event_id"] for e in c["evidence"]})} for c in concerns], "report_count": 1, "independence": "unverified", "nearest_pattern": tags[0] if tags else None, "proposed_difference": "Review the contributed sequence for a difference from the nearest category. No new global scam or campaign is established.", "limitations": ["Original case messages, title and goal are not automatically included.", "An optional narrative is user-written and unverified. Automatic redaction is incomplete; inspect it before sharing.", "Action categories and a narrative do not independently verify the underlying incident.", "Similarity does not establish fraud, a shared campaign, incident independence or real-world emergence."]}
    result["preview_digest"] = hashlib.sha256(dump({"case_id": case["id"], "revision": case["revision"], "report": result}).encode()).hexdigest()
    return result

@app.get("/v1/cases/{case_id}/contributions/preview")
def preview_contribution(case_id: str, user=Depends(auth)):
    with db() as c:
        return contribution_preview(detail(c, case_id, user))

@app.post("/v1/cases/{case_id}/contributions/preview")
def preview_contribution_note(case_id: str, body: ContributionPreviewBody, user=Depends(auth)):
    with db() as c:
        return contribution_preview(detail(c, case_id, user), body.narrative)

@app.post("/v1/cases/{case_id}/contributions")
def contribute(case_id: str, body: ContributionBody, user=Depends(auth)):
    if not body.consent:
        raise HTTPException(422, "Separate affirmative contribution consent is required.")
    with db(write=True) as c:
        case = detail(c, case_id, user)
        if not case["assessment"] or case["assessment"]["processing_status"] == "unavailable":
            raise HTTPException(409, "Assess the current source revision before contributing its action categories.")
        preview = contribution_preview(case, body.narrative)
        if body.narrative.strip() and not body.preview_digest:
            raise HTTPException(409, "Preview the workflow description and explicitly consent before sharing it.")
        if body.preview_digest and not hmac.compare_digest(body.preview_digest.encode(), preview["preview_digest"].encode()):
            raise HTTPException(409, "The case or report changed. Preview it again before sharing.")
        previous = c.execute("SELECT data FROM contributions WHERE case_id=?", (case_id,)).fetchone()
        if previous:
            existing = json.loads(previous[0])
            if existing["preview"].get("workflow_narrative", "") != preview["workflow_narrative"]:
                raise HTTPException(409, "Withdraw the existing report before contributing a changed description.")
            return existing
        candidate = {"id": uid("candidate"), **preview, "status": "candidate", "reviews": [], "created_at": now(), "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()}
        item = {"id": uid("contribution"), "candidate_id": candidate["id"], "consent_version": "previewed-workflow-v2", "created_at": now(), "case_revision": case["revision"], "preview": preview}
        c.execute("INSERT INTO candidates(id,data) VALUES(?,?)", (candidate["id"], dump(candidate)))
        c.execute("INSERT INTO contributions(id,case_id,candidate_id,data) VALUES(?,?,?,?)", (item["id"], case_id, candidate["id"], dump(item)))
    return item

@app.delete("/v1/cases/{case_id}/contributions/{contribution_id}")
def withdraw(case_id: str, contribution_id: str, user=Depends(auth)):
    with db(write=True) as c:
        owned(c, case_id, user)
        row = c.execute("SELECT candidate_id FROM contributions WHERE id=? AND case_id=?", (contribution_id, case_id)).fetchone()
        if not row:
            raise HTTPException(404, "Contribution not found.")
        c.execute("DELETE FROM contributions WHERE id=?", (contribution_id,))
        withdraw_candidate_source(c, row[0])
        audit(c, "contribution_withdrawn", contribution_id)
    return {"withdrawn": True}

@app.get("/v1/analyst/candidates")
def candidates(user=Depends(auth)):
    require(user, {"analyst", "admin"})
    expire()
    with db() as c:
        items = [json.loads(r[0]) for r in c.execute("SELECT data FROM candidates ORDER BY rowid DESC")]
    for item in items:
        tags = set(item["workflow_tags"])
        stop = {"this", "that", "they", "with", "from", "were", "have", "their", "then", "when", "before", "after", "about", "would", "could", "user", "asked"}
        terms = set(re.findall(r"[a-z]{4,}", item.get("workflow_narrative", "").lower())) - stop
        related = []
        for other in items:
            if other["id"] == item["id"]:
                continue
            shared = tags & set(other["workflow_tags"])
            other_terms = set(re.findall(r"[a-z]{4,}", other.get("workflow_narrative", "").lower())) - stop
            overlap = terms & other_terms
            similarity = len(overlap) / max(1, len(terms | other_terms))
            if shared or (len(overlap) >= 3 and similarity >= .2):
                related.append({"id": other["id"], "shared_tags": sorted(shared), "shared_terms": sorted(overlap), "text_overlap": round(similarity, 3), "method": "category_and_opted_in_word_overlap", "independence": "unverified"})
        item["similar_candidates"] = sorted(related, key=lambda r: (len(r["shared_tags"]), r["text_overlap"]), reverse=True)[:10]
    return {"candidates": items}

class ReviewBody(Body):
    status: Literal["needs_evidence", "existing_pattern", "rejected", "accepted_for_evaluation"]
    reason: str = Field(min_length=5, max_length=2000)

@app.post("/v1/analyst/candidates/{candidate_id}/reviews")
def review(candidate_id: str, body: ReviewBody, user=Depends(auth)):
    require(user, {"analyst", "admin"})
    with db(write=True) as c:
        row = c.execute("SELECT data FROM candidates WHERE id=?", (candidate_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Candidate not found.")
        candidate = json.loads(row[0])
        candidate["status"] = body.status
        candidate["reviews"].append({"status": body.status, "reason": minimize(body.reason), "created_at": now(), "reviewer_role": user["role"]})
        c.execute("UPDATE candidates SET data=? WHERE id=?", (dump(candidate), candidate_id))
        audit(c, "candidate_reviewed", candidate_id)
    return candidate

class PatternBody(Body):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,50}$")
    description: str = Field(min_length=10, max_length=300)
    term_groups: list[list[str]] = Field(min_length=1, max_length=5)
    next_action: str = Field(min_length=10, max_length=500)

class UpdateBody(Body):
    candidate_id: str
    title: str = Field(min_length=3, max_length=120)
    pattern: PatternBody

@app.post("/v1/analyst/updates")
def update_proposal(body: UpdateBody, user=Depends(auth)):
    require(user, {"analyst", "admin"})
    if any(not group or len(group) > 8 or any(len(t.strip()) < 3 or len(t) > 80 for t in group) for group in body.pattern.term_groups):
        raise HTTPException(422, "Pattern term groups must contain 1–8 literal terms of 3–80 characters.")
    with db(write=True) as c:
        row = c.execute("SELECT data FROM candidates WHERE id=?", (body.candidate_id,)).fetchone()
        if not row or json.loads(row[0])["status"] != "accepted_for_evaluation":
            raise HTTPException(409, "The source candidate must first be accepted for evaluation.")
        baseline = active_bundle(c)
        if body.pattern.id in {"advance_payment", "credential_request", "remote_access", "safe_account"} or any(p["id"] == body.pattern.id for p in baseline["patterns"]):
            raise HTTPException(422, "Pattern identifier already exists.")
        bundle = {"id": uid("bundle"), "title": body.title, "candidate_id": body.candidate_id, "parent_id": baseline["id"], "patterns": baseline["patterns"] + [body.pattern.model_dump()], "status": "proposed", "evaluation": None, "created_at": now(), "limitations": ["Literal term patterns are a local baseline; review is not evidence of field efficacy."]}
        c.execute("INSERT INTO bundles(id,active,data) VALUES(?,0,?)", (bundle["id"], dump(bundle)))
    return bundle

REGRESSION_CASES = [
    ("credential request", "Please share your OTP so I can access your bank account.", True),
    ("withdrawal fee", "Pay INR 2000 before we release your withdrawal.", True),
    ("remote support", "Install AnyDesk for this bank refund.", True),
    ("safe account", "Transfer money to this safe account now.", True),
    ("ordinary payment", "Please pay INR 120 for your groceries.", False),
    ("educational warning", "Never share your OTP. Scammers may ask you to pay a fee before withdrawal.", False),
    ("legitimate invoice", "Your invoice is ready. Pay the agreed monthly software subscription.", False),
    ("release without deposit", "Your release code is ready. No processing deposit is required.", False),
    ("processing terminology", "The receipt records your processing deposit from last week.", False),
    ("proposed variation", "To get the release code, first transfer a processing deposit of INR 1200.", True),
]

@app.get("/v1/analyst/bundles")
def list_bundles(user=Depends(auth)):
    require(user, {"analyst", "admin"})
    with db() as c:
        return {"bundles": [dict(json.loads(r["data"]), active=bool(r["active"])) for r in c.execute("SELECT * FROM bundles ORDER BY rowid DESC")]}

@app.post("/v1/analyst/updates/{bundle_id}/evaluate")
def evaluate_update(bundle_id: str, user=Depends(auth)):
    require(user, {"analyst", "admin"})
    with db(write=True) as c:
        row = c.execute("SELECT data FROM bundles WHERE id=?", (bundle_id,)).fetchone()
        if not row or bundle_id == "baseline-v1":
            raise HTTPException(404, "Proposed bundle not found.")
        bundle = json.loads(row[0])
        parent = c.execute("SELECT data FROM bundles WHERE id=?", (bundle["parent_id"],)).fetchone()
        if not parent:
            raise HTTPException(409, "The parent bundle is unavailable.")
        parent = json.loads(parent[0])
        results = []
        for name, text, expected in REGRESSION_CASES:
            events = [{"id": "fixture", "text": text}]
            before = assess(events, 1, parent)["response"] == "warn"
            after = assess(events, 1, bundle)["response"] == "warn"
            results.append({"name": name, "expected_warning": expected, "before": before, "after": after, "regression": before == expected and after != expected, "improvement": before != expected and after == expected})
        regressions = sum(r["regression"] for r in results)
        improvements = sum(r["improvement"] for r in results)
        bundle["evaluation"] = {"passed": regressions == 0 and improvements > 0, "regressions": regressions, "improvements": improvements, "total": len(results), "results": results, "created_at": now(), "dataset": "hand-authored-engineering-regression-v1", "limitations": ["Small synthetic engineering checks; this does not measure real-world accuracy or prove adaptation value.", "These published fixtures are regression material, not an untouched independent test set.", "A separate independent evaluation remains a deployment requirement."]}
        bundle["status"] = "evaluated" if bundle["evaluation"]["passed"] else "rejected"
        c.execute("UPDATE bundles SET data=? WHERE id=?", (dump(bundle), bundle_id))
        audit(c, "bundle_evaluated", bundle_id)
    return bundle

def activate_bundle(c, bundle_id, rollback=False):
    row = c.execute("SELECT data FROM bundles WHERE id=?", (bundle_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Bundle not found.")
    bundle = json.loads(row[0])
    if bundle_id != "baseline-v1":
        if not (bundle.get("evaluation") or {}).get("passed") or (rollback and not bundle.get("activated_at")):
            raise HTTPException(409, "A passing evaluation and approved release history are required.")
        candidate = c.execute("SELECT data FROM candidates WHERE id=?", (bundle["candidate_id"],)).fetchone()
        if not candidate or json.loads(candidate[0])["status"] != "accepted_for_evaluation":
            raise HTTPException(409, "Source candidate approval is no longer valid.")
        if not rollback and active_bundle(c)["id"] not in {bundle["parent_id"], bundle_id}:
            raise HTTPException(409, "The active baseline changed after this proposal. Create and evaluate a new proposal against it.")
    c.execute("UPDATE bundles SET active=0")
    bundle.update(status="active", activated_at=now())
    c.execute("UPDATE bundles SET active=1,data=? WHERE id=?", (dump(bundle), bundle_id))
    audit(c, "bundle_rolled_back" if rollback else "bundle_activated", bundle_id)
    return {**bundle, "active": True, "note": "Existing cases retain their recorded assessment; reassess explicitly to use this bundle."}

@app.post("/v1/admin/bundles/{bundle_id}/activate")
def activate(bundle_id: str, user=Depends(auth)):
    require(user, {"admin"})
    with db(write=True) as c:
        return activate_bundle(c, bundle_id)

@app.post("/v1/admin/bundles/{bundle_id}/rollback")
def rollback(bundle_id: str, user=Depends(auth)):
    require(user, {"admin"})
    with db(write=True) as c:
        return activate_bundle(c, bundle_id, True)

class PaymentBody(Body):
    case_id: str
    uri: str = Field(min_length=1, max_length=4096)

@app.post("/v1/payment-requests")
def payment_request(body: PaymentBody, user=Depends(auth)):
    try:
        parsed = parse_payment(body.uri)
    except ValueError as e:
        raise HTTPException(422, str(e))
    with db(write=True) as c:
        case = detail(c, body.case_id, user)
        if not case["assessment"] or case["assessment"]["processing_status"] == "unavailable":
            raise HTTPException(409, "Assess the current case revision before binding a payment preview.")
        item = {"id": uid("payment"), **parsed, "case_id": body.case_id, "case_revision": case["revision"], "assessment_id": case["assessment"]["id"], "assessment_response": case["assessment"]["response"], "status": "reviewed", "mode": "preview", "created_at": now()}
        c.execute("INSERT INTO payments(id,case_id,data) VALUES(?,?,?)", (item["id"], body.case_id, dump(item)))
    return item

class HandoffBody(Body):
    digest: str = Field(min_length=64, max_length=64)

def bound_payment(c, payment_id, digest, user):
    row = c.execute("SELECT data FROM payments WHERE id=?", (payment_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Payment request not found.")
    item = json.loads(row[0])
    case = detail(c, item["case_id"], user)
    if not hmac.compare_digest(item["digest"].encode(), digest.encode()) or case["revision"] != item["case_revision"] or not case["assessment"] or case["assessment"]["id"] != item["assessment_id"]:
        raise HTTPException(409, "Payment binding is stale or the request has changed. Review the current request again.")
    return item

@app.post("/v1/payment-requests/{payment_id}/handoff")
def handoff(payment_id: str, body: HandoffBody, user=Depends(auth)):
    with db() as c:
        bound_payment(c, payment_id, body.digest, user)
    raise HTTPException(409, "Live handoff is disabled pending provider prerequisites and device validation.")

def gateway_configured():
    return os.getenv("RAZORPAY_KEY_ID", "").startswith("rzp_test_") and bool(os.getenv("RAZORPAY_KEY_SECRET")) and bool(os.getenv("RAZORPAY_WEBHOOK_SECRET"))

class OrderBody(Body):
    payment_request_id: str
    digest: str = Field(min_length=64, max_length=64)
    idempotency_key: str = Field(min_length=1, max_length=100)

@app.post("/v1/payments/test-orders")
def test_order(body: OrderBody, user=Depends(auth)):
    if not gateway_configured():
        raise HTTPException(503, "Razorpay test keys and webhook secret must be configured. No simulated success is substituted.")
    with db(write=True) as c:
        payment = bound_payment(c, body.payment_request_id, body.digest, user)
        if not payment["amount"]:
            raise HTTPException(422, "An explicit amount is required for a test order.")
        request_key = hashlib.sha256((user["owner"] + ":" + body.idempotency_key).encode()).hexdigest()
        attempt = c.execute("SELECT * FROM order_attempts WHERE request_key=?", (request_key,)).fetchone()
        if attempt:
            if attempt["payment_id"] != payment["id"]:
                raise HTTPException(409, "Idempotency key is already bound to a different request.")
            if attempt["status"] == "created":
                return json.loads(c.execute("SELECT data FROM orders WHERE id=?", (attempt["order_id"],)).fetchone()[0])
            raise HTTPException(409, "This order attempt is pending or uncertain. Check the gateway test dashboard before creating another attempt.")
        c.execute("INSERT INTO order_attempts(request_key,case_id,payment_id,status,order_id) VALUES(?,?,?,'pending',NULL)", (request_key, payment["case_id"], payment["id"]))
    from decimal import Decimal
    amount = int(Decimal(payment["amount"]) * 100)
    receipt = "sachet_" + request_key[:30]
    try:
        with httpx.Client(timeout=20) as client:
            response = client.post("https://api.razorpay.com/v1/orders", auth=(os.environ["RAZORPAY_KEY_ID"], os.environ["RAZORPAY_KEY_SECRET"]), json={"amount": amount, "currency": "INR", "receipt": receipt, "notes": {"sachet_mode": "test"}})
        if response.status_code >= 400:
            raise HTTPException(502, "Gateway test-order creation failed; inspect the provider dashboard before retrying.")
        created = response.json()
        if not isinstance(created, dict) or created.get("amount") != amount or created.get("currency") != "INR" or not str(created.get("id", "")).startswith("order_"):
            raise HTTPException(502, "Gateway returned mismatched test-order details.")
    except (httpx.HTTPError, ValueError, TypeError):
        with db(write=True) as c:
            c.execute("UPDATE order_attempts SET status='uncertain' WHERE request_key=?", (request_key,))
        raise HTTPException(502, "Gateway response unavailable; order creation may be uncertain. Check the test dashboard before retrying.")
    except HTTPException:
        with db(write=True) as c:
            c.execute("UPDATE order_attempts SET status='uncertain' WHERE request_key=?", (request_key,))
        raise
    order = {"id": created["id"], "case_id": payment["case_id"], "payment_request_id": payment["id"], "request_key": request_key, "amount": amount, "currency": "INR", "status": "created", "mode": "test", "verified": False, "created_at": now(), "key_id": os.environ["RAZORPAY_KEY_ID"], "limitations": ["This order is payable to your configured test merchant, not the UPI payee in the preview.", "Only a matched signed gateway event can confirm captured status."]}
    with db(write=True) as c:
        # Source deletion while the network request runs prevents retaining an orphan order.
        owned(c, payment["case_id"], user)
        c.execute("INSERT INTO orders(id,case_id,data) VALUES(?,?,?)", (order["id"], payment["case_id"], dump(order)))
        c.execute("UPDATE order_attempts SET status='created',order_id=? WHERE request_key=?", (order["id"], request_key))
    return order

@app.get("/v1/payments/test-orders/{order_id}")
def get_order(order_id: str, user=Depends(auth)):
    with db() as c:
        row = c.execute("SELECT data FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Order not found.")
        order = json.loads(row[0])
        owned(c, order["case_id"], user)
    return order

@app.post("/v1/webhooks/payments/razorpay")
async def webhook(request: Request):
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    if not gateway_configured() or not secret:
        raise HTTPException(503, "Test gateway is not configured.")
    raw = await request.body()
    if len(raw) > 100000:
        raise HTTPException(413, "Webhook is too large.")
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected.encode(), request.headers.get("x-razorpay-signature", "").encode()):
        raise HTTPException(401, "Invalid webhook signature.")
    try:
        payload = json.loads(raw)
        kind = payload["event"]
        payment = payload["payload"]["payment"]["entity"]
        order_id = payment["order_id"]
        payment_id = payment["id"]
        if not isinstance(kind, str) or not isinstance(order_id, str) or not isinstance(payment_id, str) or not payment_id.startswith("pay_"):
            raise ValueError("Invalid identifiers")
    except (ValueError, KeyError, TypeError):
        raise HTTPException(422, "Unsupported gateway event structure.")
    statuses = {"payment.authorized": "authorized", "payment.captured": "captured", "payment.failed": "failed"}
    if kind not in statuses:
        return {"ignored": True}
    digest = hashlib.sha256(raw).hexdigest()
    event_id = request.headers.get("x-razorpay-event-id") or digest
    with db(write=True) as c:
        existing = c.execute("SELECT digest FROM gateway_events WHERE id=?", (event_id,)).fetchone()
        if existing:
            if existing[0] != digest:
                raise HTTPException(409, "Gateway event identifier was reused with different content.")
            return {"accepted": True, "duplicate": True}
        row = c.execute("SELECT data FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Matching test order not found.")
        order = json.loads(row[0])
        if order["mode"] != "test" or payment.get("amount") != order["amount"] or payment.get("currency") != order["currency"] or payment.get("status") != statuses[kind]:
            raise HTTPException(422, "Gateway order, amount, currency or status does not match.")
        c.execute("INSERT INTO gateway_events(id,order_id,digest) VALUES(?,?,?)", (event_id, order_id, digest))
        # Captured is terminal. Reordered authorized/failed callbacks cannot downgrade it.
        if order["status"] != "captured":
            if kind != "payment.authorized" or order["status"] in {"created", "authorized"}:
                order.update(status=statuses[kind], payment_id=payment_id, verified=True, updated_at=now())
        c.execute("UPDATE orders SET data=? WHERE id=?", (dump(order), order_id))
    return {"accepted": True, "status": order["status"], "mode": "test"}
