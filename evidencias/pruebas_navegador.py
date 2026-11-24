"""Pruebas de MiRitmo en un navegador real con Playwright (Chrome o Edge instalados).

Recorre el flujo completo desde la interfaz: crear cuenta, iniciar sesión, registrar días,
editar uno (RF-05), revisar "Mi semana" (RF-06, RF-07), mensajes de validación y la vista
de 360 px (RNF-04). Imprime un JSON con los resultados. Nunca imprime contraseñas ni tokens.

La contraseña se lee de la variable de entorno MIRITMO_CLAVE (si no existe, se genera una
aleatoria que no se muestra).

Ejemplos:
  python evidencias/pruebas_navegador.py --url http://localhost:8080 --correo a@mail.com --crear \
      --dias "0:6,4,7.5,4;2:5,3,8,3" --editar "2:tareas=5"
  python evidencias/pruebas_navegador.py --url https://dnfx295km7eni.cloudfront.net --canal msedge ...
"""
import argparse
import json
import os
import secrets
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime, timedelta, timezone

from playwright.sync_api import sync_playwright

CAMPOS = ("horas_trabajo", "tareas", "horas_sueno", "energia")


def hoy_cdmx():
    return (datetime.now(timezone.utc) + timedelta(hours=-6)).date()


def calificacion(h, t, s, e):
    """Regla del documento, para comparar con lo que muestra la app (cálculo a mano)."""
    sueno = 25 if 7 <= s <= 9 else 15 if (6 <= s <= 6.5 or 9.5 <= s <= 10) else 5
    total = min(h / 8, 1) * 25 + min(t / 5, 1) * 25 + sueno + e * 5
    return int(total + 0.5)


def parsear_dias(texto):
    dias = {}
    for parte in filter(None, (texto or "").split(";")):
        atras, valores = parte.split(":")
        h, t, s, e = valores.split(",")
        dias[int(atras)] = {"horas_trabajo": float(h), "tareas": int(t), "horas_sueno": float(s), "energia": int(e)}
    return dias


