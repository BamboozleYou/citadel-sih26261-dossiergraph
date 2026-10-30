"""Paths and tunable settings for the DossierGraph prototype."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DG_DATA", ROOT / "data"))

KEYS = DATA / "keys"            # master key + test PKI (never committed)
VAULT = DATA / "vault"          # encrypted document store
SAMPLES = DATA / "samples"      # generated synthetic dossiers
REGISTRY = DATA / "registry"    # mock issuing-authority registries
DB_PATH = DATA / "dossiergraph.db"

RULES_FILE = Path(__file__).resolve().parent / "rules" / "aph_2024_27.yaml"
AUTHORITIES_FILE = Path(__file__).resolve().parent / "rules" / "competent_authorities.yaml"

# Academic year being applied for (Extension of Approval 2027-28)
ACADEMIC_YEAR_START = dt.date(2027, 7, 1)
TODAY = dt.date(2026, 10, 30)

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}

# Forensics thresholds (tuned on the dev split only, see bench/README section of README.md)
ELA_Z_THRESHOLD = float(os.environ.get("DG_ELA_Z", 9.0))
ELA_MIN_BLOCKS = 3
PHASH_MAX_DISTANCE = 8
GPS_MAX_KM = 1.5
AREA_TOLERANCE = 0.02           # Affidavit 2 vs approved plan
FUZZY_ADDRESS_MIN = 88          # rapidfuzz token_set_ratio

SESSION_SECRET = os.environ.get("DG_SESSION_SECRET", "dev-only-session-secret-change-me")


def ensure_dirs() -> None:
    for p in (DATA, KEYS, VAULT, SAMPLES, REGISTRY):
        p.mkdir(parents=True, exist_ok=True)
