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

## [10] Paso 3: cuenta examen@miritmo.mx creada desde la app; 4 días registrados (19, 21, 23 y 24 de nov; vacíos 18, 20 y 22), el 23 editado (tareas 3 -> 5), validaciones y 360 px

2026-11-24 13:58 · código de salida 0

```powershell
$env:MIRITMO_CLAVE = <contraseña aleatoria, solo en memoria>; python evidencias/pruebas_navegador.py --url https://dnfx295km7eni.cloudfront.net --canal chrome --correo examen@miritmo.mx --crear --validaciones --movil --dias "0:6,4,7.5,4;1:5,3,8,3;3:8,5,6.5,5;5:4,2,5,2" --editar "1:tareas=5"
```

```text
Navegador: chrome 158.0.8127.38 · URL https://dnfx295km7eni.cloudfront.net · hoy (CDMX) 2026-11-24
OK  Sin sesión, dia.html regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Sin sesión, semana.html regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Validación: contraseña de 7 caracteres | Revisa los datos marcados. / La contraseña debe tener al menos 8 caracteres.
OK  Crear cuenta y entrar a Mi día | https://dnfx295km7eni.cloudfront.net/dia.html
OK  Fechas: hoy y los 6 días anteriores | 2026-11-24, 2026-11-23, 2026-11-22, 2026-11-21, 2026-11-20, 2026-11-19, 2026-11-18
OK  Validación: 17 h de estudio (máximo 16) | HTTP 400: Revisa los datos marcados. / Debe estar entre 0 y 16 horas.
OK  Validación: formulario vacío | horas_trabajo: Escribe las horas de estudio o trabajo.; tareas: Escribe las tareas completadas.; horas_sueno: Escribe las horas de sueño.; energia: Escribe tu nivel de energía.
OK  Registrar 2026-11-19 {'horas_trabajo': 4.0, 'tareas': 2, 'horas_sueno': 5.0, 'energia': 2} | HTTP 200, muestra 38, cálculo a mano 38, 0.3 s
OK  Registrar 2026-11-21 {'horas_trabajo': 8.0, 'tareas': 5, 'horas_sueno': 6.5, 'energia': 5} | HTTP 200, muestra 90, cálculo a mano 90, 0.31 s
OK  Registrar 2026-11-23 {'horas_trabajo': 5.0, 'tareas': 3, 'horas_sueno': 8.0, 'energia': 3} | HTTP 200, muestra 71, cálculo a mano 71, 0.29 s
OK  Registrar 2026-11-24 {'horas_trabajo': 6.0, 'tareas': 4, 'horas_sueno': 7.5, 'energia': 4} | HTTP 200, muestra 84, cálculo a mano 84, 0.22 s
OK  RF-05: al elegir 2026-11-23 el formulario muestra sus datos | aviso 'Ya registraste este día. Puedes cambiar los datos y guardar de nuevo.', datos {'horas_trabajo': '5', 'tareas': '3', 'horas_sueno': '8', 'energia': '3'}, calificación mostrada 71, botón 'Guardar cambios'
OK  RF-05: editar 2026-11-23 tareas=5 recalcula | antes 71, después 81, cálculo a mano 81, 0.22 s
OK  RF-06: gráfica de 7 días con 'Sin registro' en los vacíos | 4 con barra, 3 'Sin registro', 24038 pixeles dibujados
OK  RF-07: promedio y mejor día | app: promedio 73.3, mejor 90 (Sábado, 21 de noviembre); a mano: 38 + 90 + 81 + 84 = 293 / 4 = 73.25, máximo 90
OK  La semana coincide con lo guardado | guardado en esta corrida: {'2026-11-19': 38, '2026-11-21': 90, '2026-11-23': 81, '2026-11-24': 84}
OK  RNF-04: semana.html a 360 px | {"scrollWidth": 360, "clientWidth": 360, "fuera": []}
OK  RNF-04: dia.html a 360 px | {"scrollWidth": 360, "clientWidth": 360, "fuera": []}
OK  Cerrar sesión regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  RNF-04: index.html a 360 px | {"scrollWidth": 360, "clientWidth": 360, "fuera": []}
OK  Contraseña incorrecta muestra error | Correo o contraseña incorrectos.
OK  Iniciar sesión con datos correctos | https://dnfx295km7eni.cloudfront.net/dia.html
Errores de consola: ninguno · todo OK: True
```

## [11] Paso 4 · Regresión con curl: 13 pruebas del Entregable 1 + 5 de GET /registros

2026-11-24 13:59 · código de salida 0

```powershell
powershell -ExecutionPolicy Bypass -File evidencias\pruebas_curl_e2.ps1
```

