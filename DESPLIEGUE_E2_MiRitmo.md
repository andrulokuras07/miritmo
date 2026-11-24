# Despliegue de MiRitmo – Entregable 2 (Examen final)

- Fecha: 24 de noviembre de 2026
- Alcance: MVP completo (RF-01 a RF-07, RNF-01 a RNF-07) desplegado **sobre la misma infraestructura del Entregable 1**: no se creó ningún recurso nuevo en AWS ni en IBM Cloud.
- Bitácora completa, con cada comando y su salida numerados y sin secretos: [`evidencias/despliegue_e2_log.md`](evidencias/despliegue_e2_log.md) (entradas 1 a 31). En este documento, `[n]` remite a esa entrada.
- Resultados detallados de aceptación: [`entregable-2/docs/pruebas-aceptacion.md`](entregable-2/docs/pruebas-aceptacion.md).
- Ningún secreto quedó en archivos, en git ni en las capturas. Las credenciales de Cloudant solo se leyeron en memoria desde el CLI de IBM; las variables de entorno de la Lambda no se tocaron. La contraseña de `examen@miritmo.mx` no está escrita en ningún archivo.

## 1. URLs

| Qué | URL |
|---|---|
| Aplicación (CloudFront, HTTPS) | https://dnfx295km7eni.cloudfront.net |
| API (URL de función Lambda) | https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws |
| **Repositorio público (GitHub, RNF-07)** | **https://github.com/andrulokuras07/miritmo** |

Cuentas de demostración: `examen@miritmo.mx` (4 días del 19 al 24 de noviembre; el 23 editado; vacíos el 18, el 20 y el 22) y `demo@miritmo.mx` (del Entregable 1).

## 2. Qué cambió respecto al Entregable 1

**Funciones nuevas (código de `entregable-2/`)**
- `GET /registros?desde=&hasta=` (rango de hasta 31 días, solo los registros del usuario del token).
- **RF-05** Mi día carga los datos de una fecha ya registrada, muestra "Ya registraste este día…" y guarda con "Guardar cambios" (mismo documento, `_rev` nuevo, calificación recalculada).
- **RF-06 / RF-07** Pantalla **Mi semana**: gráfica de barras con Chart.js 4.4.4 (copia local en `vendor/`), "Sin registro" en los días vacíos, promedio, mejor día y lista "Día por día" con enlaces para editar o registrar.
- Validaciones con mensajes claros por campo en Acceso, Mi día y Mi semana.

**Correcciones del Entregable 1 aplicadas al Entregable 2 (paso 1)**
- CORS duplicado: el código solo agrega encabezados CORS con `CORS_EN_CODIGO=1` (lo pone `servidor_local.py`); en AWS los pone la URL de función.
- `requirements.txt` con las versiones fijas del Entregable 1 (`ibmcloudant==0.11.13`, etc.).
- `NaN`/`Infinity` responden 400 (`validacion.py`) y su prueba unitaria: 36 pruebas en total.
- `scripts/empaquetar_lambda.py` (los `.sh` no corren en Windows).

**Otros cambios**
- `scripts/publicar_frontend.py`: escribe `config.js` en una copia temporal, sube cada archivo con su Content-Type (y `Cache-Control: no-cache`, para que nadie vea una versión vieja después de publicar), invalida `/*` y espera.
- Mi semana: etiquetas del eje en dos renglones ("Sáb" / "21") porque a 360 px se encimaban.
- `scripts/desplegar_aws.sh` (ruta de Linux): la URL de función ahora se crea con CORS; antes confiaba en el CORS del código.
- `entregable-2/README.md`: decía "Deja CORS desactivado"; ahora dice cómo configurarlo.
- `README.md` de la raíz reescrito para desplegar desde Windows con PowerShell (RNF-07) y plantillas JSON en `entregable-2/config/`.
- Descripción de la Lambda: "API de MiRitmo (Entregable 2)" [29].
- `.gitignore`: `CLAUDE.md`, `.claude/` y `.env*`.
- Scripts de prueba nuevos en `evidencias/`: `pruebas_curl_e2.ps1`, `pruebas_navegador.py` (Playwright), `rendimiento_api.py`, `unitarias.ps1`.

