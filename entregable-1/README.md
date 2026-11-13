# MiRitmo · Entregable 1

Base funcional en la nube: **crear cuenta, iniciar sesión, registrar el día y ver la calificación.**

| Incluye | Requerimientos |
|---|---|
| Pantallas **Acceso** y **Mi día** | RF-01, RF-02, RF-03, RF-04 |
| API en Lambda: `POST /cuentas`, `POST /sesiones`, `PUT /registros/{fecha}` | RNF-01, RNF-02 |
| Bases `usuarios` y `registros` en Cloudant | |

**Criterio de entrega:** desde la URL pública, un usuario nuevo crea su cuenta, inicia sesión, registra su día y ve su calificación; el documento del registro aparece en el dashboard de Cloudant.

## Estructura

```
entregable-1/
├── backend/                  API (AWS Lambda, Python 3.12)
│   ├── lambda_function.py    Handler, rutas y CORS
│   ├── miritmo/
│   │   ├── calificacion.py   Regla de calificación (0 a 100)
│   │   ├── seguridad.py      PBKDF2-SHA256 con sal y tokens HMAC-SHA256 (7 días)
│   │   ├── validacion.py     Validación de datos con mensajes en español
│   │   └── almacen.py        Cloudant (nube) y memoria (local)
│   ├── requirements.txt
│   └── tests/test_api.py     28 pruebas
├── frontend/                 Interfaz (S3 + CloudFront)
│   ├── index.html            Acceso
│   ├── dia.html              Mi día
│   ├── css/  js/  img/
└── scripts/
    ├── desplegar_aws.sh      Despliega todo en AWS con un comando
    ├── crear_bases_cloudant.py
    ├── servidor_local.py     Corre todo en tu computadora
    ├── empaquetar_lambda.sh  Genera build/miritmo-lambda.zip
    └── publicar_frontend.sh  Sube la interfaz a S3 e invalida CloudFront
```

## Probar en tu computadora

Solo necesitas Python 3.10 o superior. No se necesita AWS ni Cloudant (los datos quedan en memoria).

```bash
python3 scripts/servidor_local.py
```

Abre http://localhost:8080.

Pruebas automáticas:

```bash
cd backend && python3 -m unittest discover -s tests -v
```

## Despliegue automático (recomendado)

Un solo script crea y configura todo: bases en Cloudant, rol IAM, Lambda con su URL, bucket S3 privado, CloudFront con HTTPS y la interfaz. Se puede correr varias veces: crea lo que falte y actualiza lo demás.

**Requisitos:** macOS o Linux (en Windows, usa WSL), Python 3.10+, `zip` y [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) 2.32 o más reciente.

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

Orden recomendado: Cloudant → Lambda → S3 + CloudFront → conectar las piezas.

### 1. IBM Cloudant (reutiliza la instancia Lite de la práctica DB server)

1. En el dashboard de Cloudant crea dos bases de datos **no particionadas**: `usuarios` y `registros`.
2. En *Service credentials* crea una credencial nueva (rol **Writer**). Anota `url` y `apikey`.

### 2. AWS Lambda (región us-east-2, Ohio)

1. Genera el paquete:
   ```bash
   scripts/empaquetar_lambda.sh
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
6. *Configuration → Function URL* → **Create function URL**: Auth type **NONE**. **Deja CORS desactivado**: el código ya responde CORS y solo acepta el dominio de `ALLOWED_ORIGIN`. Anota la URL (`https://xxxx.lambda-url.us-east-2.on.aws`).

### 3. Amazon S3 (bucket privado)

1. **Create bucket** en us-east-2, ej. `miritmo-web-equipo`. Deja activado **Block all public access**.

### 4. Amazon CloudFront (HTTPS)

1. **Create distribution** → Origin: el bucket de S3 → *Origin access*: **Origin access control settings** (crea un OAC).
2. *Viewer protocol policy*: **Redirect HTTP to HTTPS**. *Default root object*: `index.html`. WAF: *Do not enable* (para mantener costo $0).
3. Al crear, CloudFront muestra una **política de bucket**: cópiala y pégala en S3 → bucket → *Permissions → Bucket policy*.
4. Anota el dominio (`https://dxxxx.cloudfront.net`) y ponlo en `ALLOWED_ORIGIN` de Lambda (paso 2.5).

### 5. Publicar la interfaz

Con AWS CLI configurado:

```bash
scripts/publicar_frontend.sh <bucket> <id-distribucion> <url-funcion-lambda>
```

Sin AWS CLI: edita `frontend/js/config.js` con la URL de la función, sube el contenido de `frontend/` al bucket desde la consola de S3 y en CloudFront crea una invalidación de `/*`.

### 6. Verificar (criterio de entrega)

1. Abre la URL de CloudFront desde el celular (con datos móviles) y desde una computadora.
2. Crea una cuenta, cierra sesión y vuelve a entrar.
3. Registra 6 h de estudio, 4 tareas, 7.5 h de sueño y energía 4 → la calificación debe ser **84**.
4. En el dashboard de Cloudant, base `registros`, aparece el documento `tu-correo:AAAA-MM-DD`.
5. En `usuarios`, el documento tiene `hash` y `sal`, nunca la contraseña.

Si algo falla, revisa los logs en **CloudWatch → Log groups → /aws/lambda/miritmo-api**.

## API

Todas las rutas usan JSON. `PUT /registros/{fecha}` requiere `Authorization: Bearer <token>`.

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| POST | `/cuentas` | `{nombre, correo, contrasena}` | `201 {token, nombre, correo}` · `409` correo repetido · `400` datos inválidos |
| POST | `/sesiones` | `{correo, contrasena}` | `200 {token, nombre, correo}` · `401` datos incorrectos |
| PUT | `/registros/AAAA-MM-DD` | `{horas_trabajo, tareas, horas_sueno, energia}` | `200 {registro}` con `calificacion` · `400` · `401` sin token o token inválido |

Errores: `{"error": "mensaje", "campos": {"campo": "mensaje"}}`.

## Regla de calificación

| Dato | Valor permitido | Puntos (máx. 25) |
|---|---|---|
| Horas de estudio o trabajo | 0 a 16, pasos de 0.5 | horas ÷ 8 × 25 (8 h o más = 25) |
| Tareas completadas | 0 a 20, entero | tareas ÷ 5 × 25 (5 o más = 25) |
| Horas de sueño | 0 a 14, pasos de 0.5 | 7–9 h = 25; 6–6.5 h o 9.5–10 h = 15; otro = 5 |
| Energía | 1 a 5, entero | energía × 5 |

La suma se redondea al entero más cercano. Ejemplo: 18.75 + 20 + 25 + 20 = 83.75 → **84**.
