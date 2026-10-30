"""Benchmark: run the full pipeline on a labelled synthetic set and score it.

    python -m bench.run_benchmark --n 200 --seed 2026

Metrics
* recall per tamper type (was the forged document / dossier flagged by the right family of checks?)
* precision of authenticity and consistency flags
* false flags per genuine application (authenticity + consistency findings on untouched dossiers)
* compliance-gap recall and false compliance failures
* field extraction accuracy (text layer vs OCR) against ground truth
* verification status mix and processing time per application

Thresholds were fixed before this run using different generation seeds (5, 9).
Results on synthetic data overstate real-world performance; see README.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

from dossiergraph import config, db, pipeline
from synth.generate import Gen
from dossiergraph import pki

DOC_TAMPERS = {"altered_date", "altered_identifier", "swapped_seal", "pasted_signature", "pdf_text_edit"}
GAP_RULES = {"fire_expired": {"BLDG_FIRE"}, "faculty_shortfall": {"FAC_RATIO_UG", "FAC_RATIO_DIP"},
             "missing_stability": {"BLDG_STRUCT_STAB"}, "classroom_shortfall": {"BUA_CLASSROOMS"}}
FIELD_TRUTH = {"land_deed": ["survey", "land_acres:area_acres", "owner"], "land_use_certificate": ["owner:applicant", "land_acres:area_acres"],
               "building_plan": ["survey", "area_sqm", "address"], "occupancy_certificate": ["address"],
               "fire_safety_certificate": ["address"], "affidavit_2": ["declared_area_sqm", "deponent", "address"],
               "structural_stability": ["address"]}


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="bench")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--regen", action="store_true")
    a = ap.parse_args()
    config.ensure_dirs()
    pki.ensure_root()
    S = config.SAMPLES / a.set
    if a.regen or not (S / "manifest.json").exists():
        t = time.time()
        Gen(a.set, a.n, a.seed, tamper_rate=0.4, gap_rate=0.25).run()
        print(f"generated {a.n} dossiers in {time.time() - t:.0f}s")
    man = json.loads((S / "manifest.json").read_text())
    dbp = config.DATA / f"{a.set}.db"
    dbp.unlink(missing_ok=True)
    times, app_of = [], {}
    with db.session(dbp) as con:
        for inst in man["institutions"]:
            t = time.time()
            app_of[inst["id"]] = pipeline.process(con, pipeline.load_dir(S / inst["id"]), S / "registry", "benchmark",
                                                  inst_id=inst["id"], source_set=a.set)
            times.append(time.time() - t)
            con.commit()
        docs = [dict(r) for r in con.execute("SELECT * FROM documents")]
        finds = [dict(r) for r in con.execute("SELECT * FROM findings")]
        apps = {r["id"]: dict(r) for r in con.execute("SELECT * FROM applications")}

    by_app = defaultdict(list)
    for f in finds:
        by_app[f["app_id"]].append(f)
    doc_by_app_file = {(d["app_id"], d["filename"]): d for d in docs}
    counterparts = {l["counterpart"] for i in man["institutions"] for l in i["labels"].values() if l.get("counterpart")}

    # ---- recall per tamper type ----
    recall = defaultdict(lambda: [0, 0])
    for inst in man["institutions"]:
        t = inst["tamper"]
        if not t:
            continue
        aid = app_of[inst["id"]]
        F = by_app[aid]
        fn = next(iter(inst["labels"]))
        doc = doc_by_app_file.get((aid, fn))
        if t in DOC_TAMPERS:
            hit = any(f["doc_id"] == doc["id"] and f["category"] == "authenticity" for f in F)
        elif t == "photo_reuse":
            hit = any(f["doc_id"] == doc["id"] and f["code"] == "PHOTO_REUSED" for f in F)
        elif t == "faculty_double":
            hit = any(f["code"] in ("FACULTY_CROSS_CLAIM", "FAC_ID_UPDATE") for f in F)
        else:
            hit = any(f["code"] == "BUA_AFFIDAVIT2" and f["category"] == "consistency" for f in F)
        recall[t][0] += hit
        recall[t][1] += 1

    # ---- precision & false flags ----
    tampered_docs = {(app_of[i["id"]], fn) for i in man["institutions"] for fn in i["labels"]}
    tampered_apps = {app_of[i["id"]] for i in man["institutions"] if i["tamper"]}
    cp_apps = {app_of[c] for c in counterparts}
    doc_file = {d["id"]: d["filename"] for d in docs}
    auth = [f for f in finds if f["category"] == "authenticity"]
    auth_tp = sum(1 for f in auth if (f["app_id"], doc_file.get(f["doc_id"])) in tampered_docs or f["app_id"] in cp_apps or
                  (f["app_id"] in tampered_apps and f["code"] == "PHOTO_GPS"))
    cons = [f for f in finds if f["category"] == "consistency"]
    cons_tp = sum(1 for f in cons if f["app_id"] in tampered_apps or f["app_id"] in cp_apps)
    genuine = [app_of[i["id"]] for i in man["institutions"] if not i["tamper"] and i["id"] not in counterparts]
    ff = [sum(1 for f in by_app[a] if f["category"] in ("authenticity", "consistency")) for a in genuine]
    ff_codes = Counter(f["code"] for a in genuine for f in by_app[a] if f["category"] in ("authenticity", "consistency"))

    # ---- compliance gaps ----
    gap_hit, gap_n, false_comp, comp_n = 0, 0, Counter(), 0
    for inst in man["institutions"]:
        aid = app_of[inst["id"]]
        failed = {f["rule_id"] for f in by_app[aid] if f["rule_id"] and f["category"] in ("compliance", "consistency") and f["severity"] != "low"}
        if inst["gap"]:
            gap_n += 1
            gap_hit += bool(failed & GAP_RULES[inst["gap"]])
        elif not inst["tamper"] and inst["id"] not in counterparts:
            comp_n += 1
            for r in failed:
                false_comp[r] += 1

    # ---- extraction accuracy ----
    acc = defaultdict(lambda: [0, 0])
    truth = {app_of[i["id"]]: i["truth"] for i in man["institutions"]}
    for d in docs:
        tr = truth.get(d["app_id"], {})
        flds = json.loads(d["fields"])
        if (d["app_id"], d["filename"]) in tampered_docs:
            continue
        for spec in FIELD_TRUTH.get(d["doc_type"], []):
            tk, fk = (spec.split(":") + [spec])[:2]
            if tk not in tr:
                continue
            got = flds.get(fk, {}).get("value")
            ok = got is not None and str(got).replace(" ", "").lower() == str(tr[tk]).replace(" ", "").lower()
            acc[d["mode"]][0] += ok
            acc[d["mode"]][1] += 1

    status_mix = Counter((d["doc_type"], d["status"]) for d in docs)
    res = {
        "set": a.set, "seed": man["seed"], "applications": len(apps), "documents": len(docs),
        "tampered_applications": len(tampered_apps), "genuine_applications": len(genuine),
        "recall_by_tamper": {k: {"detected": v[0], "total": v[1], "recall_pct": pct(*v)} for k, v in sorted(recall.items())},
        "overall_tamper_recall_pct": pct(sum(v[0] for v in recall.values()), sum(v[1] for v in recall.values())),
        "authenticity_flag_precision_pct": pct(auth_tp, len(auth)), "authenticity_flags": len(auth),
        "consistency_flag_precision_pct": pct(cons_tp, len(cons)), "consistency_flags": len(cons),
        "false_flags_per_genuine_application": round(statistics.mean(ff), 3) if ff else None,
        "genuine_applications_with_any_false_flag_pct": pct(sum(1 for x in ff if x), len(ff)),
        "false_flag_codes": dict(ff_codes),
        "compliance_gap_recall_pct": pct(gap_hit, gap_n), "compliance_gaps": gap_n,
        "false_compliance_failures_on_clean_apps": dict(false_comp), "clean_apps": comp_n,
        "extraction_accuracy_pct": {m: {"correct": v[0], "total": v[1], "accuracy_pct": pct(*v)} for m, v in acc.items()},
        "status_mix": {f"{k[0]}:{k[1]}": v for k, v in sorted(status_mix.items())},
        "seconds_per_application": {"mean": round(statistics.mean(times), 2), "p95": round(sorted(times)[int(0.95 * len(times)) - 1], 2)},
    }
    out = Path(__file__).parent / "results.json"
    out.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
