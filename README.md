# MiRitmo

Medidor de rendimiento diario para estudiantes y jóvenes profesionistas: un registro de menos de un minuto, una calificación del día de 0 a 100 y una gráfica semanal.

Infraestructura y Cómputo en la Nube · Universidad Anáhuac Querétaro

- **Aplicación:** https://dnfx295km7eni.cloudfront.net
- **API:** https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws

Esta guía sirve para que cualquier integrante del equipo despliegue MiRitmo **desde Windows con PowerShell**. No necesitas WSL ni los scripts `.sh` (esos son para Linux o macOS).

## Contenido

1. [Arquitectura](#1-arquitectura)
2. [Estructura del repositorio](#2-estructura-del-repositorio)
3. [Requisitos](#3-requisitos)
4. [Probar en tu computadora (sin nube)](#4-probar-en-tu-computadora-sin-nube)
5. [Iniciar sesión en AWS e IBM Cloud](#5-iniciar-sesión-en-aws-e-ibm-cloud)
6. [Publicar una nueva versión (lo más común)](#6-publicar-una-nueva-versión-lo-más-común)
7. [Desplegar la primera vez](#7-desplegar-la-primera-vez)
8. [Pruebas](#8-pruebas)
9. [Problemas comunes](#9-problemas-comunes)
10. [API y regla de calificación](#10-api-y-regla-de-calificación)

## 1. Arquitectura

```
Navegador ──HTTPS──▶ CloudFront ──(OAC)──▶ S3 privado (HTML, CSS, JS, Chart.js)
    │  (js/config.js dice cuál es la URL de la API)
    └──HTTPS + "Authorization: Bearer <token>"──▶ URL de función Lambda (Python 3.12)
                                                    ├──▶ IBM Cloudant Lite (bases usuarios y registros)
                                                    └──▶ CloudWatch Logs
```

| Pieza | Recurso de este proyecto |
|---|---|
| Bucket S3 privado (us-east-2) | `miritmo-frontend-5e016053` |
| Distribución CloudFront | `E1C3936GEOWFBQ` → `dnfx295km7eni.cloudfront.net` |
| Función Lambda | `miritmo-api` (Python 3.12, x86_64, 256 MB, 10 s) |
| Rol IAM de la Lambda | `miritmo-lambda-rol` (solo `AWSLambdaBasicExecutionRole`) |
| Cloudant (IBM Cloud, us-south, plan Lite) | instancia `miritmo-cloudant`, credencial `miritmo-cloudant-cred` |

Todo está dentro del plan gratuito de AWS y del plan Lite de Cloudant.

**Seguridad.** Las credenciales de Cloudant y el secreto de los tokens viven **solo** en las variables de entorno de la Lambda (`CLOUDANT_URL`, `CLOUDANT_APIKEY`, `TOKEN_SECRET`, `ALLOWED_ORIGIN`). Nunca se escriben en el código, en este repositorio ni en archivos del proyecto.

**CORS.** En AWS, los encabezados CORS los pone la **configuración CORS de la URL de función** (origen = dominio de CloudFront). El código solo los agrega si `CORS_EN_CODIGO=1`, valor que usa el servidor local. Si los dos los agregan, `Access-Control-Allow-Origin` sale duplicado y el navegador muestra "No se pudo conectar con el servidor".

## 2. Estructura del repositorio

```
MiRitmo/
├── README.md                  ← esta guía
├── entregable-1/              Entregable 1 (RF-01 a RF-04), ya entregado
├── entregable-2/              Examen final: MVP completo (RF-01 a RF-07) ← lo que está desplegado
│   ├── backend/               API (lambda_function.py, miritmo/, requirements.txt con versiones fijas, tests/)
│   ├── frontend/              index.html (Acceso), dia.html (Mi día), semana.html (Mi semana), vendor/chart.umd.min.js
│   ├── config/                Plantillas JSON para el primer despliegue (CloudFront, políticas, CORS)
│   ├── scripts/
│   │   ├── empaquetar_lambda.py   Arma build/miritmo-lambda.zip para Lambda (Linux) desde Windows
│   │   ├── publicar_frontend.py   Sube frontend/ a S3 con su Content-Type e invalida CloudFront
│   │   ├── crear_bases_cloudant.py
│   │   ├── servidor_local.py      Corre todo en tu PC
│   │   └── *.sh                   Equivalentes para Linux/macOS
│   └── docs/pruebas-aceptacion.md
├── evidencias/                Bitácoras de despliegue y scripts de prueba (curl, navegador, rendimiento)
├── DESPLIEGUE_MiRitmo.md      Despliegue del Entregable 1
└── DESPLIEGUE_E2_MiRitmo.md   Despliegue del Entregable 2
```

## 3. Requisitos

Windows 10 u 11 con PowerShell. Instala lo que falte con `winget` (una sola vez) y **abre una ventana nueva de PowerShell** al terminar:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id Amazon.AWSCLI -e
winget install --id IBM.Cloud.CLI -e
```

| Herramienta | Versión | Para qué |
|---|---|---|
| Git | cualquiera | Clonar el repositorio |
| Python | 3.12 (sirve 3.10 o más reciente) | Empaquetar la Lambda, publicar el frontend, servidor local |
| AWS CLI v2 | **2.32 o más reciente** (trae `aws login`) | Lambda, S3, CloudFront |
| IBM Cloud CLI | cualquiera | Solo para crear Cloudant o leer su credencial |

Comprueba:

```powershell
git --version; python --version; aws --version; ibmcloud --version
```

Clona el repositorio:

```powershell
git clone https://github.com/andrulokuras07/miritmo.git
cd miritmo
```

## 4. Probar en tu computadora (sin nube)

Los datos quedan en memoria y se borran al detener el servidor.

```powershell
python entregable-2\scripts\servidor_local.py
```

Abre http://localhost:8080. Para detenerlo, presiona `Ctrl+C`.

## 5. Iniciar sesión en AWS e IBM Cloud

### AWS

MiRitmo vive en un **proyecto** de AWS (nueva experiencia de AWS). Si te invitaron como team member, primero entra a la consola con la invitación que te llegó por correo. La región del proyecto es **us-east-2 (Ohio)**; puedes confirmarla en AWS Settings → *View all projects* → *Overview* → *Additional Info* → *Region*.

```powershell
aws configure set region us-east-2 --profile miritmo
aws login --profile miritmo
aws sts get-caller-identity --profile miritmo
```

`aws login` abre el navegador para que inicies sesión. La sesión dura algunas horas; si un comando responde *"Your session has expired"*, vuelve a correr `aws login --profile miritmo`. Todos los comandos de esta guía usan `--profile miritmo`.

### IBM Cloud

Solo hace falta para crear Cloudant o para leer su credencial.

```powershell
ibmcloud login --sso -r us-south
```

Cuando pregunte *"Open the URL in the default browser?"*, responde `Y`, inicia sesión y pega el **código de un solo uso** que te muestra la página (vence en unos minutos). Si tienes varias cuentas de IBM, elige la que tiene `miritmo-cloudant`. Después:

```powershell
ibmcloud target -g Default
```

## 6. Publicar una nueva versión (lo más común)

Úsalo cuando cambia el código (backend o frontend) y la infraestructura ya existe. **No crea recursos nuevos ni toca las variables de entorno de la Lambda.**

```powershell
cd entregable-2
$Perfil = "miritmo"
$Funcion = "miritmo-api"
$Bucket = "miritmo-frontend-5e016053"
$Distribucion = "E1C3936GEOWFBQ"
```

> ¿Otro despliegue? Busca tus valores con
> `aws cloudfront list-distributions --profile miritmo --query "DistributionList.Items[].{Id:Id,Dominio:DomainName,Comentario:Comment}" --output table`
> (el comentario dice `MiRitmo <bucket>`).

**1. Pruebas automáticas** (deben salir todas `OK`):

```powershell
python -m unittest discover -s backend\tests
```

**2. Empaquetar la Lambda** (instala las dependencias con binarios para Linux y arma el zip):

```powershell
python scripts\empaquetar_lambda.py
```

**3. Subir el código a la Lambda y esperar a que termine:**

```powershell
aws lambda update-function-code --function-name $Funcion --zip-file fileb://build/miritmo-lambda.zip --profile $Perfil --query "{Estado:LastUpdateStatus,Sha256:CodeSha256}"
aws lambda wait function-updated-v2 --function-name $Funcion --profile $Perfil
```

**4. Publicar el frontend** (escribe `js/config.js` con la URL de la API en una copia temporal, sube cada archivo con su Content-Type, invalida `/*` y espera a que la invalidación termine, de 1 a 3 minutos):

```powershell
$Api = aws lambda get-function-url-config --function-name $Funcion --profile $Perfil --query FunctionUrl --output text
python scripts\publicar_frontend.py --bucket $Bucket --distribucion $Distribucion --api $Api --perfil $Perfil --esperar
```

**5. Verificar:**

```powershell
$Dominio = aws cloudfront get-distribution --id $Distribucion --profile $Perfil --query Distribution.DomainName --output text
curl.exe -s "https://$Dominio/js/config.js"
curl.exe -s -o NUL -w "semana.html: %{http_code} %{content_type}`n" "https://$Dominio/semana.html"
curl.exe -s -w "`nGET /registros sin token: %{http_code}`n" "$($Api.TrimEnd('/'))/registros?desde=2026-11-01&hasta=2026-11-07"
```

Debe mostrar la URL de la API en `config.js`, `200 text/html; charset=utf-8` y `401`. Al final abre `https://<dominio>` en el navegador, inicia sesión y revisa **Mi día** y **Mi semana**.

## 7. Desplegar la primera vez

Solo si la infraestructura **no existe** (por ejemplo, en otro proyecto de AWS). Son los mismos pasos del despliegue del Entregable 1 ([`DESPLIEGUE_MiRitmo.md`](DESPLIEGUE_MiRitmo.md)). Corre los bloques en orden **en la misma ventana de PowerShell**, porque cada bloque usa variables del anterior.

### 7.0 Variables y función auxiliar

```powershell
cd entregable-2
$Perfil = "miritmo"; $Region = "us-east-2"
$Funcion = "miritmo-api"; $Rol = "miritmo-lambda-rol"
$Cuenta = aws sts get-caller-identity --profile $Perfil --query Account --output text
$Bucket = "miritmo-frontend-" + (python -c "import secrets; print(secrets.token_hex(4))")

# Llena una plantilla de config\ (__BUCKET__, __CUENTA__, ...) y devuelve "file://<ruta temporal>".
function New-MiRitmoArchivo([string]$Plantilla, [hashtable]$Valores) {
  $texto = [IO.File]::ReadAllText((Resolve-Path $Plantilla))
  foreach ($k in $Valores.Keys) { $texto = $texto.Replace("__${k}__", [string]$Valores[$k]) }
  $destino = Join-Path $env:TEMP ("miritmo-" + (Split-Path $Plantilla -Leaf))
  [IO.File]::WriteAllText($destino, $texto, (New-Object Text.UTF8Encoding($false)))
  return "file://$destino"
}
"Cuenta $Cuenta, bucket $Bucket"
```

### 7.1 IBM Cloudant (plan Lite, us-south)

IBM permite **una sola instancia Lite por cuenta**. Si ya tienes una, reutilízala y salta al `service-key-create`.

```powershell
ibmcloud resource service-instance-create miritmo-cloudant cloudantnosqldb lite us-south -p config\cloudant.json
ibmcloud resource service-instance miritmo-cloudant      # repite hasta que diga State: active
ibmcloud resource service-key-create miritmo-cloudant-cred Manager --instance-name miritmo-cloudant | Out-Null
```

Lee la credencial **a variables de entorno de esta ventana** (no la imprimas ni la guardes en archivos) y crea las bases `usuarios` y `registros`:

```powershell
$cred = (ibmcloud resource service-key miritmo-cloudant-cred --output json | Out-String | ConvertFrom-Json)[0].credentials
$env:CLOUDANT_URL = $cred.url; $env:CLOUDANT_APIKEY = $cred.apikey; Remove-Variable cred
python scripts\crear_bases_cloudant.py
```

### 7.2 S3 privado

```powershell
aws s3api create-bucket --bucket $Bucket --region $Region --create-bucket-configuration LocationConstraint=$Region --profile $Perfil
aws s3api put-public-access-block --bucket $Bucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" --profile $Perfil
```

### 7.3 CloudFront con OAC (HTTPS)

```powershell
$Oac = aws cloudfront create-origin-access-control --origin-access-control-config "Name=miritmo-oac-$Bucket,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3" --profile $Perfil --query OriginAccessControl.Id --output text
$Distribucion = aws cloudfront create-distribution --distribution-config (New-MiRitmoArchivo config\cloudfront.json @{BUCKET=$Bucket; REGION=$Region; OAC=$Oac}) --profile $Perfil --query Distribution.Id --output text
$Dominio = aws cloudfront get-distribution --id $Distribucion --profile $Perfil --query Distribution.DomainName --output text
aws s3api put-bucket-policy --bucket $Bucket --policy (New-MiRitmoArchivo config\politica-bucket.json @{BUCKET=$Bucket; CUENTA=$Cuenta; DISTRIBUCION=$Distribucion}) --profile $Perfil
"Distribución $Distribucion -> https://$Dominio"
```

### 7.4 Rol IAM con permisos mínimos

```powershell
aws iam create-role --role-name $Rol --assume-role-policy-document (New-MiRitmoArchivo config\confianza-lambda.json @{CUENTA=$Cuenta}) --profile $Perfil --query Role.Arn --output text
aws iam attach-role-policy --role-name $Rol --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole --profile $Perfil
Start-Sleep -Seconds 15   # el rol nuevo tarda unos segundos en estar disponible para Lambda
```

### 7.5 Lambda con su URL de función

Las variables de entorno se pasan con un archivo temporal que se borra enseguida. `TOKEN_SECRET` se genera aleatorio y no se guarda en ningún lado.

```powershell
python scripts\empaquetar_lambda.py
$env:TOKEN_SECRET = python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:ALLOWED_ORIGIN = "https://$Dominio"
$env:MIRITMO_ENTORNO = Join-Path $env:TEMP "miritmo-entorno.json"
python -c "import json, os; json.dump({'Variables': {k: os.environ[k] for k in ('CLOUDANT_URL', 'CLOUDANT_APIKEY', 'TOKEN_SECRET', 'ALLOWED_ORIGIN')}}, open(os.environ['MIRITMO_ENTORNO'], 'w'))"
aws lambda create-function --function-name $Funcion --runtime python3.12 --architectures x86_64 --handler lambda_function.lambda_handler --role "arn:aws:iam::${Cuenta}:role/$Rol" --timeout 10 --memory-size 256 --zip-file fileb://build/miritmo-lambda.zip --environment "file://$env:MIRITMO_ENTORNO" --profile $Perfil --query FunctionArn --output text
Remove-Item $env:MIRITMO_ENTORNO
Remove-Item Env:CLOUDANT_URL, Env:CLOUDANT_APIKEY, Env:TOKEN_SECRET, Env:MIRITMO_ENTORNO
aws lambda wait function-active-v2 --function-name $Funcion --profile $Perfil
```

URL de función pública (la seguridad la dan el token y CORS) con CORS solo para CloudFront:

```powershell
$Api = aws lambda create-function-url-config --function-name $Funcion --auth-type NONE --cors (New-MiRitmoArchivo config\cors-lambda.json @{DOMINIO=$Dominio}) --profile $Perfil --query FunctionUrl --output text
aws lambda add-permission --function-name $Funcion --statement-id url-publica --action lambda:InvokeFunctionUrl --principal "*" --function-url-auth-type NONE --profile $Perfil
aws lambda add-permission --function-name $Funcion --statement-id url-publica-invocar --action lambda:InvokeFunction --principal "*" --invoked-via-function-url --profile $Perfil
"API: $Api"
```

### 7.6 Publicar el frontend

CloudFront tarda de 5 a 10 minutos en activarse la primera vez.

```powershell
aws cloudfront wait distribution-deployed --id $Distribucion --profile $Perfil
python scripts\publicar_frontend.py --bucket $Bucket --distribucion $Distribucion --api $Api --perfil $Perfil --esperar
"Aplicación: https://$Dominio"
```

Después verifica como en el paso 5 de la [sección 6](#6-publicar-una-nueva-versión-lo-más-común). Anota `$Bucket` y `$Distribucion`: los necesitarás para publicar nuevas versiones.

## 8. Pruebas

| Qué | Comando (desde la raíz del repositorio) |
|---|---|
| Pruebas unitarias (36) | `python -m unittest discover -s entregable-2\backend\tests` |
| API con curl (18 pruebas; crea dos cuentas `prueba*@miritmo.mx`) | `powershell -ExecutionPolicy Bypass -File evidencias\pruebas_curl_e2.ps1` |
| Flujo completo en Chrome o Edge (requiere `pip install playwright`) | `python evidencias\pruebas_navegador.py --url https://dnfx295km7eni.cloudfront.net --canal msedge --correo prueba-<algo>@miritmo.mx --crear --dias "0:6,4,7.5,4" --movil` |
| Rendimiento RNF-03 (20 peticiones) | `python evidencias\rendimiento_api.py` |
| Errores en CloudWatch | `aws logs filter-log-events --log-group-name /aws/lambda/miritmo-api --filter-pattern "?Traceback ?ERROR" --profile miritmo --query "length(events)"` |

Los resultados de la entrega están en [`entregable-2/docs/pruebas-aceptacion.md`](entregable-2/docs/pruebas-aceptacion.md).

## 9. Problemas comunes

| Síntoma | Causa y solución |
|---|---|
| `Your session has expired. Please reauthenticate using 'aws login'` | Corre `aws login --profile miritmo`. |
| *Access Denied* en operaciones que antes funcionaban | Revisa si el proyecto tiene un límite de gasto (*spend limit*) que lo pausó: AWS Settings → Billing. Solo el dueño del proyecto puede cambiarlo. |
| La app dice "No se pudo conectar con el servidor" | Revisa la configuración CORS de la URL de función: el origen debe ser exactamente `https://<dominio de CloudFront>` y debe permitir GET, POST y PUT. El código no debe agregar CORS en AWS (no definas `CORS_EN_CODIGO` en la Lambda). |
| `OPTIONS` no se acepta en `AllowMethods` de la URL de función | Es normal: la URL de función responde el preflight sola. Deja `GET, POST, PUT`. |
| La página sigue mostrando la versión anterior | Espera a que termine la invalidación (`--esperar`) y recarga sin caché (`Ctrl+F5`). |
| `pip` falla al empaquetar | Usa Python 3.10 o más reciente con internet. El zip se arma en una carpeta temporal fuera de OneDrive. |
| Ya tienes una instancia Cloudant Lite | Reutilízala (solo se permite una por cuenta) y crea las bases con `crear_bases_cloudant.py`. |
| `ibmcloud login` pide elegir cuenta | Elige la que tiene `miritmo-cloudant`, o agrega `-c <id de cuenta>`. |

## 10. API y regla de calificación

Todas las rutas usan JSON. Excepto crear cuenta e iniciar sesión, requieren `Authorization: Bearer <token>` (token HMAC-SHA256 válido 7 días; contraseñas con PBKDF2-SHA256 y sal).

| Método | Ruta | Cuerpo / parámetros | Respuesta |
|---|---|---|---|
| POST | `/cuentas` | `{nombre, correo, contrasena}` | `201 {token, nombre, correo}` · `409` correo repetido · `400` datos inválidos |
| POST | `/sesiones` | `{correo, contrasena}` | `200 {token, nombre, correo}` · `401` datos incorrectos |
| PUT | `/registros/AAAA-MM-DD` | `{horas_trabajo, tareas, horas_sueno, energia}` | `200 {registro}` con `calificacion` · `400` · `401` |
| GET | `/registros?desde=AAAA-MM-DD&hasta=AAAA-MM-DD` | rango de hasta 31 días | `200 {registros: [...]}` ordenados por fecha · `400` · `401` |

| Dato | Valor permitido | Puntos (máx. 25) |
|---|---|---|
| Horas de estudio o trabajo | 0 a 16, pasos de 0.5 | horas ÷ 8 × 25 (8 h o más = 25) |
| Tareas completadas | 0 a 20, entero | tareas ÷ 5 × 25 (5 o más = 25) |
| Horas de sueño | 0 a 14, pasos de 0.5 | 7–9 h = 25; 6–6.5 h o 9.5–10 h = 15; otro = 5 |
| Energía | 1 a 5, entero | energía × 5 |

La suma se redondea al entero más cercano. Ejemplo: 6 h, 4 tareas, 7.5 h de sueño y energía 4 → 18.75 + 20 + 25 + 20 = 83.75 → **84**.
