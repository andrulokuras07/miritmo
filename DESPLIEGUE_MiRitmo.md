# Despliegue de MiRitmo – Entregable 1

- Fecha: 13 de noviembre de 2026
- Diseño seguido: `REVISION_MiRitmo.md` (S3 privado → CloudFront con OAC → URL de función Lambda → IBM Cloudant).
- Bitácora completa, con cada comando y su salida numerados y sin secretos: [`evidencias/despliegue_log.md`](evidencias/despliegue_log.md) (entradas 1 a 71). En este documento, `[n]` remite a esa entrada.
- Archivos de configuración usados (sin secretos): [`evidencias/config/`](evidencias/config/).
- Ningún secreto quedó en archivos, en git ni en las capturas. Las credenciales de Cloudant pasaron directo de la salida del CLI de IBM a la Lambda, y `TOKEN_SECRET` (48 bytes aleatorios) se generó en memoria. El JSON de variables existió unos segundos en un archivo temporal fuera del proyecto y se borró.

## 1. URLs públicas

| Qué | URL |
|---|---|
| Aplicación (CloudFront, HTTPS) | https://dnfx295km7eni.cloudfront.net |
| API (URL de función Lambda) | https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws |

Cuenta de demostración: `demo@miritmo.mx`, con el registro de hoy (2026-11-13) en **84**. La contraseña no está escrita en ningún archivo.

## 2. Recursos creados

### AWS (proyecto "Proof of Concept", cuenta 299335570017, plan gratuito, región us-east-2)

| Recurso | Nombre / ID | ARN |
|---|---|---|
| Bucket S3 (privado, Block Public Access activado) | `miritmo-frontend-5e016053` (us-east-2) | `arn:aws:s3:::miritmo-frontend-5e016053` |
| Origin Access Control | `miritmo-oac` (`E2LN3JMLIJCR54`), SigV4, firma siempre | `arn:aws:cloudfront::299335570017:origin-access-control/E2LN3JMLIJCR54` |
| Distribución CloudFront | `E1C3936GEOWFBQ` → `dnfx295km7eni.cloudfront.net`; redirect-to-https; raíz `index.html`; PriceClass_100 | `arn:aws:cloudfront::299335570017:distribution/E1C3936GEOWFBQ` |
| Rol IAM de la Lambda (solo `AWSLambdaBasicExecutionRole`) | `miritmo-lambda-rol` | `arn:aws:iam::299335570017:role/miritmo-lambda-rol` |
| Función Lambda (Python 3.12, x86_64, 10 s, 256 MB) | `miritmo-api` | `arn:aws:lambda:us-east-2:299335570017:function:miritmo-api` |
| URL de función (auth NONE, CORS solo para CloudFront) | `https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws/` | (pertenece a la función) |
| Grupo de logs | `/aws/lambda/miritmo-api` | `arn:aws:logs:us-east-2:299335570017:log-group:/aws/lambda/miritmo-api` |

### IBM Cloud (cuenta "Andrés Angulo", grupo de recursos Default)

| Recurso | Nombre | Identificador |
|---|---|---|
| Instancia Cloudant (plan **lite**, **us-south**/Dallas, solo IAM: `legacyCredentials: false`) | `miritmo-cloudant` | `crn:v1:bluemix:public:cloudantnosqldb:us-south:a/f191d50cebbb4ec195285a71fedde14c:6dabef3a-2b91-42fe-9990-863c9ae57483::` |
| Credencial de servicio (rol **Manager**) | `miritmo-cloudant-cred` | `crn:v1:bluemix:public:cloudantnosqldb:us-south:a/f191d50cebbb4ec195285a71fedde14c:6dabef3a-2b91-42fe-9990-863c9ae57483:resource-key:b0bce5b8-36a7-438a-a64a-2c4e61e5772d` |
| Base de datos | `usuarios` | dentro de `miritmo-cloudant` (Cloudant no asigna CRN a las bases) |
| Base de datos | `registros` | dentro de `miritmo-cloudant` |

Variables de entorno de la Lambda (solo nombres): `CLOUDANT_URL`, `CLOUDANT_APIKEY`, `TOKEN_SECRET`, `ALLOWED_ORIGIN` (= `https://dnfx295km7eni.cloudfront.net`) [71].

