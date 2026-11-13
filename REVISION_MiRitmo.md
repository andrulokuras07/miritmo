# Revisión de MiRitmo antes del despliegue

- Fecha: 13 de noviembre de 2026
- Alcance: toda la carpeta, con foco en `entregable-1/`, que es lo que se entrega ahora. `entregable-2/` se revisó por encima.
- Punto de partida: commit `b29f65b "estado recibido"`. Ningún archivo del proyecto se modificó; este documento es el único archivo nuevo.

---

## 1. Qué hay en la carpeta

```
MiRitmo/
├── README.md, .gitignore, despliegue.env.ejemplo   (plantilla de credenciales, vacía)
├── entregable-1/   ← lo que se entrega ahora (RF-01 a RF-04)
│   ├── backend/    API en Python para AWS Lambda
│   ├── frontend/   páginas web (Acceso y Mi día)
│   └── scripts/    desplegar, empaquetar, publicar, servidor local
└── entregable-2/   misma base + GET /registros, pantalla "Mi semana" con Chart.js (examen final)
```

**Frontend** (`entregable-1/frontend/`): HTML, CSS y JavaScript sin frameworks ni compilación.
- `index.html` + `js/acceso.js`: pantalla **Acceso**, con pestañas para iniciar sesión o crear cuenta.
- `dia.html` + `js/dia.js`: pantalla **Mi día**, con fecha (hoy o 6 días atrás), los 4 datos y la calificación.
- `js/comun.js`: funciones compartidas: guarda el token en `localStorage`, hace las llamadas `fetch` a la API y calcula la fecha de hoy en hora de CDMX.
- `js/config.js`: **el único lugar** donde va la URL de la API.

**Backend** (`entregable-1/backend/`): una sola función Lambda en Python 3.12.
- `lambda_function.py`: recibe la petición de la URL de función, revisa CORS, elige la ruta (`POST /cuentas`, `POST /sesiones`, `PUT /registros/{fecha}`) y responde JSON.
- `miritmo/seguridad.py`: PBKDF2-SHA256 con sal (200 000 iteraciones) y token firmado con HMAC-SHA256 (7 días).
- `miritmo/validacion.py`: valida datos y fechas y devuelve mensajes en español.
- `miritmo/calificacion.py`: la regla de 0 a 100.
- `miritmo/almacen.py`: habla con Cloudant usando el SDK `ibmcloudant`. Sin credenciales usa un almacén en memoria, que solo sirve para pruebas locales.
- `requirements.txt`: una dependencia, `ibmcloudant>=0.11,<1.0`, que trae `ibm-cloud-sdk-core`, `requests`, etc.
- `tests/test_api.py`: 28 pruebas automáticas.

**Cómo se conecta:**

```
Navegador ──HTTPS──▶ CloudFront ──(OAC)──▶ S3 privado (HTML/CSS/JS)
    │  (lee js/config.js para saber la URL de la API)
    └──fetch HTTPS + "Authorization: Bearer <token>"──▶ URL de función Lambda
                                                         ├──▶ IBM Cloudant (usuarios, registros)
                                                         └──▶ CloudWatch Logs
```

**Scripts** (`entregable-1/scripts/`):
- `desplegar_aws.sh`: crea todo con un comando: bases en Cloudant, rol IAM, bucket, CloudFront con OAC, Lambda con su URL, y publica el frontend.
- `empaquetar_lambda.sh`: arma `build/miritmo-lambda.zip` con dependencias para Linux.
- `publicar_frontend.sh`: escribe `config.js` con la URL real, sube a S3 e invalida CloudFront.
- `servidor_local.py`: corre todo en tu PC sin nube.

---

## 2. Tabla de cumplimiento (Entregable 1)

Leyenda: ✅ se cumple · ⚠️ se cumple con matices · ❌ no se cumple · ❔ no se puede saber sin desplegar

### Arquitectura