```text
MiRitmo - pruebas con curl contra https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws
Hoy (CDMX): 2026-11-24

[OK ] RF-01   Crear cuenta nueva                                         HTTP 201  token recibido (oculto)
[OK ] RF-01   Crear cuenta con el mismo correo                           HTTP 409  Ya existe una cuenta con ese correo.
[OK ] RF-01   Crear cuenta con contraseña de 7 caracteres                HTTP 400  Revisa los datos marcados.
[OK ] RF-02   Iniciar sesión con datos correctos                         HTTP 200  token recibido (oculto)
[OK ] RF-02   Iniciar sesión con contraseña incorrecta                   HTTP 401  Correo o contraseña incorrectos.
[OK ] RF-03   Guardar registro de hoy (2026-11-24)                       HTTP 200  calificación 71
[OK ] RF-03   Guardar registro con fecha futura (2026-11-25)             HTTP 400  No puedes registrar días futuros.
[OK ] RF-03   Guardar registro de hace 7 días (2026-11-17)               HTTP 400  Solo puedes registrar hoy o los 6 días anteriores.
[OK ] RF-04   6 h, 4 tareas, 7.5 h sueño, energía 4 (esperado 84)        HTTP 200  calificación 84
[OK ] RNF-02  PUT sin token                                              HTTP 401  Tu sesión no es válida o expiró. Inicia sesión de nuevo.
[OK ] RNF-02  PUT con token alterado                                     HTTP 401  Tu sesión no es válida o expiró. Inicia sesión de nuevo.
[OK ] RNF-02  Usuario B manda usuario=A en el cuerpo (se guarda como B)  HTTP 200  calificación 10
[OK ] RNF-02  Usuario B intenta la ruta /registros/<correo A>:<fecha>    HTTP 400  Fecha inválida.
[OK ] RNF-02  GET /registros sin token                                   HTTP 401  Tu sesión no es válida o expiró. Inicia sesión de nuevo.
[OK ] RNF-02  GET /registros con token alterado                          HTTP 401  Tu sesión no es válida o expiró. Inicia sesión de nuevo.
[OK ] RF-06   GET rango válido (7 días) con token de A: solo los de A    HTTP 200  1 registro(s): 2026-11-24=84
[OK ] RF-06   GET rango válido con token de B: solo los de B             HTTP 200  1 registro(s): 2026-11-24=10
[OK ] RF-06   GET rango inválido (desde posterior a hasta)               HTTP 400  El rango de fechas es inválido.

Resultado: 18 de 18 pruebas como se esperaba.
Cuentas de prueba: pruebaA-20261124135944@miritmo.mx y pruebaB-20261124135944@miritmo.mx
```

## [12] Paso 4 · RNF-03: 20 peticiones a la API (GET y PUT alternados), se descarta la primera

2026-11-24 14:00 · código de salida 0

```powershell
python evidencias/rendimiento_api.py
```

```text
MiRitmo · RNF-03 · 20 peticiones a https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws
Cuenta temporal: pruebaE2-rend-20261124135957@miritmo.mx  (hoy CDMX: 2026-11-24)

  #  Método Ruta                                         HTTP    Tiempo
  1  GET    /registros?desde=2026-11-18&hasta=2026-11-24  200   0.324 s  (descartada: primera petición)
  2  PUT    /registros/2026-11-23                         200   0.392 s
  3  GET    /registros?desde=2026-11-18&hasta=2026-11-24  200   0.300 s
  4  PUT    /registros/2026-11-22                         200   0.343 s
  5  GET    /registros?desde=2026-11-18&hasta=2026-11-24  200   0.308 s
  6  PUT    /registros/2026-11-21                         200   0.359 s
  7  GET    /registros?desde=2026-11-18&hasta=2026-11-24  200   0.299 s
  8  PUT    /registros/2026-11-20                         200   0.338 s
  9  GET    /registros?desde=2026-11-18&hasta=2026-11-24  200   0.307 s
 10  PUT    /registros/2026-11-19                         200   0.358 s
 11  GET    /registros?desde=2026-11-18&hasta=2026-11-24  200   0.339 s
 12  PUT    /registros/2026-11-18                         200   0.341 s
 13  GET    /registros?desde=2026-11-18&hasta=2026-11-24  200   0.296 s
 14  PUT    /registros/2026-11-24                         200   0.333 s
 15  GET    /registros?desde=2026-11-18&hasta=2026-11-24  200   0.328 s
 16  PUT    /registros/2026-11-23                         200   0.343 s
 17  GET    /registros?desde=2026-11-18&hasta=2026-11-24  200   0.285 s
 18  PUT    /registros/2026-11-22                         200   0.374 s
 19  GET    /registros?desde=2026-11-18&hasta=2026-11-24  200   0.313 s
 20  PUT    /registros/2026-11-21                         200   0.352 s

Contadas: 19 · menos de 3 s con HTTP 200: 19 de 19 (100 %; criterio: 90 % o más)
Mínimo 0.285 s · mediana 0.338 s · máximo 0.392 s · promedio 0.332 s
RNF-03: CUMPLE
CUENTA_TEMPORAL=pruebaE2-rend-20261124135957@miritmo.mx
```

