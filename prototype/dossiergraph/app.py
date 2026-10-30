"""DossierGraph web app: institution pre-check portal + officer evidence workstation."""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
from starlette.middleware.sessions import SessionMiddleware

from . import access, config, db, pipeline, rules, viewer
from .pipeline import NICE

HERE = Path(__file__).parent
app = FastAPI(title="DossierGraph", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET, same_site="strict", https_only=False,
                   max_age=8 * 3600)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
T = Jinja2Templates(directory=HERE / "templates")

STATUS = {"verified": ("Verified", "ok"), "mismatch": ("Mismatch", "bad"), "expired": ("Expired", "warn"),
          "pending": ("Pending", "info"), "source_unavailable": ("Source unavailable", "muted"),
          "manual_review": ("Manual review", "purple"), "advisory": ("Advisory", "muted")}
ADVERSE = {"show_cause": "Issue show-cause notice", "recommend_rejection": "Recommend rejection (LoR)",
           "refer_fraud": "Refer under Cl. 2.3.5(b) (fraudulent document)"}
NEUTRAL = {"deficiency_letter": "Send deficiency letter (institution can rectify)",
           "clear_to_scrutiny": "Clear to Scrutiny Committee", "refer_evc": "Refer items to Expert Visit Committee"}
GRID = {"deed": (0, 0), "luc": (1, 0), "plan": (2, 0), "roster": (0, 1), "app": (1, 1), "aff": (2, 1),
        "stab": (0, 2), "oc": (1, 2), "fire": (2, 2)}
T.env.globals.update(STATUS=STATUS, NICE=NICE, ADVERSE=ADVERSE, NEUTRAL=NEUTRAL)


def con():
    return db.connect()


def user(request: Request) -> dict:
    u = request.session.get("user")
    if not u:
        raise HTTPException(303, headers={"Location": "/login"})
    return u


def load_app(c, app_id: str, u: dict) -> dict:
    a = c.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
    if not a or not access.can(u, "view_app", dict(a)):
        db.audit(c, u["username"], "access_denied", app_id, {})
        c.commit()
        raise HTTPException(403, "Not permitted by access policy")
    return dict(a)


def redact(text: str, u: dict) -> str:
    """Institutions never learn which other institution matched (privacy-preserving matching)."""
    if u["role"] != "institution" or not text:
        return text
    return re.sub(r"INST-\d{4}(-[0-9A-F]{6})?", "another institution", text)


T.env.filters["fromjson"] = lambda s: json.loads(s) if s else []


@app.exception_handler(HTTPException)
async def http_exc(request: Request, exc: HTTPException):
    if exc.status_code == 303:
        return RedirectResponse(exc.headers["Location"], 303)
    return T.TemplateResponse(request, "error.html", {"u": request.session.get("user"), "code": exc.status_code,
                                                      "msg": exc.detail}, status_code=exc.status_code)


