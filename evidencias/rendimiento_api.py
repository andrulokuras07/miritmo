"""RNF-03: mide 20 peticiones a la API pública de MiRitmo (mezcla de GET y PUT).

Crea una cuenta temporal (pruebaE2-rend-<marca>@miritmo.mx, contraseña aleatoria que no se muestra),
alterna GET /registros (7 días) y PUT /registros/<fecha> y mide el tiempo total de cada petición
(conexión HTTPS nueva en cada una, como el peor caso de un navegador). La primera no cuenta
(puede incluir el arranque en frío de la Lambda). Criterio: al menos 9 de cada 10 en menos de 3 s.

Uso: python evidencias/rendimiento_api.py [--api https://xxxx.lambda-url.us-east-2.on.aws]
"""
import argparse
import json
import secrets
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")
API = "https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws"


def llamar(api, metodo, ruta, cuerpo=None, token=None):
    datos = None if cuerpo is None else json.dumps(cuerpo).encode()
    req = urllib.request.Request(api + ruta, data=datos, method=metodo, headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            estado, texto = r.status, r.read()
    except urllib.error.HTTPError as e:
        estado, texto = e.code, e.read()
    return estado, json.loads(texto or b"{}"), time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=API)
    ap.add_argument("-n", type=int, default=20)
    a = ap.parse_args()
    api = a.api.rstrip("/")

    hoy = (datetime.now(timezone.utc) - timedelta(hours=6)).date()
    correo = f"pruebaE2-rend-{datetime.now():%Y%m%d%H%M%S}@miritmo.mx"
    estado, cuerpo, _ = llamar(api, "POST", "/cuentas", {"nombre": "Prueba rendimiento", "correo": correo,
                                                       "contrasena": secrets.token_urlsafe(12)})
    if estado != 201:
        sys.exit(f"No se pudo crear la cuenta temporal: HTTP {estado}")
    token = cuerpo["token"]
    print(f"MiRitmo · RNF-03 · {a.n} peticiones a {api}")
    print(f"Cuenta temporal: {correo}  (hoy CDMX: {hoy})\n")
    print(f"{'#':>3}  {'Método':<6} {'Ruta':<44} {'HTTP':>4}  {'Tiempo':>8}")

    tiempos = []
    for i in range(1, a.n + 1):
        if i % 2:
            ruta = f"/registros?desde={hoy - timedelta(days=6)}&hasta={hoy}"
            estado, _, t = llamar(api, "GET", ruta, token=token)
            metodo = "GET"
        else:
            fecha = hoy - timedelta(days=(i // 2) % 7)
            ruta = f"/registros/{fecha}"
            dia = {"horas_trabajo": 6, "tareas": (i // 2) % 6, "horas_sueno": 7.5, "energia": 4}
            estado, _, t = llamar(api, "PUT", ruta, dia, token=token)
            metodo = "PUT"
        nota = "  (descartada: primera petición)" if i == 1 else ""
        print(f"{i:>3}  {metodo:<6} {ruta:<44} {estado:>4}  {t:>6.3f} s{nota}")
        if i > 1:
            tiempos.append((t, estado))

    rapidas = sum(1 for t, e in tiempos if t < 3 and e == 200)
    ts = sorted(t for t, _ in tiempos)
    print(f"\nContadas: {len(tiempos)} · menos de 3 s con HTTP 200: {rapidas} de {len(tiempos)} "
          f"({100 * rapidas / len(tiempos):.0f} %; criterio: 90 % o más)")
    print(f"Mínimo {ts[0]:.3f} s · mediana {ts[len(ts) // 2]:.3f} s · máximo {ts[-1]:.3f} s · promedio {sum(ts) / len(ts):.3f} s")
    print("RNF-03:", "CUMPLE" if rapidas >= 0.9 * len(tiempos) else "NO CUMPLE")
    print(f"CUENTA_TEMPORAL={correo}")


if __name__ == "__main__":
    main()