## [13] Paso 4 · CORS de GET /registros: preflight y petición desde CloudFront y desde otro origen

2026-11-24 14:00 · código de salida 0

```powershell
curl.exe -X OPTIONS <api>/registros?... -H 'Origin: https://dnfx295km7eni.cloudfront.net' -H 'Access-Control-Request-Method: GET'  (y GET desde CloudFront y desde otro origen)
```

```text
--- Preflight de GET /registros desde CloudFront:
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://dnfx295km7eni.cloudfront.net
Access-Control-Allow-Headers: content-type,authorization
Access-Control-Allow-Methods: GET,POST,PUT
Access-Control-Max-Age: 300
--- GET real desde CloudFront (sin token): ¿un solo Access-Control-Allow-Origin?
HTTP/1.1 401 Unauthorized
Access-Control-Allow-Origin: https://dnfx295km7eni.cloudfront.net
--- GET desde otro origen:
HTTP/1.1 403 Forbidden
{"error": "Origen no permitido."}
```

## [14] Paso 4 · RNF-06: flujo completo en chrome (cuenta, validaciones, registro, editar, Mi semana, 360 px, cerrar e iniciar sesión)

2026-11-24 14:01 · código de salida 0

```powershell
python evidencias/pruebas_navegador.py --url https://dnfx295km7eni.cloudfront.net --canal chrome --correo pruebaE2-chrome-<marca>@miritmo.mx --crear --validaciones --movil --dias "0:6,4,7.5,4;2:7,5,8,5;4:3,1,6,2" --editar "2:horas_sueno=5"
```

```text
Navegador: chrome 158.0.8127.38 · URL https://dnfx295km7eni.cloudfront.net · hoy (CDMX) 2026-11-24
OK  Sin sesión, dia.html regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Sin sesión, semana.html regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Validación: contraseña de 7 caracteres | Revisa los datos marcados. / La contraseña debe tener al menos 8 caracteres.
OK  Crear cuenta y entrar a Mi día | https://dnfx295km7eni.cloudfront.net/dia.html
OK  Fechas: hoy y los 6 días anteriores | 2026-11-24, 2026-11-23, 2026-11-22, 2026-11-21, 2026-11-20, 2026-11-19, 2026-11-18
OK  Validación: 17 h de estudio (máximo 16) | HTTP 400: Revisa los datos marcados. / Debe estar entre 0 y 16 horas.
OK  Validación: formulario vacío | horas_trabajo: Escribe las horas de estudio o trabajo.; tareas: Escribe las tareas completadas.; horas_sueno: Escribe las horas de sueño.; energia: Escribe tu nivel de energía.
OK  Registrar 2026-11-20 {'horas_trabajo': 3.0, 'tareas': 1, 'horas_sueno': 6.0, 'energia': 2} | HTTP 200, muestra 39, cálculo a mano 39, 0.31 s
OK  Registrar 2026-11-22 {'horas_trabajo': 7.0, 'tareas': 5, 'horas_sueno': 8.0, 'energia': 5} | HTTP 200, muestra 97, cálculo a mano 97, 0.29 s
OK  Registrar 2026-11-24 {'horas_trabajo': 6.0, 'tareas': 4, 'horas_sueno': 7.5, 'energia': 4} | HTTP 200, muestra 84, cálculo a mano 84, 0.22 s
OK  RF-05: al elegir 2026-11-22 el formulario muestra sus datos | aviso 'Ya registraste este día. Puedes cambiar los datos y guardar de nuevo.', datos {'horas_trabajo': '7', 'tareas': '5', 'horas_sueno': '8', 'energia': '5'}, calificación mostrada 97, botón 'Guardar cambios'
OK  RF-05: editar 2026-11-22 horas_sueno=5 recalcula | antes 97, después 77, cálculo a mano 77, 0.21 s
OK  RF-06: gráfica de 7 días con 'Sin registro' en los vacíos | 3 con barra, 4 'Sin registro', 18162 pixeles dibujados
OK  RF-07: promedio y mejor día | app: promedio 66.7, mejor 84 (Hoy); a mano: 39 + 77 + 84 = 200 / 3 = 66.67, máximo 84
OK  La semana coincide con lo guardado | guardado en esta corrida: {'2026-11-20': 39, '2026-11-22': 77, '2026-11-24': 84}
OK  RNF-04: semana.html a 360 px | {"scrollWidth": 360, "clientWidth": 360, "fuera": []}
OK  RNF-04: dia.html a 360 px | {"scrollWidth": 360, "clientWidth": 360, "fuera": []}
OK  Cerrar sesión regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  RNF-04: index.html a 360 px | {"scrollWidth": 360, "clientWidth": 360, "fuera": []}
OK  Contraseña incorrecta muestra error | Correo o contraseña incorrectos.
OK  Iniciar sesión con datos correctos | https://dnfx295km7eni.cloudfront.net/dia.html
Errores de consola: ninguno · todo OK: True
```

