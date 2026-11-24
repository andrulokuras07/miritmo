# Bitácora de despliegue – Entregable 2

Cada entrada: comando y salida (sin secretos). Hora de CDMX.

## [1] Identidad y región

2026-11-24 13:54 · código de salida 0

```powershell
aws sts get-caller-identity --profile miritmo --query "[Account,Arn]" --output text && aws configure get region --profile miritmo
```

```text
299335570017	arn:aws:sts::299335570017:assumed-role/AccountFullAccessRole/94d80438-5021-70c9-8465-db1f91703d30
us-east-2
```

## [2] Estado del plan gratuito

2026-11-24 13:54 · código de salida 0

```powershell
aws freetier get-account-plan-state --profile miritmo --region us-east-1
```

```text
{
    "accountId": "299335570017",
    "accountPlanType": "FREE",
    "accountPlanStatus": "ACTIVE",
    "accountPlanRemainingCredits": {
        "amount": 119.999901,
        "unit": "USD"
    },
    "accountPlanExpirationDate": "2027-05-13T14:33:30.809000+00:00"
}
```

## [3] Estado actual de la Lambda (antes de actualizar)

2026-11-24 13:54 · código de salida 0

```powershell
aws lambda get-function-configuration --function-name miritmo-api --profile miritmo --query "{Runtime:Runtime,Handler:Handler,Arch:Architectures,Memoria:MemorySize,Timeout:Timeout,UltimaModificacion:LastModified,CodeSha256:CodeSha256,Variables:keys(Environment.Variables)}"
```

```text
{
    "Runtime": "python3.12",
    "Handler": "lambda_function.lambda_handler",
    "Arch": [
        "x86_64"
    ],
    "Memoria": 256,
    "Timeout": 10,
    "UltimaModificacion": "2026-11-13T18:07:30.000+0000",
    "CodeSha256": "s05LVtBa1poOz3Lm3vLW6vw4cubyheUsv9ewn976bx8=",
    "Variables": [
        "CLOUDANT_URL",
        "CLOUDANT_APIKEY",
        "TOKEN_SECRET",
        "ALLOWED_ORIGIN"
    ]
}
```

## [4] Configuración de la URL de función (CORS)

2026-11-24 13:54 · código de salida 0

```powershell
aws lambda get-function-url-config --function-name miritmo-api --profile miritmo
```

```text
{
    "FunctionUrl": "https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws/",
    "FunctionArn": "arn:aws:lambda:us-east-2:299335570017:function:miritmo-api",
    "AuthType": "NONE",
    "Cors": {
        "AllowHeaders": [
            "content-type",
            "authorization"
        ],
        "AllowMethods": [
            "GET",
            "POST",
            "PUT"
        ],
        "AllowOrigins": [
            "https://dnfx295km7eni.cloudfront.net"
        ],
        "MaxAge": 300
    },
    "CreationTime": "2026-11-13T17:59:33.397825856Z",
    "LastModifiedTime": "2026-11-13T17:59:33.397825856Z",
    "InvokeMode": "BUFFERED"
}
```

## [5] Actualizar el código de miritmo-api (zip del Entregable 2, 886 archivos, 1.5 MB)

2026-11-24 13:54 · código de salida 0

```powershell
aws lambda update-function-code --function-name miritmo-api --zip-file fileb://entregable-2/build/miritmo-lambda.zip --profile miritmo --query "{Estado:LastUpdateStatus,CodeSha256:CodeSha256,Tamano:CodeSize,UltimaModificacion:LastModified}"
```

```text
{
    "Estado": "InProgress",
    "CodeSha256": "nKDwmF0hp5HY2mRTbtUU/OqK1rlJ+9pBkdQZNC6Z5C8=",
    "Tamano": 1479322,
    "UltimaModificacion": "2026-11-24T19:54:39.000+0000"
}
```

## [6] Esperar a que termine la actualización

2026-11-24 13:54 · código de salida 0

```powershell
aws lambda wait function-updated-v2 --function-name miritmo-api --profile miritmo && aws lambda get-function-configuration --function-name miritmo-api --profile miritmo --query "{Estado:LastUpdateStatus,CodeSha256:CodeSha256,UltimaModificacion:LastModified,Variables:keys(Environment.Variables)}"
```

```text
{
    "Estado": "Successful",
    "CodeSha256": "nKDwmF0hp5HY2mRTbtUU/OqK1rlJ+9pBkdQZNC6Z5C8=",
    "UltimaModificacion": "2026-11-24T19:54:39.000+0000",
    "Variables": [
        "CLOUDANT_URL",
        "CLOUDANT_APIKEY",
        "TOKEN_SECRET",
        "ALLOWED_ORIGIN"
    ]
}
```

## [7] Publicar el frontend del Entregable 2 en S3 e invalidar CloudFront (espera a que termine)

2026-11-24 13:56 · código de salida 0

