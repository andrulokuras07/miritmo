"""Corre MiRitmo en tu computadora sin AWS ni Cloudant.

- Interfaz:  http://localhost:8080   (simula S3 + CloudFront)
- API:       http://localhost:8787   (simula la URL de función de Lambda)

Los datos se guardan en memoria y se borran al detener el servidor.
Si defines CLOUDANT_URL y CLOUDANT_APIKEY, la API local usa tu Cloudant real.

Uso:  python3 scripts/servidor_local.py
"""

import functools
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

RAIZ = Path(__file__).resolve().parents[1]
PUERTO_WEB, PUERTO_API = 8080, 8787

os.environ.setdefault("TOKEN_SECRET", "solo-para-desarrollo-local-no-usar-en-la-nube")
os.environ.setdefault("ALLOWED_ORIGIN", f"http://localhost:{PUERTO_WEB}")
sys.path.insert(0, str(RAIZ / "backend"))

import lambda_function  # noqa: E402


class ApiLocal(SimpleHTTPRequestHandler):
    """Convierte cada petición HTTP en un evento de URL de función (formato 2.0)."""

    def _atender(self):
        partes = urlsplit(self.path)
        largo = int(self.headers.get("Content-Length") or 0)
        evento = {
            "rawPath": partes.path,
            "rawQueryString": partes.query,
            "queryStringParameters": dict(parse_qsl(partes.query)) or None,
            "headers": {k.lower(): v for k, v in self.headers.items()},
            "body": self.rfile.read(largo).decode("utf-8") if largo else None,
            "isBase64Encoded": False,
            "requestContext": {"http": {"method": self.command, "path": partes.path}},
        }
        r = lambda_function.lambda_handler(evento, None)
        cuerpo = r["body"].encode("utf-8")
        self.send_response(r["statusCode"])
        for nombre, valor in r["headers"].items():
            self.send_header(nombre, valor)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    do_GET = do_POST = do_PUT = do_DELETE = do_OPTIONS = _atender


class WebLocal(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def main():
    web = ThreadingHTTPServer(("localhost", PUERTO_WEB), functools.partial(WebLocal, directory=str(RAIZ / "frontend")))
    api = ThreadingHTTPServer(("localhost", PUERTO_API), ApiLocal)
    threading.Thread(target=web.serve_forever, daemon=True).start()
    almacen = "Cloudant" if os.environ.get("CLOUDANT_URL") else "memoria"
    print(f"MiRitmo local\n  Interfaz: http://localhost:{PUERTO_WEB}\n  API:      http://localhost:{PUERTO_API} (datos en {almacen})\nCtrl+C para detener.")
    try:
        api.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