def numero_texto(v):
    return str(int(v)) if float(v).is_integer() else str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--canal", default="chrome", help="chrome o msedge")
    ap.add_argument("--correo", required=True)
    ap.add_argument("--nombre", default="Examen MiRitmo")
    ap.add_argument("--crear", action="store_true", help="crear la cuenta desde la pantalla Acceso")
    ap.add_argument("--dias", default="", help='"diasAtras:h,t,s,e;..."')
    ap.add_argument("--editar", default="", help='"diasAtras:campo=valor"')
    ap.add_argument("--validaciones", action="store_true", help="probar mensajes de error")
    ap.add_argument("--movil", action="store_true", help="revisar las tres pantallas a 360 px")
    ap.add_argument("--capturas", default="", help="carpeta para capturas de página (opcional)")
    ap.add_argument("--con-ventana", action="store_true")
    a = ap.parse_args()

    clave = os.environ.get("MIRITMO_CLAVE") or secrets.token_urlsafe(12)
    url = a.url.rstrip("/")
    hoy = hoy_cdmx()
    fecha = lambda atras: (hoy - timedelta(days=atras)).isoformat()
    r = {"url": url, "canal": a.canal, "hoy_cdmx": hoy.isoformat(), "pasos": [], "errores_consola": []}

    def paso(nombre, ok, detalle=""):
        r["pasos"].append({"paso": nombre, "ok": bool(ok), "detalle": detalle})

    def captura(pagina, nombre):
        if a.capturas:
            os.makedirs(a.capturas, exist_ok=True)
            # La captura de página completa redimensiona la vista y Chart.js se vuelve a dibujar en blanco;
            # por eso primero se hace la ventana tan alta como la página y luego se captura la vista.
            antes = pagina.viewport_size
            alto = pagina.evaluate("document.documentElement.scrollHeight")
            pagina.set_viewport_size({"width": antes["width"], "height": max(alto, antes["height"])})
            pagina.wait_for_timeout(1200)
            pagina.screenshot(path=os.path.join(a.capturas, f"{a.canal}-{nombre}.png"))
            pagina.set_viewport_size(antes)
            pagina.wait_for_timeout(300)

    with sync_playwright() as p:
        nav = p.chromium.launch(channel=a.canal, headless=not a.con_ventana)
        r["version_navegador"] = nav.version
        ctx = nav.new_context(viewport={"width": 1280, "height": 900}, locale="es-MX")
        pg = ctx.new_page()
        # Los 400/401 provocados a propósito (validaciones, contraseña incorrecta) no cuentan como error.
        es_esperado = lambda txt: "Failed to load resource" in txt and ("(Bad Request)" in txt or "(Unauthorized)" in txt)
        pg.on("console", lambda m: m.type == "error" and not es_esperado(m.text) and r["errores_consola"].append(m.text))
        pg.on("pageerror", lambda e: r["errores_consola"].append(str(e)))

        # RF-02: sin sesión no se abren Mi día ni Mi semana
        for pantalla in ("dia.html", "semana.html"):
            pg.goto(f"{url}/{pantalla}")
            pg.wait_for_url("**/index.html", timeout=15000)
            paso(f"Sin sesión, {pantalla} regresa a Acceso", pg.url.endswith("/index.html"), pg.url)

        # RF-01 / RF-02: entrar a la cuenta
        if a.crear:
            pg.click("#tab-cuenta")
            if a.validaciones:
                pg.fill("#cuenta-nombre", a.nombre)
                pg.fill("#cuenta-correo", a.correo)
                pg.fill("#cuenta-contrasena", "abc1234")
                pg.click("#form-cuenta button[type=submit]")
                pg.wait_for_selector("#alerta:not([hidden])")
                texto = pg.locator("#form-cuenta [data-error=contrasena]").inner_text()
                paso("Validación: contraseña de 7 caracteres", texto != "", f"{pg.inner_text('#alerta')} / {texto}")
                captura(pg, "validacion-contrasena")
            pg.fill("#cuenta-nombre", a.nombre)
            pg.fill("#cuenta-correo", a.correo)
            pg.fill("#cuenta-contrasena", clave)
            pg.click("#form-cuenta button[type=submit]")
            pg.wait_for_url("**/dia.html", timeout=20000)
            paso("Crear cuenta y entrar a Mi día", True, pg.url)
        else:
            pg.fill("#entrar-correo", a.correo)
            pg.fill("#entrar-contrasena", clave)
            pg.click("#form-entrar button[type=submit]")
            pg.wait_for_url("**/dia.html", timeout=20000)
            paso("Iniciar sesión y entrar a Mi día", True, pg.url)

        # RF-03: opciones de fecha
        opciones = pg.eval_on_selector_all("#fecha option", "os => os.map(o => o.value)")
        esperadas = [fecha(i) for i in range(7)]
        paso("Fechas: hoy y los 6 días anteriores", opciones == esperadas, ", ".join(opciones))

        def elegir(atras):
            pg.select_option("#fecha", fecha(atras))
            pg.wait_for_function("!document.getElementById('form-dia').hasAttribute('aria-busy')")
            pg.wait_for_timeout(300)

        def guardar_y_leer():
            t0 = time.perf_counter()
            with pg.expect_response(lambda resp: "/registros/" in resp.url and resp.request.method == "PUT") as info:
                pg.click("#form-dia button[type=submit]")
            estado = info.value.status
            if estado == 200:
                pg.wait_for_selector("#resultado:not([hidden])")
                pg.wait_for_function("document.querySelector('#form-dia button[type=submit]').textContent === 'Guardar cambios'")
            return estado, pg.inner_text("#calificacion"), round(time.perf_counter() - t0, 2)

        def llenar(d):
            for c in ("horas_trabajo", "tareas", "horas_sueno"):
                pg.fill(f"#{c}", numero_texto(d[c]))
            pg.click(f"label[for=energia-{d['energia']}]")

        # Validaciones de Mi día
        if a.validaciones:
            elegir(0)
            pg.fill("#horas_trabajo", "17"); pg.fill("#tareas", "4"); pg.fill("#horas_sueno", "7.5")
            pg.click("label[for=energia-4]")
            estado, _, _ = guardar_y_leer()
            err = pg.locator("#form-dia [data-error=horas_trabajo]").inner_text()
            paso("Validación: 17 h de estudio (máximo 16)", estado == 400 and err != "", f"HTTP {estado}: {pg.inner_text('#alerta')} / {err}")
            captura(pg, "validacion-horas")
            pg.fill("#horas_trabajo", ""); pg.fill("#tareas", ""); pg.fill("#horas_sueno", "")
            pg.evaluate("document.querySelectorAll('input[name=energia]').forEach(r => r.checked = false)")
            estado, _, _ = guardar_y_leer()
            faltan = pg.eval_on_selector_all("#form-dia .error-campo", "es => es.filter(e => e.textContent).map(e => e.dataset.error + ': ' + e.textContent)")
            paso("Validación: formulario vacío", estado == 400 and len(faltan) == 4, "; ".join(faltan))

        # RF-03 / RF-04: registrar días
        registrados = {}
        for atras, d in sorted(parsear_dias(a.dias).items(), reverse=True):
            elegir(atras)
            llenar(d)
            estado, calif, seg = guardar_y_leer()
            esperado = calificacion(d["horas_trabajo"], d["tareas"], d["horas_sueno"], d["energia"])
            registrados[fecha(atras)] = int(calif)
            paso(f"Registrar {fecha(atras)} {d}", estado == 200 and int(calif) == esperado,
                 f"HTTP {estado}, muestra {calif}, cálculo a mano {esperado}, {seg} s")
            if (d["horas_trabajo"], d["tareas"], d["horas_sueno"], d["energia"]) == (6, 4, 7.5, 4):
                captura(pg, "dia-84")

        # RF-05: consultar y editar un día
        if a.editar:
            atras, cambio = a.editar.split(":")
            atras = int(atras)
            campo, valor = cambio.split("=")
            elegir(atras)
            aviso = pg.inner_text("#aviso") if pg.is_visible("#aviso") else ""
            antes = {c: pg.input_value(f"#{c}") for c in ("horas_trabajo", "tareas", "horas_sueno")}
            antes["energia"] = pg.eval_on_selector("input[name=energia]:checked", "e => e.value") if pg.locator("input[name=energia]:checked").count() else None
            calif_antes = pg.inner_text("#calificacion")
            paso(f"RF-05: al elegir {fecha(atras)} el formulario muestra sus datos", "Ya registraste" in aviso and antes["tareas"] != "",
                 f"aviso '{aviso}', datos {antes}, calificación mostrada {calif_antes}, botón '{pg.inner_text('#form-dia button[type=submit]')}'")
            captura(pg, "editar-antes")
            if campo == "energia":
                pg.click(f"label[for=energia-{valor}]")
            else:
                pg.fill(f"#{campo}", valor)
            estado, calif, seg = guardar_y_leer()
            nuevo = {k: float(v) if v not in (None, "") else None for k, v in antes.items()}
            nuevo[campo] = float(valor)
            esperado = calificacion(nuevo["horas_trabajo"], int(nuevo["tareas"]), nuevo["horas_sueno"], int(nuevo["energia"]))
            registrados[fecha(atras)] = int(calif)
            paso(f"RF-05: editar {fecha(atras)} {campo}={valor} recalcula", estado == 200 and int(calif) == esperado,
                 f"antes {calif_antes}, después {calif}, cálculo a mano {esperado}, {seg} s")
            captura(pg, "editar-despues")
            r["editado"] = {"fecha": fecha(atras), "campo": campo, "valor": valor, "antes": calif_antes, "despues": calif}

        # RF-06 / RF-07: Mi semana
        pg.click("nav.pestanas a[href='semana.html']")
        pg.wait_for_url("**/semana.html")
        pg.wait_for_function("window.Chart && Chart.getChart('grafica')", timeout=15000)
        pg.wait_for_timeout(800)
        datos = pg.evaluate("Chart.getChart('grafica').data.datasets[0].data")
        etiquetas = pg.evaluate("Chart.getChart('grafica').data.labels.map(e => [].concat(e).join(' ').trim())")
        # La gráfica debe tener pixeles dibujados (no un lienzo en blanco).
        pintado = pg.evaluate("""() => { const c = document.getElementById('grafica'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
            let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return n; }""")
        lista = pg.eval_on_selector_all("#dias li", "ls => ls.map(l => [...l.children].map(c => c.textContent))")
        sem = {"promedio": pg.inner_text("#promedio"), "registrados": pg.inner_text("#registrados"),
               "mejor": pg.inner_text("#mejor"), "mejor_fecha": pg.inner_text("#mejor-fecha"),
               "grafica": dict(zip(etiquetas, datos)), "lista": lista}
        r["semana"] = sem
        captura(pg, "semana")
        vacios = sum(1 for x in datos if x is None)
        paso("RF-06: gráfica de 7 días con 'Sin registro' en los vacíos",
             len(datos) == 7 and pintado > 1000 and vacios == sum(1 for f in lista if f[1] == "Sin registro"),
             f"{7 - vacios} con barra, {vacios} 'Sin registro', {pintado} pixeles dibujados")
        valores = [x for x in datos if x is not None]
        if valores:
            prom = sum(valores) / len(valores)
            # Intl.NumberFormat redondea .x5 hacia arriba (73.25 -> 73.3); se replica sin el redondeo bancario de Python.
            prom_txt = f"{int(prom * 10 + 0.5) / 10:.1f}".rstrip("0").rstrip(".")
            paso("RF-07: promedio y mejor día", sem["promedio"] == prom_txt and int(sem["mejor"]) == max(valores),
                 f"app: promedio {sem['promedio']}, mejor {sem['mejor']} ({sem['mejor_fecha']}); a mano: {' + '.join(map(str, valores))} = {sum(valores)} / {len(valores)} = {prom:.2f}, máximo {max(valores)}")
        if registrados:
            coincide = all(sem["grafica"].get(et) == v for et, v in [(e, d) for e, d in zip(etiquetas, datos) if d is not None])
            paso("La semana coincide con lo guardado", coincide and sorted(valores) == sorted(registrados.values()) if len(valores) == len(registrados) else coincide,
                 f"guardado en esta corrida: {registrados}")

        # RNF-04: 360 px
        if a.movil:
            pg.set_viewport_size({"width": 360, "height": 780})
            revisar = """() => {
                const w = document.documentElement.clientWidth;
                const fuera = [...document.querySelectorAll('body *')].filter(e => {
                    const b = e.getBoundingClientRect(); return b.width && (b.right > w + 0.5 || b.left < -0.5);
                }).map(e => e.tagName + (e.id ? '#' + e.id : ''));
                return {scrollWidth: document.documentElement.scrollWidth, clientWidth: w, fuera: fuera.slice(0, 5)};
            }"""
            for pantalla in ("semana.html", "dia.html"):
                pg.goto(f"{url}/{pantalla}")
                pg.wait_for_timeout(1500)
                m = pg.evaluate(revisar)
                paso(f"RNF-04: {pantalla} a 360 px", m["scrollWidth"] <= 360 and not m["fuera"], json.dumps(m))
                captura(pg, f"360-{pantalla.split('.')[0]}")

        # RF-02: cerrar sesión, contraseña incorrecta y volver a entrar
        pg.goto(f"{url}/dia.html")
        pg.click("#salir")
        pg.wait_for_url("**/index.html")
        paso("Cerrar sesión regresa a Acceso", pg.evaluate("localStorage.getItem('miritmo.sesion')") is None, pg.url)
        if a.movil:
            pg.wait_for_timeout(500)
            m = pg.evaluate(revisar)
            paso("RNF-04: index.html a 360 px", m["scrollWidth"] <= 360 and not m["fuera"], json.dumps(m))
            captura(pg, "360-index")
            pg.set_viewport_size({"width": 1280, "height": 900})
        pg.fill("#entrar-correo", a.correo)
        pg.fill("#entrar-contrasena", "incorrecta123")
        pg.click("#form-entrar button[type=submit]")
        pg.wait_for_selector("#alerta:not([hidden])")
        paso("Contraseña incorrecta muestra error", True, pg.inner_text("#alerta"))
        pg.fill("#entrar-contrasena", clave)
        pg.click("#form-entrar button[type=submit]")
        pg.wait_for_url("**/dia.html", timeout=20000)
        paso("Iniciar sesión con datos correctos", True, pg.url)
        nav.close()

    r["todo_ok"] = all(x["ok"] for x in r["pasos"]) and not r["errores_consola"]
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r["todo_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
