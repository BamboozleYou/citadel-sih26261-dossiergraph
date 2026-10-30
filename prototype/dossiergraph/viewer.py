"""Secure viewing: originals never leave the server. Pages are rasterised, evidence
boxes drawn on top, and every image carries a watermark naming the viewer and time."""
from __future__ import annotations

import datetime as dt
import io

import fitz
from PIL import Image, ImageDraw, ImageFont

from . import crypto

SEV_COLOR = {"high": (192, 57, 43), "medium": (217, 154, 0), "low": (31, 95, 173), "info": (107, 114, 128)}
DPI = 110


def _font(size: int):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _page_image(doc_id: str, page: int, mime_pdf: bool) -> tuple[Image.Image, float]:
    data = crypto.load(doc_id)
    if not mime_pdf:
        return Image.open(io.BytesIO(data)).convert("RGB"), 1.0
    doc = fitz.open(stream=data, filetype="pdf")
    page = max(0, min(page, len(doc) - 1))
    pix = doc[page].get_pixmap(dpi=DPI)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples), DPI / 72.0


def watermark(img: Image.Image, viewer: str) -> Image.Image:
    stamp = f"{viewer} · {dt.datetime.now():%d-%m-%Y %H:%M} · CONFIDENTIAL · DossierGraph"
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = _font(max(14, img.width // 45))
    tw = d.textlength(stamp, font=f)
    tile = Image.new("RGBA", (int(tw) + 60, f.size + 20), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((10, 5), stamp, font=f, fill=(27, 42, 74, 38))
    tile = tile.rotate(28, expand=True)
    for y in range(-tile.height, img.height + tile.height, int(tile.height * 0.9)):
        for x in range(-tile.width // 2, img.width, tile.width):
            layer.alpha_composite(tile, (max(0, x + (y // 7) % 200), max(0, y)))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def render_page(doc_id: str, page: int, boxes: list[dict], viewer: str, mime_pdf: bool = True) -> bytes:
    img, s = _page_image(doc_id, page, mime_pdf)
    d = ImageDraw.Draw(img, "RGBA")
    for b in boxes:
        if b.get("page", 0) != page or not b.get("bbox"):
            continue
        x0, y0, x1, y1 = [v * s for v in b["bbox"]]
        col = SEV_COLOR.get(b.get("severity", "medium"), (217, 154, 0))
        d.rectangle((x0 - 4, y0 - 3, x1 + 4, y1 + 3), outline=col + (255,), width=3, fill=col + (40,))
    img = watermark(img, viewer)
    bio = io.BytesIO()
    img.save(bio, format="PNG", optimize=True)
    return bio.getvalue()


def evidence_crop(doc_id: str, page: int, bbox, viewer: str, severity: str, mime_pdf: bool = True) -> bytes:
    img, s = _page_image(doc_id, page, mime_pdf)
    x0, y0, x1, y1 = [v * s for v in bbox]
    box = (int(max(0, x0 - 230 * s)), int(max(0, y0 - 22 * s)), int(min(img.width, x1 + 60 * s)), int(min(img.height, y1 + 22 * s)))
    d = ImageDraw.Draw(img, "RGBA")
    col = SEV_COLOR.get(severity, (217, 154, 0))
    d.rectangle((x0 - 4, y0 - 3, x1 + 4, y1 + 3), outline=col + (255,), width=3, fill=col + (35,))
    crop = watermark(img.crop(box), viewer)
    bio = io.BytesIO()
    crop.save(bio, format="PNG")
    return bio.getvalue()
