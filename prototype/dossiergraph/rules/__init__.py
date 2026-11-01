"""Rules-as-code engine for the APH rule pack.

Expressions use a tiny whitelisted language parsed with `ast`; nothing is passed
to Python's eval. Missing facts make a rule "undetermined" (sent to the officer),
never silently pass or fail.
"""
from __future__ import annotations

import ast
import datetime as dt
import math
import operator

import yaml
from rapidfuzz import fuzz

from .. import config


class Undetermined(Exception):
    pass


def _date(s):
    if s is None:
        raise Undetermined("date missing")
    d, m, y = str(s).split("-")
    return dt.date(int(y), int(m), int(d))


def _num(x):
    if x is None:
        raise Undetermined("number missing")
    return float(str(x).replace(",", ""))


def _competent(doc_type, issuer, state):
    if not issuer:
        raise Undetermined("issuer missing")
    cfg = yaml.safe_load(config.AUTHORITIES_FILE.read_text())
    pats = cfg.get(state, cfg["default"]).get(doc_type, [])
    return any(p.lower() in issuer.lower() for p in pats)


FUNCS = {
    "exists": lambda x: x is not None and str(x).strip() != "",
    "num": _num,
    "date": _date,
    "years_between": lambda a, b: (b - a).days / 365.25,
    "fuzzy": lambda a, b: a is not None and b is not None and fuzz.token_set_ratio(str(a), str(b)) >= config.FUZZY_ADDRESS_MIN,
    "same_id": lambda a, b: a is not None and b is not None and str(a).replace(" ", "").upper() == str(b).replace(" ", "").upper(),
    "ceil": math.ceil,
    "abs": abs,
    "competent": _competent,
}
BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
CMP = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le,
       ast.Gt: operator.gt, ast.GtE: operator.ge, ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b}


def evaluate(expr: str, facts: dict):
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.BoolOp):
            if isinstance(n.op, ast.And):
                return all(ev(v) for v in n.values)
            for v in n.values:
                try:
                    if ev(v):
                        return True
                except Undetermined:
                    continue
            return False
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return not ev(n.operand)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        if isinstance(n, ast.BinOp) and type(n.op) in BIN:
            return BIN[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.Compare):
            left = ev(n.left)
            for op, comp in zip(n.ops, n.comparators):
                right = ev(comp)
                if left is None or right is None:
                    raise Undetermined("comparison with missing value")
                if not CMP[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in FUNCS:
            return FUNCS[n.func.id](*[ev(a) for a in n.args])
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
            if n.attr.startswith("_") or n.value.id.startswith("_"):
                raise ValueError("private attributes are not allowed in rules")
            obj = facts.get(n.value.id) or {}
            return obj.get(n.attr)
        if isinstance(n, ast.Name):
            return facts.get(n.id)
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, (ast.List, ast.Tuple)):
            return [ev(e) for e in n.elts]
        raise ValueError(f"disallowed expression element: {ast.dump(n)[:60]}")
    return ev(ast.parse(expr, mode="eval"))


def load_pack():
    return yaml.safe_load(config.RULES_FILE.read_text())


def run(facts: dict) -> list[dict]:
    pack = load_pack()
    results = []
    for r in pack["rules"]:
        res = {k: r.get(k) for k in ("id", "title", "aph_ref", "category", "severity", "on_fail", "on_fail_hi", "evidence", "edge")}
        res["mode"] = r.get("mode", "auto")
        try:
            if r.get("when") and not evaluate(r["when"], facts):
                res["outcome"] = "not_applicable"
                results.append(res)
                continue
        except Undetermined:
            pass
        if res["mode"] == "manual":
            res["outcome"] = "manual"
        else:
            try:
                res["outcome"] = "pass" if evaluate(r["check"], facts) else "fail"
            except Undetermined as e:
                res["outcome"] = "undetermined"
                res["note"] = str(e)
            except Exception as e:  # noqa: BLE001 - surface rule bugs to the officer, never crash a dossier
                res["outcome"] = "undetermined"
                res["note"] = f"rule error: {e}"
        results.append(res)
    return results


