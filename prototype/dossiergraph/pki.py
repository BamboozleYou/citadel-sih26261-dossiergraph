"""Test PKI: a throwaway root CA plus one signing certificate per issuing authority.

Real issuers sign with CCA-licensed DSCs. For the prototype we mint our own
"TEST ROOT" so signed PDFs can be produced and validated end to end offline.
Nothing here is a real certificate.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from . import config

PKI_DIR = config.KEYS / "pki"


def _name(cn: str, org: str) -> x509.Name:
    return x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
        x509.NameAttribute(NameOID.COMMON_NAME, cn),
    ])


def _write(path: Path, key, cert) -> None:
    path.with_suffix(".key.pem").write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    path.with_suffix(".crt.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def root_paths() -> tuple[Path, Path]:
    base = PKI_DIR / "test_root"
    return base.with_suffix(".key.pem"), base.with_suffix(".crt.pem")


def ensure_root():
    PKI_DIR.mkdir(parents=True, exist_ok=True)
    kp, cp = root_paths()
    if cp.exists():
        key = serialization.load_pem_private_key(kp.read_bytes(), None)
        return key, x509.load_pem_x509_certificate(cp.read_bytes())
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = _name("DossierGraph TEST ROOT CA (not a real CA)", "DossierGraph Prototype")
    now = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now)
            .not_valid_after(now + dt.timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True, crl_sign=True,
                                         content_commitment=False, key_encipherment=False, data_encipherment=False,
                                         key_agreement=False, encipher_only=False, decipher_only=False), critical=True)
            .sign(key, hashes.SHA256()))
    _write(PKI_DIR / "test_root", key, cert)
    return key, cert


def issuer_cert(slug: str, display: str):
    """Return (key_path, cert_path) for an issuer, creating it if needed."""
    base = PKI_DIR / slug
    if base.with_suffix(".crt.pem").exists():
        return base.with_suffix(".key.pem"), base.with_suffix(".crt.pem")
    root_key, root_cert = ensure_root()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(_name(display, "Government of India (TEST)"))
            .issuer_name(root_cert.subject).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now)
            .not_valid_after(now + dt.timedelta(days=1825))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=True, key_cert_sign=False,
                                         crl_sign=False, key_encipherment=False, data_encipherment=False,
                                         key_agreement=False, encipher_only=False, decipher_only=False), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.EMAIL_PROTECTION]), critical=False)
            .sign(root_key, hashes.SHA256()))
    _write(base, key, cert)
    return base.with_suffix(".key.pem"), base.with_suffix(".crt.pem")