## [15] Paso 4 · RNF-06: flujo completo en msedge (cuenta, validaciones, registro, editar, Mi semana, 360 px, cerrar e iniciar sesión)

2026-11-24 14:01 · código de salida 0

```powershell
python evidencias/pruebas_navegador.py --url https://dnfx295km7eni.cloudfront.net --canal msedge --correo pruebaE2-msedge-<marca>@miritmo.mx --crear --validaciones --movil --dias "0:6,4,7.5,4;2:7,5,8,5;4:3,1,6,2" --editar "2:horas_sueno=5"
```

```text
Navegador: msedge 158.0.4370.33 · URL https://dnfx295km7eni.cloudfront.net · hoy (CDMX) 2026-11-24
OK  Sin sesión, dia.html regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Sin sesión, semana.html regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Validación: contraseña de 7 caracteres | Revisa los datos marcados. / La contraseña debe tener al menos 8 caracteres.
OK  Crear cuenta y entrar a Mi día | https://dnfx295km7eni.cloudfront.net/dia.html
OK  Fechas: hoy y los 6 días anteriores | 2026-11-24, 2026-11-23, 2026-11-22, 2026-11-21, 2026-11-20, 2026-11-19, 2026-11-18
OK  Validación: 17 h de estudio (máximo 16) | HTTP 400: Revisa los datos marcados. / Debe estar entre 0 y 16 horas.
OK  Validación: formulario vacío | horas_trabajo: Escribe las horas de estudio o trabajo.; tareas: Escribe las tareas completadas.; horas_sueno: Escribe las horas de sueño.; energia: Escribe tu nivel de energía.
OK  Registrar 2026-11-20 {'horas_trabajo': 3.0, 'tareas': 1, 'horas_sueno': 6.0, 'energia': 2} | HTTP 200, muestra 39, cálculo a mano 39, 0.33 s
OK  Registrar 2026-11-22 {'horas_trabajo': 7.0, 'tareas': 5, 'horas_sueno': 8.0, 'energia': 5} | HTTP 200, muestra 97, cálculo a mano 97, 0.32 s
OK  Registrar 2026-11-24 {'horas_trabajo': 6.0, 'tareas': 4, 'horas_sueno': 7.5, 'energia': 4} | HTTP 200, muestra 84, cálculo a mano 84, 0.23 s
OK  RF-05: al elegir 2026-11-22 el formulario muestra sus datos | aviso 'Ya registraste este día. Puedes cambiar los datos y guardar de nuevo.', datos {'horas_trabajo': '7', 'tareas': '5', 'horas_sueno': '8', 'energia': '5'}, calificación mostrada 97, botón 'Guardar cambios'
OK  RF-05: editar 2026-11-22 horas_sueno=5 recalcula | antes 97, después 77, cálculo a mano 77, 0.23 s
OK  RF-06: gráfica de 7 días con 'Sin registro' en los vacíos | 3 con barra, 4 'Sin registro', 18162 pixeles dibujados
OK  RF-07: promedio y mejor día | app: promedio 66.7, mejor 84 (Hoy); a mano: 39 + 77 + 84 = 200 / 3 = 66.67, máximo 84
OK  La semana coincide con lo guardado | guardado en esta corrida: {'2026-11-20': 39, '2026-11-22': 77, '2026-11-24': 84}
OK  RNF-04: semana.html a 360 px | {"scrollWidth": 360, "clientWidth": 360, "fuera": []}
OK  RNF-04: dia.html a 360 px | {"scrollWidth": 360, "clientWidth": 360, "fuera": []}
OK  Cerrar sesión regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  RNF-04: index.html a 360 px | {"scrollWidth": 360, "clientWidth": 360, "fuera": []}
OK  Contraseña incorrecta muestra error | Correo o contraseña incorrectos.
OK  Iniciar sesión con datos correctos | https://dnfx295km7eni.cloudfront.net/dia.html
Errores de consola: ninguno · todo OK: True
```

## [16] Paso 4 · CloudWatch: errores desde el despliegue del Entregable 2 (19:50 UTC)