## 3. Recursos (los mismos del Entregable 1)

| Recurso | Nombre / ID | Cambio en el E2 |
|---|---|---|
| Función Lambda (Python 3.12, x86_64, 256 MB, 10 s) | `miritmo-api` | Código nuevo y descripción. Variables de entorno sin tocar (`CLOUDANT_URL`, `CLOUDANT_APIKEY`, `TOKEN_SECRET`, `ALLOWED_ORIGIN`) [6] |
| URL de función (auth NONE, CORS solo CloudFront: GET, POST, PUT) | `https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws/` | Ninguno: ya permitía GET [4] |
| Bucket S3 privado | `miritmo-frontend-5e016053` | Archivos nuevos: `semana.html`, `js/semana.js`, `vendor/chart.umd.min.js` [7] |
| Distribución CloudFront | `E1C3936GEOWFBQ` → `dnfx295km7eni.cloudfront.net` | Invalidaciones `/*` [7][25] |
| Rol IAM | `miritmo-lambda-rol` | Ninguno |
| Cloudant Lite (us-south) | `miritmo-cloudant`, bases `usuarios` y `registros` | Ninguno (solo datos) |

## 4. Comandos, en orden (sin secretos)

Todo desde PowerShell en Windows con AWS CLI 2.40 (`--profile miritmo`, us-east-2), IBM Cloud CLI y Python 3.12.

**Paso 1 – Correcciones y pruebas locales**
```powershell
cd entregable-2\backend; python -m unittest discover -s tests          # 36/36 OK
python entregable-2\scripts\servidor_local.py                           # http://localhost:8080
python evidencias\pruebas_navegador.py --url http://localhost:8080 --correo local@mail.com --crear --validaciones --movil --dias "0:6,4,7.5,4;1:5,3,8,3;3:8,5,6.5,5;5:4,2,5,2" --editar "1:tareas=5"   # 22/22
```

**Paso 2 – Nueva versión sobre los mismos recursos**
```powershell
aws login --profile miritmo
aws sts get-caller-identity --profile miritmo                                         # [1]
aws freetier get-account-plan-state --profile miritmo --region us-east-1             # [2] FREE, ACTIVE
aws lambda get-function-configuration --function-name miritmo-api --profile miritmo  # [3]
aws lambda get-function-url-config --function-name miritmo-api --profile miritmo     # [4] CORS ya incluye GET
python entregable-2\scripts\empaquetar_lambda.py                                      # 886 archivos, 1.5 MB
aws lambda update-function-code --function-name miritmo-api --zip-file fileb://entregable-2/build/miritmo-lambda.zip --profile miritmo   # [5]
aws lambda wait function-updated-v2 --function-name miritmo-api --profile miritmo    # [6] Successful, mismo SHA-256 que el zip local
python entregable-2\scripts\publicar_frontend.py --bucket miritmo-frontend-5e016053 --distribucion E1C3936GEOWFBQ --api https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws --perfil miritmo --esperar   # [7]
curl.exe -s -o NUL -w "%{http_code} %{content_type}" https://dnfx295km7eni.cloudfront.net/<archivo>   # [8] 11 archivos
python evidencias\pruebas_navegador.py --url https://dnfx295km7eni.cloudfront.net --canal chrome --correo pruebaE2-reg-<marca>@miritmo.mx --crear --dias "0:5,3,8,3"   # [9] regresión 11/11
```