## 3. Comandos, en orden (sin secretos)

Todo se corrió desde PowerShell con AWS CLI 2.40 (`--profile miritmo`) e IBM Cloud CLI 2.16.1. No se usaron los scripts `.sh`.

**Verificación previa, sin crear recursos de prueba**
```powershell
aws sts get-caller-identity --profile miritmo                                   # [1]
aws freetier get-account-plan-state --profile miritmo --region us-east-1        # [2] FREE, ACTIVE
aws iam simulate-principal-policy --profile miritmo `
  --policy-source-arn arn:aws:iam::299335570017:role/managed/AccountFullAccessRole `
  --action-names s3:CreateBucket s3:PutBucketPolicy cloudfront:CreateDistribution iam:CreateRole lambda:CreateFunction lambda:CreateFunctionUrlConfig lambda:AddPermission ... `
  --context-entries "ContextKeyName=aws:RequestedRegion,ContextKeyValues=us-east-2,ContextKeyType=string"   # [6][7] todas "allowed"
```
También se leyeron las políticas SCP y RCP publicadas para los proyectos. Ninguna bloquea S3, CloudFront, IAM ni Lambda en la región del proyecto, y las RCP no cubren Lambda, así que la URL pública está permitida.

**1. Cloudant**
```powershell
winget install --id IBM.Cloud.CLI -e
ibmcloud login --sso -r us-south                     # código de un solo uso dado por el usuario (no registrado) [8]
ibmcloud resource service-instance-delete Cloudant-cr --recursive -f    # [9] instancia Lite previa (ver problemas)
ibmcloud resource reclamation-delete a4431e27-847e-4e1f-b34b-ccba8de3de94 -f   # [11]
ibmcloud target -g Default                                              # [12]
ibmcloud resource service-instance-create miritmo-cloudant cloudantnosqldb lite us-south -p '{"legacyCredentials": false}'   # [13]
ibmcloud resource service-key-create miritmo-cloudant-cred Manager --instance-name miritmo-cloudant --output json   # [15] solo se registraron campos sin secretos
python con_cloudant.py python entregable-1/scripts/crear_bases_cloudant.py   # [17] la credencial pasa por variables de entorno del proceso
```

**2–4. S3, CloudFront y rol IAM**
```powershell
aws s3api create-bucket --bucket miritmo-frontend-5e016053 --region us-east-2 --create-bucket-configuration LocationConstraint=us-east-2   # [18]
aws s3api put-public-access-block --bucket miritmo-frontend-5e016053 --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true   # [19]
aws cloudfront create-origin-access-control --origin-access-control-config "Name=miritmo-oac,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3"   # [22]
aws cloudfront create-distribution --distribution-config file://evidencias/config/cloudfront.json        # [23]
aws s3api put-bucket-policy --bucket miritmo-frontend-5e016053 --policy file://evidencias/config/politica-bucket.json   # [24]
aws iam create-role --role-name miritmo-lambda-rol --assume-role-policy-document file://evidencias/config/confianza-lambda.json   # [26]
aws iam attach-role-policy --role-name miritmo-lambda-rol --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole   # [27]
```

**5. Lambda**
```powershell
python entregable-1/scripts/empaquetar_lambda.py     # [30][65] pip --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all: + zipfile
aws lambda create-function --function-name miritmo-api --runtime python3.12 --architectures x86_64 `
  --handler lambda_function.lambda_handler --role arn:aws:iam::299335570017:role/miritmo-lambda-rol `
  --timeout 10 --memory-size 256 --zip-file fileb://build/miritmo-lambda.zip --environment file://<temporal, borrado>   # [31]
