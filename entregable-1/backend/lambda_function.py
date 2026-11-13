"""API de MiRitmo en AWS Lambda (URL de función HTTPS, formato de evento 2.0).

Entregable 1:
  POST /cuentas           Crea la cuenta (RF-01)
  POST /sesiones          Inicia sesión y devuelve el token (RF-02)
  PUT  /registros/{fecha} Guarda el día y devuelve la calificación (RF-03, RF-04)

Variables de entorno:
  CLOUDANT_URL, CLOUDANT_APIKEY  Credencial de servicio de Cloudant
  TOKEN_SECRET                   Secreto para firmar tokens (mínimo 32 caracteres)
  ALLOWED_ORIGIN                 Dominio de CloudFront, ej. https://d123.cloudfront.net
  DB_USUARIOS, DB_REGISTROS      Opcionales (por defecto: usuarios, registros)
  TZ_OFFSET_HORAS                Opcional (por defecto -6, hora del centro de México)
  CORS_EN_CODIGO                 Opcional. "1" hace que el código agregue los encabezados CORS
                                 (lo usa servidor_local.py). En AWS no se define: los agrega la
                                 configuración CORS de la URL de función; si los dos los agregan,
                                 Access-Control-Allow-Origin sale duplicado y el navegador lo rechaza.
"""

import base64
import json
import os
import re
import traceback
from datetime import datetime, timezone

from miritmo import seguridad
from miritmo import validacion as v
from miritmo.almacen import CorreoDuplicado, crear_almacen
from miritmo.calificacion import calcular_calificacion

ORIGENES_PERMITIDOS = {o.strip().rstrip("/") for o in os.environ.get("ALLOWED_ORIGIN", "").split(",") if o.strip()}
OFFSET_HORAS = float(os.environ.get("TZ_OFFSET_HORAS", "-6"))
RUTA_REGISTRO = re.compile(r"^/registros/([^/]+)$")

# Hash de relleno para que un correo inexistente tarde lo mismo que una contraseña incorrecta.
_SAL_FALSA = seguridad.generar_sal()
_HASH_FALSO = seguridad.hash_contrasena("contrasena-de-relleno", _SAL_FALSA)

_almacen = None  # se reutiliza entre invocaciones mientras Lambda mantenga el contenedor


def almacen():
    global _almacen
    if _almacen is None:
        _almacen = crear_almacen()
    return _almacen


def secreto_token() -> str:
    secreto = os.environ.get("TOKEN_SECRET", "")
    if len(secreto) < 32:
        raise RuntimeError("TOKEN_SECRET no está configurado o es muy corto (mínimo 32 caracteres)")
    return secreto


class NoAutorizado(Exception):
    pass


class ErrorHttp(Exception):
    def __init__(self, estado: int, mensaje: str):
        super().__init__(mensaje)
        self.estado = estado
        self.mensaje = mensaje


# ------------------------------------------------------------------- utilidades

def ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def leer_cuerpo(evento) -> dict:
    cuerpo = evento.get("body") or ""
    if evento.get("isBase64Encoded"):
        cuerpo = base64.b64decode(cuerpo).decode("utf-8")
    try:
        datos = json.loads(cuerpo) if cuerpo else {}
    except json.JSONDecodeError:
        raise ErrorHttp(400, "El cuerpo de la petición no es JSON válido.")
    if not isinstance(datos, dict):
        raise ErrorHttp(400, "El cuerpo de la petición debe ser un objeto JSON.")
    return datos


def usuario_autenticado(encabezados: dict) -> dict:
    """Valida el encabezado Authorization: Bearer <token>. Responde 401 si falta o es inválido."""
    valor = encabezados.get("authorization", "")
    if not valor.startswith("Bearer "):
        raise NoAutorizado()
    try:
        return seguridad.verificar_token(valor[7:].strip(), secreto_token())
    except seguridad.TokenInvalido:
        raise NoAutorizado()


def respuesta(estado: int, cuerpo, origen=None) -> dict:
    encabezados = {"Content-Type": "application/json; charset=utf-8"}
    if origen and os.environ.get("CORS_EN_CODIGO") == "1":
        encabezados.update({
            "Access-Control-Allow-Origin": origen,
            "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Max-Age": "86400",
            "Vary": "Origin",
        })
    return {
        "statusCode": estado,
        "headers": encabezados,
        "body": "" if cuerpo is None else json.dumps(cuerpo, ensure_ascii=False),
    }


