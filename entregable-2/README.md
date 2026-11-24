# MiRitmo · Entregable 2 (Examen final)

MVP completo: **registrar el día, ver la calificación, editar días y seguir la semana.**

| Incluye | Requerimientos |
|---|---|
| Pantallas **Acceso**, **Mi día** (con edición) y **Mi semana** | RF-01 a RF-07 |
| API en Lambda: `POST /cuentas`, `POST /sesiones`, `PUT /registros/{fecha}`, `GET /registros` | RNF-01 a RNF-07 |
| Validaciones con mensajes de error claros en todas las pantallas | |
| Tabla de pruebas de aceptación: [`docs/pruebas-aceptacion.md`](docs/pruebas-aceptacion.md) | |

> **Desde Windows** (PowerShell, sin WSL), sigue el [README de la raíz](../README.md): requisitos, inicio de sesión en AWS e IBM, primer despliegue y publicación de nuevas versiones con `scripts/empaquetar_lambda.py` y `scripts/publicar_frontend.py`. Esta página describe el entregable y la ruta con scripts `.sh` (Linux/macOS) o la consola de AWS.

**Criterio de entrega:** un usuario registra al menos tres días distintos, edita uno y ve la gráfica semanal y su promedio actualizados, desde celular y computadora.

## Estructura

```
entregable-2/
├── backend/                  API (AWS Lambda, Python 3.12)
│   ├── lambda_function.py    Handler, rutas y CORS
│   ├── miritmo/
│   │   ├── calificacion.py   Regla de calificación (0 a 100)
│   │   ├── seguridad.py      PBKDF2-SHA256 con sal y tokens HMAC-SHA256 (7 días)
│   │   ├── validacion.py     Validación de datos con mensajes en español
│   │   └── almacen.py        Cloudant (nube) y memoria (local)
│   ├── requirements.txt
│   └── tests/test_api.py     36 pruebas
├── frontend/                 Interfaz (S3 + CloudFront)
│   ├── index.html            Acceso
│   ├── dia.html              Mi día (registrar y editar)
│   ├── semana.html           Mi semana (gráfica, promedio y mejor día)
│   ├── vendor/               Chart.js 4.4.4
│   └── css/  js/  img/
├── config/                   Plantillas JSON del primer despliegue (README de la raíz)
├── docs/pruebas-aceptacion.md
└── scripts/
    ├── desplegar_aws.sh      Despliega todo en AWS con un comando
    ├── crear_bases_cloudant.py
    ├── servidor_local.py     Corre todo en tu computadora
    ├── empaquetar_lambda.py  Genera build/miritmo-lambda.zip (Windows, Linux o macOS)
    ├── empaquetar_lambda.sh  Lo mismo para Linux/macOS (requiere zip)
    ├── publicar_frontend.py  Sube la interfaz a S3 con su Content-Type e invalida CloudFront
    └── publicar_frontend.sh  Lo mismo para Linux/macOS
```

## Probar en tu computadora

Solo necesitas Python 3.10 o superior. No se necesita AWS ni Cloudant (los datos quedan en memoria).

```bash
python3 scripts/servidor_local.py      # en Windows: python scripts\servidor_local.py
```

Abre http://localhost:8080.

Pruebas automáticas:

```bash
cd backend && python3 -m unittest discover -s tests -v
```

## Actualizar desde el Entregable 1

Si ya tienes desplegado el Entregable 1, solo hay que publicar la nueva versión (no cambia la infraestructura):

