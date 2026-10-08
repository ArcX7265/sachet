"""Operator-provisioned pilot accounts. No public role creation or signup."""
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from .database import db

ITERATIONS = 600_000
DUMMY_SALT = "00" * 32


def normalize_username(username):
    value = username.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.@+-]{2,119}", value):
        raise ValueError("Use 3–120 letters, digits, dots, @, +, - or underscores for the username.")
    return value


def hash_password(password):
    if not 12 <= len(password) <= 256:
        raise ValueError("Use a password between 12 and 256 characters.")
    salt = secrets.token_hex(32)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"


def verify_password(password, encoded):
    if encoded:
        _, rounds, salt, expected = encoded.split("$")
    else:
        rounds, salt, expected = ITERATIONS, DUMMY_SALT, "00" * 32
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds)).hex()
    return hmac.compare_digest(actual, expected) and bool(encoded)


def provision(username, role, password):
    username = normalize_username(username)
    if role not in {"user", "analyst", "admin"}:
        raise ValueError("Unsupported role.")
    encoded = hash_password(password)
    with db(write=True) as c:
        old = c.execute("SELECT id FROM accounts WHERE username=?", (username,)).fetchone()
        owner = old[0] if old else "account_" + secrets.token_hex(16)
        c.execute("""INSERT INTO accounts(id,username,password_hash,role,disabled) VALUES(?,?,?,?,0)
                     ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash,
                     role=excluded.role,disabled=0""", (owner, username, encoded, role))
        c.execute("DELETE FROM sessions WHERE owner=?", (owner,))
    return owner


def disable(username):
    with db(write=True) as c:
        row = c.execute("SELECT id FROM accounts WHERE username=?", (normalize_username(username),)).fetchone()
        if not row:
            raise ValueError("Account not found.")
        c.execute("UPDATE accounts SET disabled=1 WHERE id=?", (row[0],))
        c.execute("DELETE FROM sessions WHERE owner=?", (row[0],))


def authenticate(username, password, client):
    username = username.strip().lower()
    subject = hashlib.sha256(username.encode()).hexdigest()
    client_hash = hashlib.sha256(client.encode()).hexdigest()
    stamp = datetime.now(timezone.utc)
    since = (stamp - timedelta(minutes=15)).isoformat()
    with db(write=True) as c:
        count = c.execute("SELECT COUNT(*) FROM login_attempts WHERE created_at>? AND subject=?", (since, subject)).fetchone()[0]
        client_count = c.execute("SELECT COUNT(*) FROM login_attempts WHERE created_at>? AND client=?", (since, client_hash)).fetchone()[0]
        if count >= 10 or client_count >= 60:
            raise HTTPException(429, "Too many sign-in attempts. Try again in 15 minutes.")
        c.execute("INSERT INTO login_attempts(id,subject,client,created_at) VALUES(?,?,?,?)",
                  (secrets.token_hex(16), subject, client_hash, stamp.isoformat()))
        row = c.execute("SELECT * FROM accounts WHERE username=?", (username,)).fetchone()
    encoded = row["password_hash"] if row else None
    valid = verify_password(password, encoded)
    if not valid or row["disabled"]:
        raise HTTPException(401, "Incorrect username or password.")
    token = secrets.token_urlsafe(40)
    expires = (stamp + timedelta(hours=8)).isoformat()
    with db(write=True) as c:
        # A password reset or account disable during verification must win.
        current = c.execute("SELECT * FROM accounts WHERE id=?", (row["id"],)).fetchone()
        if not current or current["disabled"] or current["password_hash"] != encoded:
            raise HTTPException(401, "Incorrect username or password.")
        c.execute("INSERT INTO sessions(token_hash,owner,role,expires_at) VALUES(?,?,?,?)",
                  (hashlib.sha256(token.encode()).hexdigest(), current["id"], current["role"], expires))
    return {"token": token, "role": current["role"], "demo": False, "expires_at": expires}
