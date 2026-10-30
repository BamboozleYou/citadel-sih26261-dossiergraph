"""Generate synthetic AICTE approval dossiers with labelled forgeries.

    python -m synth.generate --set demo --n 12 --seed 11
    python -m synth.generate --set bench --n 200 --seed 2026

Writes data/samples/<set>/ with one folder per institution, the issuing
authorities' registries (registry/*.json) and manifest.json (ground truth).
Every person, institution, address and document is fictitious.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import math
import random
import shutil
import tempfile
from pathlib import Path

import fitz
from faker import Faker
from PIL import Image
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields as sig_fields
from pyhanko.sign import signers

from dossiergraph import config, pki
from synth import render

STATES = {
    "Karnataka": {"region": "South", "cities": [("Bengaluru", "Bengaluru Urban", 12.97, 77.59, "560"), ("Mysuru", "Mysuru", 12.30, 76.64, "570")]},
    "Tamil Nadu": {"region": "South", "cities": [("Chennai", "Chennai", 13.08, 80.27, "600"), ("Coimbatore", "Coimbatore", 11.02, 76.96, "641")]},
    "Telangana": {"region": "South", "cities": [("Hyderabad", "Hyderabad", 17.38, 78.48, "500")]},
    "Maharashtra": {"region": "West", "cities": [("Pune", "Pune", 18.52, 73.85, "411"), ("Nagpur", "Nagpur", 21.15, 79.09, "440")]},
    "Rajasthan": {"region": "West", "cities": [("Jaipur", "Jaipur", 26.91, 75.79, "302")]},
    "Uttar Pradesh": {"region": "North", "cities": [("Lucknow", "Lucknow", 26.85, 80.95, "226"), ("Noida", "Gautam Buddh Nagar", 28.54, 77.39, "201")]},
}
AVAILABILITY = {
    "land_records": {"Karnataka": "available", "Maharashtra": "available", "Telangana": "available",
                     "Uttar Pradesh": "pending", "Tamil Nadu": "unavailable", "Rajasthan": "unavailable"},
    "fire_services": {"Tamil Nadu": "unavailable"},
}
TAMPERS = ["altered_date", "altered_identifier", "swapped_seal", "pasted_signature",
           "pdf_text_edit", "photo_reuse", "faculty_double", "cross_doc_inconsistency"]
GAPS = ["fire_expired", "faculty_shortfall", "missing_stability", "classroom_shortfall"]
BRANCHES = ["Computer Science and Engineering", "Electronics and Communication Engineering",
            "Mechanical Engineering", "Civil Engineering", "Electrical and Electronics Engineering",
            "Information Technology", "Artificial Intelligence and Data Science"]
DESIG = ["Professor", "Associate Professor", "Assistant Professor", "Assistant Professor", "Assistant Professor"]
QUAL = ["Ph.D.", "M.Tech.", "M.E.", "Ph.D.", "M.Tech."]

fmt = lambda d: d.strftime("%d-%m-%Y")


def sign_pdf(pdf: bytes, slug: str, display: str) -> bytes:
    key, cert = pki.issuer_cert(slug, display)
    _, root = pki.root_paths()
    signer = signers.SimpleSigner.load(str(key), str(cert), ca_chain_files=(str(root),))
    w = IncrementalPdfFileWriter(io.BytesIO(pdf))
    out = signers.sign_pdf(w, signers.PdfSignatureMetadata(field_name="IssuerSignature", reason="Issued electronically",
                                                           location="India"),
                           signer=signer, new_field_spec=sig_fields.SigFieldSpec("IssuerSignature", box=(400, 20, 560, 60)))
    return out.getvalue()


def incremental_edit(pdf: bytes, old: str, new: str) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "d.pdf"
        p.write_bytes(pdf)
        doc = fitz.open(p)
        page = doc[0]
        hits = page.search_for(old)
        if not hits:
            raise ValueError(f"text {old!r} not found")
        r = hits[0]
        page.add_redact_annot(r, fill=(1, 1, 1))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        page.insert_text((r.x0, r.y1 - 2.2), new, fontname="helv", fontsize=10.5, color=(0.1, 0.1, 0.1))
        doc.saveIncr()
        doc.close()
        return p.read_bytes()


class Gen:
    def __init__(self, set_name: str, n: int, seed: int, tamper_rate: float, gap_rate: float):
        self.rnd = random.Random(seed)
        self.fake = Faker("en_IN")
        Faker.seed(seed)
        self.n, self.seed = n, seed
        self.tamper_rate, self.gap_rate = tamper_rate, gap_rate
        self.out = config.SAMPLES / set_name
        if self.out.exists():
            shutil.rmtree(self.out)
        (self.out / "registry").mkdir(parents=True)
        self.registry: dict[str, dict] = {k: {} for k in ("land_records", "town_planning", "municipal_plans",
                                                          "municipal_oc", "fire_services")}
        self.used_fac: set[str] = set()
        self.institutions: list[dict] = []

    # ---------- profile ----------
    def profile(self, i: int) -> dict:
        r, f = self.rnd, self.fake
        state = r.choice(list(STATES))
        city, district, lat, lon, pin = r.choice(STATES[state]["cities"])
        founder = f.last_name()
        kind = r.choice(["Institute of Technology", "College of Engineering", "Institute of Engineering and Technology",
                         "School of Engineering", "Polytechnic and Engineering College"])
        name = f"{founder} {kind}"
        trust = f"{f.last_name()} Educational Trust"
        established = r.randint(1984, 2016)
        programmes = [{"name": "B.Tech. " + b, "level": "UG", "intake": r.choice([60, 60, 120]), "years": 4}
                      for b in r.sample(BRANCHES, r.randint(3, 6))]
        if r.random() < 0.3:
            programmes.append({"name": "Diploma in Mechanical Engineering", "level": "Diploma", "intake": 60, "years": 3})
        ug = sum(p["intake"] * p["years"] for p in programmes if p["level"] == "UG")
        dip = sum(p["intake"] * p["years"] for p in programmes if p["level"] == "Diploma")
        required_fac = math.ceil(ug / 20) + math.ceil(dip / 25)
        divisions = sum(math.ceil(p["intake"] / 60) * p["years"] for p in programmes)
        students = ug + dip
        area = round(students * r.uniform(9.5, 12.5) / 10) * 10
        lease = r.random() < 0.15
        clat, clon = lat + r.uniform(-0.12, 0.12), lon + r.uniform(-0.12, 0.12)
        survey = f"{r.randint(12, 980)}/{r.randint(1, 9)}{r.choice('ABCDE')}"
        addr = f"Survey No. {survey}, {f.street_name()}, {city}, {state} - {pin}{r.randint(100, 999):03d}"
        completion = dt.date(established - 1, r.randint(1, 12), r.randint(1, 28))
        return dict(
            id=f"INST-{i + 1:04d}", name=name, trust=trust, state=state, region=STATES[state]["region"], city=city,
            district=district, address=addr, survey=survey, land_acres=round(r.uniform(5, 25), 2),
            deed_type="Lease" if lease else "Sale", lease_years=r.choice([30, 33, 50, 99]) if lease else None,
            lease_start=dt.date(r.randint(1995, 2015), r.randint(1, 12), 1) if lease else None,
            established=established, completion=completion, programmes=programmes, ug_students=ug,
            dip_students=dip, required_faculty=required_fac, divisions=divisions, area=area,
            classrooms=divisions + r.randint(0, 6), classroom_sqm=r.choice([66, 68, 72, 75, 80]),
            lat=clat, lon=clon, floors=r.randint(3, 6),
            fire_valid_until=dt.date(r.randint(2027, 2029), r.choice([8, 9, 12]), r.choice([15, 30])),
            principal=f"Dr. {f.name()}", chairman=f"{f.name()}",
            aicte_pid=f"1-{r.randint(10**9, 10**10 - 1)}",
        )

    def fac_id(self) -> str:
        while True:
            fid = f"1-{self.rnd.randint(10**9, 10**10 - 1)}"
            if fid not in self.used_fac:
                self.used_fac.add(fid)
                return fid

    # ---------- documents ----------
    def write(self, d: Path, name: str, data: bytes):
        (d / name).write_bytes(data)
        return name

    def reg(self, kind: str, ref: str, rec: dict, data: bytes, state: str):
        rec = dict(rec, state=state, sha256=hashlib.sha256(data).hexdigest(), status="issued")
        self.registry[kind][ref] = rec

    def docs(self, p: dict, d: Path, tamper: str | None, gap: str | None) -> dict:
        r = self.rnd
        seeds = lambda: r.randint(0, 2**31)
        files, labels = {}, {}
        city_slug = p["city"].lower().replace(" ", "_")
        st_slug = p["state"].lower().replace(" ", "_")

        # 1 land deed (scanned)
        deed_date = dt.date(r.randint(1975, p["established"] - 2), r.randint(1, 12), r.randint(1, 28))
        deed_ref = f"SR/{p['district'][:3].upper()}/{deed_date.year}/{r.randint(1000, 99999)}"
        if p["deed_type"] == "Lease":
            # genuine leases are live: remaining term covers the programmes (APH Cl. 6.17(a))
            need = (config.ACADEMIC_YEAR_START.year - deed_date.year) + 6
            p["lease_years"] = max(p["lease_years"], need if need > 33 else 33)
            if p["lease_years"] > 50:
                p["lease_years"] = 99
        deed_fields = [("Registration No.", deed_ref), ("Date of Registration", fmt(deed_date)),
                       ("Vendor / Lessor", self.fake.name()), ("Purchaser / Lessee", p["trust"]),
                       ("Survey No.", p["survey"]), ("Locality", p["city"]), ("District", p["district"]),
                       ("Land Area (acres)", f"{p['land_acres']:.2f}"), ("Deed Type", p["deed_type"]),
                       ("Lease Term (years)", str(p["lease_years"]) if p["lease_years"] else "Not applicable")]
        spec = dict(issuer=f"Office of the Sub-Registrar, {p['district']}",
                    issuer_sub=f"Department of Stamps and Registration, Government of {p['state']}",
                    title=f"Registered {p['deed_type']} Deed", fields=deed_fields,
                    body=["The above property is conveyed free from all encumbrances and registered under",
                          "the Registration Act, 1908. Book I, Volume and page as per office record."],
                    signatory="Sub-Registrar", signatory_title=p["district"], seal=["SUB-REGISTRAR", p["district"][:16].upper(), "REGISTERED"])
        pdf, lay = render.render_pdf(spec, seeds())
        scan_pdf, jpg = render.scan(pdf, seeds())
        self.reg("land_records", deed_ref, {"survey": p["survey"], "owner": p["trust"], "area_acres": p["land_acres"],
                                            "deed_type": p["deed_type"]}, scan_pdf, p["state"])
        if tamper == "pasted_signature":
            box = render.pt_box_to_px(lay["signature"])
            jpg = render.paste_on_scan(jpg, box, render.crisp_signature_image(box[2], box[3], r), whiten=True)
            scan_pdf = render.image_pdf(jpg)
            labels["land_deed.pdf"] = {"type": tamper, "detail": "signature region replaced with a pasted digital signature"}
        files["land_deed.pdf"] = self.write(d, "land_deed.pdf", scan_pdf)

        # 2 land use certificate (QR)
        lu_ref = f"TCP/{p['city'][:3].upper()}/LU/{r.randint(2010, 2020)}/{r.randint(100, 9999)}"
        lu_survey = p["survey"]
        if tamper == "altered_identifier":
            lu_survey = f"{r.randint(12, 980)}/{r.randint(1, 9)}{r.choice('ABCDE')}"  # certificate genuinely issued for another parcel
        lu_fields = lambda sv: [("Certificate No.", lu_ref), ("Date of Issue", fmt(dt.date(r.randint(2010, 2020), 3, 14))),
                                ("Applicant", p["trust"]), ("Survey No.", sv), ("Land Area (acres)", f"{p['land_acres']:.2f}"),
                                ("Permitted Use", "Educational (Institutional)")]
        qr = {"ref": lu_ref, "survey": lu_survey, "area": p["land_acres"], "use": "EDU"}
        lspec = dict(issuer=f"{p['city']} Town and Country Planning Department",
                     issuer_sub=f"Government of {p['state']}", title="Land Use Certificate",
                     fields=lu_fields(lu_survey), qr=qr, signatory="Joint Director (Town Planning)",
                     seal=["TOWN PLANNING", p["city"][:16].upper()], producer="TCP Online Services 2.0")
        fixed_date = lspec["fields"][1]
        pdf, _ = render.render_pdf(lspec, seeds())
        self.reg("town_planning", lu_ref, {"survey": lu_survey, "applicant": p["trust"], "area_acres": p["land_acres"]}, pdf, p["state"])
        if tamper == "altered_identifier":
            lspec["fields"] = [lspec["fields"][0], fixed_date] + lu_fields(p["survey"])[2:]
            pdf, _ = render.render_pdf(lspec, seeds())  # text now shows the institution's survey no., QR still the old one
            labels["land_use_certificate.pdf"] = {"type": tamper, "detail": f"survey no. changed from {lu_survey} to {p['survey']}; QR left unchanged"}
        files["land_use_certificate.pdf"] = self.write(d, "land_use_certificate.pdf", pdf)

        # 3 building plan sanction
        bp_ref = f"{p['city'][:3].upper()}MC/BPS/{p['established'] - 2}/{r.randint(100, 9999)}"
        bp_fields = [("Sanction No.", bp_ref), ("Date of Sanction", fmt(dt.date(p["established"] - 2, r.randint(1, 12), 10))),
                     ("Owner", p["trust"]), ("Site Address", p["address"]), ("Survey No.", p["survey"]),
                     ("Sanctioned Built-up Area (sq m)", f"{p['area']}"), ("Number of Floors", f"G+{p['floors'] - 1}"),
                     ("Building Use", "Educational")]
        bspec = dict(issuer=f"{p['city']} Municipal Corporation", issuer_sub="Building Plan Approval Section",
                     title="Building Plan Sanction", fields=bp_fields, signatory="Executive Engineer (Building)",
                     seal=["MUNICIPAL", "CORPORATION", p["city"][:14].upper()], producer="MuniPlan e-Approval 3.4")
        pdf, _ = render.render_pdf(bspec, seeds())
        self.reg("municipal_plans", bp_ref, {"address": p["address"], "area_sqm": p["area"], "owner": p["trust"]}, pdf, p["state"])
        if tamper == "pdf_text_edit":
            new_area = int(round(p["area"] * r.uniform(1.18, 1.35) / 10) * 10)
            pdf = incremental_edit(pdf, f"{p['area']}", f"{new_area}")
            labels["building_plan.pdf"] = {"type": tamper, "detail": f"sanctioned area edited {p['area']} -> {new_area} via incremental save"}
            p["_plan_area_shown"] = new_area
        files["building_plan.pdf"] = self.write(d, "building_plan.pdf", pdf)

        # 4 occupancy certificate (digitally signed)
        oc_ref = f"{p['city'][:3].upper()}MC/OC/{p['completion'].year}/{r.randint(100, 9999)}"
        ospec = dict(issuer=f"{p['city']} Municipal Corporation", issuer_sub="Occupancy Certificate Section",
                     title="Occupancy Certificate",
                     fields=[("Certificate No.", oc_ref), ("Date of Issue", fmt(p["completion"] + dt.timedelta(days=40))),
                             ("Owner", p["trust"]), ("Site Address", p["address"]), ("Sanction No.", bp_ref),
                             ("Completion Date", fmt(p["completion"])), ("Built-up Area (sq m)", f"{p['area']}")],
                     signatory="Commissioner", seal=["MUNICIPAL", "CORPORATION", p["city"][:14].upper()],
                     footer="Digitally signed document. Verify signature to confirm authenticity.")
        pdf, _ = render.render_pdf(ospec, seeds())
        pdf = sign_pdf(pdf, f"muni_{city_slug}", f"{p['city']} Municipal Corporation (TEST)")
        self.reg("municipal_oc", oc_ref, {"address": p["address"], "completion": fmt(p["completion"]), "area_sqm": p["area"]}, pdf, p["state"])
        files["occupancy_certificate.pdf"] = self.write(d, "occupancy_certificate.pdf", pdf)

        # 5 fire safety certificate (digitally signed)
        fs_ref = f"{p['state'][:2].upper()}FES/{r.randint(2024, 2025)}/{r.randint(10000, 99999)}"
        valid_until = p["fire_valid_until"]
        if gap == "fire_expired" or tamper == "altered_date":
            valid_until = dt.date(2027, 3, 31) if gap == "fire_expired" else dt.date(2026, 12, 31)
        valid_from = valid_until.replace(year=valid_until.year - 3) + dt.timedelta(days=1)
        fields = [("Certificate No.", fs_ref), ("Date of Issue", fmt(valid_from)), ("Occupant", p["name"]),
                  ("Premises Address", p["address"]), ("Occupancy Type", "Educational"),
                  ("Valid From", fmt(valid_from)), ("Valid Until", fmt(valid_until))]
        fspec = dict(issuer=f"{p['state']} Fire and Emergency Services", issuer_sub="Fire Prevention Wing",
                     title="Fire Safety Certificate", fields=fields, signatory="Chief Fire Officer",
                     seal=["FIRE AND", "EMERGENCY", "SERVICES"], footer="Digitally signed document. Verify signature to confirm authenticity.")
        pdf, _ = render.render_pdf(fspec, seeds())
        signed = sign_pdf(pdf, f"fire_{st_slug}", f"{p['state']} Fire and Emergency Services (TEST)")
        self.reg("fire_services", fs_ref, {"address": p["address"], "valid_until": fmt(valid_until), "occupant": p["name"]}, signed, p["state"])
        if tamper == "altered_date":
            forged = dt.date(r.choice([2028, 2029]), 12, 31)
            if r.random() < 0.5:
                signed = incremental_edit(signed, fmt(valid_until), fmt(forged))
                how = "edited after signing (incremental save)"
            else:
                fspec["fields"] = fields[:-1] + [("Valid Until", fmt(forged))]
                signed, _ = render.render_pdf(fspec, seeds())
                how = "re-typed without the issuer's digital signature"
            labels["fire_safety_certificate.pdf"] = {"type": tamper, "detail": f"Valid Until changed {fmt(valid_until)} -> {fmt(forged)}; {how}"}
        files["fire_safety_certificate.pdf"] = self.write(d, "fire_safety_certificate.pdf", signed)

        # 6 structural stability (scanned) — only for buildings older than 30 years
        if (config.TODAY - p["completion"]).days > 30 * 365 and gap != "missing_stability":
            eng = f"Er. {self.fake.name()}"
            insp = dt.date(r.randint(2023, 2025), r.randint(1, 12), r.randint(1, 28))
            sspec = dict(issuer=f"{eng}, Registered Structural Engineer",
                         issuer_sub=f"Licence No. RSE/{p['state'][:2].upper()}/{r.randint(1000, 9999)}",
                         title="Structural Stability Certificate",
                         fields=[("Certificate No.", f"SSC/{r.randint(100, 999)}/{insp.year}"), ("Date of Issue", fmt(insp)),
                                 ("Premises Address", p["address"]), ("Building Completed On", fmt(p["completion"])),
                                 ("Finding", "Structurally safe for human habitation")],
                         signatory=eng, signatory_title="Registered Structural Engineer", seal=["STRUCTURAL", "ENGINEER", "REGD."])
            pdf, _ = render.render_pdf(sspec, seeds())
            files["structural_stability.pdf"] = self.write(d, "structural_stability.pdf", render.scan(pdf, seeds())[0])

        # 7 affidavit 2 (scanned, notarised)
        declared = p["area"]
        p["_declared"] = declared
        if tamper == "cross_doc_inconsistency":
            declared = int(round(p["area"] * r.uniform(1.15, 1.3) / 10) * 10)
            p["_declared"] = declared
            labels["affidavit_2.pdf"] = {"type": tamper, "detail": f"declared area {declared} vs sanctioned {p['area']}"}
        aspec = dict(stamp_paper="ONE HUNDRED RUPEES", estamp=f"IN-{p['state'][:2].upper()}{r.randint(10**11, 10**12 - 1)}",
                     issuer="", title="Affidavit 2",
                     intro=["I, the undersigned, Chairman of the Trust, do hereby solemnly affirm that the built-up",
                            "area of the institution remains unchanged and the details below are true."],
                     fields=[("Deponent", p["chairman"]), ("Institution", p["name"]), ("Address", p["address"]),
                             ("Declared Built-up Area (sq m)", f"{declared}"), ("Date of Affidavit", fmt(dt.date(2026, r.randint(8, 10), r.randint(1, 28))))],
                     signatory=p["chairman"], signatory_title="Deponent", seal=["NOTARY", p["district"][:14].upper(), "GOVT. OF INDIA"])
        pdf, lay = render.render_pdf(aspec, seeds())
        apdf, jpg = render.scan(pdf, seeds())
        if tamper == "swapped_seal":
            box = render.pt_box_to_px(lay["seal"])
            ov = render.crisp_seal_image(box[2], ["NOTARY", "PUBLIC", "ATTESTED"], r.choice(render.SEAL_COLORS), r.uniform(-15, 15))
            apdf = render.image_pdf(render.paste_on_scan(jpg, box, ov, whiten=True))
            labels["affidavit_2.pdf"] = {"type": tamper, "detail": "notary seal replaced with a pasted seal image"}
        files["affidavit_2.pdf"] = self.write(d, "affidavit_2.pdf", apdf)

        # 8 faculty roster
        n_fac = p["required_faculty"] + r.randint(0, 8)
        if gap == "faculty_shortfall":
            n_fac = max(5, p["required_faculty"] - r.randint(4, 12))
        roster = [{"id": self.fac_id(), "name": f"{'Dr. ' if q == 'Ph.D.' else ''}{self.fake.name()}",
                   "designation": dg, "qualification": q, "joined": fmt(dt.date(r.randint(2005, 2025), r.randint(1, 12), 1))}
                  for dg, q in (r.choice(list(zip(DESIG, QUAL))) for _ in range(n_fac))]
        p["roster"] = roster
        files["faculty_roster.pdf"] = None  # written after cross-institution tampering
        p["_files"], p["_labels"] = files, labels

        # campus photos
        when = f"2026:{r.randint(6, 9):02d}:{r.randint(1, 28):02d} 11:{r.randint(10, 59)}:00"
        p["photos"] = []
        for kind in ("building", "classroom", "lab", "library"):
            img = render.campus_photo(kind, r)
            data = render.photo_jpeg(img, p["lat"] + r.uniform(-0.0015, 0.0015), p["lon"] + r.uniform(-0.0015, 0.0015), when)
            fn = f"photo_{kind}.jpg"
            self.write(d, fn, data)
            p["photos"].append(fn)
        return files

    def roster_pdf(self, p: dict, d: Path):
        rows = [[i + 1, f["id"], f["name"][:30], f["designation"], f["qualification"], f["joined"]] for i, f in enumerate(p["roster"])]
        spec = dict(issuer=p["name"], issuer_sub=p["address"][:95], title="Faculty Roster 2027-28",
                    fields=[("Institution", p["name"]), ("AICTE Permanent ID", p["aicte_pid"]), ("Total Faculty", str(len(rows)))],
                    table={"columns": ["S.No", "Faculty ID", "Name", "Designation", "Qualification", "Joined"],
                           "widths": [12, 30, 55, 38, 26, 22], "rows": rows},
                    signatory=p["principal"], signatory_title="Principal", seal=["PRINCIPAL", p["name"][:20].upper()],
                    producer="AICTE Portal Export")
        pdf, _ = render.render_pdf(spec, self.rnd.randint(0, 2**31))
        self.write(d, "faculty_roster.pdf", pdf)

    def application(self, p: dict, d: Path, gap: str | None):
        classrooms = p["classrooms"]
        if gap == "classroom_shortfall":
            classrooms = max(4, p["divisions"] - self.rnd.randint(3, 8))
        app = {"application_type": "Extension of Approval", "academic_year": "2027-28",
               "institution": {"name": p["name"], "aicte_permanent_id": p["aicte_pid"], "trust": p["trust"],
                               "address": p["address"], "state": p["state"], "region": p["region"],
                               "campus_gps": [round(p["lat"], 6), round(p["lon"], 6)], "established": p["established"]},
               "programmes": p["programmes"],
               "infrastructure": {"classrooms": classrooms, "classroom_area_sqm": p["classroom_sqm"],
                                  "declared_built_up_sqm": p["area"]},
               "principal": p["principal"], "documents": sorted(x for x in os_list(d) if x != "application.json")}
        (d / "application.json").write_text(json.dumps(app, indent=2))

    # ---------- main ----------
    def run(self):
        profs, plans = [], []
        n_t = round(self.n * self.tamper_rate)
        tampers = [TAMPERS[i % len(TAMPERS)] for i in range(n_t)] + [None] * (self.n - n_t)
        self.rnd.shuffle(tampers)
        for i in range(self.n):
            p = self.profile(i)
            t = tampers[i]
            g = self.rnd.choice(GAPS) if (t is None and self.rnd.random() < self.gap_rate) else None
            if g == "missing_stability" and (config.TODAY - p["completion"]).days <= 30 * 365:
                g = None
            d = self.out / p["id"]
            d.mkdir()
            self.docs(p, d, t, g)
            profs.append(p)
            plans.append((t, g))

        # cross-institution tampers need a donor
        clean = [q for q, (tq, _) in zip(profs, plans) if tq not in ("photo_reuse", "faculty_double")]
        for p, (t, g) in zip(profs, plans):
            donor = self.rnd.choice([q for q in clean if q is not p])
            d = self.out / p["id"]
            if t == "photo_reuse":
                src = Image.open(self.out / donor["id"] / "photo_classroom.jpg")
                w, h = src.size
                m = self.rnd.uniform(0.0, 0.02)
                crop = src.crop((int(w * m), int(h * m), int(w * (1 - m)), int(h * (1 - m)))).resize((w, h))
                (d / "photo_classroom.jpg").write_bytes(render.photo_jpeg(crop, donor["lat"], donor["lon"], "2026:07:12 10:31:00", q=84))
                p["_labels"]["photo_classroom.jpg"] = {"type": t, "detail": f"classroom photo copied from {donor['id']}", "counterpart": donor["id"]}
            if t == "faculty_double":
                k = self.rnd.randint(3, 8)
                borrowed = self.rnd.sample(donor["roster"], k)
                p["roster"] = p["roster"][:-k] + [dict(b) for b in borrowed]
                p["_labels"]["faculty_roster.pdf"] = {"type": t, "detail": f"{k} faculty IDs also claimed by {donor['id']}", "counterpart": donor["id"]}
        for p, (t, g) in zip(profs, plans):
            d = self.out / p["id"]
            self.roster_pdf(p, d)
            self.application(p, d, g)
            self.institutions.append({"id": p["id"], "name": p["name"], "state": p["state"], "region": p["region"],
                                      "tamper": t, "gap": g, "labels": p["_labels"],
                                      "truth": {"survey": p["survey"], "land_acres": f"{p['land_acres']:.2f}", "owner": p["trust"],
                                                "area_sqm": str(p.get("_plan_area_shown", p["area"])), "address": p["address"],
                                                "declared_area_sqm": str(p["_declared"]), "deponent": p["chairman"],
                                                "faculty": len(p["roster"])}})

        for k, v in self.registry.items():
            (self.out / "registry" / f"{k}.json").write_text(json.dumps(v, indent=1))
        (self.out / "registry" / "availability.json").write_text(json.dumps(AVAILABILITY, indent=1))
        (self.out / "manifest.json").write_text(json.dumps({"seed": self.seed, "n": self.n, "institutions": self.institutions}, indent=1))
        return self.out


def os_list(d: Path):
    return [x.name for x in d.iterdir()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="demo")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--tamper-rate", type=float, default=0.4)
    ap.add_argument("--gap-rate", type=float, default=0.25)
    a = ap.parse_args()
    config.ensure_dirs()
    pki.ensure_root()
    out = Gen(a.set, a.n, a.seed, a.tamper_rate, a.gap_rate).run()
    print("wrote", out)


if __name__ == "__main__":
    main()
