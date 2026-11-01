"""End-to-end processing of one institution's dossier."""
from __future__ import annotations

import datetime as dt
import json
import math
import uuid
from pathlib import Path

from . import config, crypto, extract, forensics, intake, rules
from .db import audit
from .verify import Registry, ocr_near, verify

ALIAS = {"deed": "land_deed", "luc": "land_use_certificate", "plan": "building_plan", "oc": "occupancy_certificate",
         "fire": "fire_safety_certificate", "stab": "structural_stability", "aff": "affidavit_2", "roster": "faculty_roster"}
REV = {v: k for k, v in ALIAS.items()}
REQUIRED = ["land_deed", "land_use_certificate", "building_plan", "occupancy_certificate",
            "fire_safety_certificate", "affidavit_2", "faculty_roster"]
NICE = {"land_deed": "Land deed", "land_use_certificate": "Land-use certificate", "building_plan": "Building plan",
        "occupancy_certificate": "Occupancy certificate", "fire_safety_certificate": "Fire safety certificate",
        "structural_stability": "Structural stability cert.", "affidavit_2": "Affidavit 2", "faculty_roster": "Faculty roster",
        "photo": "Campus photo", "unknown": "Unclassified"}
WEIGHT = {("authenticity", "high"): 10, ("authenticity", "medium"): 6, ("consistency", "high"): 7,
          ("consistency", "medium"): 4, ("compliance", "high"): 4, ("compliance", "medium"): 2,
          ("compliance", "low"): 1, ("source", "low"): 1}


def score(findings) -> tuple[float, list, bool]:
    """Explainable triage score: weighted sum of findings an officer has not overridden."""
    factors = {}
    for f in findings:
        if f.get("state", "open") == "overridden":
            continue
        w = WEIGHT.get((f["category"], f["severity"]), 0)
        if w:
            factors[f["title"]] = factors.get(f["title"], 0) + w
    top = sorted(factors.items(), key=lambda kv: -kv[1])[:4]
    escalate = any(f["category"] == "authenticity" and f["severity"] == "high" and f.get("state", "open") != "overridden"
                   for f in findings)
    return sum(factors.values()), top, escalate


def rescore(con, app_id: str) -> None:
    rows = [dict(r) for r in con.execute("SELECT category, severity, title, state FROM findings WHERE app_id=?", (app_id,))]
    s, top, esc = score(rows)
    rep = json.loads(con.execute("SELECT report FROM applications WHERE id=?", (app_id,)).fetchone()["report"])
    rep["escalate"] = esc
    for r in rep.get("rules", []):
        if r["id"] == "FRAUD_ESCALATE":
            r["outcome"] = "fail" if esc else "pass"
    con.execute("UPDATE applications SET score=?, factors=?, report=? WHERE id=?", (s, json.dumps(top), json.dumps(rep, default=str), app_id))


def _app_facts(app: dict) -> dict:
    progs = app.get("programmes", [])
    ug = sum(p["intake"] * p["years"] for p in progs if p["level"] == "UG")
    dip = sum(p["intake"] * p["years"] for p in progs if p["level"] == "Diploma")
    inst, infra = app.get("institution", {}), app.get("infrastructure", {})
    return {"name": inst.get("name"), "address": inst.get("address"), "state": inst.get("state"),
            "region": inst.get("region"), "gps": inst.get("campus_gps"), "ug_students": ug, "dip_students": dip,
            "divisions": sum(math.ceil(p["intake"] / 60) * p["years"] for p in progs),
            "max_programme_years": max([p["years"] for p in progs] or [0]),
            "classrooms": infra.get("classrooms"), "classroom_area_sqm": infra.get("classroom_area_sqm")}


