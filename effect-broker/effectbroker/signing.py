import base64
import hashlib
import hmac


class HmacSigner:
    alg = "hmac-sha256"

    def __init__(self, key):
        self.key = key

    def sign(self, payload: bytes) -> str:
        return hmac.new(self.key, payload, hashlib.sha256).hexdigest()

    def verify(self, payload: bytes, sig: str) -> bool:
        try:
            return hmac.compare_digest(self.sign(payload), sig)
        except Exception:
            return False

    def public_pem(self):
        return None


class Ed25519Signer:
    alg = "ed25519"

    def __init__(self, private_key=None, private_key_pem=None):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        if private_key is not None:
            self._key = private_key
        elif private_key_pem is not None:
            self._key = serialization.load_pem_private_key(private_key_pem, password=None)
        else:
            self._key = Ed25519PrivateKey.generate()
        self._pub = self._key.public_key()

    def sign(self, payload: bytes) -> str:
        return base64.urlsafe_b64encode(self._key.sign(payload)).decode()

    def verify(self, payload: bytes, sig: str) -> bool:
        try:
            self._pub.verify(base64.urlsafe_b64decode(sig.encode()), payload)
            return True
        except Exception:
            return False

    def public_pem(self) -> bytes:
        from cryptography.hazmat.primitives import serialization

        return self._pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )


class Ed25519Verifier:
    alg = "ed25519"

    def __init__(self, public_pem: bytes):
        from cryptography.hazmat.primitives import serialization

        self._pub = serialization.load_pem_public_key(public_pem)

    def sign(self, payload: bytes) -> str:
        raise NotImplementedError("verifier holds no private key")

    def verify(self, payload: bytes, sig: str) -> bool:
        try:
            self._pub.verify(base64.urlsafe_b64decode(sig.encode()), payload)
            return True
        except Exception:
            return False
