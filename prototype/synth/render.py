"""Render realistic-looking synthetic government documents (PDF / scanned PDF / photos).

All documents are fictitious. Seals are generic rings with text; no real emblem,
logo or signature is reproduced.
"""
from __future__ import annotations

import io
import json
import math
import random

import fitz  # PyMuPDF
import numpy as np
import piexif
import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

W, H = A4
SCAN_DPI = 200
INK_BLUE = HexColor("#1d2f80")
SEAL_COLORS = ["#2a3d9e", "#6b2a9e", "#9e2a3d", "#1f6f5c"]


def _seal(c: canvas.Canvas, x: float, y: float, r: float, lines: list[str], color: str, rot: float):
    c.saveState()
    c.translate(x, y)
    c.rotate(rot)
    col = HexColor(color)
    c.setStrokeColor(col)
    c.setFillColor(col)
    c.setLineWidth(2)
    c.circle(0, 0, r)
    c.setLineWidth(0.8)
    c.circle(0, 0, r - 5)
    c.setFont("Helvetica-Bold", 6.5)
    for i, ln in enumerate(lines[:4]):
        c.drawCentredString(0, 8 - i * 8, ln[:22])
    c.restoreState()


def _signature(c: canvas.Canvas, x: float, y: float, w: float, rnd: random.Random):
    c.saveState()
    c.setStrokeColor(INK_BLUE)
    c.setLineWidth(1.1)
    p = c.beginPath()
    p.moveTo(x, y)
    cx = x
    for _ in range(rnd.randint(4, 7)):
        nx = cx + w / 6
        p.curveTo(cx + rnd.uniform(0, 12), y + rnd.uniform(-14, 18), nx - rnd.uniform(0, 12),
                  y + rnd.uniform(-16, 14), nx, y + rnd.uniform(-5, 5))
        cx = nx
    c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


def render_pdf(spec: dict, seed: int) -> tuple[bytes, dict]:
    """Return (pdf_bytes, layout) where layout gives seal/signature boxes in PDF points."""
    rnd = random.Random(seed)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(spec["title"])
    c.setAuthor(spec["issuer"])
    c.setProducer(spec.get("producer", "e-Office Document Service 4.2"))
    c.setCreator(spec.get("producer", "e-Office Document Service 4.2"))
    layout: dict = {}

    if spec.get("stamp_paper"):
        c.setFillColor(HexColor("#e8f0e0"))
        c.rect(15 * mm, H - 70 * mm, W - 30 * mm, 52 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor("#365b2d"))
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(W / 2, H - 32 * mm, "INDIA NON JUDICIAL")
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(W / 2, H - 41 * mm, spec["stamp_paper"])
        c.setFont("Helvetica", 9)
        c.drawCentredString(W / 2, H - 49 * mm, "e-Stamp Certificate No. " + spec["estamp"])
        top = H - 82 * mm
    else:
        c.setFillColor(HexColor("#1b2a4a"))
        c.setFont("Times-Bold", 15)
        c.drawCentredString(W / 2, H - 25 * mm, spec["issuer"].upper())
        c.setFont("Times-Roman", 10.5)
        c.drawCentredString(W / 2, H - 31 * mm, spec.get("issuer_sub", ""))
        c.setStrokeColor(HexColor("#1b2a4a"))
        c.setLineWidth(1.2)
        c.line(20 * mm, H - 35 * mm, W - 20 * mm, H - 35 * mm)
        top = H - 45 * mm

    c.setFillColor(Color(0.1, 0.1, 0.1))
    c.setFont("Times-Bold", 14)
    c.drawCentredString(W / 2, top, spec["title"].upper())
    y = top - 12 * mm

    if spec.get("intro"):
        c.setFont("Times-Roman", 10.5)
        for ln in spec["intro"]:
            c.drawString(22 * mm, y, ln)
            y -= 6 * mm
        y -= 3 * mm

    for label, value in spec["fields"]:
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(22 * mm, y, f"{label}:")
        c.setFont("Times-Roman", 11)
        c.drawString(82 * mm, y, str(value))
        layout.setdefault("fields", {})[label] = (82 * mm, y)
        y -= 7.5 * mm

    if spec.get("table"):
        y -= 4 * mm
        cols = spec["table"]["columns"]
        widths = spec["table"]["widths"]
        rows = spec["table"]["rows"]
        def header(yy):
            c.setFont("Helvetica-Bold", 9)
            xx = 18 * mm
            for col, wd in zip(cols, widths):
                c.drawString(xx, yy, col)
                xx += wd * mm
            c.line(18 * mm, yy - 2, W - 18 * mm, yy - 2)
            return yy - 6 * mm
        y = header(y)
        c.setFont("Times-Roman", 9.5)
        for row in rows:
            if y < 30 * mm:
                c.showPage()
                y = header(H - 20 * mm)
                c.setFont("Times-Roman", 9.5)
            xx = 18 * mm
            for v, wd in zip(row, widths):
                c.drawString(xx, y, str(v))
                xx += wd * mm
            y -= 5.6 * mm

    if spec.get("body"):
        y -= 4 * mm
        c.setFont("Times-Roman", 10.5)
        for ln in spec["body"]:
            c.drawString(22 * mm, y, ln)
            y -= 6 * mm

    if spec.get("qr"):
        img = qrcode.make(json.dumps(spec["qr"], separators=(",", ":"))).get_image()
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        c.drawImage(ImageReader(bio), W - 58 * mm, 22 * mm, 38 * mm, 38 * mm)
        layout["qr"] = (W - 58 * mm, 22 * mm, 38 * mm, 38 * mm)

    # signature block
    sy = 42 * mm
    sx = 110 * mm if not spec.get("qr") else 70 * mm
    _signature(c, sx, sy + 12 * mm, 50 * mm, rnd)
    layout["signature"] = (sx - 4, sy + 4 * mm, 60 * mm, 22 * mm)
    c.setFont("Times-Roman", 10)
    c.setFillColor(Color(0.1, 0.1, 0.1))
    c.drawString(sx, sy, spec.get("signatory", "Authorised Signatory"))
    c.drawString(sx, sy - 5 * mm, spec.get("signatory_title", ""))
    seal_x, seal_y = (45 * mm, 50 * mm)
    _seal(c, seal_x, seal_y, 17 * mm, spec.get("seal", ["ISSUING", "AUTHORITY"]),
          rnd.choice(SEAL_COLORS), rnd.uniform(-12, 12))
    layout["seal"] = (seal_x - 19 * mm, seal_y - 19 * mm, 38 * mm, 38 * mm)
    c.setFont("Helvetica", 7)
    c.setFillColor(Color(0.4, 0.4, 0.4))
    c.drawString(20 * mm, 12 * mm, spec.get("footer", "This is a system-generated document."))
    c.showPage()
    c.save()
    return buf.getvalue(), layout


