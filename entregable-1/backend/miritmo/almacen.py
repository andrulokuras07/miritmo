"""Acceso a datos: IBM Cloudant en la nube y un almacén en memoria para pruebas locales.

Bases de datos:
- usuarios:  _id = correo                 -> nombre, correo, hash, sal, creado
- registros: _id = correo:fecha (AAAA-MM-DD) -> usuario, fecha, horas_trabajo, tareas,
                                               horas_sueno, energia, calificacion, actualizado
"""

import copy
import os


class CorreoDuplicado(Exception):
    pass


class AlmacenCloudant:
    def __init__(self, url: str, apikey: str, db_usuarios: str = "usuarios", db_registros: str = "registros"):
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
        from ibmcloudant.cloudant_v1 import CloudantV1

        self.cliente = CloudantV1(authenticator=IAMAuthenticator(apikey))
        self.cliente.set_service_url(url)
        self.db_usuarios = db_usuarios
        self.db_registros = db_registros

    def _obtener(self, db: str, doc_id: str):
        from ibm_cloud_sdk_core import ApiException

        try:
            return self.cliente.get_document(db=db, doc_id=doc_id).get_result()
        except ApiException as e:
            if e.code == 404:
                return None
            raise

    def obtener_usuario(self, correo: str):
        return self._obtener(self.db_usuarios, correo)

    def crear_usuario(self, doc: dict) -> None:
        from ibm_cloud_sdk_core import ApiException

        try:
            # Sin _rev: si el correo ya existe, Cloudant responde 409 (conflicto).
            self.cliente.put_document(db=self.db_usuarios, doc_id=doc["_id"], document=doc)
        except ApiException as e:
            if e.code == 409:
                raise CorreoDuplicado()
            raise

    def guardar_registro(self, doc: dict) -> None:
        """Crea o actualiza el registro del día (un solo documento por usuario y fecha)."""
        from ibm_cloud_sdk_core import ApiException

        for _ in range(2):  # un reintento si otra petición lo modificó al mismo tiempo
            actual = self._obtener(self.db_registros, doc["_id"])
            datos = dict(doc)
            if actual:
                datos["_rev"] = actual["_rev"]
            try:
                self.cliente.put_document(db=self.db_registros, doc_id=doc["_id"], document=datos)
                return
            except ApiException as e:
                if e.code != 409:
                    raise
        raise RuntimeError("No se pudo guardar el registro por un conflicto de versiones")


class AlmacenMemoria:
    """Mismo comportamiento que Cloudant, en memoria. Solo para desarrollo y pruebas."""

    def __init__(self):
        self.usuarios: dict[str, dict] = {}
        self.registros: dict[str, dict] = {}

    def obtener_usuario(self, correo: str):
        return copy.deepcopy(self.usuarios.get(correo))

    def crear_usuario(self, doc: dict) -> None:
        if doc["_id"] in self.usuarios:
            raise CorreoDuplicado()
        self.usuarios[doc["_id"]] = copy.deepcopy(doc)

    def guardar_registro(self, doc: dict) -> None:
        self.registros[doc["_id"]] = copy.deepcopy(doc)


def crear_almacen():
    """Usa Cloudant si hay credenciales en variables de entorno; si no, memoria (modo local)."""
    url = os.environ.get("CLOUDANT_URL")
    apikey = os.environ.get("CLOUDANT_APIKEY")
    if url and apikey:
        return AlmacenCloudant(
            url,
            apikey,
            os.environ.get("DB_USUARIOS", "usuarios"),
            os.environ.get("DB_REGISTROS", "registros"),
        )
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        raise RuntimeError("Faltan CLOUDANT_URL y CLOUDANT_APIKEY en las variables de entorno de Lambda")
    return AlmacenMemoria()