**Paso 3 – Cuenta de demostración**
```powershell
$env:MIRITMO_CLAVE = <contraseña aleatoria, solo en memoria>
python evidencias\pruebas_navegador.py --url https://dnfx295km7eni.cloudfront.net --canal chrome --correo examen@miritmo.mx --crear --validaciones --movil --dias "0:6,4,7.5,4;1:5,3,8,3;3:8,5,6.5,5;5:4,2,5,2" --editar "1:tareas=5"   # [10] 22/22
```

**Paso 4 – Pruebas de aceptación**
```powershell
powershell -ExecutionPolicy Bypass -File evidencias\pruebas_curl_e2.ps1     # [11] 18/18
python evidencias\rendimiento_api.py                                         # [12] 19/19 < 3 s
curl.exe -X OPTIONS <api>/registros?... -H "Origin: https://dnfx295km7eni.cloudfront.net" -H "Access-Control-Request-Method: GET"   # [13]
python evidencias\pruebas_navegador.py ... --canal chrome  /  --canal msedge  # [14][15] 22/22 cada uno
aws logs filter-log-events --log-group-name /aws/lambda/miritmo-api --start-time <19:50 UTC> --filter-pattern "?Traceback ?ERROR ?""Task timed out"" ?Exception"   # [16] 0
aws logs filter-log-events --log-group-name /aws/lambda/miritmo-api --start-time <19:50 UTC> --filter-pattern REPORT   # [17][18]
cd entregable-2\backend; python -m unittest discover -s tests -v            # [19] 36/36
ibmcloud login --sso -r us-south -c <cuenta> -g Default                      # código de un solo uso (no registrado)
ibmcloud resource service-instance miritmo-cloudant                         # [20] plan lite
python con_cloudant.py listar | ver examen@miritmo.mx | borrar <lista>      # [21]-[24] credencial solo en memoria
```

**Paso 5 – README y GitHub**
```powershell
git clone <repo> <carpeta temporal>\miritmo; cd miritmo; <bloques de la sección 6 del README>   # [25][26]
git grep -I -E "<15 patrones>" $(git rev-list --all); git log --all --name-only             # [27] historial limpio
gh auth switch --user andrulokuras07; gh api user --jq .login                               # andrulokuras07 (cuenta de la escuela)
gh repo create andrulokuras07/miritmo --public --source . --remote origin
git config --local credential.https://github.com.username andrulokuras07
git push -u origin master; gh repo edit andrulokuras07/miritmo --default-branch master     # [28]
```

**Paso 6 – Capturas y limpieza**
```powershell
aws lambda update-function-configuration --function-name miritmo-api --description "API de MiRitmo (Entregable 2)" --profile miritmo   # [29]
python con_cloudant.py borrar <3 cuentas creadas por las capturas 13 y 14>                                                            # [30][31]
```

## 5. Pruebas (requerimiento | pasos | esperado | obtenido)

Todas contra las URLs públicas. Las cuentas de prueba (`prueba*@miritmo.mx`, contraseñas aleatorias) se borraron al final [23][24][30][31]; quedan solo `examen@` y `demo@`.