2026-11-24 14:01 · código de salida 0

```powershell
aws logs filter-log-events --log-group-name /aws/lambda/miritmo-api --start-time <2026-11-24 19:50 UTC> --filter-pattern '?Traceback ?ERROR ?"Task timed out" ?Exception' --query 'length(events)'
```

```text
0
```

## [17] Paso 4 · CloudWatch: ejecuciones (REPORT) desde el despliegue: cantidad, duración y memoria

2026-11-24 14:02 · código de salida 0

```powershell
aws logs filter-log-events --log-group-name /aws/lambda/miritmo-api --start-time <19:50 UTC> --filter-pattern REPORT  (resumen con Python)
```

```text
Ejecuciones: 137
Duracion ms: min 1.49 max 6072.5 promedio 210.8
Memoria max usada MB: 99 de 256
Arranques en frio: 1 Init ms: [218.93]
```

## [18] Paso 4 · Resumen de CloudWatch: la ejecución de 6072 ms es la primera tras el despliegue (arranque en frío, Init Duration 218.93 ms, POST /cuentas); el resto <= 775 ms

2026-11-24 14:02 · código de salida 0

```powershell
aws logs filter-log-events --log-group-name /aws/lambda/miritmo-api --start-time <19:50 UTC> --filter-pattern REPORT  (10 duraciones más altas)
```

```text
Ejecuciones 137 | 10 mas lentas (ms): [742.32, 742.91, 743.58, 746.26, 749.61, 753.51, 753.57, 758.82, 774.6, 6072.5]
```

## [19] Paso 4 · Pruebas unitarias del Entregable 2

2026-11-24 14:02 · código de salida 0

```powershell
cd entregable-2\backend; python -m unittest discover -s tests -v
```

```text
test_ejemplo_del_documento_es_84 (test_api.PruebasCalificacion.test_ejemplo_del_documento_es_84) ... ok
test_maximo_100_y_topes (test_api.PruebasCalificacion.test_maximo_100_y_topes) ... ok
test_minimo (test_api.PruebasCalificacion.test_minimo) ... ok
test_niveles_de_sueno (test_api.PruebasCalificacion.test_niveles_de_sueno) ... ok
test_redondeo_al_entero_mas_cercano (test_api.PruebasCalificacion.test_redondeo_al_entero_mas_cercano) ... ok
test_correo_parecido_no_se_mezcla (test_api.PruebasConsulta.test_correo_parecido_no_se_mezcla) ... ok
test_devuelve_los_dias_registrados_en_orden (test_api.PruebasConsulta.test_devuelve_los_dias_registrados_en_orden) ... ok
test_editar_dia_actualiza_y_recalcula (test_api.PruebasConsulta.test_editar_dia_actualiza_y_recalcula) ... ok
test_no_ve_registros_de_otro_usuario (test_api.PruebasConsulta.test_no_ve_registros_de_otro_usuario) ... ok
test_rango_invalido (test_api.PruebasConsulta.test_rango_invalido) ... ok
test_sin_token_responde_401 (test_api.PruebasConsulta.test_sin_token_responde_401) ... ok
test_contrasena_minimo_8 (test_api.PruebasCuentas.test_contrasena_minimo_8) ... ok
test_contrasena_no_se_guarda_en_texto_plano (test_api.PruebasCuentas.test_contrasena_no_se_guarda_en_texto_plano) ... ok
test_crear_cuenta_devuelve_token (test_api.PruebasCuentas.test_crear_cuenta_devuelve_token) ... ok
test_datos_invalidos (test_api.PruebasCuentas.test_datos_invalidos) ... ok
test_mismo_correo_no_se_registra_dos_veces (test_api.PruebasCuentas.test_mismo_correo_no_se_registra_dos_veces) ... ok
test_cors_en_aws_lo_pone_la_url_de_funcion (test_api.PruebasHttp.test_cors_en_aws_lo_pone_la_url_de_funcion) ... ok
test_cors_para_cloudfront_en_codigo (test_api.PruebasHttp.test_cors_para_cloudfront_en_codigo) ... ok
test_json_invalido (test_api.PruebasHttp.test_json_invalido) ... ok
test_origen_no_permitido (test_api.PruebasHttp.test_origen_no_permitido) ... ok
test_ruta_inexistente (test_api.PruebasHttp.test_ruta_inexistente) ... ok
test_cada_usuario_escribe_solo_sus_registros (test_api.PruebasRegistros.test_cada_usuario_escribe_solo_sus_registros) ... ok
test_fecha_con_formato_invalido (test_api.PruebasRegistros.test_fecha_con_formato_invalido) ... ok
test_fecha_futura_rechazada (test_api.PruebasRegistros.test_fecha_futura_rechazada) ... ok
test_guardar_dia_devuelve_calificacion (test_api.PruebasRegistros.test_guardar_dia_devuelve_calificacion) ... ok
test_mas_de_seis_dias_atras_rechazada (test_api.PruebasRegistros.test_mas_de_seis_dias_atras_rechazada) ... ok
test_nan_e_infinity_responden_400 (test_api.PruebasRegistros.test_nan_e_infinity_responden_400) ... ok
test_seis_dias_anteriores_permitidos (test_api.PruebasRegistros.test_seis_dias_anteriores_permitidos) ... ok
test_sin_token_responde_401 (test_api.PruebasRegistros.test_sin_token_responde_401) ... ok
test_token_expirado_responde_401 (test_api.PruebasRegistros.test_token_expirado_responde_401) ... ok
test_token_invalido_responde_401 (test_api.PruebasRegistros.test_token_invalido_responde_401) ... ok
test_un_solo_registro_por_usuario_y_fecha (test_api.PruebasRegistros.test_un_solo_registro_por_usuario_y_fecha) ... ok
test_valores_fuera_de_rango (test_api.PruebasRegistros.test_valores_fuera_de_rango) ... ok
test_contrasena_incorrecta (test_api.PruebasSesiones.test_contrasena_incorrecta) ... ok
test_correo_inexistente (test_api.PruebasSesiones.test_correo_inexistente) ... ok
test_inicio_correcto (test_api.PruebasSesiones.test_inicio_correcto) ... ok

----------------------------------------------------------------------
Ran 36 tests in 2.546s

OK
```