aws lambda create-function-url-config --function-name miritmo-api --auth-type NONE --cors file://evidencias/config/cors-lambda.json   # [33]
aws lambda add-permission --function-name miritmo-api --statement-id url-publica --action lambda:InvokeFunctionUrl --principal "*" --function-url-auth-type NONE   # [34]
aws lambda add-permission --function-name miritmo-api --statement-id url-publica-invocar --action lambda:InvokeFunction --principal "*" --invoked-via-function-url   # [35]
aws lambda update-function-code --function-name miritmo-api --zip-file fileb://build/miritmo-lambda.zip   # [66] corrección de CORS
```

**6. Frontend**
```powershell
# js/config.js -> apiUrl: "https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws"
aws s3 cp <archivo> s3://miritmo-frontend-5e016053/<archivo> --content-type <tipo>   # [36]-[43]
#   .html -> text/html; charset=utf-8   .css -> text/css; charset=utf-8
#   .js   -> application/javascript; charset=utf-8   .svg -> image/svg+xml
aws cloudfront create-invalidation --distribution-id E1C3936GEOWFBQ --paths "/*"   # [45]
```

**7. Pruebas**: `powershell -File evidencias/pruebas_curl.ps1` [53] y las comprobaciones [47]–[52], [54]–[58] y [70].

## 4. Pruebas

Todas se hicieron contra las URLs públicas. El script de curl crea cuentas `prueba*@miritmo.mx` con contraseñas aleatorias, y al final se borraron [60][68]. Solo queda la cuenta demo [69].

| Requerimiento | Pasos | Resultado esperado | Resultado obtenido |
|---|---|---|---|
| RF-01 | `POST /cuentas` con datos nuevos | 201 y token | ✅ 201, token recibido (oculto) |
| RF-01 | `POST /cuentas` con el mismo correo | Error | ✅ 409 "Ya existe una cuenta con ese correo." |
| RF-01 | `POST /cuentas` con contraseña de 7 caracteres | Error | ✅ 400 "Revisa los datos marcados." |
| RF-01 | Revisar el documento en `usuarios` | Sin contraseña en texto plano | ✅ Solo `hash` y `sal` [52] |
| RF-02 | `POST /sesiones` con datos correctos | Token | ✅ 200, token recibido |
| RF-02 | `POST /sesiones` con contraseña incorrecta | Error | ✅ 401 "Correo o contraseña incorrectos." |
| RF-03 | `PUT /registros/2026-11-13` (hoy) | Se guarda | ✅ 200 |
| RF-03 | `PUT /registros/2026-11-14` (futuro) | Error | ✅ 400 "No puedes registrar días futuros." |
| RF-03 | `PUT /registros/2026-11-06` (hace 7 días) | Error | ✅ 400 "Solo puedes registrar hoy o los 6 días anteriores." |
| RF-04 | 6 h, 4 tareas, 7.5 h de sueño, energía 4 | 84 | ✅ 84 (API, Cloudant [50] y navegador, captura 18) |
| RNF-02 | `PUT` sin token | 401 | ✅ 401 |
| RNF-02 | `PUT` con el token alterado (un carácter de la firma) | 401 | ✅ 401 |
| RNF-02 | El usuario B manda `usuario: A` en el cuerpo | Se guarda como B y A no cambia | ✅ 200; `registros/<B>:fecha` con `usuario` = B; el registro de A sigue en 84 [50][51] |
| RNF-02 | El usuario B usa la ruta `/registros/<correo A>:<fecha>` | Rechazo | ✅ 400 "Fecha inválida." (el `_id` siempre sale del token) |
| RNF-02 / CORS | `POST` con `Origin: https://otro-sitio.example` | Rechazo | ✅ 403 "Origen no permitido." [54] |
| RNF-02 / CORS | Preflight desde CloudFront | Permitido solo para CloudFront | ✅ 200, `Access-Control-Allow-Origin: https://dnfx295km7eni.cloudfront.net` [55] |
| RNF-02 / CORS | Petición real desde el navegador (Chrome/Playwright) | Funciona | ✅ Tras la corrección (problema 5): un solo `Access-Control-Allow-Origin` [67]; capturas 16–18 |
| RNF-01 | `http://` de CloudFront | Redirige a HTTPS | ✅ 301 → https [47] |
| RNF-01 | `https://` de CloudFront | Sirve la app | ✅ 200 `text/html; charset=utf-8` [48] |
| S3 privado | Pedir el objeto directo al bucket | Denegado | ✅ 403 [49] |
| Logs | CloudWatch: `?Traceback ?ERROR ?"Task timed out"` | 0 eventos | ✅ 0 [57][70]; duraciones de 2 a 81 ms y 99 MB de memoria usada [58] |
| Unitarias | `python -m unittest` (E1) | Todas OK | ✅ 30/30 (29 originales + 1 nueva de CORS) |

