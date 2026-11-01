"""Classify documents and extract labelled fields with page coordinates.

Digital PDFs are read from their text layer (with font names, used later by
forensics). Scanned PDFs and images go through Tesseract OCR. Every extracted
value keeps its page number and bounding box so findings can point at evidence.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

import cv2
import fitz
import numpy as np
import pytesseract
from PIL import Image
from rapidfuzz import fuzz

DOC_TYPES = {
    "land_deed": ["REGISTERED SALE DEED", "REGISTERED LEASE DEED", "SALE DEED", "LEASE DEED"],
    "land_use_certificate": ["LAND USE CERTIFICATE"],
    "building_plan": ["BUILDING PLAN SANCTION", "BUILDING PLAN APPROVAL"],
    "occupancy_certificate": ["OCCUPANCY CERTIFICATE", "COMPLETION CERTIFICATE"],
    "fire_safety_certificate": ["FIRE SAFETY CERTIFICATE", "FIRE NOC"],
    "structural_stability": ["STRUCTURAL STABILITY CERTIFICATE"],
    "affidavit_2": ["AFFIDAVIT 2", "AFFIDAVIT"],
    "faculty_roster": ["FACULTY ROSTER"],
}
LABELS = {
    "land_deed": {"ref": ["Registration No.", "पंजीकरण संख्या"], "date": ["Date of Registration", "पंजीकरण तिथि"],
                  "owner": ["Purchaser / Lessee", "क्रेता / पट्टाधारक"], "survey": ["Survey No.", "सर्वे नं.", "खसरा संख्या"],
                  "district": ["District", "जिला"], "area_acres": ["Land Area (acres)", "भूमि क्षेत्रफल (एकड़)"],
                  "deed_type": ["Deed Type", "विलेख प्रकार"], "lease_years": ["Lease Term (years)", "पट्टा अवधि (वर्ष)"]},
    "land_use_certificate": {"ref": ["Certificate No.", "प्रमाणपत्र संख्या"], "date": ["Date of Issue", "जारी तिथि"],
                             "applicant": ["Applicant", "आवेदक"], "survey": ["Survey No.", "सर्वे नं.", "खसरा संख्या"],
                             "area_acres": ["Land Area (acres)", "भूमि क्षेत्रफल"], "use": ["Permitted Use", "अनुमत उपयोग"]},
    "building_plan": {"ref": ["Sanction No.", "स्वीकृति संख्या"], "date": ["Date of Sanction", "स्वीकृति तिथि"],
                      "owner": ["Owner", "स्वामी"], "address": ["Site Address", "स्थल का पता"],
                      "survey": ["Survey No.", "सर्वे नं."], "area_sqm": ["Sanctioned Built-up Area (sq m)", "स्वीकृत निर्मित क्षेत्रफल"],
                      "floors": ["Number of Floors", "मंजिलों की संख्या"]},
    "occupancy_certificate": {"ref": ["Certificate No.", "प्रमाणपत्र संख्या"], "date": ["Date of Issue", "जारी तिथि"],
                              "owner": ["Owner", "स्वामी"], "address": ["Site Address", "स्थल का पता"],
                              "sanction_ref": ["Sanction No.", "स्वीकृति संख्या"], "completion": ["Completion Date", "पूर्णता तिथि"],
                              "area_sqm": ["Built-up Area (sq m)", "निर्मित क्षेत्रफल"]},
    "fire_safety_certificate": {"ref": ["Certificate No.", "प्रमाणपत्र संख्या"], "date": ["Date of Issue", "जारी तिथि"],
                                "occupant": ["Occupant", "अधिभोगी"], "address": ["Premises Address", "परिसर का पता"],
                                "occupancy": ["Occupancy Type", "अधिभोग प्रकार"],
                                "valid_from": ["Valid From", "से वैध"], "valid_until": ["Valid Until", "तक वैध"]},
    "structural_stability": {"ref": ["Certificate No.", "प्रमाणपत्र संख्या"], "date": ["Date of Issue", "जारी तिथि"],
                             "address": ["Premises Address", "परिसर का पता"],
                             "completion": ["Building Completed On", "भवन निर्माण पूर्णता"], "finding": ["Finding", "निष्कर्ष"]},
    "affidavit_2": {"deponent": ["Deponent", "शपथकर्ता"], "institution": ["Institution", "संस्थान"],
                    "address": ["Address", "पता"], "declared_area_sqm": ["Declared Built-up Area (sq m)", "घोषित निर्मित क्षेत्रफल"],
                    "date": ["Date of Affidavit", "शपथपत्र तिथि"]},
    "faculty_roster": {"institution": ["Institution", "संस्थान"], "aicte_pid": ["AICTE Permanent ID", "एआईसीटीई स्थायी आईडी"],
                       "total": ["Total Faculty", "कुल संकाय"]},
}
NUMERIC = {"area_acres", "area_sqm", "declared_area_sqm", "lease_years", "total"}
DATES = {"date", "completion", "valid_from", "valid_until"}
OCR_DPI = 200
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


@dataclass
class Line:
    text: str
    bbox: tuple
    page: int
    spans: list = field(default_factory=list)   # [(text, font, bbox)]
    conf: float = 100.0


@dataclass
class Extracted:
    doc_type: str
    mode: str                        # "text-layer" | "ocr" | "image"
    fields: dict
    lines: list
    pages: int
    qr: str | None = None
    images: list = field(default_factory=list)  # embedded JPEG bytes of scanned pages
    faculty_ids: list = field(default_factory=list)
    text: str = ""


def _digital_lines(doc: fitz.Document) -> list[Line]:
    out = []
    for pno, page in enumerate(doc):
        spans = []
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for sp in ln["spans"]:
                    if sp["text"].strip():
                        spans.append((sp["text"], sp["font"], tuple(sp["bbox"])))
        spans.sort(key=lambda s: ((s[2][1] + s[2][3]) / 2, s[2][0]))
        groups: list[list] = []
        for sp in spans:
            yc = (sp[2][1] + sp[2][3]) / 2
            if groups and abs(((groups[-1][0][2][1] + groups[-1][0][2][3]) / 2) - yc) < 3.5:
                groups[-1].append(sp)
            else:
                groups.append([sp])
        for g in groups:
            g.sort(key=lambda s: s[2][0])
            x0 = min(s[2][0] for s in g); y0 = min(s[2][1] for s in g)
            x1 = max(s[2][2] for s in g); y1 = max(s[2][3] for s in g)
            out.append(Line(" ".join(s[0].strip() for s in g), (x0, y0, x1, y1), pno, g))
    return out


def _ocr_lines(img: Image.Image, pno: int, scale: float) -> list[Line]:
    data = pytesseract.image_to_data(img, config="--psm 4", output_type=pytesseract.Output.DICT)
    groups: dict = {}
    for i, word in enumerate(data["text"]):
        if not word.strip():
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        groups.setdefault(key, []).append(i)
    out = []
    for key in sorted(groups, key=lambda k: min(data["top"][i] for i in groups[k])):
        idx = sorted(groups[key], key=lambda i: data["left"][i])
        spans = []
        for i in idx:
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            spans.append((data["text"][i], "ocr", (x * scale, y * scale, (x + w) * scale, (y + h) * scale)))
        confs = [float(data["conf"][i]) for i in idx if float(data["conf"][i]) >= 0]
        x0 = min(s[2][0] for s in spans); y0 = min(s[2][1] for s in spans)
        x1 = max(s[2][2] for s in spans); y1 = max(s[2][3] for s in spans)
        out.append(Line(" ".join(s[0] for s in spans), (x0, y0, x1, y1), pno, spans, sum(confs) / max(len(confs), 1)))
    return out


def classify(lines: list[Line]) -> str:
    head = " ".join(l.text.upper() for l in lines[:14])
    best, score = "unknown", 0
    for t, keys in DOC_TYPES.items():
        for k in keys:
            s = fuzz.partial_ratio(k, head)
            if s > score + (2 if len(k) < 10 else 0):
                best, score = t, s
    return best if score >= 85 else "unknown"


DIGIT_FIX = str.maketrans({"S": "5", "O": "0", "o": "0", "I": "1", "l": "1", "|": "1", "B": "8", "Z": "2", "G": "6"})
LETTER_FIX = {"8": "B", "0": "D", "6": "C"}


def _survey(v: str) -> str:
    s = v.translate(DEVANAGARI_DIGITS).replace(" ", "").upper()
    m = re.match(r"^([0-9SOIBZG|]+)/([0-9SOIBZG|])([806])?[^A-Z]*?([A-E])?[A-Z]*?([A-E])?$", s)
    if not m:
        # Also recover if '/' was read as 'I', 'l', '|' or dropped before [digit][letter]
        m2 = re.match(r"^([0-9SOIBZG]{2,3})[Il|]?([1-9])([A-E8])$", s)
        if m2:
            tail = LETTER_FIX.get(m2.group(3), m2.group(3))
            return f"{m2.group(1).translate(DIGIT_FIX)}/{m2.group(2)}{tail}"
        return s
    letter = m.group(5) or m.group(4) or (LETTER_FIX.get(m.group(3), "") if m.group(3) else "")
    return f"{m.group(1).translate(DIGIT_FIX)}/{m.group(2).translate(DIGIT_FIX)}{letter}"


def _norm(key: str, value: str) -> str:
    v = value.translate(DEVANAGARI_DIGITS).strip().strip(".,;")
    if key == "survey":
        return _survey(v)
    if key in ("ref", "sanction_ref"):
        return re.sub(r"\s+", "", v)
    if key in NUMERIC:
        m = re.search(r"\d[\d,]*(\.\d+)?", v.replace(" ", ""))
        return m.group(0).replace(",", "") if m else v
    if key in DATES:
        m = re.search(r"(\d{1,2})\s*[-/.]\s*(\d{1,2})\s*[-/.]\s*(\d{4})", v)
        return f"{int(m.group(1)):02d}-{int(m.group(2)):02d}-{m.group(3)}" if m else v
    return re.sub(r"\s+", " ", v)


def extract_fields(doc_type: str, lines: list[Line]) -> dict:
    schema = LABELS.get(doc_type, {})
    fields: dict = {}
    for ln in lines:
        if ":" not in ln.text:
            continue
        label, value = ln.text.split(":", 1)
        if not value.strip():
            continue
        best, score = None, 0
        for key, variants in schema.items():
            for v in variants:
                s = fuzz.ratio(label.strip().lower(), v.lower())
                if s > score:
                    best, score = key, s
        if best and score >= 82 and best not in fields:
            # value bbox: spans after the colon
            vspans, seen = [], False
            for sp in ln.spans:
                if seen:
                    vspans.append(sp)
                if ":" in sp[0]:
                    seen = True
                    tail = sp[0].split(":", 1)[1].strip()
                    if tail:
                        vspans.append((tail, sp[1], sp[2]))
            vb = vspans or ln.spans
            bbox = (min(s[2][0] for s in vb), min(s[2][1] for s in vb), max(s[2][2] for s in vb), max(s[2][3] for s in vb))
            fields[best] = {"value": _norm(best, value), "raw": value.strip(), "page": ln.page, "bbox": bbox,
                            "conf": round(ln.conf, 1), "fonts": sorted({s[1] for s in vb})}
    return fields


def decode_qr(doc: fitz.Document) -> str | None:
    det = cv2.QRCodeDetector()
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        txt, pts, _ = det.detectAndDecode(arr[:, :, :3].copy())
        if txt:
            return txt
    return None


def extract_pdf(data: bytes) -> Extracted:
    doc = fitz.open(stream=data, filetype="pdf")
    words = sum(len(p.get_text("words")) for p in doc)
    images = []
    if words >= 15:
        lines, mode = _digital_lines(doc), "text-layer"
    else:
        lines, mode = [], "ocr"
        for pno, page in enumerate(doc):
            imgs = page.get_images(full=True)
            if imgs:
                raw = doc.extract_image(imgs[0][0])["image"]
                images.append(raw)
                img = Image.open(io.BytesIO(raw)).convert("RGB")
            else:
                pix = page.get_pixmap(dpi=OCR_DPI)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            lines += _ocr_lines(img, pno, page.rect.width / img.width)
    dtype = classify(lines)
    ex = Extracted(dtype, mode, extract_fields(dtype, lines), lines, len(doc), images=images,
                   text="\n".join(l.text for l in lines))
    if dtype == "land_use_certificate":
        ex.qr = decode_qr(doc)
    if dtype == "faculty_roster":
        ex.faculty_ids = re.findall(r"\b1-\d{10}\b", ex.text)
    return ex


def extract_image(data: bytes) -> Extracted:
    return Extracted("photo", "image", {}, [], 1, images=[data])