## [20] Paso 4 · RNF-05: plan de la instancia de Cloudant

2026-11-24 14:23 · código de salida 0

```powershell
ibmcloud resource service-instance miritmo-cloudant
```

```text
{'name': 'miritmo-cloudant', 'region_id': 'us-south', 'state': 'active', 'type': 'service_instance'} plan: cloudant-lite
Name:                  miritmo-cloudant
Location:              us-south
Service Name:          cloudantnosqldb
Service Plan Name:     lite
Resource Group Name:   Default
State:                 active
```

## [21] Paso 4 · Cloudant antes de limpiar: usuarios y número de registros de cada uno

2026-11-24 14:23 · código de salida 0

```powershell
python con_cloudant.py listar  (credencial de servicio solo en memoria)
```

```text
Base usuarios: 10 documentos
   demo@miritmo.mx -> 1 registro(s)
   examen@miritmo.mx -> 4 registro(s)
   pruebaa-20261124135906@miritmo.mx -> 1 registro(s)
   pruebaa-20261124135944@miritmo.mx -> 1 registro(s)
   pruebab-20261124135906@miritmo.mx -> 1 registro(s)
   pruebab-20261124135944@miritmo.mx -> 1 registro(s)
   pruebae2-chrome-20261124140027@miritmo.mx -> 3 registro(s)
   pruebae2-msedge-20261124140100@miritmo.mx -> 3 registro(s)
   pruebae2-reg-20261124135648@miritmo.mx -> 1 registro(s)
   pruebae2-rend-20261124135957@miritmo.mx -> 7 registro(s)
Base registros: 23 documentos
```

## [22] Paso 4 · Cloudant: documentos de examen@miritmo.mx (sin contraseña en texto plano; el 23 editado)

2026-11-24 14:23 · código de salida 0

```powershell
python con_cloudant.py ver examen@miritmo.mx
```

```text
usuarios/examen@miritmo.mx: campos ['_id', '_rev', 'correo', 'creado', 'hash', 'nombre', 'sal']; ¿tiene 'contrasena'? False; hash 64 caracteres, sal 32 caracteres
  registros/examen@miritmo.mx:2026-11-19: trabajo 4.0, tareas 2, sueño 5.0, energía 2 -> calificación 38; actualizado 2026-11-24T19:57:52+00:00; _rev 1-..
  registros/examen@miritmo.mx:2026-11-21: trabajo 8.0, tareas 5, sueño 6.5, energía 5 -> calificación 90; actualizado 2026-11-24T19:57:53+00:00; _rev 1-..
  registros/examen@miritmo.mx:2026-11-23: trabajo 5.0, tareas 5, sueño 8.0, energía 3 -> calificación 81; actualizado 2026-11-24T19:57:59+00:00; _rev 2-..
  registros/examen@miritmo.mx:2026-11-24: trabajo 6.0, tareas 4, sueño 7.5, energía 4 -> calificación 84; actualizado 2026-11-24T19:57:55+00:00; _rev 1-..
```

## [23] Paso 4 · Borrar las 8 cuentas de prueba creadas hoy (usuario y sus registros); se conservan examen@ y demo@

2026-11-24 14:24 · código de salida 0

