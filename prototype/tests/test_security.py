import io
import json

import pikepdf
import pytest
from cryptography.exceptions import InvalidTag

from dossiergraph import access, crypto, db, intake, rules


def test_envelope_encryption_roundtrip_and_tamper():
    blob = crypto.encrypt_blob(b"confidential deed", b"DOC-1")
    assert b"confidential" not in blob
    assert crypto.decrypt_blob(blob, b"DOC-1") == b"confidential deed"
    broken = blob[:-1] + bytes([blob[-1] ^ 1])
    with pytest.raises(InvalidTag):
        crypto.decrypt_blob(broken, b"DOC-1")
    with pytest.raises(InvalidTag):
        crypto.decrypt_blob(blob, b"DOC-2")  # bound to its document id


def test_faculty_tokens_are_keyed_and_normalised():
    t1, t2 = crypto.faculty_token("1-1234567890"), crypto.faculty_token(" 1 1234567890 ")
    assert t1 == t2 and "1234567890" not in t1 and len(t1) == 64


def test_audit_chain_detects_edits(tmp_path):
    con = db.connect(tmp_path / "a.db")
    for i in range(5):
        db.audit(con, "officer", "view", f"APP-{i}", {"i": i})
    assert db.verify_audit(con)["ok"]
    con.execute("UPDATE audit SET payload='{\"i\": 99}' WHERE seq=3")
    res = db.verify_audit(con)
    assert not res["ok"] and res["broken_at"] == 3


def test_abac_and_four_eyes():
    south = {"username": "o1", "role": "officer", "region": "South", "inst_id": None}
    inst = {"username": "inst-0001", "role": "institution", "region": "South", "inst_id": "INST-0001"}
    senior = {"username": "s1", "role": "senior_officer", "region": "All", "inst_id": None}
    app_s = {"inst_id": "INST-0001", "region": "South"}
    app_n = {"inst_id": "INST-0002", "region": "North"}
    assert access.can(south, "view_app", app_s) and not access.can(south, "view_app", app_n)
    assert access.can(inst, "view_app", app_s) and not access.can(inst, "view_app", app_n)
    assert not access.can(inst, "propose_decision", app_s)
    assert not access.four_eyes_ok(south, {"proposed_by": "x"})[0]
    assert not access.four_eyes_ok(senior, {"proposed_by": "s1"})[0]
    assert access.four_eyes_ok(senior, {"proposed_by": "o1"})[0]


def test_password_hashing():
    h = access.hash_pw("pw-123")
    assert access.check_pw("pw-123", h) and not access.check_pw("pw-124", h)


def test_intake_rejects_disguised_files_and_flags_javascript():
    assert not intake.inspect(b"MZ\x90\x00 fake", "x.pdf")["ok"]
    pdf = pikepdf.new()
    pdf.add_blank_page()
    pdf.Root.OpenAction = pikepdf.Dictionary(S=pikepdf.Name.JavaScript, JS=pikepdf.String("app.alert(1)"))
    bio = io.BytesIO()
    pdf.save(bio)
    res = intake.inspect(bio.getvalue(), "js.pdf")
    assert res["ok"] and "/OpenAction" in res["active"]


@pytest.mark.parametrize("expr", ["__import__('os').system('id')", "app.__class__", "(lambda: 1)()", "open('x')"])
def test_rule_language_rejects_code(expr):
    with pytest.raises(Exception):
        rules.evaluate(expr, {"app": {}})


def test_rule_language_basics():
    facts = {"plan": {"area_sqm": "1000"}, "aff": {"declared_area_sqm": "1015"}}
    assert rules.evaluate("abs(num(aff.declared_area_sqm) - num(plan.area_sqm)) <= 0.02 * num(plan.area_sqm)", facts)
    facts["aff"]["declared_area_sqm"] = "1300"
    assert not rules.evaluate("abs(num(aff.declared_area_sqm) - num(plan.area_sqm)) <= 0.02 * num(plan.area_sqm)", facts)
    with pytest.raises(rules.Undetermined):
        rules.evaluate("num(missing.x) > 1", facts)


def test_devanagari_and_ocr_survey_normalisation():
    from dossiergraph import extract, verify
    assert extract._norm("survey", "४५२/१B") == "452/1B"
    assert extract._norm("area_acres", "१२.५०") == "12.50"
    assert extract._norm("survey", "452/18") == "452/1B"
    assert verify.ocr_near("1.35", 7.35)
    assert verify.ocr_near("12.48", 12.4)
    assert not verify.ocr_near("412/3B", "89/2A")


def test_orb_photo_scene_verification():
    import random
    from dossiergraph import forensics
    from synth import render
    r1, r2 = random.Random(101), random.Random(202)
    img1 = render.campus_photo("building", r1)
    img2 = render.campus_photo("building", r2)
    b1 = render.jpeg_bytes(img1, q=88)
    b2 = render.jpeg_bytes(img2, q=88)
    w, h = img1.size
    cropped = img1.crop((int(w * 0.015), int(h * 0.015), int(w * 0.985), int(h * 0.985))).resize((w, h))
    b1_reused = render.jpeg_bytes(cropped, q=84)
    assert forensics.photo_same_scene(b1, b1_reused, pdist=7)
    assert not forensics.photo_same_scene(b1, b2, pdist=8)

