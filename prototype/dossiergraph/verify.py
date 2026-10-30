"""Verification against issuing authorities.

Order of trust: (1) the issuer's digital signature, (2) the issuer's registry
(DigiLocker-style pull, municipal/land/fire portals; mocked here), (3) QR payloads.
Forensics only matter where none of these can vouch for a document.

Statuses: verified, mismatch, expired, pending, source_unavailable, manual_review.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from pyhanko.keys import load_cert_from_pemder
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext
from rapidfuzz import fuzz

from . import config, pki
from .crypto import sha256

logging.getLogger("pyhanko").setLevel(logging.ERROR)
logging.getLogger("pyhanko_certvalidator").setLevel(logging.ERROR)

SOURCES = {
    "land_deed": ("land_records", "State land records (Sub-Registrar)"),
    "land_use_certificate": ("town_planning", "Town & Country Planning registry"),
    "building_plan": ("municipal_plans", "Municipal building-plan registry"),
    "occupancy_certificate": ("municipal_oc", "Municipal OC registry (DigiLocker pull)"),
    "fire_safety_certificate": ("fire_services", "State Fire Services portal (DigiLocker pull)"),
}
ALWAYS_SIGNED = {"occupancy_certificate", "fire_safety_certificate"}
COMPARE = {
    "land_deed": [("survey", "survey", "id"), ("owner", "owner", "fuzzy"), ("area_acres", "area_acres", "num")],
    "land_use_certificate": [("survey", "survey", "id"), ("applicant", "applicant", "fuzzy"), ("area_acres", "area_acres", "num")],
    "building_plan": [("address", "address", "fuzzy"), ("area_sqm", "area_sqm", "num"), ("owner", "owner", "fuzzy")],
    "occupancy_certificate": [("address", "address", "fuzzy"), ("completion", "completion", "exact"), ("area_sqm", "area_sqm", "num")],
    "fire_safety_certificate": [("address", "address", "fuzzy"), ("valid_until", "valid_until", "exact"), ("occupant", "occupant", "fuzzy")],
}


def parse_date(s):
    try:
        d, m, y = str(s).split("-")
        return dt.date(int(y), int(m), int(d))
    except Exception:
        return None


def same(kind: str, a, b) -> bool:
    if a is None or b is None:
        return False
    if kind == "num":
        try:
            return abs(float(a) - float(b)) <= 0.011 * max(1.0, abs(float(b)) / 100)
        except ValueError:
            return False
    if kind == "id":
        return str(a).replace(" ", "").upper() == str(b).replace(" ", "").upper()
    if kind == "fuzzy":
        return fuzz.token_set_ratio(str(a), str(b)) >= config.FUZZY_ADDRESS_MIN
    return str(a).strip() == str(b).strip()


@dataclass
class Verification:
    status: str
    source: str
    checks: list = field(default_factory=list)   # [(name, ok, detail)]
    signature: dict | None = None
    registry: dict | None = None
    timestamp: str = ""
    findings: list = field(default_factory=list)

    def to_dict(self):
        return {"status": self.status, "source": self.source, "checks": self.checks, "signature": self.signature,
                "registry": self.registry, "timestamp": self.timestamp}


def check_signature(data: bytes) -> dict | None:
    r = PdfFileReader(io.BytesIO(data), strict=False)
    sigs = r.embedded_signatures
    if not sigs:
        return None
    pki.ensure_root()
    root = load_cert_from_pemder(str(pki.root_paths()[1]))
    vc = ValidationContext(trust_roots=[root], allow_fetching=False, revocation_mode="soft-fail")
    st = validate_pdf_signature(sigs[0], vc)
    coverage = st.coverage.name if st.coverage else "UNKNOWN"
    modlevel = st.modification_level.name if st.modification_level else "UNKNOWN"
    untouched = coverage == "ENTIRE_FILE" or modlevel in ("NONE", "LTA_UPDATES")
    return {"intact": bool(st.intact), "valid": bool(st.valid), "trusted": bool(st.trusted),
            "coverage": coverage, "modification_level": modlevel, "untouched_after_signing": untouched,
            "signer": st.signing_cert.subject.human_friendly if st.signing_cert else "?"}


class Registry:
    """Mock issuer registries. Production: DigiLocker requester APIs / state portals via adapters."""

    def __init__(self, path: Path):
        self.path = path
        self.data = {}
        for f in path.glob("*.json"):
            self.data[f.stem] = json.loads(f.read_text())

    def availability(self, kind: str, state: str) -> str:
        return self.data.get("availability", {}).get(kind, {}).get(state, "available")

    def lookup(self, kind: str, ref: str):
        return self.data.get(kind, {}).get(ref)


def ocr_near(a, b) -> bool:
    """A one-character slip or a dropped decimal on a scan is more likely OCR than forgery."""
    if a is None or b is None:
        return False
    x, y = str(a).replace(" ", "").upper(), str(b).replace(" ", "").upper()
    if y.startswith(x) and len(x) >= 2:
        return True
    return fuzz.ratio(x, y) >= 80


def verify(doc_type: str, data: bytes, fields: dict, qr: str | None, state: str, registry: Registry,
           mode: str = "text-layer") -> Verification:
    now = dt.datetime.now().isoformat(timespec="seconds")
    v = Verification("manual_review", "No issuing-authority source for this document type", timestamp=now)
    val = lambda k: fields.get(k, {}).get("value")

    # 1. digital signature
    sig = check_signature(data) if doc_type != "photo" else None
    v.signature = sig
    sig_ok = bool(sig and sig["intact"] and sig["valid"] and sig["trusted"] and sig["untouched_after_signing"])
    if sig:
        v.checks.append(("Issuer digital signature", sig_ok,
                         f"{sig['signer']}; coverage {sig['coverage']}; changes after signing: {sig['modification_level']}"))
        if not sig["untouched_after_signing"]:
            v.findings.append(dict(code="SIG_MODIFIED", category="authenticity", severity="high",
                                   title="Document changed after the issuer signed it",
                                   detail=f"Signature covers an earlier revision only (modification level {sig['modification_level']}). "
                                          "The visible content differs from what the issuer signed.",
                                   suggestion="Request the original signed copy from the issuer / DigiLocker."))
        elif not sig["trusted"] or not sig["valid"]:
            v.findings.append(dict(code="SIG_UNTRUSTED", category="authenticity", severity="high",
                                   title="Signature does not chain to a trusted issuer",
                                   detail="The certificate is not issued by a trusted root.", suggestion="Verify with issuer."))
    elif doc_type in ALWAYS_SIGNED:
        v.checks.append(("Issuer digital signature", False, "No signature, but this issuer always signs electronically"))
        v.findings.append(dict(code="SIG_MISSING", category="authenticity", severity="high",
                               title="Expected digital signature is missing",
                               detail="This issuer issues these certificates only as digitally signed PDFs; this copy is unsigned.",
                               suggestion="Ask for the DigiLocker / signed original."))

    # 2. QR payload vs printed text
    if doc_type == "land_use_certificate":
        if qr:
            try:
                q = json.loads(qr)
                ok = same("id", q.get("survey"), val("survey")) and q.get("ref") == val("ref")
                v.checks.append(("QR code matches printed text", ok, f"QR survey {q.get('survey')} / printed {val('survey')}"))
                if not ok:
                    v.findings.append(dict(code="QR_MISMATCH", category="authenticity", severity="high",
                                           title="QR code contradicts the printed certificate",
                                           detail=f"QR encodes survey no. {q.get('survey')} but the page shows {val('survey')}.",
                                           field="survey", suggestion="Treat printed values as unverified; confirm with Town Planning."))
            except json.JSONDecodeError:
                v.checks.append(("QR code readable", False, "QR payload not parseable"))
        else:
            v.checks.append(("QR code readable", False, "No QR code found"))

    # 3. issuer registry
    if doc_type in SOURCES:
        kind, label = SOURCES[doc_type]
        v.source = label
        avail = registry.availability(kind, state)
        rec = registry.lookup(kind, val("ref") or "") if avail == "available" else None
        if rec is None and avail == "available" and mode == "ocr" and val("ref"):
            near = [k for k in registry.data.get(kind, {}) if fuzz.ratio(k, val("ref")) >= 92]
            if len(near) == 1:
                rec = registry.lookup(kind, near[0])
                v.checks.append(("Issuer registry", None, f"matched {near[0]!r} to OCR reading {val('ref')!r}"))
        if avail == "pending":
            v.status = "pending"
            v.checks.append(("Issuer registry", None, "Request queued with the state portal; response pending"))
        elif avail == "unavailable":
            v.status = "verified" if sig_ok else "source_unavailable"
            v.checks.append(("Issuer registry", None, "Source unavailable (portal down / no API); retry scheduled"))
        elif rec is None:
            v.status = "mismatch"
            v.checks.append(("Issuer registry", False, f"Reference {val('ref')!r} not found in issuer records"))
            v.findings.append(dict(code="REF_NOT_FOUND", category="authenticity", severity="high",
                                   title="Reference number not found with the issuer", field="ref",
                                   detail=f"{label} has no record of {val('ref')!r}.", suggestion="Confirm with issuing office."))
        else:
            v.registry = {k: rec[k] for k in rec if k not in ("sha256",)}
            diffs, misreads = [], []
            for fk, rk, kind_ in COMPARE.get(doc_type, []):
                ok = same(kind_, val(fk), rec.get(rk))
                if not ok and mode == "ocr" and ocr_near(val(fk), rec.get(rk)):
                    misreads.append((fk, val(fk), rec.get(rk)))
                    v.checks.append((f"Registry: {fk}", None, f"possible OCR misread: {val(fk)!r} vs issuer {rec.get(rk)!r}"))
                    continue
                v.checks.append((f"Registry: {fk}", ok, f"document {val(fk)!r} / issuer {rec.get(rk)!r}"))
                if not ok:
                    diffs.append((fk, val(fk), rec.get(rk)))
            for fk, a_, b_ in misreads:
                v.findings.append(dict(code="OCR_NEAR_MATCH", category="compliance", severity="low", field=fk,
                                       title=f"{fk.replace('_', ' ').title()} probably misread by OCR",
                                       detail=f"Scan reads {a_!r}; issuer record says {b_!r}. One-character difference, so treated as a reading error.",
                                       suggestion="Officer to confirm the value on the page image."))
            identical = sha256(data) == rec.get("sha256")
            v.checks.append(("Byte-identical to issuer copy", identical, "SHA-256 compared with issuer record"))
            if diffs:
                v.status = "mismatch"
                for fk, a, b in diffs:
                    v.findings.append(dict(code="REGISTRY_MISMATCH", category="authenticity", severity="high", field=fk,
                                           title=f"{fk.replace('_', ' ').title()} differs from issuer record",
                                           detail=f"Document shows {a!r}; issuer record says {b!r}.",
                                           suggestion="Use the issuer's value; ask the institution to explain."))
            else:
                v.status = "verified"

    if v.status in ("verified",) and doc_type == "fire_safety_certificate":
        vu = parse_date(val("valid_until"))
        if vu and vu < config.ACADEMIC_YEAR_START:
            v.status = "expired"
    if doc_type in ALWAYS_SIGNED and v.status == "manual_review" and sig_ok:
        v.status = "verified"
    if v.status == "verified" and any(f["code"] == "OCR_NEAR_MATCH" for f in v.findings):
        v.status = "manual_review"
    if v.findings and v.status not in ("mismatch",):
        v.status = "mismatch" if any(f["severity"] == "high" for f in v.findings) else v.status
    return v
