"""Publica frontend/ en S3 e invalida CloudFront (Windows, Linux o macOS; equivale a publicar_frontend.sh).

- Copia frontend/ a una carpeta temporal y ahí escribe js/config.js con la URL de la API
  (el config.js del repositorio se queda apuntando a localhost para pruebas locales).
- Sube cada archivo con su Content-Type correcto (html, css, js, svg) con `aws s3 cp`.
- Crea la invalidación "/*" y, con --esperar, espera a que termine.

Uso (desde entregable-2/):
  python scripts/publicar_frontend.py --bucket miritmo-frontend-xxxx --distribucion E123ABC ^
      --api https://xxxx.lambda-url.us-east-2.on.aws --perfil miritmo --esperar
"""
import argparse
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.path.join(RAIZ, "frontend")
TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


def aws(*args, perfil=None, salida=False):
    cmd = ["aws", *args] + (["--profile", perfil] if perfil else [])
    print("  $", " ".join(cmd))
    r = subprocess.run(cmd, check=True, capture_output=salida, text=True)
    return r.stdout if salida else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--distribucion", required=True, help="ID de la distribución de CloudFront")
    ap.add_argument("--api", required=True, help="URL de función de la Lambda")
    ap.add_argument("--perfil", default=os.environ.get("AWS_PROFILE"))
    ap.add_argument("--esperar", action="store_true", help="esperar a que termine la invalidación")
    a = ap.parse_args()

    api = a.api.rstrip("/")
    if not api.startswith("https://"):
        sys.exit("La URL de la API debe empezar con https://")

    tmp = tempfile.mkdtemp(prefix="miritmo-web-")
    try:
        sitio = os.path.join(tmp, "frontend")
        shutil.copytree(FRONTEND, sitio)
        with open(os.path.join(sitio, "js", "config.js"), "w", encoding="utf-8", newline="\n") as f:
            f.write("// Generado por scripts/publicar_frontend.py: URL de la API (URL de función de Lambda).\n")
            f.write(f"window.MIRITMO_CONFIG = {{\n  apiUrl: {json.dumps(api)},\n}};\n")

        print(f"Subiendo a s3://{a.bucket} ...")
        n = 0
        for carpeta, _, archivos in os.walk(sitio):
            for nombre in sorted(archivos):
                ruta = os.path.join(carpeta, nombre)
                clave = os.path.relpath(ruta, sitio).replace(os.sep, "/")
                ext = os.path.splitext(nombre)[1].lower()
                tipo = TIPOS.get(ext) or mimetypes.guess_type(nombre)[0] or "application/octet-stream"
                aws("s3", "cp", ruta, f"s3://{a.bucket}/{clave}", "--content-type", tipo,
                    "--cache-control", "no-cache", "--only-show-errors", perfil=a.perfil)
                n += 1
        print(f"{n} archivos subidos.")

        salida = aws("cloudfront", "create-invalidation", "--distribution-id", a.distribucion,
                     "--paths", "/*", "--output", "json", perfil=a.perfil, salida=True)
        inv = json.loads(salida)["Invalidation"]
        print(f"Invalidación {inv['Id']}: {inv['Status']}")
        if a.esperar:
            aws("cloudfront", "wait", "invalidation-completed", "--distribution-id", a.distribucion,
                "--id", inv["Id"], perfil=a.perfil)
            print(f"Invalidación {inv['Id']}: Completed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