def process(con, files: dict[str, bytes], registry_dir: Path, actor: str, status: str = "submitted",
            inst_id: str | None = None, source_set: str = "") -> str:
    app_json = json.loads(files.pop("application.json", b"{}") or b"{}")
    A = _app_facts(app_json)
    inst_id = inst_id or app_json.get("institution", {}).get("aicte_permanent_id", "UNKNOWN")
    app_id = f"{inst_id}-{uuid.uuid4().hex[:6].upper()}"
    reg = Registry(registry_dir)
    findings, docs, fields_by_type, verif_by_type = [], [], {}, {}

    def add(f: dict, doc_id: str | None, evidence: list | None = None):
        f = dict(f)
        f["doc_id"] = doc_id
        f["evidence"] = evidence or []
        findings.append(f)

    for name, data in sorted(files.items()):
        doc_id = f"{app_id}-{len(docs) + 1:02d}"
        chk = intake.inspect(data, name)
        if not chk["ok"]:
            add(dict(code="INTAKE_REJECTED", category="compliance", severity="high", title=f"{name} rejected at intake",
                     detail="; ".join(chk["reasons"]), suggestion="Re-upload a valid PDF/JPEG."), None)
            continue
        crypto.store(doc_id, data)
        if chk["mime"] == "application/pdf":
            ex = extract.extract_pdf(data)
        else:
            ex = extract.extract_image(data)
        if ex.doc_type == "faculty_roster":
            pid = ex.fields.get("aicte_pid", {}).get("value")
            ex.faculty_ids = [x for x in ex.faculty_ids if x != pid]
        doc = {"id": doc_id, "filename": name, "doc_type": ex.doc_type, "mode": ex.mode, "sha256": crypto.sha256(data),
               "size": len(data), "pages": ex.pages, "fields": ex.fields, "status": "manual_review", "verification": {}}
        if chk["active"]:
            add(dict(code="ACTIVE_CONTENT", category="authenticity", severity="medium",
                     title="PDF contains active content", detail="Found " + ", ".join(chk["active"]) +
                     ". Officers only see rasterised pages, so it never runs.", suggestion="Ask for a clean copy."), doc_id)
        ev = lambda key: ([{"doc_id": doc_id, "page": ex.fields[key]["page"], "bbox": ex.fields[key]["bbox"],
                            "label": f"{key}: {ex.fields[key]['value']}"}] if key in ex.fields else [])

        if ex.doc_type == "photo":
            ph = forensics.phash(data)
            for r in con.execute("SELECT * FROM photo_hashes WHERE inst_id != ?", (inst_id,)).fetchall():
                d = forensics.phash_distance(ph, r["phash"])
                if d <= config.PHASH_MAX_DISTANCE:
                    try:
                        same_scene = forensics.photo_same_scene(data, crypto.load(r["doc_id"]), d)
                    except Exception:
                        same_scene = d <= 6
                    if not same_scene:
                        continue
                    msg = dict(code="PHOTO_REUSED", category="authenticity", severity="high",
                               title="Campus photo also submitted by another institution",
                               detail=f"{name} matches {r['filename']} of {r['inst_id']} (perceptual-hash distance {d}, ORB keypoint match confirmed).",
                               suggestion="Ask for fresh geotagged photos; flag for EVC.")
                    add(msg, doc_id)
                    if status == "submitted":
                        con.execute("INSERT INTO findings(app_id, doc_id, code, category, severity, title, detail, evidence, suggestion) "
                                    "VALUES (?,?,?,?,?,?,?,?,?)", (r["app_id"], r["doc_id"], "PHOTO_REUSED", "authenticity", "high",
                                    "Campus photo also submitted by another institution",
                                    f"{r['filename']} matches {name} of {inst_id} (distance {d}).", "[]", "Ask both institutions for fresh photos."))
            gps = forensics.exif_gps(data)
            if gps and A.get("gps"):
                km = forensics.haversine_km(gps, A["gps"])
                if km > config.GPS_MAX_KM:
                    add(dict(code="PHOTO_GPS", category="authenticity", severity="medium",
                             title="Photo geotag is away from the campus",
                             detail=f"EXIF location is {km:.1f} km from the declared campus coordinates.",
                             suggestion="Request geotagged photos taken on campus."), doc_id)
            elif not gps:
                add(dict(code="PHOTO_NO_GPS", category="compliance", severity="low", title="Photo has no geotag",
                         detail="Location cannot be confirmed.", suggestion="Use the portal's geotagged capture."), doc_id)
            if status == "submitted":
                con.execute("INSERT INTO photo_hashes VALUES (?,?,?,?,?)", (ph, app_id, inst_id, doc_id, name))
            doc["status"] = "advisory"
            docs.append(doc)
            continue

        v = verify(ex.doc_type, data, ex.fields, ex.qr, A.get("state") or "", reg, ex.mode)
        doc["status"], doc["verification"] = v.status, v.to_dict()
        for f in v.findings:
            add(f, doc_id, ev(f["field"]) if f.get("field") else [])
        nsig = 1 if v.signature else 0
        if ex.mode == "text-layer":
            for f in forensics.pdf_structure(data, nsig, ex.fields):
                add(f, doc_id, ev(f["field"]) if f.get("field") else [])
        if ex.mode == "ocr" and ex.images and not (v.status == "verified" and v.signature):
            hits = forensics.scan_forensics(ex.images[0], 595.28)
            if hits:
                f = dict(hits[0])
                f["detail"] = f"{len(hits)} region(s): " + hits[0]["detail"]
                add(f, doc_id, [{"doc_id": doc_id, "page": 0, "bbox": h["bbox"], "label": "noise-free region"} for h in hits])
        low = [k for k, x in ex.fields.items() if x.get("conf", 100) < 60]
        if low:
            add(dict(code="LOW_OCR_CONFIDENCE", category="compliance", severity="low", title="Some fields were hard to read",
                     detail="Low OCR confidence for: " + ", ".join(low) + ". Values need a human check.",
                     suggestion="Re-scan at 300 dpi."), doc_id, sum((ev(k) for k in low), []))
        if v.status in ("pending", "source_unavailable"):
            add(dict(code="SOURCE_" + v.status.upper(), category="source", severity="low",
                     title="Issuer could not confirm yet" if v.status == "pending" else "Issuer source unavailable",
                     detail=v.source + ": " + ("response pending." if v.status == "pending" else "portal unavailable; retry scheduled."),
                     suggestion="Route to manual confirmation if not resolved in 7 days."), doc_id)

        if ex.doc_type == "faculty_roster":
            tokens = [crypto.faculty_token(x) for x in ex.faculty_ids]
            claimed = {}
            for t in set(tokens):
                for r in con.execute("SELECT app_id, inst_id FROM faculty_tokens WHERE token=? AND inst_id != ?", (t, inst_id)):
                    claimed.setdefault(r["inst_id"], set()).add(t)
            if status == "submitted":
                con.executemany("INSERT INTO faculty_tokens VALUES (?,?,?)", [(t, app_id, inst_id) for t in set(tokens)])
            n_claimed = sum(len(s) for s in claimed.values())
            doc["cross_claimed"] = n_claimed
            doc["faculty_count"] = len(set(ex.faculty_ids))
            for other, toks in claimed.items():
                add(dict(code="FACULTY_CROSS_CLAIM", category="consistency", severity="high",
                         title=f"{len(toks)} faculty also claimed by {other}",
                         detail="Matched on keyed hashes of faculty IDs (no IDs are shared between institutions).",
                         suggestion="Ask both institutions for appointment letters and salary statements."), doc_id)
                if status == "submitted":
                    for r in con.execute("SELECT DISTINCT app_id FROM faculty_tokens WHERE inst_id=?", (other,)):
                        con.execute("INSERT INTO findings(app_id, doc_id, code, category, severity, title, detail, evidence, suggestion) "
                                    "VALUES (?,?,?,?,?,?,?,?,?)", (r["app_id"], None, "FACULTY_CROSS_CLAIM", "consistency", "high",
                                    f"{len(toks)} faculty also claimed by {inst_id}", "Matched on keyed hashes of faculty IDs.",
                                    "[]", "Ask both institutions for appointment letters."))
        fields_by_type[ex.doc_type] = (doc_id, ex.fields, ex.lines[0].text if ex.lines else "")
        verif_by_type[ex.doc_type] = v.status
        docs.append(doc)

    # ---- rules ----
    facts = {"app": A, "ay_start": config.ACADEMIC_YEAR_START, "today": config.TODAY,
             "authenticity_high": sum(1 for f in findings if f["category"] == "authenticity" and f["severity"] == "high")}
    for t, (doc_id, flds, header) in fields_by_type.items():
        if t in REV:
            facts[REV[t]] = {k: v["value"] for k, v in flds.items()} | {"issuer": header}
    if "deed" in facts and "plan" in facts:
        ds, ps = facts["deed"].get("survey"), facts["plan"].get("survey")
        if ds and ps and ds != ps and ocr_near(ds, ps):
            deed_doc_id, deed_flds, _ = fields_by_type["land_deed"]
            if not any(f.get("doc_id") == deed_doc_id and f["code"] == "OCR_NEAR_MATCH" and f.get("field") == "survey" for f in findings):
                ev_s = [{"doc_id": deed_doc_id, "page": deed_flds["survey"]["page"], "bbox": deed_flds["survey"]["bbox"],
                         "label": f"survey: {ds}"}] if "survey" in deed_flds else []
                add(dict(code="OCR_NEAR_MATCH", category="compliance", severity="low", field="survey",
                         title="Survey probably misread by OCR",
                         detail=f"Scan reads {ds!r}; digital building plan says {ps!r}. One-character difference, so treated as a reading error.",
                         suggestion="Officer to confirm the value on the page image."), deed_doc_id, ev_s)
            facts["deed"]["survey"] = ps
    roster_doc = next((d for d in docs if d["doc_type"] == "faculty_roster"), None)
    if roster_doc:
        facts.setdefault("roster", {})
        facts["roster"]["count"] = roster_doc.get("faculty_count", 0)
        facts["roster"]["cross_claimed"] = roster_doc.get("cross_claimed", 0)
    results = rules.run(facts)
    present = {d["doc_type"] for d in docs}
    for t in REQUIRED:
        if t not in present:
            add(dict(code="MISSING_DOCUMENT", category="compliance", severity="high", title=f"Required document missing: {NICE[t]}",
                     detail="This document is required for the application type.", suggestion="Upload it before submission."), None)
    for r in results:
        if r["outcome"] in ("fail", "undetermined") and r["category"] != "escalation":
            evid = []
            for e in r.get("evidence") or []:
                k, fld = e.split(".")
                if k in ALIAS and ALIAS[k] in fields_by_type:
                    did, flds, _ = fields_by_type[ALIAS[k]]
                    if fld in flds:
                        evid.append({"doc_id": did, "page": flds[fld]["page"], "bbox": flds[fld]["bbox"],
                                     "label": f"{NICE[ALIAS[k]]}: {fld} = {flds[fld]['value']}"})
            sev = r["severity"] if r["outcome"] == "fail" else "low"
            cat = r["category"] if r["outcome"] == "fail" else "compliance"
            add(dict(code=r["id"], category=cat, severity=sev, rule_id=r["id"], aph_ref=r["aph_ref"],
                     title=r["title"] + (" (could not be checked)" if r["outcome"] == "undetermined" else " — not met"),
                     detail=r["on_fail"] if r["outcome"] == "fail" else f"Missing evidence: {r.get('note', '')}",
                     suggestion=r["on_fail"]), evid[0]["doc_id"] if evid else None, evid)

    # ---- graph ----
    nodes = {REV.get(d["doc_type"], d["doc_type"]): {"label": NICE.get(d["doc_type"], d["doc_type"]), "status": d["status"],
                                                      "doc_id": d["id"]} for d in docs if d["doc_type"] != "photo"}
    nodes["app"] = {"label": "Application form", "status": "verified", "doc_id": None}
    edges = []
    for r in results:
        if r.get("edge") and r["outcome"] in ("pass", "fail", "undetermined"):
            a, b = r["edge"]
            edges.append({"a": a, "b": b, "rule": r["id"], "outcome": r["outcome"],
                          "kind": r["category"], "label": r["id"].replace("_", " ").title()})
    if "deed" in nodes:
        edges.append({"a": "app", "b": "deed", "rule": "LAND_TITLE", "kind": "compliance", "label": "Land Title",
                      "outcome": next(r["outcome"] for r in results if r["id"] == "LAND_TITLE")})

    # ---- score ----
    total, top, escalate = score(findings)
    for r in results:
        if r["id"] == "FRAUD_ESCALATE":
            r["outcome"] = "fail" if escalate else "pass"

    rule_facts_json = {k: v for k, v in facts.items() if k not in ("ay_start", "today")}
    report = {"facts": {k: v for k, v in A.items()}, "rule_facts": rule_facts_json, "rules": results,
              "graph": {"nodes": nodes, "edges": edges},
              "checklist": [r for r in results if r["outcome"] == "manual"], "escalate": escalate,
              "rules_version": rules.load_pack()["version"], "processed": dt.datetime.now().isoformat(timespec="seconds")}
    con.execute("INSERT INTO applications VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (app_id, inst_id, A.get("name"), A.get("state"), A.get("region"), status,
                 dt.datetime.now().isoformat(timespec="seconds"), total, json.dumps(top), json.dumps(report, default=str),
                 report["rules_version"], source_set))
    for d in docs:
        con.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (d["id"], app_id, d["filename"], d["doc_type"], d["mode"], d["sha256"], d["size"], d["status"],
                     json.dumps(d["fields"], default=str), json.dumps(d["verification"], default=str), d["pages"]))
    for f in findings:
        con.execute("INSERT INTO findings(app_id, doc_id, code, category, severity, title, detail, rule_id, aph_ref, evidence, suggestion) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (app_id, f.get("doc_id"), f["code"], f["category"], f["severity"], f["title"], f.get("detail", ""),
                     f.get("rule_id"), f.get("aph_ref"), json.dumps(f.get("evidence", []), default=str), f.get("suggestion", "")))
    if status == "submitted":
        for other in {r["app_id"] for r in con.execute("SELECT app_id FROM findings WHERE app_id != ? AND (detail LIKE ? OR title LIKE ?)",
                                                        (app_id, f"%{inst_id}%", f"%{inst_id}%"))}:
            rescore(con, other)
    audit(con, actor, "process_dossier", app_id, {"inst_id": inst_id, "documents": len(docs), "findings": len(findings),
                                                   "score": total, "rules_version": report["rules_version"], "status": status})
    return app_id


def load_dir(d: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(d.iterdir()) if p.is_file()}