```powershell
python con_cloudant.py borrar <lista de 8 cuentas prueba*-20261124*>
```

```text
pruebaa-20261124135906@miritmo.mx: usuario borrado=True, registros borrados=1
  pruebaa-20261124135944@miritmo.mx: usuario borrado=True, registros borrados=1
  pruebab-20261124135906@miritmo.mx: usuario borrado=True, registros borrados=1
  pruebab-20261124135944@miritmo.mx: usuario borrado=True, registros borrados=1
  pruebae2-chrome-20261124140027@miritmo.mx: usuario borrado=True, registros borrados=3
  pruebae2-msedge-20261124140100@miritmo.mx: usuario borrado=True, registros borrados=3
  pruebae2-reg-20261124135648@miritmo.mx: usuario borrado=True, registros borrados=1
  pruebae2-rend-20261124135957@miritmo.mx: usuario borrado=True, registros borrados=7
```

## [24] Paso 4 · Cloudant después de limpiar

2026-11-24 14:24 · código de salida 0

```powershell
python con_cloudant.py listar
```

```text
Base usuarios: 2 documentos
   demo@miritmo.mx -> 1 registro(s)
   examen@miritmo.mx -> 4 registro(s)
Base registros: 5 documentos
```

## [25] Paso 5 · RNF-07: README validado al pie de la letra desde un clon limpio (git clone en carpeta temporal, commit 1b5083e), sección 6 'Publicar una nueva versión' contra los recursos existentes

2026-11-24 14:31 · código de salida 0

```powershell
git clone <repo> %TEMP%\...\validacion-readme\miritmo; cd miritmo; (bloques de la sección 6 del README, copiados tal cual)
```