def registro_publico(doc: dict) -> dict:
    """Quita los campos internos de Cloudant antes de enviarlo al navegador."""
    campos = ("fecha", "horas_trabajo", "tareas", "horas_sueno", "energia", "calificacion", "actualizado")
    return {c: doc[c] for c in campos if c in doc}


# ------------------------------------------------------------------------ rutas

def crear_cuenta(evento):
    nombre, correo, contrasena = v.validar_cuenta(leer_cuerpo(evento))
    sal = seguridad.generar_sal()
    doc = {
        "_id": correo,
        "nombre": nombre,
        "correo": correo,
        "hash": seguridad.hash_contrasena(contrasena, sal),
        "sal": sal,
        "creado": ahora_iso(),
    }
    try:
        almacen().crear_usuario(doc)
    except CorreoDuplicado:
        raise v.ErrorValidacion(
            "Ya existe una cuenta con ese correo.", {"correo": "Este correo ya está registrado."}, estado=409
        ) from None
    token = seguridad.crear_token(correo, nombre, secreto_token())
    return 201, {"token": token, "nombre": nombre, "correo": correo}


def iniciar_sesion(evento):
    correo, contrasena = v.validar_inicio_sesion(leer_cuerpo(evento))
    usuario = almacen().obtener_usuario(correo)
    if usuario is None:
        seguridad.verificar_contrasena(contrasena, _SAL_FALSA, _HASH_FALSO)
        raise ErrorHttp(401, "Correo o contraseña incorrectos.")
    if not seguridad.verificar_contrasena(contrasena, usuario["sal"], usuario["hash"]):
        raise ErrorHttp(401, "Correo o contraseña incorrectos.")
    token = seguridad.crear_token(usuario["correo"], usuario["nombre"], secreto_token())
    return 200, {"token": token, "nombre": usuario["nombre"], "correo": usuario["correo"]}


def guardar_registro(evento, encabezados, fecha_txt):
    usuario = usuario_autenticado(encabezados)
    fecha = v.validar_fecha_registro(fecha_txt, v.hoy(OFFSET_HORAS))
    datos = v.validar_datos_dia(leer_cuerpo(evento))
    correo = usuario["sub"]  # siempre del token: un usuario nunca toca registros de otro
    doc = {
        "_id": f"{correo}:{fecha.isoformat()}",
        "usuario": correo,
        "fecha": fecha.isoformat(),
        **datos,
        "calificacion": calcular_calificacion(**datos),
        "actualizado": ahora_iso(),
    }
    almacen().guardar_registro(doc)
    return 200, {"registro": registro_publico(doc)}


def enrutar(metodo, ruta, encabezados, evento):
    if ruta == "/cuentas" and metodo == "POST":
        return crear_cuenta(evento)
    if ruta == "/sesiones" and metodo == "POST":
        return iniciar_sesion(evento)
    coincidencia = RUTA_REGISTRO.match(ruta)
    if coincidencia and metodo == "PUT":
        return guardar_registro(evento, encabezados, coincidencia.group(1))
    raise ErrorHttp(404, "Ruta no encontrada.")


# ---------------------------------------------------------------------- handler

def lambda_handler(evento, contexto=None):
    http = (evento.get("requestContext") or {}).get("http") or {}
    metodo = http.get("method", "GET").upper()
    ruta = (evento.get("rawPath") or "/").rstrip("/") or "/"
    encabezados = {k.lower(): val for k, val in (evento.get("headers") or {}).items()}

    # CORS: solo se aceptan peticiones del navegador que vengan del dominio de CloudFront.
    origen = encabezados.get("origin", "").rstrip("/")
    if origen and origen not in ORIGENES_PERMITIDOS:
        return respuesta(403, {"error": "Origen no permitido."})
    cors = origen or None

    if metodo == "OPTIONS":
        return respuesta(204, None, cors)

    try:
        estado, cuerpo = enrutar(metodo, ruta, encabezados, evento)
        return respuesta(estado, cuerpo, cors)
    except v.ErrorValidacion as e:
        return respuesta(e.estado, {"error": e.mensaje, "campos": e.campos}, cors)
    except NoAutorizado:
        return respuesta(401, {"error": "Tu sesión no es válida o expiró. Inicia sesión de nuevo."}, cors)
    except ErrorHttp as e:
        return respuesta(e.estado, {"error": e.mensaje}, cors)
    except Exception:
        traceback.print_exc()  # queda en CloudWatch Logs
        return respuesta(500, {"error": "Ocurrió un error en el servidor. Intenta de nuevo."}, cors)