| Requerimiento | Pasos | Resultado esperado | Resultado obtenido |
|---|---|---|---|
| RF-01 | `POST /cuentas` con datos nuevos; luego desde la pantalla Crear cuenta | 201 y entra a Mi día | ✅ 201, token (oculto) [11]; en Chrome y Edge entra a Mi día [14][15] |
| RF-01 | Mismo correo | Error | ✅ 409 "Ya existe una cuenta con ese correo." [11] |
| RF-01 | Contraseña de 7 caracteres | Error claro | ✅ 400 "Revisa los datos marcados." y en el campo "La contraseña debe tener al menos 8 caracteres." [10][11] |
| RF-01 | Documento en `usuarios` | Sin contraseña en texto plano | ✅ Solo `_id, _rev, correo, creado, hash, nombre, sal` [22] |
| RF-02 | Iniciar sesión correcto / incorrecto | Entra / "Correo o contraseña incorrectos." | ✅ 200 / 401 con ese mensaje (curl y navegador) [9][11] |
| RF-02 | Sin sesión abrir `/dia.html` y `/semana.html`; cerrar sesión | Regresa a Acceso | ✅ Ambas regresan a `index.html`; cerrar sesión borra la sesión [9][14][15] |
| RF-03 | Opciones de fecha | Hoy y 6 días atrás | ✅ 2026-11-24 a 2026-11-18 [10] |
| RF-03 | `PUT` hoy / futuro / hace 7 días | 200 / 400 / 400 | ✅ 200 / 400 "No puedes registrar días futuros." / 400 "Solo puedes registrar hoy o los 6 días anteriores." [11] |
| RF-04 | 6 h, 4 tareas, 7.5 h, energía 4 | 84 | ✅ 84 "Buen día" (navegador [10], curl [11], Cloudant [22]) |
| RF-05 | Elegir el 23 (ya registrado), cambiar tareas 3 → 5 y guardar | Muestra los datos; recalcula en el mismo registro | ✅ Formulario con 5 / 3 / 8 / energía 3 y 71 → guardado **81** (a mano: 15.625 + 25 + 25 + 15 = 80.6 → 81); `_rev 2-` [10][22] |
| RF-06 | Mi semana con 3 días vacíos | Barras de 7 días y "Sin registro" | ✅ 38, 90, 81, 84 y "Sin registro" en el 18, el 20 y el 22 [10] |
| RF-07 | Resumen de Mi semana | Promedio y mejor día correctos | ✅ Promedio **73.3** ((38 + 90 + 81 + 84) / 4 = 73.25), mejor día **90** (sábado 21) [10] |
| Validaciones | 17 h de estudio; formulario vacío; rango inválido; NaN | Mensajes claros | ✅ "Debe estar entre 0 y 16 horas."; un mensaje en cada uno de los 4 campos; 400 "El rango de fechas es inválido."; NaN/Infinity 400 (unitaria) [10][11][19] |
| RNF-01 | `http://` y `https://` de CloudFront | 301 → https; 200 | ✅ [8]. Celular con datos móviles: **pendiente** (iPhone del usuario) |
| RNF-02 | `PUT` y `GET /registros` sin token / con token alterado | 401 | ✅ 401 los cuatro [11] |
| RNF-02 | `GET /registros` con token de A y de B | Cada uno solo ve lo suyo | ✅ A: `2026-11-24=84`; B: `2026-11-24=10` [11] |
| RNF-02 | B manda `usuario: A` o usa la ruta `/registros/<A>:<fecha>` | Se guarda como B / rechazo | ✅ 200 como B / 400 "Fecha inválida." [11] |
| RNF-02 / CORS | Preflight GET y GET desde CloudFront; GET desde otro origen | Permitido solo CloudFront, un solo encabezado | ✅ 200 con `Access-Control-Allow-Origin` de CloudFront (uno solo); otro origen 403 [13] |
| RNF-02 | S3 directo | Denegado | ✅ 403 [8] |
| RNF-03 | 20 peticiones GET/PUT, sin la primera | ≥ 9 de 10 en < 3 s | ✅ 19/19 en las dos corridas (ver sección 6) [12], captura 13 |
| RNF-04 | Acceso, Mi día y Mi semana a 360 px | Sin scroll horizontal ni nada cortado | ✅ `scrollWidth = 360` y 0 elementos fuera en las tres, Chrome y Edge [10][14][15]. Cronómetro con 5 compañeros: **pendiente** |
| RNF-05 | Plan de AWS y de Cloudant | $0; Lite | ✅ AWS FREE/ACTIVE, 119.99 USD de crédito sin usar [2], captura 18; Cloudant **lite** [20], captura 19 |
| RNF-06 | Flujo completo en Chrome 158 y Edge 158 | Funciona | ✅ 22/22 pasos en cada uno, sin errores de consola [14][15]. Safari (iPhone): **pendiente** |
| RNF-07 | README seguido al pie de la letra desde un clon limpio | Despliega y funciona | ✅ Sección 6 *Publicar una nueva versión* sin cambios: 36/36, zip, Lambda, frontend, invalidación y verificación [25]; la app siguió funcionando [26]. Repositorio público en GitHub |
| Logs | CloudWatch desde el despliegue | 0 errores | ✅ 0 eventos con `Traceback`, `ERROR`, `Task timed out` o `Exception` [16], captura 17 |
| Unitarias | `python -m unittest` (E2) | Todas OK | ✅ 36/36 [19], captura 15 |

