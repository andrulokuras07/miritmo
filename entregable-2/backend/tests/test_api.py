"""Pruebas del Entregable 2 (RF-01 a RF-07, RNF-02).

Ejecutar desde la carpeta backend:  python3 -m unittest discover -s tests -v
"""

import json
import os
import sys
import time
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["TOKEN_SECRET"] = "secreto-de-pruebas-con-mas-de-32-caracteres"
os.environ["ALLOWED_ORIGIN"] = "https://d123.cloudfront.net"
os.environ.pop("CLOUDANT_URL", None)

import lambda_function  # noqa: E402
from miritmo import seguridad  # noqa: E402
from miritmo import validacion  # noqa: E402
from miritmo.almacen import AlmacenMemoria  # noqa: E402
from miritmo.calificacion import calcular_calificacion  # noqa: E402

ORIGEN = "https://d123.cloudfront.net"
HOY = validacion.hoy(lambda_function.OFFSET_HORAS)
DIA = {"horas_trabajo": 6, "tareas": 4, "horas_sueno": 7.5, "energia": 4}


def peticion(metodo, ruta, cuerpo=None, token=None, origen=ORIGEN, encabezados=None, parametros=None):
    h = {"content-type": "application/json"}
    if origen:
        h["origin"] = origen
    if token:
        h["authorization"] = f"Bearer {token}"
    h.update(encabezados or {})
    evento = {
        "rawPath": ruta,
        "queryStringParameters": parametros,
        "headers": h,
        "body": json.dumps(cuerpo) if cuerpo is not None else None,
        "isBase64Encoded": False,
        "requestContext": {"http": {"method": metodo}},
    }
    r = lambda_function.lambda_handler(evento, None)
    return r["statusCode"], (json.loads(r["body"]) if r["body"] else None), r["headers"]


class Base(unittest.TestCase):
    def setUp(self):
        self.almacen = AlmacenMemoria()
        lambda_function._almacen = self.almacen

    def crear_cuenta(self, correo="ana@mail.com", contrasena="contrasena123", nombre="Ana"):
        return peticion("POST", "/cuentas", {"nombre": nombre, "correo": correo, "contrasena": contrasena})

    def token(self, correo="ana@mail.com"):
        estado, cuerpo, _ = self.crear_cuenta(correo=correo)
        self.assertEqual(estado, 201)
        return cuerpo["token"]


class PruebasCalificacion(unittest.TestCase):
    """RF-04: regla de calificación."""

    def test_ejemplo_del_documento_es_84(self):
        self.assertEqual(calcular_calificacion(6, 4, 7.5, 4), 84)

    def test_maximo_100_y_topes(self):
        self.assertEqual(calcular_calificacion(8, 5, 8, 5), 100)
        self.assertEqual(calcular_calificacion(16, 20, 9, 5), 100)

    def test_minimo(self):
        self.assertEqual(calcular_calificacion(0, 0, 0, 1), 10)

    def test_niveles_de_sueno(self):
        base = calcular_calificacion(0, 0, 7, 1)  # 25 + 5
        self.assertEqual(base, 30)
        self.assertEqual(calcular_calificacion(0, 0, 9, 1), 30)
        self.assertEqual(calcular_calificacion(0, 0, 6, 1), 20)
        self.assertEqual(calcular_calificacion(0, 0, 6.5, 1), 20)
        self.assertEqual(calcular_calificacion(0, 0, 9.5, 1), 20)
        self.assertEqual(calcular_calificacion(0, 0, 10, 1), 20)
        self.assertEqual(calcular_calificacion(0, 0, 5.5, 1), 10)
        self.assertEqual(calcular_calificacion(0, 0, 10.5, 1), 10)

    def test_redondeo_al_entero_mas_cercano(self):
        # 4 h = 12.5 puntos -> 12.5 + 0 + 5 + 5 = 22.5 -> 23
        self.assertEqual(calcular_calificacion(4, 0, 0, 1), 23)


