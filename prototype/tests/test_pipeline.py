"""End-to-end: generate one dossier per tamper type and check each forgery is caught."""
import json

import pytest

from dossiergraph import config, db, pipeline, pki
from synth.generate import Gen

EXPECT = {
    "altered_date": lambda F, doc: any(f["doc_id"] == doc and f["category"] == "authenticity" for f in F),
    "altered_identifier": lambda F, doc: any(f["code"] == "QR_MISMATCH" for f in F),
    "pdf_text_edit": lambda F, doc: any(f["code"] in ("PDF_INCREMENTAL_EDIT", "FONT_INCONSISTENT") for f in F),
    "swapped_seal": lambda F, doc: any(f["code"] == "SCAN_NOISE_ANOMALY" and f["doc_id"] == doc for f in F),
    "pasted_signature": lambda F, doc: any(f["code"] == "SCAN_NOISE_ANOMALY" and f["doc_id"] == doc for f in F),
    "photo_reuse": lambda F, doc: any(f["code"] == "PHOTO_REUSED" for f in F),
    "faculty_double": lambda F, doc: any(f["code"] == "FACULTY_CROSS_CLAIM" for f in F),
    "cross_doc_inconsistency": lambda F, doc: any(f["code"] == "BUA_AFFIDAVIT2" for f in F),
}


@pytest.fixture(scope="module")
def processed():
    config.ensure_dirs()
    pki.ensure_root()
    out = Gen("pytest", 10, 4242, tamper_rate=0.8, gap_rate=0.0).run()
    man = json.loads((out / "manifest.json").read_text())
    con = db.connect(config.DATA / "pytest.db")
    apps = {i["id"]: pipeline.process(con, pipeline.load_dir(out / i["id"]), out / "registry", "pytest", inst_id=i["id"])
            for i in man["institutions"]}
    con.commit()
    return con, man, apps


def test_every_tamper_type_detected(processed):
    con, man, apps = processed
    seen = set()
    for inst in man["institutions"]:
        t = inst["tamper"]
        if not t:
            continue
        aid = apps[inst["id"]]
        F = [dict(r) for r in con.execute("SELECT * FROM findings WHERE app_id=?", (aid,))]
        fn = next(iter(inst["labels"]))
        doc = con.execute("SELECT id FROM documents WHERE app_id=? AND filename=?", (aid, fn)).fetchone()
        assert EXPECT[t](F, doc["id"] if doc else None), f"{t} not detected for {inst['id']}"
        seen.add(t)
    assert seen == set(EXPECT)


def test_audit_chain_intact_after_processing(processed):
    con, _, _ = processed
    assert db.verify_audit(con)["ok"]


def test_documents_stored_encrypted(processed):
    con, _, apps = processed
    doc = con.execute("SELECT id FROM documents LIMIT 1").fetchone()["id"]
    raw = (config.VAULT / f"{doc}.bin").read_bytes()
    assert not raw.startswith(b"%PDF") and b"%%EOF" not in raw


def test_rule_dry_run_and_pdf_export(processed):
    from dossiergraph import rules, viewer
    con, _, apps = processed
    sim = rules.dry_run(con, "FAC_RATIO_UG", "roster.count - ceil(app.dip_students / 25) >= ceil(app.ug_students / 10)")
    assert sim["ok"] and sim["total_apps"] == 10 and sim["after"]["fail"] >= sim["before"]["fail"]
    bad = rules.dry_run(con, "FAC_RATIO_UG", "__import__('os').system('id')")
    assert not bad["ok"]
    aid = next(iter(apps.values()))
    a = dict(con.execute("SELECT * FROM applications WHERE id=?", (aid,)).fetchone())
    docs = [dict(d) for d in con.execute("SELECT * FROM documents WHERE app_id=?", (aid,))]
    finds = [dict(f) for f in con.execute("SELECT * FROM findings WHERE app_id=?", (aid,))]
    pdf = viewer.scrutiny_pdf(a, json.loads(a["report"]), docs, finds, [], "a" * 64, "officer.south", pipeline.NICE)
    assert pdf.startswith(b"%PDF-") and len(pdf) > 1000