| Requerimiento | ¿Se cumple? | Evidencia (archivo:línea) | Qué falta |
|---|---|---|---|
| S3 bucket **privado** en us-east-2 | ✅ | `scripts/desplegar_aws.sh:24` (región por defecto us-east-2), `:65-73` (crea el bucket y bloquea todo acceso público), `:123-136` (solo esta distribución de CloudFront puede leer) | Nada |
| HTML/CSS/JS + **Chart.js** | ⚠️ | E1 no usa Chart.js porque no tiene gráfica. Está en `entregable-2/frontend/vendor/chart.umd.min.js` (v4.4.4, copia local, sin CDN) | Nada para E1. Chart.js llega con E2 |
| CloudFront con HTTPS, dominio cloudfront.net | ✅ | `desplegar_aws.sh:86-115` (`redirect-to-https`, OAC, `DefaultRootObject index.html`) | Nada |
| **Una sola** Lambda Python 3.12 con URL de función HTTPS | ✅ | `desplegar_aws.sh:157` (`python3.12`, x86_64), `:172-183` (URL de función, AuthType NONE) | Nada |
| Usa el SDK `ibmcloudant` | ✅ | `backend/requirements.txt:1`, `miritmo/almacen.py:19-23`. Verifiqué que `get_document`, `put_document` y `post_all_docs` existen con esos parámetros en la versión 0.11.13 | Fijar versiones (ver riesgo R4) |
| Cloudant Lite con bases `usuarios` y `registros` | ✅ / ❔ | `scripts/crear_bases_cloudant.py:52-53`, `almacen.py:96-97` | No se puede comprobar el plan Lite desde el código; hay que verlo en IBM Cloud |
| Rol IAM con permisos mínimos (solo CloudWatch Logs) | ⚠️ | `desplegar_aws.sh:52-56` usa solo `AWSLambdaBasicExecutionRole`. **Pero** con `LAMBDA_ROLE_ARN` (`:46-48`, pensado para el `LabRole` de AWS Academy) se usa un rol con muchos más permisos | Si usan AWS Academy, el requisito no se cumple. Hay que documentarlo como limitación (ver R3) |

### Modelo de datos

| Requerimiento | ¿Se cumple? | Evidencia | Qué falta |
|---|---|---|---|
| `usuarios`: `_id` = correo; nombre, correo, hash, sal, creado | ✅ | `lambda_function.py:122-129`. La prueba `test_contrasena_no_se_guarda_en_texto_plano` comprueba exactamente esos 6 campos | Nada |
| `registros`: `_id` = `correo:AAAA-MM-DD`; usuario, fecha, horas_trabajo, tareas, horas_sueno, energia, calificacion, actualizado | ✅ | `lambda_function.py:157-164` | Nada. Cloudant agrega `_rev` por su cuenta, como es normal |

### API

| Requerimiento | ¿Se cumple? | Evidencia | Qué falta |
|---|---|---|---|
| JSON | ✅ | `lambda_function.py:94-108` | Nada |
| `POST /cuentas` (RF-01) | ✅ | `lambda_function.py:119-137, 170-171`. Responde 201, 400 o 409 | Nada |
| `POST /sesiones` (RF-02) | ✅ | `lambda_function.py:140-149, 172-173`. Responde 200 o 401 | Nada |
| `PUT /registros/{fecha}` guarda o actualiza y devuelve la calificación | ✅ | `lambda_function.py:152-166, 174-176`, `almacen.py:51-66` (usa `_rev` para actualizar) | Nada |
| Todas menos cuentas y sesiones exigen token en `Authorization` | ✅ | `lambda_function.py:83-91, 153` | Nada |
| `GET /registros?desde=&hasta=` (opcional) | ✅ (solo en E2) | `entregable-2/backend/lambda_function.py:170-175, 179-180` | Nada; no es obligatorio en E1 |

### Regla de calificación (RF-04)