## 6. Tiempos de RNF-03

Script `evidencias/rendimiento_api.py`: cuenta temporal, 20 peticiones alternando `GET /registros` (7 días) y `PUT /registros/<fecha>`, conexión HTTPS nueva en cada una, sin contar la primera.

| # | Método | Corrida 1 [12] (s) | Corrida 2, captura 13 (s) |
|---|---|---|---|
| 1 | GET | 0.324 (descartada) | 0.323 (descartada) |
| 2 | PUT | 0.392 | 0.479 |
| 3 | GET | 0.300 | 0.297 |
| 4 | PUT | 0.343 | 0.347 |
| 5 | GET | 0.308 | 0.319 |
| 6 | PUT | 0.359 | 0.380 |
| 7 | GET | 0.299 | 0.324 |
| 8 | PUT | 0.338 | 0.358 |
| 9 | GET | 0.307 | 0.327 |
| 10 | PUT | 0.358 | 0.375 |
| 11 | GET | 0.339 | 0.334 |
| 12 | PUT | 0.341 | 0.365 |
| 13 | GET | 0.296 | 0.306 |
| 14 | PUT | 0.333 | 0.355 |
| 15 | GET | 0.328 | 0.349 |
| 16 | PUT | 0.343 | 0.378 |
| 17 | GET | 0.285 | 0.305 |
| 18 | PUT | 0.374 | 0.344 |
| 19 | GET | 0.313 | 0.319 |
| 20 | PUT | 0.352 | 0.397 |
| | **Menos de 3 s** | **19 de 19 (100 %)** | **19 de 19 (100 %)** |
| | Mín. / mediana / máx. | 0.285 / 0.338 / 0.392 | 0.297 / 0.347 / 0.479 |

Arranque en frío: la primera invocación después de actualizar el código tardó 6.07 s dentro de la Lambda (`Init Duration` 219 ms + primera conexión a Cloudant + PBKDF2 de `POST /cuentas`) [17][18]. El criterio no cuenta la primera petición después de un rato sin uso; las otras 136 ejecuciones registradas tardaron 775 ms o menos.

## 7. Repositorio (RNF-07)

- URL: **https://github.com/andrulokuras07/miritmo** (público, cuenta de la escuela `andrulokuras07`, rama `master`, remoto `origin`).
- Antes de subir se revisó **todo el historial** (16 commits, todas las versiones de cada archivo) [27]: sin apikeys, tokens, contraseñas reales, host de Cloudant, URLs con credenciales, llaves de AWS ni llaves privadas. `CLAUDE.md`, `build/` y `.env` nunca se subieron y están en `.gitignore`. Las únicas "contraseñas" son valores de prueba de los tests (`abc1234`, `contrasena123`, …).
- El README de la raíz explica cómo desplegar desde Windows: requisitos, `aws login` e `ibmcloud login`, crear Cloudant, primer despliegue y publicar una nueva versión.

## 8. Capturas

