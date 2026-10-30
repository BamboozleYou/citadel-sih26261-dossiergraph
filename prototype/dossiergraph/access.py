"""Authentication and attribute-based access control (prototype stand-in for Keycloak + OPA).

Policy, in words:
* institution users see only their own institution's applications;
* scrutiny officers see applications from their region only;
* senior officers see all regions and are the only ones who approve adverse outcomes;
* nobody approves an adverse outcome they proposed (four-eyes rule);
* admins manage rules and audit but cannot decide applications.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

ROLES = {"institution", "officer", "senior_officer", "admin"}


def hash_pw(pw: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt.hex() + "$" + dk.hex()


def check_pw(pw: str, stored: str) -> bool:
    salt, dk = stored.split("$")
    return hmac.compare_digest(hash_pw(pw, bytes.fromhex(salt)).split("$")[1], dk)


def can(user: dict, action: str, app: dict | None = None) -> bool:
    role = user["role"]
    if action == "view_app":
        if role == "institution":
            return app is not None and app["inst_id"] == user["inst_id"]
        if role == "officer":
            return app is not None and app["region"] == user["region"]
        return role in ("senior_officer", "admin")
    if action in ("review_finding", "propose_decision"):
        return role in ("officer", "senior_officer") and can(user, "view_app", app)
    if action == "approve_decision":
        return role == "senior_officer"
    if action in ("view_audit", "view_rules", "view_bench"):
        return role in ("admin", "senior_officer", "officer")
    if action == "precheck":
        return role == "institution"
    return False


def four_eyes_ok(user: dict, decision: dict) -> tuple[bool, str]:
    if user["role"] != "senior_officer":
        return False, "Only a senior officer can approve an adverse outcome."
    if decision["proposed_by"] == user["username"]:
        return False, "Four-eyes rule: the officer who proposed this outcome cannot approve it."
    return True, ""