# ---------------- scanning ----------------

def rasterize(pdf_bytes: bytes, dpi: int = SCAN_DPI) -> Image.Image:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pix = doc[0].get_pixmap(dpi=dpi)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def scan_effects(img: Image.Image, rnd: random.Random) -> Image.Image:
    img = img.rotate(rnd.uniform(-0.6, 0.6), resample=Image.BICUBIC, fillcolor=(255, 255, 255))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    arr = np.asarray(img).astype(np.float32)
    tint = np.array([250, 247, 238], dtype=np.float32) / 255.0
    arr = arr * tint
    nrng = np.random.default_rng(rnd.randint(0, 2**31))
    arr += nrng.normal(0, 4.0, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def jpeg_bytes(img: Image.Image, q: int = 82) -> bytes:
    bio = io.BytesIO()
    img.save(bio, format="JPEG", quality=q)
    return bio.getvalue()


def image_pdf(jpeg: bytes, producer: str = "ScanSmart Pro 7.1 (TWAIN)") -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=W, height=H)
    page.insert_image(page.rect, stream=jpeg)
    doc.set_metadata({"producer": producer, "creator": producer})
    return doc.tobytes(garbage=3, deflate=True)


def scan(pdf_bytes: bytes, seed: int) -> tuple[bytes, bytes]:
    rnd = random.Random(seed)
    img = scan_effects(rasterize(pdf_bytes), rnd)
    jpg = jpeg_bytes(img)
    return image_pdf(jpg), jpg


def pt_box_to_px(box, dpi: int = SCAN_DPI):
    x, y, w, h = box
    s = dpi / 72.0
    return int(x * s), int((H - y - h) * s), int(w * s), int(h * s)


def crisp_seal_image(size: int, lines: list[str], color: str, rot: float) -> Image.Image:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    m = 6
    d.ellipse((m, m, size - m, size - m), outline=col, width=5)
    d.ellipse((m + 14, m + 14, size - m - 14, size - m - 14), outline=col, width=2)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", int(size / 11))
    except OSError:
        font = ImageFont.load_default()
    for i, ln in enumerate(lines[:4]):
        tw = d.textlength(ln, font=font)
        d.text(((size - tw) / 2, size / 2 - size / 7 + i * size / 9), ln, fill=col, font=font)
    return im.rotate(rot, resample=Image.BICUBIC)


def crisp_signature_image(w: int, h: int, rnd: random.Random) -> Image.Image:
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(40):
        x = 10 + i * (w - 20) / 39
        pts.append((x, h / 2 + math.sin(i / 2.3 + rnd.random()) * h / 4 + rnd.uniform(-6, 6)))
    d.line(pts, fill=(29, 47, 128, 255), width=4, joint="curve")
    return im