class PruebasCuentas(Base):
    """RF-01 y RNF-02."""

    def test_crear_cuenta_devuelve_token(self):
        estado, cuerpo, _ = self.crear_cuenta()
        self.assertEqual(estado, 201)
        self.assertEqual(cuerpo["nombre"], "Ana")
        self.assertTrue(cuerpo["token"])

    def test_contrasena_no_se_guarda_en_texto_plano(self):
        self.crear_cuenta(contrasena="contrasena123")
        doc = self.almacen.usuarios["ana@mail.com"]
        self.assertEqual(set(doc), {"_id", "nombre", "correo", "hash", "sal", "creado"})
        self.assertNotIn("contrasena123", json.dumps(doc))
        self.assertEqual(len(doc["hash"]), 64)  # SHA-256 en hexadecimal

    def test_mismo_correo_no_se_registra_dos_veces(self):
        self.crear_cuenta()
        estado, cuerpo, _ = self.crear_cuenta(correo="  ANA@mail.com ")
        self.assertEqual(estado, 409)
        self.assertIn("correo", cuerpo["campos"])

    def test_contrasena_minimo_8(self):
        estado, cuerpo, _ = self.crear_cuenta(contrasena="1234567")
        self.assertEqual(estado, 400)
        self.assertIn("contrasena", cuerpo["campos"])

    def test_datos_invalidos(self):
        estado, cuerpo, _ = peticion("POST", "/cuentas", {"nombre": "", "correo": "no-es-correo", "contrasena": "x"})
        self.assertEqual(estado, 400)
        self.assertEqual(set(cuerpo["campos"]), {"nombre", "correo", "contrasena"})


class PruebasSesiones(Base):
    """RF-02."""

    def test_inicio_correcto(self):
        self.crear_cuenta()
        estado, cuerpo, _ = peticion("POST", "/sesiones", {"correo": "Ana@Mail.com", "contrasena": "contrasena123"})
        self.assertEqual(estado, 200)
        self.assertEqual(seguridad.verificar_token(cuerpo["token"], os.environ["TOKEN_SECRET"])["sub"], "ana@mail.com")

    def test_contrasena_incorrecta(self):
        self.crear_cuenta()
        estado, cuerpo, _ = peticion("POST", "/sesiones", {"correo": "ana@mail.com", "contrasena": "otra-clave"})
        self.assertEqual(estado, 401)
        self.assertEqual(cuerpo["error"], "Correo o contraseña incorrectos.")

    def test_correo_inexistente(self):
        estado, _, _ = peticion("POST", "/sesiones", {"correo": "nadie@mail.com", "contrasena": "contrasena123"})
        self.assertEqual(estado, 401)


