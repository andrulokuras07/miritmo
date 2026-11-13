"""Contraseñas con PBKDF2-SHA256 + sal y tokens firmados con HMAC-SHA256 (RNF-02)."""

import base64
import hashlib
import hmac
import json
import secrets
import time

ITERACIONES_PBKDF2 = 200_000
DURACION_TOKEN_SEGUNDOS = 7 * 24 * 60 * 60  # 7 días


class TokenInvalido(Exception):
    pass


# ---------------------------------------------------------------- contraseñas

def generar_sal() -> str:
    return secrets.token_hex(16)


def hash_contrasena(contrasena: str, sal: str) -> str:
    derivada = hashlib.pbkdf2_hmac(
        "sha256", contrasena.encode("utf-8"), bytes.fromhex(sal), ITERACIONES_PBKDF2
    )
    return derivada.hex()


def verificar_contrasena(contrasena: str, sal: str, hash_guardado: str) -> bool:
    return hmac.compare_digest(hash_contrasena(contrasena, sal), hash_guardado)


# --------------------------------------------------------------------- tokens

def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _desb64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _firma(carga: str, secreto: str) -> str:
    return _b64(hmac.new(secreto.encode("utf-8"), carga.encode("ascii"), hashlib.sha256).digest())


def crear_token(correo: str, nombre: str, secreto: str, ahora: float | None = None) -> str:
    ahora = time.time() if ahora is None else ahora
    datos = {"sub": correo, "nombre": nombre, "exp": int(ahora) + DURACION_TOKEN_SEGUNDOS}
    carga = _b64(json.dumps(datos, separators=(",", ":")).encode("utf-8"))
    return f"{carga}.{_firma(carga, secreto)}"


def verificar_token(token: str, secreto: str, ahora: float | None = None) -> dict:
    """Devuelve los datos del token o lanza TokenInvalido."""
    ahora = time.time() if ahora is None else ahora
    try:
        carga, firma = token.split(".")
    except (ValueError, AttributeError):
        raise TokenInvalido("Formato de token inválido")
    if not hmac.compare_digest(firma, _firma(carga, secreto)):
        raise TokenInvalido("Firma inválida")
    try:
        datos = json.loads(_desb64(carga))
    except (ValueError, UnicodeDecodeError):
        raise TokenInvalido("Contenido inválido")
    if not isinstance(datos, dict) or not isinstance(datos.get("sub"), str):
        raise TokenInvalido("Contenido inválido")
    if not isinstance(datos.get("exp"), int) or datos["exp"] < ahora:
        raise TokenInvalido("Token expirado")
    return datos
