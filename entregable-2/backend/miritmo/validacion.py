"""Validación de datos de entrada con mensajes claros en español."""

import re
from datetime import date, datetime, timedelta, timezone

PATRON_CORREO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
DIAS_ANTERIORES_PERMITIDOS = 6
MAX_DIAS_CONSULTA = 31


class ErrorValidacion(Exception):
    def __init__(self, mensaje: str, campos: dict | None = None, estado: int = 400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campos = campos or {}
        self.estado = estado


def hoy(offset_horas: float) -> date:
    """Fecha de hoy en la zona horaria del producto (México centro = UTC-6)."""
    return (datetime.now(timezone.utc) + timedelta(hours=offset_horas)).date()


# --------------------------------------------------------------------- cuenta

def normalizar_correo(valor) -> str:
    return valor.strip().lower() if isinstance(valor, str) else ""


def validar_cuenta(cuerpo: dict) -> tuple[str, str, str]:
    campos = {}
    nombre = cuerpo.get("nombre")
    nombre = nombre.strip() if isinstance(nombre, str) else ""
    correo = normalizar_correo(cuerpo.get("correo"))
    contrasena = cuerpo.get("contrasena")

    if not nombre:
        campos["nombre"] = "Escribe tu nombre."
    elif len(nombre) > 60:
        campos["nombre"] = "El nombre debe tener máximo 60 caracteres."

    if not correo:
        campos["correo"] = "Escribe tu correo."
    elif len(correo) > 254 or not PATRON_CORREO.match(correo):
        campos["correo"] = "El correo no es válido."

    if not isinstance(contrasena, str) or len(contrasena) < 8:
        campos["contrasena"] = "La contraseña debe tener al menos 8 caracteres."
    elif len(contrasena) > 128:
        campos["contrasena"] = "La contraseña debe tener máximo 128 caracteres."

    if campos:
        raise ErrorValidacion("Revisa los datos marcados.", campos)
    return nombre, correo, contrasena


def validar_inicio_sesion(cuerpo: dict) -> tuple[str, str]:
    correo = normalizar_correo(cuerpo.get("correo"))
    contrasena = cuerpo.get("contrasena")
    campos = {}
    if not correo:
        campos["correo"] = "Escribe tu correo."
    if not isinstance(contrasena, str) or not contrasena:
        campos["contrasena"] = "Escribe tu contraseña."
    if campos:
        raise ErrorValidacion("Revisa los datos marcados.", campos)
    return correo, contrasena[:128]


# ---------------------------------------------------------------------- fechas

def parsear_fecha(texto, campo: str = "fecha") -> date:
    try:
        if not isinstance(texto, str) or len(texto) != 10:
            raise ValueError
        return date.fromisoformat(texto)
    except ValueError:
        raise ErrorValidacion("Fecha inválida.", {campo: "Usa el formato AAAA-MM-DD."})


def validar_fecha_registro(texto, hoy_: date) -> date:
    """Hoy o uno de los 6 días anteriores, nunca futura (RF-03)."""
    fecha = parsear_fecha(texto)
    if fecha > hoy_:
        raise ErrorValidacion("No puedes registrar días futuros.", {"fecha": "La fecha no puede ser futura."})
    if fecha < hoy_ - timedelta(days=DIAS_ANTERIORES_PERMITIDOS):
        raise ErrorValidacion(
            "Solo puedes registrar hoy o los 6 días anteriores.",
            {"fecha": "Elige hoy o uno de los 6 días anteriores."},
        )
    return fecha


def validar_rango(desde_txt, hasta_txt) -> tuple[date, date]:
    """Rango para GET /registros: máximo 31 días."""
    desde = parsear_fecha(desde_txt, "desde")
    hasta = parsear_fecha(hasta_txt, "hasta")
    if desde > hasta:
        raise ErrorValidacion("El rango de fechas es inválido.", {"desde": "Debe ser anterior o igual a 'hasta'."})
    if (hasta - desde).days >= MAX_DIAS_CONSULTA:
        raise ErrorValidacion(f"El rango máximo es de {MAX_DIAS_CONSULTA} días.", {"hasta": "Rango demasiado grande."})
    return desde, hasta


# --------------------------------------------------------------- datos del día

def _numero(valor):
    # bool es subclase de int; no lo aceptamos como número.
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return None
    return valor


def _medias_horas(valor, minimo, maximo, campo, etiqueta, campos):
    n = _numero(valor)
    if n is None:
        campos[campo] = f"Escribe {etiqueta}."
    elif not (minimo <= n <= maximo):
        campos[campo] = f"Debe estar entre {minimo} y {maximo} horas."
    elif (n * 2) != int(n * 2):
        campos[campo] = "Usa pasos de 0.5 horas (ej. 6 o 6.5)."
    else:
        return float(n)
    return None


def _entero(valor, minimo, maximo, campo, etiqueta, campos):
    n = _numero(valor)
    if n is None:
        campos[campo] = f"Escribe {etiqueta}."
    elif n != int(n):
        campos[campo] = "Debe ser un número entero."
    elif not (minimo <= n <= maximo):
        campos[campo] = f"Debe estar entre {minimo} y {maximo}."
    else:
        return int(n)
    return None


def validar_datos_dia(cuerpo: dict) -> dict:
    campos = {}
    datos = {
        "horas_trabajo": _medias_horas(cuerpo.get("horas_trabajo"), 0, 16, "horas_trabajo", "las horas de estudio o trabajo", campos),
        "tareas": _entero(cuerpo.get("tareas"), 0, 20, "tareas", "las tareas completadas", campos),
        "horas_sueno": _medias_horas(cuerpo.get("horas_sueno"), 0, 14, "horas_sueno", "las horas de sueño", campos),
        "energia": _entero(cuerpo.get("energia"), 1, 5, "energia", "tu nivel de energía", campos),
    }
    if campos:
        raise ErrorValidacion("Revisa los datos marcados.", campos)
    return datos