```powershell
python entregable-2/scripts/publicar_frontend.py --bucket miritmo-frontend-5e016053 --distribucion E1C3936GEOWFBQ --api https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws --perfil miritmo --esperar
```

```text
Subiendo a s3://miritmo-frontend-5e016053 ...
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\dia.html s3://miritmo-frontend-5e016053/dia.html --content-type text/html; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\index.html s3://miritmo-frontend-5e016053/index.html --content-type text/html; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\semana.html s3://miritmo-frontend-5e016053/semana.html --content-type text/html; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\css\estilos.css s3://miritmo-frontend-5e016053/css/estilos.css --content-type text/css; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\img\icono.svg s3://miritmo-frontend-5e016053/img/icono.svg --content-type image/svg+xml --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\js\acceso.js s3://miritmo-frontend-5e016053/js/acceso.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\js\comun.js s3://miritmo-frontend-5e016053/js/comun.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\js\config.js s3://miritmo-frontend-5e016053/js/config.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\js\dia.js s3://miritmo-frontend-5e016053/js/dia.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\js\semana.js s3://miritmo-frontend-5e016053/js/semana.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-v3m7a1ts\frontend\vendor\chart.umd.min.js s3://miritmo-frontend-5e016053/vendor/chart.umd.min.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
11 archivos subidos.
  $ aws cloudfront create-invalidation --distribution-id E1C3936GEOWFBQ --paths /* --output json --profile miritmo
Invalidación ICUV64D214A8Q7CE9OV1B9R3KG: InProgress
  $ aws cloudfront wait invalidation-completed --distribution-id E1C3936GEOWFBQ --id ICUV64D214A8Q7CE9OV1B9R3KG --profile miritmo
Invalidación ICUV64D214A8Q7CE9OV1B9R3KG: Completed
```


## [8] Content-Type de cada archivo servido por CloudFront, config.js, HTTPS y S3 privado

2026-11-24 13:56 · código de salida 0

```powershell
foreach ($f in <11 archivos>) { curl.exe -s -o NUL -w '%{http_code}  %{content_type}' https://dnfx295km7eni.cloudfront.net/$f }
```

```text
200  text/html; charset=utf-8  index.html
200  text/html; charset=utf-8  dia.html
200  text/html; charset=utf-8  semana.html
200  text/css; charset=utf-8  css/estilos.css
200  image/svg+xml  img/icono.svg
200  application/javascript; charset=utf-8  js/acceso.js
200  application/javascript; charset=utf-8  js/comun.js
200  application/javascript; charset=utf-8  js/config.js
200  application/javascript; charset=utf-8  js/dia.js
200  application/javascript; charset=utf-8  js/semana.js
200  application/javascript; charset=utf-8  vendor/chart.umd.min.js
--- js/config.js publicado:
// Generado por scripts/publicar_frontend.py: URL de la API (URL de función de Lambda).
window.MIRITMO_CONFIG = {
  apiUrl: "https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws",
};
http:// -> 301 https://dnfx295km7eni.cloudfront.net//nS3 directo -> 403
```

## [9] Regresión inmediata en navegador real (Playwright con Chrome instalado) contra la URL pública; cuenta temporal pruebaE2-reg-*@miritmo.mx

2026-11-24 13:57 · código de salida 0

```powershell
python evidencias/pruebas_navegador.py --url https://dnfx295km7eni.cloudfront.net --canal chrome --correo pruebaE2-reg-<marca>@miritmo.mx --crear --dias "0:5,3,8,3"
```

```text
Navegador: chrome 158.0.8127.38 · URL https://dnfx295km7eni.cloudfront.net · hoy (CDMX) 2026-11-24
OK  Sin sesión, dia.html regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Sin sesión, semana.html regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Crear cuenta y entrar a Mi día | https://dnfx295km7eni.cloudfront.net/dia.html
OK  Fechas: hoy y los 6 días anteriores | 2026-11-24, 2026-11-23, 2026-11-22, 2026-11-21, 2026-11-20, 2026-11-19, 2026-11-18
OK  Registrar 2026-11-24 {'horas_trabajo': 5.0, 'tareas': 3, 'horas_sueno': 8.0, 'energia': 3} | HTTP 200, muestra 71, cálculo a mano 71, 0.32 s
OK  RF-06: gráfica de 7 días con 'Sin registro' en los vacíos | 1 con barra, 6 'Sin registro', 10212 pixeles dibujados
OK  RF-07: promedio y mejor día | app: promedio 71, mejor 71 (Hoy); a mano: 71 = 71 / 1 = 71.00, máximo 71
OK  La semana coincide con lo guardado | guardado en esta corrida: {'2026-11-24': 71}
OK  Cerrar sesión regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Contraseña incorrecta muestra error | Correo o contraseña incorrectos.
OK  Iniciar sesión con datos correctos | https://dnfx295km7eni.cloudfront.net/dia.html
Errores de consola: ninguno · todo OK: True
```
