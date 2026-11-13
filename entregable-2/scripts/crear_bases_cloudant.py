"""Crea las bases de datos `usuarios` y `registros` en IBM Cloudant si no existen.

Lee CLOUDANT_URL y CLOUDANT_APIKEY de las variables de entorno (las carga desplegar_aws.sh).
Solo usa la biblioteca estándar de Python.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def token_iam(apikey: str) -> str:
    datos = urllib.parse.urlencode({
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": apikey,
    }).encode()
    peticion = urllib.request.Request(
        "https://iam.cloud.ibm.com/identity/token",
        data=datos,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
    )
    with urllib.request.urlopen(peticion, timeout=20) as r:
        return json.load(r)["access_token"]


def crear_base(url: str, token: str, nombre: str) -> None:
    peticion = urllib.request.Request(
        f"{url}/{nombre}", method="PUT", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(peticion, timeout=20):
            print(f"  Base '{nombre}' creada.")
    except urllib.error.HTTPError as e:
        if e.code == 412:
            print(f"  Base '{nombre}' ya existía.")
        else:
            raise SystemExit(f"  No se pudo crear '{nombre}': HTTP {e.code} {e.read().decode()[:200]}")


def main():
    url = os.environ.get("CLOUDANT_URL", "").rstrip("/")
    apikey = os.environ.get("CLOUDANT_APIKEY", "")
    if not url or not apikey:
        sys.exit("Faltan CLOUDANT_URL y CLOUDANT_APIKEY.")
    try:
        token = token_iam(apikey)
    except urllib.error.HTTPError as e:
        sys.exit(f"IBM Cloud rechazó la apikey de Cloudant (HTTP {e.code}). Revisa CLOUDANT_APIKEY.")
    for nombre in (os.environ.get("DB_USUARIOS", "usuarios"), os.environ.get("DB_REGISTROS", "registros")):
        crear_base(url, token, nombre)


if __name__ == "__main__":
    main()