Las 13 pruebas de curl se corrieron tres veces: [53], la corrida previa a la bitácora y la corrida de la captura 14 (ya con la corrección de CORS). Las tres dieron 13 de 13.

## 5. Capturas

Carpeta: `..\Capturas Entregable 1\`. La 19 (celular) la toma el usuario. Todas se abrieron y revisaron una por una.

| Número | Archivo | Qué se ve | Revisada |
|---|---|---|---|
| 01 | 01.png | Catálogo de Cloudant: región **Dallas (us-south)**, plan **Lite** marcado, autenticación IAM, nombre `miritmo-cloudant` (sin pulsar "Create") | ✅ |
| 02 | 02.png | Lista de recursos: `miritmo-cloudant`, Dallas, Cloudant, **Activo** | ✅ |
| 03 | 03.png | Credenciales de servicio: `miritmo-cloudant-cred` **cerrada**, sin apikey | ✅ |
| 04 | 04.png | Panel de Cloudant con `registros` y `usuarios` (barra de dirección tapada: host de Cloudant) | ✅ |
| 05 | 05.png | S3: `miritmo-frontend-5e016053`, "Este de EE. UU. (Ohio) us-east-2" | ✅ |
| 06 | 06.png | S3 → Permisos: "Bloquear todo el acceso público: Activado" y la política completa (solo `cloudfront.amazonaws.com` con `AWS:SourceArn` de la distribución) | ✅ |
| 07 | 07.png | S3 → Objetos: `index.html`, `dia.html`, `css/`, `img/`, `js/` | ✅ |
| 08 | 08.png | CloudFront: `E1C3936GEOWFBQ`, **Enabled**, `dnfx295km7eni.cloudfront.net` | ✅ |
| 09 | 09.png | CloudFront → Origins: `s3-miritmo` → bucket, Origin access `E2LN3JMLIJCR54` (OAC) | ✅ |
| 10 | 10.png | IAM: `miritmo-lambda-rol` con una sola política, `AWSLambdaBasicExecutionRole` | ✅ |
| 11 | 11.png | Lambda `miritmo-api`: versión ejecutable **Python 3.12**, handler, x86_64 | ✅ |
| 12 | 12.png | Lambda → Variables de entorno: los 4 nombres, con los **valores tapados** (ocultos en la página antes de capturar y además rectángulo negro) | ✅ |
| 13 | 13.png | Lambda → URL de la función: URL, auth NONE y CORS (origen CloudFront; content-type, authorization; GET, POST, PUT) | ✅ |
| 14 | 14.png | Ventana de PowerShell con las 13 pruebas de curl: código HTTP y mensaje, token oculto | ✅ |
| 15 | 15.png | Chrome con la pantalla Acceso en `dnfx295km7eni.cloudfront.net` y el icono de sitio seguro | ✅ (ver problema 11) |
| 16 | 16.png | Crear cuenta con `demo@miritmo.mx` → "Ya existe una cuenta con ese correo." | ✅ |
| 17 | 17.png | Iniciar sesión con contraseña incorrecta → "Correo o contraseña incorrectos." | ✅ |
| 18 | 18.png | Mi día con 6 / 4 / 7.5 / energía 4 → **84 "Buen día"** | ✅ |
| 19 | — | (la toma el usuario en su celular) | — |
| 20 | 20.png | Cloudant `registros` → `demo@miritmo.mx:2026-11-13` con `calificacion: 84` (barra de dirección tapada) | ✅ |
| 21 | 21.png | Cloudant `usuarios` → `demo@miritmo.mx` con `hash` y `sal`, sin contraseña (barra de dirección tapada) | ✅ |
| 22 | 22.png | CloudWatch `/aws/lambda/miritmo-api`: ejecuciones (líneas REPORT) | ✅ |
| 22b | 22b.png | (Extra) Misma bitácora filtrada por `?ERROR ?Traceback ?Timeout`: "No se encontraron eventos" | ✅ |
| 23 | 23.png | (Opcional) Free Tier: "No se cobrará nada a la cuenta del plan gratuito" | ✅ |

Las capturas de consola se tomaron con `System.Drawing.CopyFromScreen`, recortadas a la ventana de Chrome. Las 16, 17 y 18 se hicieron con Playwright usando el Chrome instalado, en modo sin ventana.

## 6. Problemas encontrados y cómo se resolvieron

1. **Ya existía una instancia Cloudant Lite** (`Cloudant-cr`, Sídney, sin bases). IBM permite solo una Lite por cuenta. Con autorización del usuario se borró, junto con su reclamación, y se creó `miritmo-cloudant` en Dallas [9]–[13].
2. **`ibmcloud login --sso` no leía la entrada desde PowerShell 5.1**: la tubería agrega un BOM y el CLI rechazaba la respuesta "n". Se resolvió enviando la entrada con `printf` desde bash. El código de un solo uso no se registró.
3. **El simulador de IAM marcaba "explicitDeny" en S3 y Lambda** sin contexto de región, por la SCP de regiones del proyecto. Con `aws:RequestedRegion=us-east-2` todas las acciones salen "allowed" [6][7]. No hubo que cambiar nada.
4. **La configuración CORS de la URL de función no acepta `OPTIONS`** en `AllowMethods`: solo admite métodos de hasta 6 caracteres [32]. Se dejó `GET, POST, PUT`; el preflight `OPTIONS` lo responde la propia URL de función [55].
5. **CORS duplicado: la app no conectaba desde el navegador** ("No se pudo conectar con el servidor"). La URL de función y el código agregaban cada uno `Access-Control-Allow-Origin`, y Chrome rechaza la respuesta si el encabezado llega dos veces. curl no lo detecta, por eso las pruebas habían pasado [64]. Con autorización del usuario, el código solo agrega encabezados CORS si `CORS_EN_CODIGO=1`, valor que pone `servidor_local.py` para pruebas locales. En AWS los pone la URL de función, y el código sigue respondiendo 403 a otros orígenes. Se agregó una prueba unitaria (30/30) y se volvió a desplegar el código [65]–[67].
6. **Los scripts `.sh` no corren en Windows** (riesgo R1 de la revisión). Se agregó `entregable-1/scripts/empaquetar_lambda.py`, que arma el zip con `pip --platform manylinux2014_x86_64` y `zipfile`. Su primera versión falló al borrar la carpeta `build/paquete` dentro de OneDrive, y ahora arma el paquete en una carpeta temporal [62][65].
7. **Error en el script de pruebas**: usaba `$args`, que es una variable reservada de PowerShell, y curl recibía argumentos vacíos. Se renombró a `$opts`.
8. **Playwright**: el radio de energía está oculto bajo su etiqueta, así que se hace clic en la etiqueta `label[for=energia-4]`.
9. **Capturas en Chrome**:
   - La pestaña de la extensión quedó dentro de un grupo colapsado; el usuario dio un clic para activarla.
   - Mi primer método para traer Chrome al frente (simular la tecla Alt) abrió la página de Configuración de Chrome; la cerré y cambié el método a `AttachThreadInput`.
   - Una vez, otra ventana (WhatsApp) estaba encima y quedó en la captura: **se borró de inmediato** y se agregó una comprobación de ventana en primer plano antes de cada captura.
   - Otra sesión de Claude usaba el mismo Chrome al mismo tiempo, así que la barra "Claude started debugging this browser" se recortó de algunas imágenes (solo esa franja; el contenido no cambia).
10. **Host de Cloudant**: el host aparece en la barra de dirección del panel de Cloudant, que se tapó en las capturas 04, 20 y 21. No está en ningún archivo ni en git. Sí apareció en la salida interna de la herramienta del navegador durante la sesión.
11. **Captura 15**: las versiones recientes de Chrome ocultan `https://` y cambiaron el candado por el icono de "información del sitio". La captura muestra el dominio con ese icono. El HTTPS está comprobado en [47] (redirección 301) y [48].
12. **Zoom en algunas capturas** (01, 06, 10, 11): se redujo el zoom de la página con CSS para que cupiera toda la información en una sola imagen. Solo cambia la vista, no los datos.

## 7. Costos y limpieza

Todo está dentro del plan gratuito de AWS (sin cargos; la captura 23 lo muestra) y del plan Lite de Cloudant. Los recursos se dejaron funcionando para la entrega. La concurrencia reservada, la retención de logs y los encabezados de seguridad de CloudFront (R7, R11 y R9 de la revisión) no se aplicaron porque no formaban parte de este despliegue.