1. En Windows sigue la sección *Publicar una nueva versión* del [README de la raíz](../README.md#6-publicar-una-nueva-versión-lo-más-común). En Linux/macOS corre `scripts/desplegar_aws.sh` desde esta carpeta (usa el mismo `despliegue.env`), o a mano: `scripts/empaquetar_lambda.sh`, subir `build/miritmo-lambda.zip` a `miritmo-api` y `scripts/publicar_frontend.sh <bucket> <id-distribucion> <url-funcion-lambda>`.
2. Verifica el flujo completo en la URL de CloudFront.

## Despliegue automático (recomendado)

Un solo script crea y configura todo: bases en Cloudant, rol IAM, Lambda con su URL, bucket S3 privado, CloudFront con HTTPS y la interfaz. Se puede correr varias veces: crea lo que falte y actualiza lo demás.

**Requisitos:** macOS o Linux (en Windows usa el [README de la raíz](../README.md), sin WSL), Python 3.10+, `zip` y [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) 2.32 o más reciente.

1. Inicia sesión en AWS con tu cuenta de la consola:
   ```bash
   aws login --region us-east-2
   ```
   (También sirve `aws configure` con las llaves de un usuario IAM).
2. En la carpeta `MiRitmo/` copia `despliegue.env.ejemplo` como `despliegue.env` y llena `CLOUDANT_URL` y `CLOUDANT_APIKEY` (IBM Cloud → instancia de Cloudant → *Service credentials* → credencial con rol **Writer**).
   - En AWS Academy (Learner Lab) no se pueden crear roles: agrega `LAMBDA_ROLE_ARN=` con el ARN de `LabRole`.
3. Desde esta carpeta, corre:
   ```bash
   scripts/desplegar_aws.sh
   ```
4. Al terminar muestra la URL de la aplicación (`https://xxxx.cloudfront.net`). La primera vez, CloudFront tarda de 5 a 10 minutos en activarse.

`despliegue.env` guarda credenciales: no lo compartas ni lo subas a GitHub (ya está en `.gitignore`).

## Desplegar manualmente (consola de AWS)

Orden recomendado: Cloudant → Lambda → S3 + CloudFront → conectar las piezas. Cualquier integrante puede seguir estos pasos (RNF-07).

### 1. IBM Cloudant (reutiliza la instancia Lite de la práctica DB server)

1. En el dashboard de Cloudant crea dos bases de datos **no particionadas**: `usuarios` y `registros`.
2. En *Service credentials* crea una credencial nueva (rol **Writer**). Anota `url` y `apikey`.

### 2. AWS Lambda (región us-east-2, Ohio)

1. Genera el paquete:
   ```bash
   python3 scripts/empaquetar_lambda.py   # en Windows: python scripts\empaquetar_lambda.py
   ```
2. En la consola de Lambda: **Create function** → *Author from scratch*
   - Nombre: `miritmo-api` · Runtime: **Python 3.12** · Arquitectura: **x86_64**
   - Rol: *Create a new role with basic Lambda permissions* (solo escribe logs en CloudWatch).
3. *Code* → **Upload from .zip file** → `build/miritmo-lambda.zip`. Handler: `lambda_function.lambda_handler`.
4. *Configuration → General*: memoria **256 MB**, timeout **10 s** (el hash de contraseñas necesita algo de CPU).
5. *Configuration → Environment variables*:

   | Variable | Valor |
   |---|---|
   | `CLOUDANT_URL` | `url` de la credencial de Cloudant |
   | `CLOUDANT_APIKEY` | `apikey` de la credencial de Cloudant |
   | `TOKEN_SECRET` | Texto aleatorio de 32+ caracteres: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `ALLOWED_ORIGIN` | Dominio de CloudFront (paso 4), ej. `https://d1abc23xyz.cloudfront.net` |

   Las credenciales **solo** viven aquí; nunca en el código ni en GitHub (RNF-02).
6. *Configuration → Function URL* → **Create function URL**: Auth type **NONE**. **Activa CORS**: *Allow origin* = dominio de CloudFront (`https://dxxxx.cloudfront.net`), *Allow methods* = `GET, POST, PUT`, *Allow headers* = `content-type, authorization`. En AWS el código **no** agrega encabezados CORS (solo con `CORS_EN_CODIGO=1`, que usa el servidor local); si los dos los agregaran, el encabezado saldría duplicado y el navegador rechazaría la respuesta. El código sigue respondiendo 403 a otros orígenes. Anota la URL (`https://xxxx.lambda-url.us-east-2.on.aws`).

### 3. Amazon S3 (bucket privado)

1. **Create bucket** en us-east-2, ej. `miritmo-web-equipo`. Deja activado **Block all public access**.

### 4. Amazon CloudFront (HTTPS)

1. **Create distribution** → Origin: el bucket de S3 → *Origin access*: **Origin access control settings** (crea un OAC).
2. *Viewer protocol policy*: **Redirect HTTP to HTTPS**. *Default root object*: `index.html`. WAF: *Do not enable* (para mantener costo $0).
3. Al crear, CloudFront muestra una **política de bucket**: cópiala y pégala en S3 → bucket → *Permissions → Bucket policy*.
4. Anota el dominio (`https://dxxxx.cloudfront.net`) y ponlo en `ALLOWED_ORIGIN` de Lambda (paso 2.5) y en el CORS de la URL de función (paso 2.6).

### 5. Publicar la interfaz

Con AWS CLI configurado:

```bash
scripts/publicar_frontend.sh <bucket> <id-distribucion> <url-funcion-lambda>
```

Sin AWS CLI: edita `frontend/js/config.js` con la URL de la función, sube el contenido de `frontend/` al bucket desde la consola de S3 y en CloudFront crea una invalidación de `/*`.

### 6. Verificar (criterio de entrega)

1. Abre la URL de CloudFront desde el celular (con datos móviles) y desde una computadora.
2. Registra tres días distintos (hoy y dos días anteriores).
3. En **Mi semana** revisa la gráfica: los días vacíos dicen "Sin registro"; el promedio y el mejor día coinciden.
4. Toca **Editar** en uno de los días, cambia un dato y guarda: la calificación se recalcula y la semana se actualiza.
5. En el dashboard de Cloudant, base `registros`, cada día es un documento `tu-correo:AAAA-MM-DD` (uno solo por fecha).

Si algo falla, revisa los logs en **CloudWatch → Log groups → /aws/lambda/miritmo-api**.

## Requerimientos no funcionales: cómo comprobarlos

| ID | Cómo se comprueba |
|---|---|
| RNF-01 Nube | La URL de CloudFront abre con candado (HTTPS) en celular con datos móviles y en computadora. |
| RNF-02 Seguridad | `curl -i "<url-lambda>/registros?desde=2026-11-01&hasta=2026-11-07"` sin token responde **401**. En Cloudant, `usuarios` solo guarda `hash` y `sal`. Ningún secreto aparece en el repositorio. |
| RNF-03 Rendimiento | Con la sesión iniciada, abre las herramientas de desarrollador → *Network* y recarga **Mi semana** 10 veces: al menos 9 respuestas de `/registros` en menos de 3 s (la primera tras un rato sin uso puede tardar más por el arranque en frío). |
| RNF-04 Usabilidad | 5 compañeros registran su día en menos de 60 s (cronometrado). La página se ve completa en 360 px (*DevTools → modo dispositivo*). |
| RNF-05 Costo | Crea en AWS Budgets un presupuesto **Zero spend budget** que avisa por correo ante cualquier cargo. Revisa *Billing → Bills* al final: $0. Cloudant en plan **Lite**. |
| RNF-06 Compatibilidad | Flujo completo (cuenta, registro y gráfica) en las versiones actuales de Chrome, Safari y Edge. |
| RNF-07 Mantenibilidad | Otro integrante despliega siguiendo este README. |

Registra los resultados en [`docs/pruebas-aceptacion.md`](docs/pruebas-aceptacion.md).

## API

Todas las rutas usan JSON. Excepto crear cuenta e iniciar sesión, requieren `Authorization: Bearer <token>`.

| Método | Ruta | Cuerpo / parámetros | Respuesta |
|---|---|---|---|
| POST | `/cuentas` | `{nombre, correo, contrasena}` | `201 {token, nombre, correo}` · `409` correo repetido · `400` datos inválidos |
| POST | `/sesiones` | `{correo, contrasena}` | `200 {token, nombre, correo}` · `401` datos incorrectos |
| PUT | `/registros/AAAA-MM-DD` | `{horas_trabajo, tareas, horas_sueno, energia}` | `200 {registro}` con `calificacion` · `400` · `401` |
| GET | `/registros?desde=AAAA-MM-DD&hasta=AAAA-MM-DD` | rango de hasta 31 días | `200 {registros: [...]}` ordenados por fecha · `400` · `401` |

Errores: `{"error": "mensaje", "campos": {"campo": "mensaje"}}`.

## Regla de calificación

| Dato | Valor permitido | Puntos (máx. 25) |
|---|---|---|
| Horas de estudio o trabajo | 0 a 16, pasos de 0.5 | horas ÷ 8 × 25 (8 h o más = 25) |
| Tareas completadas | 0 a 20, entero | tareas ÷ 5 × 25 (5 o más = 25) |
| Horas de sueño | 0 a 14, pasos de 0.5 | 7–9 h = 25; 6–6.5 h o 9.5–10 h = 15; otro = 5 |
| Energía | 1 a 5, entero | energía × 5 |

La suma se redondea al entero más cercano. Ejemplo: 18.75 + 20 + 25 + 20 = 83.75 → **84**.
