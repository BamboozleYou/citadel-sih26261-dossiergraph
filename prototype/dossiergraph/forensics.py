"""Forensic indicators. Always advisory: they point a human at something to check.

* PDF structure: incremental revisions beyond those explained by signatures,
  values set in a font the rest of the document does not use for values.
* Scans: noise-floor analysis (pasted digital elements lack scanner noise),
  supported by error-level analysis (ELA).
* Photos: perceptual-hash reuse across institutions, EXIF GPS vs campus location.
"""
from __future__ import annotations

import io
import math
from collections import Counter

import cv2
import imagehash
import numpy as np
import piexif
from PIL import Image

from . import config

BLOCK = 24


def pdf_structure(data: bytes, n_signatures: int, fields: dict) -> list[dict]:
    out = []
    revisions = data.count(b"%%EOF")
    expected = 1 + n_signatures
    if revisions > expected:
        out.append(dict(code="PDF_INCREMENTAL_EDIT", category="authenticity", severity="medium",
                        title="PDF was modified after it was produced",
                        detail=f"{revisions} revisions found; {expected} expected for a document with "
                               f"{n_signatures} signature(s). Later revisions can overwrite visible text.",
                        suggestion="Compare with the issuer's copy."))
    fonts = Counter(f for v in fields.values() for f in v.get("fonts", []) if f != "ocr")
    if len(fonts) > 1:
        main = fonts.most_common(1)[0][0]
        for k, v in fields.items():
            odd = [f for f in v.get("fonts", []) if f not in (main, "ocr")]
            if odd:
                out.append(dict(code="FONT_INCONSISTENT", category="authenticity", severity="medium", field=k,
                                title=f"'{k}' is set in a different font",
                                detail=f"Value uses {', '.join(odd)}; other values use {main}. Typical of text pasted over the original.",
                                suggestion="Check this value against the issuer record."))
    return out


def _gray(jpeg: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(jpeg)).convert("L")).astype(np.float32)


def noise_map(g: np.ndarray) -> np.ndarray:
    resid = g - cv2.medianBlur(g.astype(np.uint8), 3).astype(np.float32)
    h, w = g.shape
    hb, wb = h // BLOCK, w // BLOCK
    r = resid[: hb * BLOCK, : wb * BLOCK].reshape(hb, BLOCK, wb, BLOCK)
    return r.std(axis=(1, 3))


def ela_map(jpeg: bytes, q: int = 90) -> np.ndarray:
    im = Image.open(io.BytesIO(jpeg)).convert("RGB")
    bio = io.BytesIO()
    im.save(bio, format="JPEG", quality=q)
    re = Image.open(io.BytesIO(bio.getvalue())).convert("RGB")
    diff = np.abs(np.asarray(im, dtype=np.float32) - np.asarray(re, dtype=np.float32)).mean(axis=2)
    h, w = diff.shape
    hb, wb = h // BLOCK, w // BLOCK
    return diff[: hb * BLOCK, : wb * BLOCK].reshape(hb, BLOCK, wb, BLOCK).mean(axis=(1, 3))


def _clusters(mask: np.ndarray):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    return [(stats[i], i) for i in range(1, n)], lab


def scan_forensics(jpeg: bytes, page_w_pt: float) -> list[dict]:
    """Find regions that lack the scanner's noise floor (pasted digital content)."""
    g = _gray(jpeg)
    nm = noise_map(g)
    med = float(np.median(nm))
    if med <= 0:
        return []
    low = nm < 0.33 * med
    # ignore the outer frame (scanner bed edges)
    low[:2, :] = low[-2:, :] = False
    low[:, :2] = low[:, -2:] = False
    comps, _ = _clusters(low)
    ela = ela_map(jpeg)
    ela_z = (ela - np.median(ela)) / (np.median(np.abs(ela - np.median(ela))) + 1e-6)
    out = []
    scale = page_w_pt / g.shape[1]
    for st, _ in comps:
        x, y, w, h, area = st
        if area < config.ELA_MIN_BLOCKS + 1:
            continue
        region_ela = float(ela_z[y:y + h, x:x + w].max()) if h and w else 0.0
        bbox = (x * BLOCK * scale, y * BLOCK * scale, (x + w) * BLOCK * scale, (y + h) * BLOCK * scale)
        out.append(dict(code="SCAN_NOISE_ANOMALY", category="authenticity", severity="medium", bbox=bbox,
                        title="Region lacks the scanner's noise pattern",
                        detail=f"{int(area)} blocks ({int(w * BLOCK * scale)}x{int(h * BLOCK * scale)} pt) are noise-free while the rest "
                               f"of the scan is not (noise floor {med:.1f}); ELA peak z={region_ela:.1f}. "
                               "Typical of a seal or signature pasted digitally.",
                        suggestion="Compare the seal/signature with the original; verify with the notary or registrar."))
    return out[:3]


def phash(data: bytes) -> str:
    return str(imagehash.phash(Image.open(io.BytesIO(data))))


def phash_distance(a: str, b: str) -> int:
    return imagehash.hex_to_hash(a) - imagehash.hex_to_hash(b)


def photo_same_scene(a_bytes: bytes, b_bytes: bytes, pdist: int = 8) -> bool:
    """Confirm perceptual-hash matches using ORB spatial keypoint alignment and 256-bit dHash."""
    if pdist <= 2:
        return True
    try:
        ima = Image.open(io.BytesIO(a_bytes)).convert("RGB")
        imb = Image.open(io.BytesIO(b_bytes)).convert("RGB")
        # 256-bit difference hash (16x16) catches fine spatial layout that 64-bit pHash blurs
        d16 = imagehash.dhash(ima, hash_size=16) - imagehash.dhash(imb, hash_size=16)
        if d16 > 48:
            return False
        ga = np.asarray(ima.convert("L"), dtype=np.uint8)
        gb = np.asarray(imb.convert("L"), dtype=np.uint8)
        if ga.shape != gb.shape:
            gb = cv2.resize(gb, (ga.shape[1], ga.shape[0]))
        orb = cv2.ORB_create(nfeatures=500)
        ka, da = orb.detectAndCompute(ga, None)
        kb, db = orb.detectAndCompute(gb, None)
        if da is None or db is None or len(ka) < 12 or len(kb) < 12:
            return d16 <= 28
        bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        raw = bf.knnMatch(da, db, k=2)
        spatially_close = 0
        max_shift = 0.04 * max(ga.shape)
        for pair in raw:
            if len(pair) == 2:
                m, n = pair
                if m.distance < 0.75 * n.distance:
                    x1, y1 = ka[m.queryIdx].pt
                    x2, y2 = kb[m.trainIdx].pt
                    if math.hypot(x1 - x2, y1 - y2) <= max_shift:
                        spatially_close += 1
        return spatially_close >= 12
    except Exception:
        return pdist <= 6


def exif_gps(data: bytes):
    try:
        ex = piexif.load(data)
        g = ex.get("GPS", {})
        def deg(v, ref):
            d = v[0][0] / v[0][1] + v[1][0] / v[1][1] / 60 + v[2][0] / v[2][1] / 3600
            return -d if ref in (b"S", b"W") else d
        return deg(g[piexif.GPSIFD.GPSLatitude], g[piexif.GPSIFD.GPSLatitudeRef]), \
            deg(g[piexif.GPSIFD.GPSLongitude], g[piexif.GPSIFD.GPSLongitudeRef])
    except Exception:
        return None


def haversine_km(a, b) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))
