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
        res = {k: r.get(k) for k in ("id", "title", "aph_ref", "category", "severity", "on_fail", "evidence", "edge")}
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
