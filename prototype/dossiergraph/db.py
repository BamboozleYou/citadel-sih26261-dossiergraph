"""SQLite persistence (prototype stand-in for PostgreSQL) and the hash-chained audit log."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, name TEXT, role TEXT, region TEXT, inst_id TEXT, pw_hash TEXT);
CREATE TABLE IF NOT EXISTS applications(id TEXT PRIMARY KEY, inst_id TEXT, name TEXT, state TEXT, region TEXT,
    status TEXT, created TEXT, score REAL, factors TEXT, report TEXT, rules_version TEXT, source_set TEXT);
CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, app_id TEXT, filename TEXT, doc_type TEXT, mode TEXT,
    sha256 TEXT, size INTEGER, status TEXT, fields TEXT, verification TEXT, pages INTEGER);
CREATE TABLE IF NOT EXISTS findings(id INTEGER PRIMARY KEY AUTOINCREMENT, app_id TEXT, doc_id TEXT, code TEXT,
    category TEXT, severity TEXT, title TEXT, detail TEXT, rule_id TEXT, aph_ref TEXT, evidence TEXT,
    suggestion TEXT, state TEXT DEFAULT 'open', officer TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY AUTOINCREMENT, app_id TEXT, action TEXT, reason TEXT,
    proposed_by TEXT, proposed_at TEXT, approved_by TEXT, approved_at TEXT, state TEXT);
CREATE TABLE IF NOT EXISTS faculty_tokens(token TEXT, app_id TEXT, inst_id TEXT);
CREATE TABLE IF NOT EXISTS photo_hashes(phash TEXT, app_id TEXT, inst_id TEXT, doc_id TEXT, filename TEXT);
CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, actor TEXT, action TEXT,
    target TEXT, payload TEXT, prev_hash TEXT, hash TEXT);
CREATE INDEX IF NOT EXISTS ix_tok ON faculty_tokens(token);
CREATE INDEX IF NOT EXISTS ix_find ON findings(app_id);
"""
GENESIS = "0" * 64


def connect(path=None) -> sqlite3.Connection:
    config.ensure_dirs()
    con = sqlite3.connect(path or config.DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


@contextmanager
def session(path=None):
    con = connect(path)
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _entry_hash(prev: str, ts: str, actor: str, action: str, target: str, payload: str) -> str:
    return hashlib.sha256("|".join([prev, ts, actor, action, target, payload]).encode()).hexdigest()


def audit(con: sqlite3.Connection, actor: str, action: str, target: str = "", payload: dict | None = None) -> None:
    row = con.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
    prev = row["hash"] if row else GENESIS
    ts = dt.datetime.now().isoformat(timespec="seconds")
    body = json.dumps(payload or {}, sort_keys=True, default=str)
    con.execute("INSERT INTO audit(ts, actor, action, target, payload, prev_hash, hash) VALUES (?,?,?,?,?,?,?)",
                (ts, actor, action, target, body, prev, _entry_hash(prev, ts, actor, action, target, body)))


def verify_audit(con: sqlite3.Connection) -> dict:
    prev, n = GENESIS, 0
    for r in con.execute("SELECT * FROM audit ORDER BY seq"):
        n += 1
        expect = _entry_hash(prev, r["ts"], r["actor"], r["action"], r["target"], r["payload"])
        if r["prev_hash"] != prev or r["hash"] != expect:
            return {"ok": False, "entries": n, "broken_at": r["seq"],
                    "detail": f"Entry #{r['seq']} ({r['action']} by {r['actor']}) does not match its hash; "
                              "the log was altered at or after this entry."}
        prev = r["hash"]
    return {"ok": True, "entries": n, "head": prev}