class PruebasRegistros(Base):
    """RF-03, RF-04 y RNF-02."""

    def test_guardar_dia_devuelve_calificacion(self):
        estado, cuerpo, _ = peticion("PUT", f"/registros/{HOY}", DIA, token=self.token())
        self.assertEqual(estado, 200)
        self.assertEqual(cuerpo["registro"]["calificacion"], 84)
        doc = self.almacen.registros[f"ana@mail.com:{HOY}"]
        self.assertEqual(doc["usuario"], "ana@mail.com")
        self.assertEqual(doc["calificacion"], 84)

    def test_un_solo_registro_por_usuario_y_fecha(self):
        token = self.token()
        peticion("PUT", f"/registros/{HOY}", DIA, token=token)
        estado, cuerpo, _ = peticion("PUT", f"/registros/{HOY}", {**DIA, "energia": 5}, token=token)
        self.assertEqual(estado, 200)
        self.assertEqual(cuerpo["registro"]["calificacion"], 89)
        self.assertEqual(len(self.almacen.registros), 1)

    def test_seis_dias_anteriores_permitidos(self):
        estado, _, _ = peticion("PUT", f"/registros/{HOY - timedelta(days=6)}", DIA, token=self.token())
        self.assertEqual(estado, 200)

    def test_fecha_futura_rechazada(self):
        estado, cuerpo, _ = peticion("PUT", f"/registros/{HOY + timedelta(days=1)}", DIA, token=self.token())
        self.assertEqual(estado, 400)
        self.assertIn("fecha", cuerpo["campos"])

    def test_mas_de_seis_dias_atras_rechazada(self):
        estado, _, _ = peticion("PUT", f"/registros/{HOY - timedelta(days=7)}", DIA, token=self.token())
        self.assertEqual(estado, 400)

    def test_fecha_con_formato_invalido(self):
        estado, _, _ = peticion("PUT", "/registros/12-11-2026", DIA, token=self.token())
        self.assertEqual(estado, 400)

    def test_valores_fuera_de_rango(self):
        token = self.token()
        casos = [
            {"horas_trabajo": 6.3},   # no es paso de 0.5
            {"horas_trabajo": 16.5},  # máximo 16
            {"tareas": 2.5},          # entero
            {"tareas": 21},
            {"horas_sueno": -1},
            {"horas_sueno": 14.5},
            {"energia": 0},
            {"energia": 6},
            {"energia": True},        # booleano no es número
            {"tareas": "4"},          # texto no es número
        ]
        for cambio in casos:
            with self.subTest(cambio=cambio):
                estado, cuerpo, _ = peticion("PUT", f"/registros/{HOY}", {**DIA, **cambio}, token=token)
                self.assertEqual(estado, 400)
                self.assertIn(next(iter(cambio)), cuerpo["campos"])
        self.assertEqual(self.almacen.registros, {})

    def test_nan_e_infinity_responden_400(self):
        token = self.token()
        for campo in ("horas_trabajo", "tareas", "horas_sueno", "energia"):
            for valor in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(campo=campo, valor=valor):
                    estado, cuerpo, _ = peticion("PUT", f"/registros/{HOY}", {**DIA, campo: valor}, token=token)
                    self.assertEqual(estado, 400)
                    self.assertIn(campo, cuerpo["campos"])
        self.assertEqual(self.almacen.registros, {})

    def test_sin_token_responde_401(self):
        estado, _, _ = peticion("PUT", f"/registros/{HOY}", DIA)
        self.assertEqual(estado, 401)

    def test_token_invalido_responde_401(self):
        token = self.token()
        for malo in ["abc", token[:-2] + "xx", "x.y.z", seguridad.crear_token("ana@mail.com", "Ana", "otro-secreto-de-mas-de-32-caracteres!!")]:
            with self.subTest(token=malo):
                estado, _, _ = peticion("PUT", f"/registros/{HOY}", DIA, token=malo)
                self.assertEqual(estado, 401)

    def test_token_expirado_responde_401(self):
        self.token()
        viejo = seguridad.crear_token("ana@mail.com", "Ana", os.environ["TOKEN_SECRET"], ahora=time.time() - 8 * 86400)
        estado, _, _ = peticion("PUT", f"/registros/{HOY}", DIA, token=viejo)
        self.assertEqual(estado, 401)

    def test_cada_usuario_escribe_solo_sus_registros(self):
        token_ana = self.token("ana@mail.com")
        token_beto = self.token("beto@mail.com")
        peticion("PUT", f"/registros/{HOY}", DIA, token=token_ana)
        # Aunque Beto mande otro "usuario" en el cuerpo, se usa el correo de su token.
        peticion("PUT", f"/registros/{HOY}", {**DIA, "energia": 1, "usuario": "ana@mail.com"}, token=token_beto)
        self.assertEqual(self.almacen.registros[f"ana@mail.com:{HOY}"]["energia"], 4)
        self.assertEqual(self.almacen.registros[f"beto@mail.com:{HOY}"]["energia"], 1)