| Requerimiento | ¿Se cumple? | Evidencia | Qué falta |
|---|---|---|---|
| Trabajo: horas ÷ 8 × 25, tope 25 | ✅ | `miritmo/calificacion.py:18-19` | Nada |
| Tareas: tareas ÷ 5 × 25, tope 25 | ✅ | `calificacion.py:22-23` | Nada |
| Sueño: 7–9 → 25; 6–6.5 o 9.5–10 → 15; otro → 5 | ✅ | `calificacion.py:26-31` | Nada |
| Energía × 5 | ✅ | `calificacion.py:34-35` | Nada |
| Redondeo al entero más cercano | ✅ | `calificacion.py:47`. Usa `floor(x + 0.5)`, así que .5 sube. Esto evita el redondeo bancario de `round()` en Python | Nada |
| **Prueba obligatoria 6 h / 4 / 7.5 / 4 → 84** | ✅ | Probado: prueba unitaria, script local y en el navegador (muestra "84 · Buen día") | Nada |
| Rangos: trabajo 0–16 y sueño 0–14 en pasos de 0.5; tareas 0–20 entero; energía 1–5 entero | ✅ | `miritmo/validacion.py:102-138` | Ver R5 (`NaN`/`Infinity`) |

### Requerimientos funcionales y no funcionales

| Requerimiento | ¿Se cumple? | Evidencia | Qué falta |
|---|---|---|---|
| **RF-01** Cuenta con nombre, correo y contraseña de 8 o más caracteres | ✅ | `validacion.py:29-53`. Probado: 7 caracteres da 400, 8 da 201 | Opcional: rechazar contraseñas de puros espacios (R8) |
| RF-01 No se repite el correo | ✅ | `almacen.py:40-49` (Cloudant responde 409 sin `_rev`), `lambda_function.py:132-135`. El correo se normaliza a minúsculas (`validacion.py:25-26`) | Nada |
| RF-01 Contraseña nunca en texto plano | ✅ | `lambda_function.py:126-127`. Probado: el documento no contiene la contraseña | Nada |
| **RF-02** Iniciar sesión: con datos correctos entra a Mi día | ✅ | `acceso.js:33-35`. Probado en el navegador | Nada |
| RF-02 Con datos incorrectos muestra error | ✅ | `lambda_function.py:143-147` ("Correo o contraseña incorrectos."), `acceso.js:37-38`. Probado (401) | Nada |
| RF-02 Cerrar sesión | ✅ | `dia.html:21`, `comun.js:30-33`. Probado: borra la sesión y regresa a Acceso | El token sigue siendo válido en el servidor hasta que vence (normal con tokens sin estado) |
| RF-02 Sin sesión no se abre Mi día ni Mi semana | ✅ | `dia.html:10-12` (revisa antes de mostrar la página), `comun.js:36-40`. Probado: `/dia.html` redirige a `index.html`. Mi semana no existe en E1; en E2, `semana.html` hace lo mismo | Nada |
| **RF-03** Registrar los 4 datos | ✅ | `dia.html:37-78`, `dia.js:65-91` | Nada |
| RF-03 Hoy por defecto o 6 días atrás, nunca futura | ✅ | Frontend: `dia.js:15-20` (7 opciones, hoy primero). Backend: `validacion.py:80-90`. Probado: +1 día da 400, −7 da 400, −6 da 200 | Nada |
| RF-03 Un solo registro por usuario y fecha en Cloudant | ✅ | `_id` determinista `correo:fecha` (`lambda_function.py:158`) y PUT con `_rev` (`almacen.py:55-66`) | Nada |
| **RF-04** Calcula y muestra 0–100 | ✅ | `lambda_function.py:162`, `dia.js:54-63` | Nada |
| **RNF-01** URL pública HTTPS, celular y computadora, sin instalar nada | ✅ / ❔ | `<meta viewport>` en `index.html:5` y `dia.html:5`, contenedor de máximo 480 px (`estilos.css:54`), botones +/− para celular | Falta probarlo en un celular real con la URL de CloudFront |
| **RNF-02** PBKDF2-SHA256 con sal | ✅ | `seguridad.py:20-28` (sal de 16 bytes, 200 000 iteraciones) | Nada |
| RNF-02 Token HMAC-SHA256 válido 7 días | ✅ | `seguridad.py:11, 45-53` | Nada |
| RNF-02 Sin token o token inválido → 401 | ✅ | `lambda_function.py:83-91, 202-203`. Probado: sin token, firma alterada, otro secreto y token vencido dan 401 | Nada |
| RNF-02 Un usuario no lee ni modifica registros de otro | ✅ | El correo siempre sale del token (`lambda_function.py:156`); se ignora el `usuario` del cuerpo. Prueba `test_cada_usuario_escribe_solo_sus_registros` | Nada |
| RNF-02 Credenciales solo en variables de entorno | ✅ | `almacen.py:90-91`, `lambda_function.py:47`. El escaneo no encontró secretos en ningún archivo (ver sección 3) | Nada |
| RNF-02 CORS: solo el dominio de CloudFront | ⚠️ | `lambda_function.py:189-192`: un navegador desde otro origen recibe 403. Las peticiones **sin** encabezado `Origin` (curl, Postman) sí pasan; la protección real en ese caso es el token | Es una limitación de CORS, no un error. Conviene explicarlo así en el reporte (R6) |
| Pantallas Acceso y Mi día | ✅ | `frontend/index.html`, `frontend/dia.html` | Nada |