Carpeta: `..\Capturas Entregable 2\`. La 12 (Safari en el iPhone con datos móviles) la toma el usuario. Todas se abrieron y revisaron una por una.

| Número | Archivo | Qué se ve | Revisada |
|---|---|---|---|
| 01 | 01.png | Lambda `miritmo-api`: descripción "API de MiRitmo (Entregable 2)", "Última modificación: hace 17 minutos", URL de función y el código del Entregable 2 en el editor | ✅ |
| 02 | 02.png | S3 → Objetos: `css/`, `dia.html`, `img/`, `index.html`, `js/`, `semana.html`, `vendor/` (24 nov 2026) | ✅ |
| 03 | 03.png | CloudFront `E1C3936GEOWFBQ` → Invalidaciones: tres invalidaciones "Completed" (dos del 24 de noviembre) | ✅ |
| 04 | 04.png | GitHub `andrulokuras07/miritmo` **Public**, rama `master`, archivos y el README visible | ✅ |
| 05 | 05.png | Mi día, 23 de noviembre ya registrado: "Ya registraste este día…", 5 / 3 / 8 / energía 3, 71 y botón "Guardar cambios" (RF-05) | ✅ |
| 06 | 06.png | Después de cambiar tareas a 5 y guardar: "Guardado…", **81** (RF-05) | ✅ |
| 07 | 07.png | Mi semana: promedio 73.3, mejor día 90 (sábado 21), gráfica con "Sin registro" en el 18, el 20 y el 22, lista día por día (RF-06, RF-07) | ✅ |
| 08 | 08.png | Validación: 17 h de estudio → "Revisa los datos marcados." y "Debe estar entre 0 y 16 horas." en el campo | ✅ |
| 09 | 09.png | Acceso, Mi día y Mi semana a 360 px, lado a lado, completas (RNF-04) | ✅ |
| 10 | 10.png | Ventana de **Chrome** con Mi semana en `dnfx295km7eni.cloudfront.net/semana.html` (RNF-06) | ✅ |
| 11 | 11.png | Ventana de **Microsoft Edge** con Mi semana en `https://dnfx295km7eni.cloudfront.net/semana.html` (RNF-06) | ✅ |
| 12 | — | (la toma el usuario: Safari en iPhone con datos móviles) | — |
| 13 | 13.png | Terminal: 20 peticiones, cada tiempo, 19 de 19 en menos de 3 s, "RNF-03: CUMPLE" | ✅ |
| 14 | 14.png | Terminal: 18 pruebas con curl (RF-01 a RF-04, RF-06, RNF-02, GET sin token y con token alterado = 401), tokens ocultos, "18 de 18" | ✅ |
| 15 | 15.png | Terminal: las 36 pruebas unitarias `ok`, "Ran 36 tests … OK" | ✅ |
| 16 | 16.png | Cloudant `registros` → `examen@miritmo.mx:2026-11-23` con `tareas: 5`, `calificacion: 81`, `actualizado: 2026-11-24T19:57:59`, `_rev 2-…` (barra de dirección tapada: host de Cloudant) | ✅ |
| 17 | 17.png | CloudWatch `/aws/lambda/miritmo-api` filtrado por `?ERROR ?Traceback ?Timeout ?Exception` (últimas 4 h): "No se encontraron eventos" | ✅ |
| 18 | 18.png | AWS Nivel gratuito: "No se cobrará nada a la cuenta del plan gratuito", 0 ofertas en uso, $120.00 de crédito restante (RNF-05) | ✅ |
| 19 | 19.png | IBM Cloud `miritmo-cloudant`, Dallas, IAM: "You are currently subscribed to the Lite plan." (filas *External endpoint* tapadas: host de Cloudant) (RNF-05) | ✅ |

Método: igual que en el Entregable 1. Las capturas de consola se tomaron en el Chrome del usuario (pestaña activada por el usuario), comprobando antes y después que Chrome estuviera al frente y recortando la ventana con `CopyFromScreen`. Cada imagen se revisó automáticamente para descartar los avisos de la extensión ("Claude started debugging", recuadro naranja); si aparecían, se repetía la captura. Las 05 a 09 son capturas de página con Playwright (como las 16–18 del Entregable 1); la 10 y la 11 son ventanas visibles de Chrome y Edge; la 13 a la 15 son ventanas de Windows Terminal.

## 9. Problemas encontrados y cómo se resolvieron

