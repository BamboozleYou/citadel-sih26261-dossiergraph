"""Command line: seed the demo, verify / tamper the audit log.

    python -m dossiergraph.cli seed            # generate demo dossiers, users, process everything
    python -m dossiergraph.cli verify-audit
    python -m dossiergraph.cli tamper-audit    # edits one audit row directly in SQLite (demo of detection)
"""
from __future__ import annotations

import argparse
import json

import yaml

from . import access, config, db, pipeline, pki
from synth.generate import Gen


def seed(n: int, seed_: int):
    config.ensure_dirs()
    pki.ensure_root()
    for p in (config.DB_PATH,):
        p.unlink(missing_ok=True)
    out = Gen("demo", n, seed_, tamper_rate=0.5, gap_rate=0.3).run()
    man = json.loads((out / "manifest.json").read_text())
    cfg = yaml.safe_load((config.ROOT / "seed_users.yaml").read_text())
    with db.session() as con:
        for u in cfg["users"]:
            con.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?)",
                        (u["username"], u["name"], u["role"], u["region"], None, access.hash_pw(u["password"])))
        for inst in man["institutions"]:
            con.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?)",
                        (inst["id"].lower(), inst["name"], "institution", inst["region"], inst["id"],
                         access.hash_pw(cfg["institution_password"])))
        db.audit(con, "system", "seed_users", "", {"count": len(cfg["users"]) + len(man["institutions"])})
        for inst in man["institutions"]:
            aid = pipeline.process(con, pipeline.load_dir(out / inst["id"]), out / "registry", "system:seed",
                                   inst_id=inst["id"], source_set="demo")
            con.commit()
            print(f"  {inst['id']}  {inst['region']:<5}  tamper={inst['tamper'] or '-':<24} gap={inst['gap'] or '-':<20} -> {aid}")
    print(f"Seeded {len(man['institutions'])} dossiers. Start the app: uvicorn dossiergraph.app:app --port 8000")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed")
    s.add_argument("--n", type=int, default=16)
    s.add_argument("--seed", type=int, default=11)
    sub.add_parser("verify-audit")
    sub.add_parser("tamper-audit")
    a = ap.parse_args()
    if a.cmd == "seed":
        seed(a.n, a.seed)
    elif a.cmd == "verify-audit":
        with db.session() as con:
            print(db.verify_audit(con))
    elif a.cmd == "tamper-audit":
        with db.session() as con:
            row = con.execute("SELECT seq, payload FROM audit WHERE action='process_dossier' ORDER BY seq LIMIT 1 OFFSET 2").fetchone()
            payload = json.loads(row["payload"])
            payload["score"] = 0
            con.execute("UPDATE audit SET payload=? WHERE seq=?", (json.dumps(payload, sort_keys=True), row["seq"]))
            print(f"Rewrote audit entry #{row['seq']} (set score to 0) without updating its hash.")
            print(db.verify_audit(con))


if __name__ == "__main__":
    main()