```text
﻿===== Bloque 1 de la sección 6 =====
PS> cd entregable-2
PS> $Perfil = "miritmo"
PS> $Funcion = "miritmo-api"
PS> $Bucket = "miritmo-frontend-5e016053"
PS> $Distribucion = "E1C3936GEOWFBQ"
===== Bloque 2 de la sección 6 =====
PS> python -m unittest discover -s backend\tests
....................................
 
----------------------------------------------------------------------
Ran 36 tests in 2.375s

OK
===== Bloque 3 de la sección 6 =====
PS> python scripts\empaquetar_lambda.py
C:\Users\aangu\AppData\Local\Temp\claude\0d04e3b7ac9416b4\58d5292c-d0e0-412d-9cdd-a80dc9e63238\scratchpad\validacion-readme\miritmo\entregable-2\build\miritmo-lambda.zip: 886 archivos, 1.5 MB
===== Bloque 4 de la sección 6 =====
PS> aws lambda update-function-code --function-name $Funcion --zip-file fileb://build/miritmo-lambda.zip --profile $Perfil --query "{Estado:LastUpdateStatus,Sha256:CodeSha256}"
{
    "Estado": "InProgress",
    "Sha256": "OhOZqWJFfdD2nAtarRbmnuiGpco4i5LE4fshNhLujZM="
}
PS> aws lambda wait function-updated-v2 --function-name $Funcion --profile $Perfil
===== Bloque 5 de la sección 6 =====
PS> $Api = aws lambda get-function-url-config --function-name $Funcion --profile $Perfil --query FunctionUrl --output text
PS> python scripts\publicar_frontend.py --bucket $Bucket --distribucion $Distribucion --api $Api --perfil $Perfil --esperar
Subiendo a s3://miritmo-frontend-5e016053 ...
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\dia.html s3://miritmo-frontend-5e016053/dia.html --content-type text/html; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\index.html s3://miritmo-frontend-5e016053/index.html --content-type text/html; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\semana.html s3://miritmo-frontend-5e016053/semana.html --content-type text/html; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\css\estilos.css s3://miritmo-frontend-5e016053/css/estilos.css --content-type text/css; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\img\icono.svg s3://miritmo-frontend-5e016053/img/icono.svg --content-type image/svg+xml --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\js\acceso.js s3://miritmo-frontend-5e016053/js/acceso.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\js\comun.js s3://miritmo-frontend-5e016053/js/comun.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\js\config.js s3://miritmo-frontend-5e016053/js/config.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\js\dia.js s3://miritmo-frontend-5e016053/js/dia.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\js\semana.js s3://miritmo-frontend-5e016053/js/semana.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
  $ aws s3 cp C:\Users\aangu\AppData\Local\Temp\miritmo-web-eltl3dvv\frontend\vendor\chart.umd.min.js s3://miritmo-frontend-5e016053/vendor/chart.umd.min.js --content-type application/javascript; charset=utf-8 --cache-control no-cache --only-show-errors --profile miritmo
11 archivos subidos.
  $ aws cloudfront create-invalidation --distribution-id E1C3936GEOWFBQ --paths /* --output json --profile miritmo
Invalidación I82FIGK66MBO1CXJF5WMKEN0S3: InProgress
  $ aws cloudfront wait invalidation-completed --distribution-id E1C3936GEOWFBQ --id I82FIGK66MBO1CXJF5WMKEN0S3 --profile miritmo
Invalidación I82FIGK66MBO1CXJF5WMKEN0S3: Completed
===== Bloque 6 de la sección 6 =====
PS> $Dominio = aws cloudfront get-distribution --id $Distribucion --profile $Perfil --query Distribution.DomainName --output text
PS> curl.exe -s "https://$Dominio/js/config.js"
// Generado por scripts/publicar_frontend.py: URL de la API (URL de función de Lambda).
window.MIRITMO_CONFIG = {
  apiUrl: "https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws",
};
PS> curl.exe -s -o NUL -w "semana.html: %{http_code} %{content_type}`n" "https://$Dominio/semana.html"
semana.html: 200 text/html; charset=utf-8
PS> curl.exe -s -w "`nGET /registros sin token: <oculto>" "$($Api.TrimEnd('/'))/registros?desde=2026-11-01&hasta=2026-11-07"
{"error": "Tu sesión no es válida o expiró. Inicia sesión de nuevo."}
GET /registros sin token: <oculto>
```

## [26] Paso 5 · Después de publicar desde el clon: la app sigue funcionando con examen@miritmo.mx (solo lectura)

2026-11-24 14:31 · código de salida 0

```powershell
python evidencias/pruebas_navegador.py --url https://dnfx295km7eni.cloudfront.net --canal chrome --correo examen@miritmo.mx
```

```text
Navegador: chrome 158.0.8127.38 · URL https://dnfx295km7eni.cloudfront.net · hoy (CDMX) 2026-11-24
OK  Sin sesión, dia.html regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Sin sesión, semana.html regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Iniciar sesión y entrar a Mi día | https://dnfx295km7eni.cloudfront.net/dia.html
OK  Fechas: hoy y los 6 días anteriores | 2026-11-24, 2026-11-23, 2026-11-22, 2026-11-21, 2026-11-20, 2026-11-19, 2026-11-18
OK  RF-06: gráfica de 7 días con 'Sin registro' en los vacíos | 4 con barra, 3 'Sin registro', 24038 pixeles dibujados
OK  RF-07: promedio y mejor día | app: promedio 73.3, mejor 90 (Sábado, 21 de noviembre); a mano: 38 + 90 + 81 + 84 = 293 / 4 = 73.25, máximo 90
OK  Cerrar sesión regresa a Acceso | https://dnfx295km7eni.cloudfront.net/index.html
OK  Contraseña incorrecta muestra error | Correo o contraseña incorrectos.
OK  Iniciar sesión con datos correctos | https://dnfx295km7eni.cloudfront.net/dia.html
Errores de consola: ninguno · todo OK: True
```

## [27] Paso 5 · Revisión de secretos en TODO el historial (16 commits, todas las versiones de todos los archivos)

2026-11-24 14:34 · código de salida 0

```powershell
git grep -I -E '<patrón>' $(git rev-list --all)   (15 patrones) ; git log --all --name-only
```

```text
Archivos prohibidos en el historial (build/, .env, CLAUDE.md, zip, pem, key, entorno.json): ninguno 
Cloudant host (appdomain.cloud): 0 
URLs con credenciales: 0 
Llaves AWS (AKIA/ASIA, SecretAccessKey): 0 
Llaves privadas: 0 
Tokens de GitHub (gh*_): 0 
Tokens JWT/MiRitmo (eyJ...): 0 
apikey con valor: 0 
TOKEN_SECRET con valor: 0 
Contrasenas: solo valores de prueba en tests y scripts (abc1234, incorrecta123, contrasena123, otra-clave, 12345678, 1234567) 
Cadenas de alta entropia: solo hashes CodeSha256, ID de la URL de Lambda, trace IDs de X-Ray 
Binarios en el historial: ninguno
```

## [28] Paso 5 · GitHub: cuenta de gh y repositorio público

2026-11-24 14:34 · código de salida 0

```powershell
gh api user --jq .login ; gh repo create andrulokuras07/miritmo --public --source . --remote origin ; git config --local credential.https://github.com.username andrulokuras07 ; git push -u origin master ; gh repo edit --default-branch master
```

```text
andrulokuras07
{"dueno":"andrulokuras07","rama":"master","url":"https://github.com/andrulokuras07/miritmo","visibilidad":"public"}
origin	https://github.com/andrulokuras07/miritmo.git (fetch)
origin	https://github.com/andrulokuras07/miritmo.git (push)
```