REV_DOC = {"land_deed": "deed", "land_use_certificate": "luc", "building_plan": "plan", "occupancy_certificate": "oc",
           "fire_safety_certificate": "fire", "structural_stability": "stab", "affidavit_2": "aff", "faculty_roster": "roster"}


def _reconstruct_facts(con, app_row: dict, rep: dict) -> dict:
    if "rule_facts" in rep:
        facts = dict(rep["rule_facts"])
    else:
        facts = {"app": rep.get("facts", {})}
        for d in con.execute("SELECT doc_type, fields FROM documents WHERE app_id=?", (app_row["id"],)):
            dt_name = d["doc_type"]
            if dt_name in REV_DOC:
                flds = yaml.safe_load(d["fields"]) if d["fields"] else {}
                facts[REV_DOC[dt_name]] = {k: v.get("value") for k, v in flds.items() if isinstance(v, dict)}
    facts["ay_start"] = config.ACADEMIC_YEAR_START
    facts["today"] = config.TODAY
    return facts


def dry_run(con, rule_id: str, new_check: str) -> dict:
    """Test a modified rule expression across all stored dossiers without mutating state."""
    pack = load_pack()
    rule = next((r for r in pack["rules"] if r["id"] == rule_id), None)
    if not rule:
        return {"ok": False, "error": f"Unknown rule ID: {rule_id}"}
    # Validate syntax & AST safety first on an empty facts dict
    try:
        evaluate(new_check, {})
    except Undetermined:
        pass
    except ValueError as e:
        return {"ok": False, "rule": rule, "old_check": rule.get("check", ""), "new_check": new_check, "error": str(e)}
    except SyntaxError as e:
        return {"ok": False, "rule": rule, "old_check": rule.get("check", ""), "new_check": new_check, "error": f"Syntax error: {e.msg}"}
    except Exception:
        pass

    before_counts = {"pass": 0, "fail": 0, "undetermined": 0, "not_applicable": 0}
    after_counts = {"pass": 0, "fail": 0, "undetermined": 0, "not_applicable": 0}
    changes, rows = [], []
    apps = [dict(a) for a in con.execute("SELECT * FROM applications WHERE status='submitted' ORDER BY id")]
    for a in apps:
        rep = yaml.safe_load(a["report"]) if a["report"] else {}
        facts = _reconstruct_facts(con, a, rep)
        old_r = next((x for x in rep.get("rules", []) if x["id"] == rule_id), None)
        old_out = old_r["outcome"] if old_r else "undetermined"
        try:
            if rule.get("when") and not evaluate(rule["when"], facts):
                new_out = "not_applicable"
            else:
                new_out = "pass" if evaluate(new_check, facts) else "fail"
        except Undetermined:
            new_out = "undetermined"
        except ValueError as e:
            return {"ok": False, "rule": rule, "old_check": rule.get("check", ""), "new_check": new_check, "error": str(e)}
        except Exception as e:
            return {"ok": False, "rule": rule, "old_check": rule.get("check", ""), "new_check": new_check, "error": f"Evaluation error: {e}"}

        before_counts[old_out] = before_counts.get(old_out, 0) + 1
        after_counts[new_out] = after_counts.get(new_out, 0) + 1
        item = {"app_id": a["id"], "inst_id": a["inst_id"], "name": a["name"], "region": a["region"],
                "before": old_out, "after": new_out, "changed": old_out != new_out}
        rows.append(item)
        if old_out != new_out:
            changes.append(item)

    return {
        "ok": True, "rule": rule, "old_check": rule.get("check", ""), "new_check": new_check,
        "total_apps": len(apps), "before": before_counts, "after": after_counts,
        "delta_fail": after_counts.get("fail", 0) - before_counts.get("fail", 0),
        "changes": changes, "rows": rows,
    }