class PruebasConsulta(Base):
    """RF-05, RF-06 y RF-07: consultar, editar y ver la semana."""

    def semana(self, token):
        return peticion("GET", "/registros", token=token,
                        parametros={"desde": str(HOY - timedelta(days=6)), "hasta": str(HOY)})

    def test_devuelve_los_dias_registrados_en_orden(self):
        token = self.token()
        for dias_atras in (0, 2, 5):
            peticion("PUT", f"/registros/{HOY - timedelta(days=dias_atras)}", DIA, token=token)
        estado, cuerpo, _ = self.semana(token)
        self.assertEqual(estado, 200)
        fechas = [r["fecha"] for r in cuerpo["registros"]]
        self.assertEqual(fechas, sorted(fechas))
        self.assertEqual(len(fechas), 3)
        self.assertNotIn("_id", cuerpo["registros"][0])
        self.assertNotIn("usuario", cuerpo["registros"][0])

    def test_editar_dia_actualiza_y_recalcula(self):
        token = self.token()
        peticion("PUT", f"/registros/{HOY}", DIA, token=token)
        _, cuerpo, _ = peticion("GET", "/registros", token=token, parametros={"desde": str(HOY), "hasta": str(HOY)})
        self.assertEqual(cuerpo["registros"][0]["tareas"], 4)  # el formulario se llena con estos datos
        peticion("PUT", f"/registros/{HOY}", {**DIA, "tareas": 5}, token=token)
        _, cuerpo, _ = self.semana(token)
        self.assertEqual(len(cuerpo["registros"]), 1)
        self.assertEqual(cuerpo["registros"][0]["tareas"], 5)
        self.assertEqual(cuerpo["registros"][0]["calificacion"], 89)

    def test_no_ve_registros_de_otro_usuario(self):
        peticion("PUT", f"/registros/{HOY}", DIA, token=self.token("ana@mail.com"))
        _, cuerpo, _ = self.semana(self.token("beto@mail.com"))
        self.assertEqual(cuerpo["registros"], [])

    def test_correo_parecido_no_se_mezcla(self):
        peticion("PUT", f"/registros/{HOY}", DIA, token=self.token("ana@mail.com"))
        _, cuerpo, _ = self.semana(self.token("ana@mail.co"))
        self.assertEqual(cuerpo["registros"], [])

    def test_rango_invalido(self):
        token = self.token()
        casos = [
            None,
            {"desde": "2026-11-12"},
            {"desde": "ayer", "hasta": "hoy"},
            {"desde": "2026-11-12", "hasta": "2026-11-01"},
            {"desde": "2026-01-01", "hasta": "2026-12-31"},
        ]
        for parametros in casos:
            with self.subTest(parametros=parametros):
                estado, _, _ = peticion("GET", "/registros", token=token, parametros=parametros)
                self.assertEqual(estado, 400)

    def test_sin_token_responde_401(self):
        estado, _, _ = peticion("GET", "/registros", parametros={"desde": str(HOY), "hasta": str(HOY)})
        self.assertEqual(estado, 401)


class PruebasHttp(Base):
    def test_cors_para_cloudfront_en_codigo(self):
        # Modo servidor local: el código agrega los encabezados CORS.
        os.environ["CORS_EN_CODIGO"] = "1"
        try:
            estado, _, encabezados = peticion("OPTIONS", "/cuentas")
        finally:
            os.environ.pop("CORS_EN_CODIGO", None)
        self.assertEqual(estado, 204)
        self.assertEqual(encabezados["Access-Control-Allow-Origin"], ORIGEN)

    def test_cors_en_aws_lo_pone_la_url_de_funcion(self):
        # En AWS los encabezados CORS los agrega la URL de función; el código no debe duplicarlos.
        estado, _, encabezados = peticion("POST", "/sesiones", {"correo": "x@mail.com", "contrasena": "12345678"})
        self.assertEqual(estado, 401)
        self.assertNotIn("Access-Control-Allow-Origin", encabezados)

    def test_origen_no_permitido(self):
        estado, _, encabezados = peticion("POST", "/cuentas", {}, origen="https://otro-sitio.com")
        self.assertEqual(estado, 403)
        self.assertNotIn("Access-Control-Allow-Origin", encabezados)

    def test_ruta_inexistente(self):
        estado, _, _ = peticion("GET", "/nada")
        self.assertEqual(estado, 404)

    def test_json_invalido(self):
        evento = {"rawPath": "/cuentas", "headers": {}, "body": "{no json", "requestContext": {"http": {"method": "POST"}}}
        self.assertEqual(lambda_function.lambda_handler(evento)["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()
