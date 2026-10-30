"""Secure intake: type/size checks, active-content detection, optional ClamAV.

Originals are kept byte-for-byte (encrypted) because rewriting a PDF would
destroy signatures and the revision history forensics relies on. Officers never
open the original: they see server-rendered page images (content disarm by
rasterisation), so embedded JavaScript or launch actions never execute.
"""
from __future__ import annotations

import io
import shutil
import subprocess

import pikepdf

from . import config

MAGIC = {b"%PDF-": "application/pdf", b"\xff\xd8\xff": "image/jpeg", b"\x89PNG": "image/png", b"{": "application/json"}
ACTIVE = ["/JavaScript", "/JS", "/OpenAction", "/Launch", "/EmbeddedFiles", "/RichMedia", "/XFA", "/AA"]


def sniff(data: bytes) -> str | None:
    for sig, mime in MAGIC.items():
        if data[: len(sig)] == sig:
            return mime
    return None


def active_content(data: bytes) -> list[str]:
    found = set()
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            for obj in pdf.objects:
                if isinstance(obj, pikepdf.Dictionary):
                    for k in obj.keys():
                        if k in ACTIVE:
                            found.add(k)
            root = pdf.Root
            for k in ("/OpenAction", "/AA"):
                if k in root:
                    found.add(k)
            if "/Names" in root and "/JavaScript" in root.Names:
                found.add("/JavaScript")
    except pikepdf.PdfError:
        found.add("malformed")
    return sorted(found)


def av_scan(data: bytes) -> str:
    exe = shutil.which("clamdscan") or shutil.which("clamscan")
    if not exe:
        return "not-configured"
    r = subprocess.run([exe, "--no-summary", "-"], input=data, capture_output=True, timeout=60)
    return "clean" if r.returncode == 0 else "infected"


def inspect(data: bytes, filename: str) -> dict:
    res = {"filename": filename, "size": len(data), "mime": sniff(data), "ok": True, "reasons": [], "active": [],
           "antivirus": av_scan(data)}
    if len(data) > config.MAX_UPLOAD_BYTES:
        res["ok"] = False
        res["reasons"].append("file larger than 15 MB")
    if res["mime"] is None:
        res["ok"] = False
        res["reasons"].append("file type not allowed (PDF, JPEG, PNG and application JSON only)")
    if res["antivirus"] == "infected":
        res["ok"] = False
        res["reasons"].append("antivirus flagged the file")
    if res["mime"] == "application/pdf":
        res["active"] = active_content(data)
        if "malformed" in res["active"]:
            res["ok"] = False
            res["reasons"].append("PDF structure is malformed")
    return res
