"""Shared helpers for the provider verifier tests: generate a throwaway RSA key,
expose it as a JWKS, and sign JWTs with it. Lets the Apple/Google tests run the
real verifiers against tokens we control instead of mocking them out.
"""
import base64
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt
from jose.constants import ALGORITHMS

KID = "test-key-1"


def rsa_keypair():
    """Return (private_key, jwks_dict) where jwks_dict is the matching public JWKS."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = jwk.construct(private_key.public_key(), ALGORITHMS.RS256).to_dict()
    public_jwk.update({"kid": KID, "use": "sig", "alg": "RS256"})
    # jwk.construct returns bytes for n/e; JWKS JSON needs str.
    for field in ("n", "e"):
        if isinstance(public_jwk.get(field), bytes):
            public_jwk[field] = public_jwk[field].decode()
    return private_key, {"keys": [public_jwk]}


def sign(private_key, claims: dict) -> str:
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return jwt.encode(claims, pem, algorithm=ALGORITHMS.RS256, headers={"kid": KID})


def sign_hs256(secret: str, claims: dict) -> str:
    """Sign a token with HS256 (a non-RS256 algorithm). A verifier that pins
    algorithms to RS256 must reject this regardless of the secret — it stands in
    for the RS256->HS256 algorithm-confusion downgrade. (python-jose refuses to
    HMAC-sign with an actual RSA key, so we use a plain string secret; the point
    under test is that the *algorithm* is rejected.)"""
    return jwt.encode(claims, secret, algorithm=ALGORITHMS.HS256, headers={"kid": KID})


def at_hash(access_token: str) -> str:
    """The OIDC at_hash: base64url of the left half of SHA-256(access_token)."""
    digest = hashlib.sha256(access_token.encode()).digest()
    half = digest[: len(digest) // 2]
    return base64.urlsafe_b64encode(half).rstrip(b"=").decode()