---

## 3. Revisiones adicionales

| Revisión | Resultado | Detalle |
|---|---|---|
| Claves, contraseñas, API keys o URLs de Cloudant escritas en archivos | ✅ No hay | Busqué `apikey`, `password`, `secret`, dominios `cloudant`/`appdomain`, llaves `AKIA…`, llaves privadas y URLs `lambda-url`/`cloudfront` reales. Solo aparecen nombres de variables, ejemplos (`d123.cloudfront.net`, `xxxx…`) y secretos de prueba local (`tests/test_api.py:15`, `scripts/servidor_local.py:23`), que no sirven en la nube. `despliegue.env.ejemplo` está vacío y `despliegue.env` está en `.gitignore`. |
| Nombre "MiRitmo" en todas partes | ✅ | 98 apariciones de "MiRitmo"; **cero** de "MiRumbo" o variantes. |
| Un solo lugar para la URL de la API | ✅ | `frontend/js/config.js:4`, que solo se lee en `comun.js:44`. Al publicar, `publicar_frontend.sh:18-23` reescribe ese archivo. Ojo: el `config.js` del repositorio apunta a `http://localhost:8787`, así que subirlo a mano sin editarlo deja la app sin API. |
| Empaquetar la Lambda como .zip para Linux | ✅ (probado en carpeta temporal) | Repetí los pasos de `empaquetar_lambda.sh` fuera del proyecto: `pip install --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:` funciona. Resultado: zip de 1.4 MB con 876 archivos, `lambda_function.py` y `miritmo/` en la raíz, y binarios de Linux (`charset_normalizer/*.cpython-312-x86_64-linux-gnu.so`). **Pero el script tal cual no corre en esta PC Windows**: en Git Bash no existen `python3` ni `zip` (ver R1). |
| Pruebas automáticas | ✅ | **E1: 28/28 OK. E2: 34/34 OK** (`python -m unittest discover -s tests -v`). |
| Calificación: caso 84 y bordes | ✅ | Script local, sin nube: |

Resultados de la calificación:

| Caso (trabajo, tareas, sueño, energía) | Esperado | Obtenido |
|---|---|---|
| 6, 4, 7.5, 4 (obligatorio) | 84 | **84** ✅ |
| 6, 4, **0 h de sueño**, 4 | 64 | 64 ✅ |
| **16 h de trabajo**, 4, 7.5, 4 | 90 | 90 ✅ |
| 6, 4, 7.5, **energía 1** | 69 | 69 ✅ |
| 0, 0, 0, 1 (mínimo posible) | 10 | 10 ✅ |
| 16, 20, 14, 5 (sueño 14 vale 5) | 80 | 80 ✅ |
| Sueño 6.5 / 9.5 (15 pts) y 5.5 / 10.5 (5 pts) | 90 / 80 | 90 / 80 ✅ |
| 4, 0, 0, 1 = 22.5 (redondeo .5 hacia arriba) | 23 | 23 ✅ |

**Prueba de punta a punta en local** (`servidor_local.py` + navegador): `/dia.html` sin sesión redirige a Acceso; login incorrecto da 401 y mensaje; contraseña corta da 400; crear cuenta da 201 y entra a Mi día; el selector muestra hoy y 6 días atrás; guardar 6/4/7.5/4 muestra **84 "Buen día"**; cerrar sesión borra el token y vuelve a Acceso.

---

## 4. Errores y riesgos (del más grave al menos grave)

| # | Gravedad | Riesgo | Dónde | Por qué importa |
|---|---|---|---|---|
| **R1** | Alta (bloquea el despliegue desde esta PC) | Los scripts `.sh` no corren en Windows tal cual: Git Bash no tiene `python3` (aquí se llama `python`) ni `zip`. | `desplegar_aws.sh:33,42,144`, `empaquetar_lambda.sh:10,17`, `README.md:58` | El README pide usar WSL. Hay que desplegar desde **WSL (Ubuntu)** o **AWS CloudShell**, con Python 3, `zip` y AWS CLI ≥ 2.32. |
| **R2** | Alta (riesgo creado por el `git init`) | Este Git tiene `core.autocrlf=true`. Hoy los `.sh` tienen fin de línea LF, pero un `git checkout`/`restore`/`reset` los reescribirá con CRLF, y bash en WSL o CloudShell fallará con `$'\r': command not found`. | Configuración de Git en Windows; no hay `.gitattributes` | Puede romper el despliegue justo al deshacer cambios. Se arregla con `.gitattributes` (`*.sh text eol=lf`). |
| **R3** | Media | Con AWS Academy (`LAMBDA_ROLE_ARN` = LabRole) el rol **no** es de permisos mínimos. | `desplegar_aws.sh:46-48`, `despliegue.env.ejemplo:13` | Incumple el diseño. Si la cuenta permite crear roles, no definan `LAMBDA_ROLE_ARN`; si no, documéntenlo como limitación del laboratorio. |
| **R4** | Media | Dependencias sin versión fija: `ibmcloudant>=0.11,<1.0` y todas las transitivas abiertas. Hoy se resolvió `python-dateutil 3.0.0`, una versión mayor nueva. | `backend/requirements.txt:1` | Otro día el zip puede salir distinto y romperse sin haber cambiado el código. Conviene fijar las versiones que ya probé. |
| **R5** | Baja | Enviar `NaN` o `Infinity` en `tareas` o `energia` (JSON escrito a mano) responde **500** en vez de 400. No se guarda nada. | `validacion.py:95-99` (`_numero` acepta valores no finitos), `:119` (`int(n)` truena) | El error queda en CloudWatch como excepción y es una respuesta incorrecta. Desde la interfaz no puede pasar. |
| **R6** | Baja | CORS solo filtra navegadores: las peticiones sin `Origin` (curl, Postman) entran. | `lambda_function.py:189-192` | No es un hueco, porque el token protege los datos, pero el requisito "solo acepta del dominio de CloudFront" debe explicarse así. |
| **R7** | Baja | Sin límite de peticiones ni de concurrencia: la URL de función es pública y cada login o registro calcula 200 000 iteraciones de PBKDF2. Alguien puede hacer fuerza bruta a `/sesiones` o generar gasto. | `desplegar_aws.sh:157-158`, `seguridad.py:10` | Con capa gratuita el impacto es pequeño. Una concurrencia reservada (por ejemplo 10) limita el costo. |
| **R8** | Baja | Se acepta una contraseña de 8 espacios. | `validacion.py:46` | El diseño solo pide mínimo 8 caracteres, así que técnicamente cumple. |
| **R9** | Baja | El token vive en `localStorage` y CloudFront no envía encabezados de seguridad (CSP, X-Frame-Options, etc.). | `comun.js:26-28`, `desplegar_aws.sh:103-112` | No encontré `innerHTML` ni `eval`: todo usa `textContent`, así que hoy no hay XSS evidente. Agregar la política administrada *SecurityHeadersPolicy* de CloudFront es barato. |
| **R10** | Muy baja | Si `desplegar_aws.sh` falla entre las líneas 144 y 169, queda `build/entorno.json` con las credenciales en disco. | `desplegar_aws.sh:143-169` | Está protegido con `umask 077` y `build/` está en `.gitignore`; basta borrarlo a mano si ocurre. |
| **R11** | Muy baja | Los logs de CloudWatch no tienen tiempo de retención y se guardan para siempre. | `desplegar_aws.sh` (no lo configura) | Costo despreciable; queda más limpio con 14 días. |
| **R12** | Muy baja | El encabezado `Authorization` exige "Bearer" con mayúscula exacta; "bearer" da 401. | `lambda_function.py:86` | El frontend siempre manda "Bearer". Solo afecta pruebas manuales. |