def paste_on_scan(jpg: bytes, box_px, overlay: Image.Image, whiten: bool) -> bytes:
    img = Image.open(io.BytesIO(jpg)).convert("RGB")
    x, y, w, h = box_px
    if whiten:
        ImageDraw.Draw(img).rectangle((x, y, x + w, y + h), fill=(250, 247, 238))
    ov = overlay.resize((w, h))
    img.paste(ov, (x, y), ov)
    return jpeg_bytes(img)


# ---------------- campus photos ----------------

def campus_photo(kind: str, rnd: random.Random) -> Image.Image:
    w, h = 960, 640
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    wall = tuple(rnd.randint(170, 235) for _ in range(3))
    floor = tuple(rnd.randint(90, 160) for _ in range(3))
    horizon = rnd.randint(int(h * 0.45), int(h * 0.6))
    d.rectangle((0, 0, w, horizon), fill=wall)
    d.rectangle((0, horizon, w, h), fill=floor)
    if kind == "building":
        sky = (rnd.randint(120, 170), rnd.randint(170, 210), 235)
        d.rectangle((0, 0, w, horizon), fill=sky)
        bx = rnd.randint(60, 200)
        bw = rnd.randint(500, 700)
        d.rectangle((bx, rnd.randint(80, 160), bx + bw, horizon), fill=tuple(rnd.randint(150, 220) for _ in range(3)))
        for r in range(rnd.randint(3, 5)):
            for col in range(rnd.randint(6, 10)):
                wx = bx + 20 + col * (bw - 40) / 10
                wy = 180 + r * 55
                if wy < horizon - 30:
                    d.rectangle((wx, wy, wx + 28, wy + 32), fill=(60, 80, 110))
    else:
        board = (rnd.randint(20, 60), rnd.randint(60, 90), rnd.randint(40, 70)) if kind == "classroom" else (230, 230, 230)
        d.rectangle((w * 0.25, h * 0.12, w * 0.75, h * 0.38), fill=board)
        n_rows = rnd.randint(3, 5)
        for r in range(n_rows):
            yy = horizon + 20 + r * (h - horizon - 30) / n_rows
            scale = 0.6 + r * 0.15
            for col in range(rnd.randint(4, 7)):
                xx = 40 + col * (w - 80) / 6.5
                colr = (rnd.randint(90, 140), rnd.randint(60, 90), rnd.randint(30, 60)) if kind != "lab" else (200, 200, 205)
                d.rectangle((xx, yy, xx + 90 * scale, yy + 22 * scale), fill=colr)
                if kind == "lab":
                    d.rectangle((xx + 20, yy - 30 * scale, xx + 60 * scale, yy), fill=(30, 30, 35))
        for k in range(rnd.randint(1, 3)):
            wx = rnd.randint(20, w - 140)
            d.rectangle((wx, 30, wx + 110, 140), fill=(200, 225, 245))
    # clutter: posters, people, furniture and light patches at random places, so no two campuses look alike
    for _ in range(rnd.randint(18, 34)):
        x0, y0 = rnd.randint(0, w - 40), rnd.randint(0, h - 40)
        x1, y1 = x0 + rnd.randint(20, 220), y0 + rnd.randint(20, 200)
        colr = tuple(rnd.randint(0, 255) for _ in range(3))
        shape = rnd.random()
        if shape < 0.45:
            d.rectangle((x0, y0, x1, y1), fill=colr)
        elif shape < 0.8:
            d.ellipse((x0, y0, x1, y1), fill=colr)
        else:
            d.polygon([(x0, y1), ((x0 + x1) / 2, y0), (x1, y1)], fill=colr)
    if rnd.random() < 0.5:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    arr = np.asarray(im.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32)
    arr += np.random.default_rng(rnd.randint(0, 2**31)).normal(0, 6, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _deg(v: float):
    v = abs(v)
    d = int(v)
    m = int((v - d) * 60)
    s = round(((v - d) * 60 - m) * 60 * 100)
    return ((d, 1), (m, 1), (s, 100))


def photo_jpeg(img: Image.Image, lat: float, lon: float, when: str, q: int = 88) -> bytes:
    exif = {"0th": {piexif.ImageIFD.Make: b"Generic", piexif.ImageIFD.Model: b"Phone Camera"},
            "Exif": {piexif.ExifIFD.DateTimeOriginal: when.encode()},
            "GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S", piexif.GPSIFD.GPSLatitude: _deg(lat),
                    piexif.GPSIFD.GPSLongitudeRef: b"E" if lon >= 0 else b"W", piexif.GPSIFD.GPSLongitude: _deg(lon)}}
    bio = io.BytesIO()
    img.save(bio, format="JPEG", quality=q, exif=piexif.dump(exif))
    return bio.getvalue()