# ---------------- auth ----------------
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return T.TemplateResponse(request, "login.html", {"u": None, "error": None})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    c = con()
    r = c.execute("SELECT * FROM users WHERE username=?", (username.strip().lower(),)).fetchone()
    if not r or not access.check_pw(password, r["pw_hash"]):
        db.audit(c, username, "login_failed", "", {})
        c.commit()
        return T.TemplateResponse(request, "login.html", {"u": None, "error": "Wrong username or password."}, status_code=401)
    request.session["user"] = {k: r[k] for k in ("username", "name", "role", "region", "inst_id")}
    db.audit(c, r["username"], "login", "", {"role": r["role"]})
    c.commit()
    return RedirectResponse("/", 303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", 303)


@app.get("/")
def home(request: Request):
    u = user(request)
    return RedirectResponse("/portal" if u["role"] == "institution" else "/queue", 303)


# ---------------- officer queue ----------------
@app.get("/queue", response_class=HTMLResponse)
def queue(request: Request, status: str = "submitted"):
    u = user(request)
    if u["role"] == "institution":
        raise HTTPException(403, "Officers only")
    c = con()
    apps = [dict(a) for a in c.execute("SELECT * FROM applications WHERE status=? ORDER BY score DESC", (status,))
            if access.can(u, "view_app", dict(a))]
    for a in apps:
        a["factors"] = json.loads(a["factors"])
        cnt = {r["category"]: r["n"] for r in c.execute(
            "SELECT category, COUNT(*) n FROM findings WHERE app_id=? AND state='open' AND severity!='low' GROUP BY category", (a["id"],))}
        a["counts"] = cnt
        a["docs"] = {r["status"]: r["n"] for r in c.execute("SELECT status, COUNT(*) n FROM documents WHERE app_id=? GROUP BY status", (a["id"],))}
        a["escalate"] = json.loads(a["report"]).get("escalate")
    pend = c.execute("SELECT COUNT(*) FROM decisions WHERE state='awaiting_approval'").fetchone()[0]
    return T.TemplateResponse(request, "queue.html", {"u": u, "apps": apps, "status": status, "pending": pend})


# ---------------- application detail ----------------
def app_context(c, a: dict, u: dict):
    report = json.loads(a["report"])
    docs = [dict(d) for d in c.execute("SELECT * FROM documents WHERE app_id=? ORDER BY doc_type", (a["id"],))]
    finds = [dict(f) for f in c.execute("SELECT * FROM findings WHERE app_id=? ORDER BY CASE severity WHEN 'high' THEN 0 "
                                        "WHEN 'medium' THEN 1 WHEN 'low' THEN 2 ELSE 3 END, category", (a["id"],))]
    for f in finds:
        f["title"], f["detail"] = redact(f["title"], u), redact(f["detail"], u)
        f["ev"] = json.loads(f["evidence"] or "[]")
    docmap = {d["id"]: d for d in docs}
    nodes = report["graph"]["nodes"]
    W, H, bw, bh = 640, 330, 150, 52
    pos = {}
    for k, (cx, cy) in GRID.items():
        pos[k] = (20 + cx * 235, 20 + cy * 120)
    gnodes = []
    for k, (x, y) in pos.items():
        n = nodes.get(k)
        gnodes.append({"k": k, "x": x, "y": y, "w": bw, "h": bh, "label": (n or {}).get("label", NICE.get(pipeline.ALIAS.get(k, ""), k)),
                       "status": (n or {}).get("status", "missing"), "doc_id": (n or {}).get("doc_id")})
    gedges = []
    for e in report["graph"]["edges"]:
        if e["a"] in pos and e["b"] in pos:
            (x1, y1), (x2, y2) = pos[e["a"]], pos[e["b"]]
            gedges.append(dict(e, x1=x1 + bw / 2, y1=y1 + bh / 2, x2=x2 + bw / 2, y2=y2 + bh / 2,
                               mx=(x1 + x2) / 2 + bw / 2, my=(y1 + y2) / 2 + bh / 2))
    decisions = [dict(d) for d in c.execute("SELECT * FROM decisions WHERE app_id=? ORDER BY id DESC", (a["id"],))]
    by_doc = {}
    for f in finds:
        by_doc.setdefault(f["doc_id"], []).append(f)
    return dict(a=a, report=report, docs=docs, finds=finds, docmap=docmap, gnodes=gnodes, gedges=gedges, gw=W + 100,
                gh=H + 30, decisions=decisions, by_doc=by_doc, factors=json.loads(a["factors"]))


@app.get("/app/{app_id}", response_class=HTMLResponse)
def app_detail(request: Request, app_id: str):
    u = user(request)
    c = con()
    a = load_app(c, app_id, u)
    db.audit(c, u["username"], "view_application", app_id, {"inst_id": a["inst_id"]})
    c.commit()
    return T.TemplateResponse(request, "app.html", {"u": u, **app_context(c, a, u)})


@app.post("/finding/{fid}/review")
def review(request: Request, fid: int, action: str = Form(...), reason: str = Form("")):
    u = user(request)
    c = con()
    f = c.execute("SELECT * FROM findings WHERE id=?", (fid,)).fetchone()
    a = load_app(c, f["app_id"], u)
    if not access.can(u, "review_finding", a):
        raise HTTPException(403, "Not permitted")
    if action not in ("accepted", "overridden", "escalated", "open"):
        raise HTTPException(400, "bad action")
    if action == "overridden" and len(reason.strip()) < 10:
        raise HTTPException(400, "An override needs a written reason (at least 10 characters).")
    c.execute("UPDATE findings SET state=?, officer=?, reason=? WHERE id=?", (action, u["username"], reason.strip(), fid))
    pipeline.rescore(c, f["app_id"])
    db.audit(c, u["username"], f"finding_{action}", f["app_id"], {"finding": fid, "code": f["code"], "reason": reason.strip()})
    c.commit()
    return RedirectResponse(f"/app/{f['app_id']}#f{fid}", 303)


@app.post("/app/{app_id}/decide")
def decide(request: Request, app_id: str, action: str = Form(...), reason: str = Form("")):
    u = user(request)
    c = con()
    a = load_app(c, app_id, u)
    if not access.can(u, "propose_decision", a):
        raise HTTPException(403, "Not permitted")
    if action not in ADVERSE and action not in NEUTRAL:
        raise HTTPException(400, "Unknown action")
    if len(reason.strip()) < 10:
        raise HTTPException(400, "Every decision needs a written reason (at least 10 characters).")
    now = dt.datetime.now().isoformat(timespec="seconds")
    state = "awaiting_approval" if action in ADVERSE else "recorded"
    c.execute("INSERT INTO decisions(app_id, action, reason, proposed_by, proposed_at, state) VALUES (?,?,?,?,?,?)",
              (app_id, action, reason.strip(), u["username"], now, state))
    db.audit(c, u["username"], "decision_proposed" if action in ADVERSE else "decision_recorded", app_id,
             {"action": action, "reason": reason.strip()})
    c.commit()
    return RedirectResponse(f"/app/{app_id}#decisions", 303)


@app.get("/approvals", response_class=HTMLResponse)
def approvals(request: Request):
    u = user(request)
    if u["role"] == "institution":
        raise HTTPException(403, "Officers only")
    c = con()
    rows = [dict(r) for r in c.execute("SELECT d.*, a.name FROM decisions d JOIN applications a ON a.id=d.app_id ORDER BY d.id DESC")
            if access.can(u, "view_app", dict(c.execute("SELECT * FROM applications WHERE id=?", (r["app_id"],)).fetchone()))]
    return T.TemplateResponse(request, "approvals.html", {"u": u, "rows": rows})


@app.post("/decision/{did}/{verdict}")
def approve(request: Request, did: int, verdict: str):
    u = user(request)
    c = con()
    d = dict(c.execute("SELECT * FROM decisions WHERE id=?", (did,)).fetchone())
    ok, why = access.four_eyes_ok(u, d)
    if not ok:
        db.audit(c, u["username"], "four_eyes_blocked", d["app_id"], {"decision": did})
        c.commit()
        raise HTTPException(403, why)
    if d["state"] != "awaiting_approval" or verdict not in ("approve", "reject"):
        raise HTTPException(400, "Nothing to approve")
    new = "approved" if verdict == "approve" else "returned"
    c.execute("UPDATE decisions SET state=?, approved_by=?, approved_at=? WHERE id=?",
              (new, u["username"], dt.datetime.now().isoformat(timespec="seconds"), did))
    db.audit(c, u["username"], f"decision_{new}", d["app_id"], {"decision": did, "action": d["action"]})
    c.commit()
    return RedirectResponse("/approvals", 303)


# ---------------- documents ----------------
def _doc_and_app(c, doc_id: str, u: dict):
    d = c.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    if not d:
        raise HTTPException(404, "No such document")
    return dict(d), load_app(c, d["app_id"], u)


@app.get("/doc/{doc_id}", response_class=HTMLResponse)
def doc_view(request: Request, doc_id: str):
    u = user(request)
    c = con()
    d, a = _doc_and_app(c, doc_id, u)
    finds = [dict(f) for f in c.execute("SELECT * FROM findings WHERE doc_id=?", (doc_id,))]
    for f in finds:
        f["title"], f["detail"] = redact(f["title"], u), redact(f["detail"], u)
        f["ev"] = json.loads(f["evidence"] or "[]")
    db.audit(c, u["username"], "view_document", a["id"], {"doc": doc_id, "inst_id": a["inst_id"]})
    c.commit()
    return T.TemplateResponse(request, "doc.html", {"u": u, "d": d, "a": a, "finds": finds,
                                                    "fields": json.loads(d["fields"]), "ver": json.loads(d["verification"] or "{}")})


@app.get("/doc/{doc_id}/page/{n}.png")
def doc_page(request: Request, doc_id: str, n: int):
    u = user(request)
    c = con()
    d, a = _doc_and_app(c, doc_id, u)
    boxes = []
    for f in c.execute("SELECT severity, evidence FROM findings WHERE app_id=?", (a["id"],)):
        for e in json.loads(f["evidence"] or "[]"):
            if e.get("doc_id") == doc_id:
                boxes.append(dict(e, severity=f["severity"]))
    png = viewer.render_page(doc_id, n, boxes, u["username"], mime_pdf=d["filename"].lower().endswith(".pdf"))
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


@app.get("/finding/{fid}/evidence/{i}.png")
def evidence(request: Request, fid: int, i: int):
    u = user(request)
    c = con()
    f = dict(c.execute("SELECT * FROM findings WHERE id=?", (fid,)).fetchone())
    load_app(c, f["app_id"], u)
    e = json.loads(f["evidence"])[i]
    d = c.execute("SELECT filename FROM documents WHERE id=?", (e["doc_id"],)).fetchone()
    png = viewer.evidence_crop(e["doc_id"], e["page"], e["bbox"], u["username"], f["severity"], d["filename"].endswith(".pdf"))
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


# ---------------- institution portal ----------------
@app.get("/portal", response_class=HTMLResponse)
def portal(request: Request):
    u = user(request)
    if u["role"] != "institution":
        raise HTTPException(403, "Institution accounts only")
    c = con()
    apps = [dict(a) for a in c.execute("SELECT * FROM applications WHERE inst_id=? ORDER BY created DESC", (u["inst_id"],))]
    for a in apps:
        a["open"] = c.execute("SELECT COUNT(*) FROM findings WHERE app_id=? AND severity IN ('high','medium')", (a["id"],)).fetchone()[0]
    sample = config.SAMPLES / "demo" / u["inst_id"]
    return T.TemplateResponse(request, "portal.html", {"u": u, "apps": apps,
                                                       "sample_files": sorted(p.name for p in sample.iterdir()) if sample.exists() else []})


@app.post("/portal/precheck")
async def precheck(request: Request):
    u = user(request)
    if u["role"] != "institution":
        raise HTTPException(403, "Institution accounts only")
    sample = config.SAMPLES / "demo" / u["inst_id"]
    bundle = pipeline.load_dir(sample) if sample.exists() else {}
    form = await request.form()
    for f in form.getlist("files"):
        if getattr(f, "filename", None):
            data = await f.read()
            if data:
                bundle[Path(f.filename).name] = data
    def run():
        c = con()
        try:
            aid = pipeline.process(c, bundle, config.SAMPLES / "demo" / "registry", u["username"], status="precheck",
                                   inst_id=u["inst_id"], source_set="portal")
            c.commit()
            return aid
        finally:
            c.close()
    aid = await run_in_threadpool(run)
    return RedirectResponse(f"/app/{aid}", 303)


@app.post("/portal/submit/{app_id}")
def submit(request: Request, app_id: str):
    u = user(request)
    c = con()
    a = load_app(c, app_id, u)
    if u["role"] != "institution" or a["status"] != "precheck":
        raise HTTPException(400, "Only a pre-check can be submitted")
    c.execute("UPDATE applications SET status='submitted' WHERE id=?", (app_id,))
    db.audit(c, u["username"], "submit_application", app_id, {})
    c.commit()
    return RedirectResponse("/portal", 303)


@app.get("/portal/access-log", response_class=HTMLResponse)
def access_log(request: Request):
    u = user(request)
    if u["role"] != "institution":
        raise HTTPException(403, "Institution accounts only")
    c = con()
    ids = [r["id"] for r in c.execute("SELECT id FROM applications WHERE inst_id=?", (u["inst_id"],))]
    rows = [dict(r) for r in c.execute(f"SELECT * FROM audit WHERE target IN ({','.join('?' * len(ids))}) ORDER BY seq DESC", ids)] if ids else []
    names = {r["username"]: (r["name"], r["role"]) for r in c.execute("SELECT * FROM users")}
    return T.TemplateResponse(request, "access_log.html", {"u": u, "rows": rows, "names": names})


# ---------------- governance ----------------
@app.get("/audit", response_class=HTMLResponse)
def audit_view(request: Request):
    u = user(request)
    if not access.can(u, "view_audit"):
        raise HTTPException(403, "Not permitted")
    c = con()
    res = db.verify_audit(c)
    rows = [dict(r) for r in c.execute("SELECT * FROM audit ORDER BY seq DESC LIMIT 300")]
    return T.TemplateResponse(request, "audit.html", {"u": u, "res": res, "rows": rows})


@app.get("/rules", response_class=HTMLResponse)
def rules_view(request: Request):
    u = user(request)
    if not access.can(u, "view_rules"):
        raise HTTPException(403, "Not permitted")
    return T.TemplateResponse(request, "rules.html", {"u": u, "pack": rules.load_pack(), "raw": config.RULES_FILE.read_text()})


@app.get("/bench", response_class=HTMLResponse)
def bench_view(request: Request):
    u = user(request)
    p = config.ROOT / "bench" / "results.json"
    res = json.loads(p.read_text()) if p.exists() else None
    return T.TemplateResponse(request, "bench.html", {"u": u, "res": res})