---

## 5. Cambios que propongo (todavía SIN aplicar)

Ordenados por prioridad. Ninguno cambia la lógica de negocio ni la regla de calificación.

1. **Agregar `.gitattributes`** en la raíz con `*.sh text eol=lf` (y `*.py text eol=lf`), para que los scripts nunca se conviertan a CRLF (R2).
2. **Decidir dónde desplegar**: WSL o AWS CloudShell (R1). No requiere cambiar código. Como alternativa, puedo hacer que los scripts detecten `python3` o `python` y empaqueten con Python en lugar de `zip`, para que también corran en Git Bash.
3. **Fijar las versiones de las dependencias** en `backend/requirements.txt` con las ya probadas: `ibmcloudant==0.11.13`, `ibm-cloud-sdk-core==3.28.1`, `requests==2.34.2`, `urllib3==2.8.0`, `python-dateutil==3.0.0`, `PyJWT==2.15.1`, `certifi`, `idna`, `charset-normalizer`, `six` (R4).
4. **Rechazar valores no finitos** en `validacion.py` (`_numero`: usar `math.isfinite`) y agregar una prueba para `NaN`/`Infinity` que espere 400 (R5).
5. **Limitar la concurrencia de la Lambda** en `desplegar_aws.sh` (`aws lambda put-function-concurrency --reserved-concurrent-executions 10`) (R7). *Ojo:* en cuentas nuevas el límite total puede ser 10 y AWS no deja reservar todo; habría que comprobarlo antes.
6. **Retención de logs a 14 días** (`aws logs put-retention-policy`) en `desplegar_aws.sh` (R11).
7. **Encabezados de seguridad en CloudFront**: agregar `ResponseHeadersPolicyId` (*Managed-SecurityHeadersPolicy*) al `DefaultCacheBehavior` (R9).
8. **Documentar** en el README del E1: CORS frente a token (R6), la limitación de LabRole (R3) y que `config.js` debe generarse con `publicar_frontend.sh` o editarse antes de subirlo a mano.
9. *(Opcional)* Rechazar contraseñas de solo espacios (R8) y aceptar "bearer" sin importar mayúsculas (R12).
10. *(Opcional)* Aplicar los cambios 3, 4 y 9 también en `entregable-2/`, que comparte el mismo backend.
