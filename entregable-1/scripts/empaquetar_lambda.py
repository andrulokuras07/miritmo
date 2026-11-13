"""Arma build/miritmo-lambda.zip para AWS Lambda (Python 3.12, x86_64) desde Windows, Linux o macOS.

Equivale a empaquetar_lambda.sh pero sin depender de `zip` ni de `python3`:
instala las dependencias con binarios para Linux y comprime con zipfile.
Uso (desde entregable-1/):  python scripts/empaquetar_lambda.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(RAIZ, "backend")
BUILD = os.path.join(RAIZ, "build")
ZIP = os.path.join(BUILD, "miritmo-lambda.zip")


def main():
    # Se arma en una carpeta temporal (fuera de OneDrive/Dropbox, que bloquean archivos al sincronizar).
    paquete = tempfile.mkdtemp(prefix="miritmo-lambda-")
    try:
        armar(paquete)
    finally:
        shutil.rmtree(paquete, ignore_errors=True)


def armar(PAQUETE):
    os.makedirs(BUILD, exist_ok=True)
    subprocess.run([
        sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
        "--platform", "manylinux2014_x86_64", "--python-version", "3.12", "--implementation", "cp",
        "--only-binary=:all:", "--target", PAQUETE, "-r", os.path.join(BACKEND, "requirements.txt"),
    ], check=True)
    shutil.copy2(os.path.join(BACKEND, "lambda_function.py"), PAQUETE)
    shutil.copytree(os.path.join(BACKEND, "miritmo"), os.path.join(PAQUETE, "miritmo"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    if os.path.exists(ZIP):
        os.remove(ZIP)
    n = 0
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for carpeta, dirs, archivos in os.walk(PAQUETE):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for a in archivos:
                if a.endswith(".pyc"):
                    continue
                ruta = os.path.join(carpeta, a)
                z.write(ruta, os.path.relpath(ruta, PAQUETE).replace(os.sep, "/"))
                n += 1
    print(f"{ZIP}: {n} archivos, {os.path.getsize(ZIP) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