1. **El código del E2 era anterior a las correcciones del E1** (CORS duplicado, versiones abiertas, NaN → 500, sin empaquetador en Python). Se aplicaron antes de desplegar (paso 1); sin eso, la app no habría conectado desde el navegador.
2. **`desplegar_aws.sh` y el README del E2 decían que el CORS lo ponía el código** ("Deja CORS desactivado"). Con la corrección, quien siguiera esa guía habría desplegado una app sin CORS. Se corrigieron los dos.
3. **Etiquetas del eje encimadas a 360 px** en Mi semana ("Sáb 21Dom 22Lun 23"). Ahora van en dos renglones.
4. **La gráfica salía en blanco en capturas de página completa**: Playwright redimensiona la vista y Chart.js se redibuja con animación. La gráfica sí estaba dibujada (24 038 píxeles pintados); se cambió el método de captura (vista tan alta como la página).
5. **Redondeo del promedio en el script de prueba**: 73.25 → la app muestra 73.3 (Intl redondea .5 hacia arriba) y Python daba 73.2 (redondeo bancario). El error era del script; se corrigió el script.
6. **Arranque en frío de 6.07 s** en la primera invocación después del despliegue. Está fuera del criterio de RNF-03 (que excluye la primera petición tras inactividad); las demás tardaron 775 ms o menos.
7. **`ibmcloud login` pidió elegir entre dos cuentas** y se consumió el primer código de un solo uso. Con el segundo se pasó `-c <cuenta>` para evitar la pregunta.
8. **El correo se guarda en minúsculas**: la lista de cuentas a borrar se normalizó antes de borrar.
9. **Push a GitHub**: el `~/.gitconfig` global tiene `credential.https://github.com.username` de otra cuenta. No se tocó la configuración global; se agregó un valor **local** del repositorio con `andrulokuras07`. El primer intento de push falló antes de enviar nada. El repositorio se creó con rama por defecto `main`; se cambió a `master` para que se vea el README.
10. **`unittest -v` (36 pruebas) no cabía en una pantalla** para la captura 15: `evidencias/unitarias.ps1` corre las mismas pruebas y las muestra en dos columnas, con el resumen original de unittest.
11. **Capturas en Chrome**:
    - La pestaña de la extensión no quedaba activa en la ventana; el usuario la activó con un clic, como en el Entregable 1.
    - La extensión muestra avisos mientras trabaja; se agregó una revisión automática de cada imagen y se repitió la captura cuando aparecían.
    - El panel de Cloudant abre su sesión en el dominio `cloudant.com`; se llegó con "Launch Dashboard" y se tapó la barra de dirección.
    - La página de la instancia muestra el host de Cloudant en *External endpoint*; esas filas se taparon en la 19. Los borradores sin tapar se borraron.
    - En la 10 y la 11 la ventana pasaba por debajo de la barra de tareas; se recortó esa franja.
12. **El script del terminal leyó mal la ruta con "ó"** (PowerShell 5.1 sin BOM) en el primer intento de la captura 13; se guardó con BOM y se repitió. Esa ventana se cerró sin capturarla.
13. **El host de Cloudant** aparece en la salida interna de las herramientas del navegador durante la sesión (igual que en el Entregable 1), pero no en archivos, git ni capturas.

## 10. Costos, limpieza y pendientes

- Todo sigue en el plan gratuito de AWS (sin cargos, captura 18) y en Cloudant Lite (captura 19). No se crearon recursos nuevos.
- Se borraron las 11 cuentas de prueba creadas hoy; en Cloudant quedan `demo@miritmo.mx` (1 registro) y `examen@miritmo.mx` (4 registros) [31].
- **Pendientes del usuario:** captura 12 y fila de Safari (iPhone con datos móviles, que también cubre RNF-01 en celular) y la tabla de tiempos de los 5 compañeros (RNF-04) en `entregable-2/docs/pruebas-aceptacion.md`.
