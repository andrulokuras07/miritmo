# Pruebas de aceptación · MiRitmo

Cada requerimiento se probó con su criterio de aceptación en la URL pública de CloudFront.
Bitácora con cada comando y su salida: [`evidencias/despliegue_e2_log.md`](../../evidencias/despliegue_e2_log.md) (`[n]` = entrada).

- URL probada: `https://dnfx295km7eni.cloudfront.net` (API: `https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws`)
- Fecha de las pruebas: 24 de noviembre de 2026
- Navegadores automatizados: Chrome 158.0.8127.38 y Edge 158.0.4370.33 (Playwright con los navegadores instalados)
- Cuenta de demostración: `examen@miritmo.mx` (4 días registrados del 18 al 24 de noviembre, el 23 editado)
- Participantes (5 compañeros): _pendiente_

## Requerimientos funcionales

| ID | Pasos | Resultado esperado | Resultado obtenido |
|---|---|---|---|
| RF-01 | Crear cuenta con nombre, correo y contraseña de 8+ caracteres. Repetir con el mismo correo. Revisar `usuarios` en Cloudant. | La cuenta se crea; el segundo intento muestra "Ya existe una cuenta con ese correo."; el documento tiene `hash` y `sal`, no la contraseña. | ✅ 201 y entra a Mi día (Chrome y Edge [14][15]). Mismo correo: 409 "Ya existe una cuenta con ese correo." [11]. Contraseña de 7: 400 "La contraseña debe tener al menos 8 caracteres." en el campo [10]. `usuarios/examen@miritmo.mx` solo tiene `_id, _rev, correo, creado, hash, nombre, sal` [22]. |
| RF-02 | Iniciar sesión con datos correctos, luego con contraseña incorrecta. Cerrar sesión y abrir `/dia.html` y `/semana.html` directamente. | Con datos correctos entra a "Mi día"; con incorrectos muestra "Correo o contraseña incorrectos."; sin sesión regresa a Acceso. | ✅ Correctos: entra a `dia.html`. Incorrectos: "Correo o contraseña incorrectos." (401). Sin sesión, `dia.html` y `semana.html` regresan a `index.html`. Cerrar sesión borra la sesión. En Chrome y Edge [9][14][15]. |
| RF-03 | Registrar el día de hoy y uno de hace 6 días. Revisar las opciones de fecha. Guardar dos veces el mismo día. | Solo se ofrecen hoy y los 6 días anteriores; los registros aparecen en `registros`; un solo documento por fecha. | ✅ El selector ofrece exactamente 2026-11-24 a 2026-11-18. Futuro (25) y hace 7 días (17): 400 [11]. Al guardar dos veces el 23 queda un solo documento `examen@miritmo.mx:2026-11-23` con `_rev 2-` [22]. |
| RF-04 | Registrar 6 h de estudio, 4 tareas, 7.5 h de sueño y energía 4. | La calificación es **84**. | ✅ 84 "Buen día" en el navegador (examen, 24 de nov) [10], por curl [11] y en Cloudant [22]. |
| RF-05 | Elegir una fecha ya registrada, cambiar un dato y guardar. | El formulario muestra los datos guardados; al guardar se actualiza el mismo registro y se recalcula la calificación. | ✅ Al elegir el 23: aviso "Ya registraste este día…", formulario con 5 / 3 / 8 / energía 3, calificación 71 y botón "Guardar cambios". Tareas 3 → 5: **71 → 81** (a mano: 15.625 + 25 + 25 + 15 = 80.6 → 81) [10]. Chrome y Edge: sueño 8 → 5 en el 22, 97 → 77 [14][15]. |
| RF-06 | Abrir "Mi semana" con algunos días sin registrar. | Gráfica de barras de los últimos 7 días; los días vacíos dicen "Sin registro". | ✅ 7 barras (Mié 18 a Hoy), 4 con calificación (38, 90, 81, 84) y "Sin registro" en el 18, el 20 y el 22, tanto en la gráfica como en la lista "Día por día" [10]. |
| RF-07 | Revisar el resumen de "Mi semana". | Muestra el promedio de los días registrados y el mejor día. | ✅ Promedio **73.3** (a mano: (38 + 90 + 81 + 84) / 4 = 293 / 4 = 73.25 → 73.3), "4 de 7 días registrados"; mejor día **90**, sábado 21 de noviembre [10]. Tras la edición, la semana muestra 81 para el 23. |
| Validaciones | Enviar datos fuera de rango y formularios vacíos en cada pantalla. | Mensajes claros por campo. | ✅ Acceso: contraseña corta → "La contraseña debe tener al menos 8 caracteres.". Mi día: 17 h → "Debe estar entre 0 y 16 horas."; vacío → un mensaje en cada uno de los 4 campos; NaN/Infinity → 400 (prueba unitaria). Mi semana: rango inválido → 400 "El rango de fechas es inválido." [10][11][19]. |

## Requerimientos no funcionales

| ID | Pasos | Resultado esperado | Resultado obtenido |
|---|---|---|---|
| RNF-01 | Abrir la URL desde un celular con datos móviles y desde una computadora. | Abre con HTTPS sin instalar nada y funciona en ambos. | ✅ Computadora: HTTPS, `http://` redirige con 301, todos los archivos 200 [8]. Celular con datos móviles: _pendiente (iPhone, junto con la fila de Safari)_. |
| RNF-02 | Llamar `GET /registros` sin token y con un token alterado. Revisar el repositorio y las variables de Lambda. | Responde 401; las credenciales solo están en variables de entorno de Lambda. | ✅ Sin token: 401. Token alterado: 401. Con token de A solo devuelve los registros de A, y con el de B solo los de B [11]. Otro origen: 403 [13]. Variables de Lambda: solo nombres `CLOUDANT_URL, CLOUDANT_APIKEY, TOKEN_SECRET, ALLOWED_ORIGIN` [6]. |
| RNF-03 | Medir 20 peticiones a la API (GET y PUT), descartando la primera. | Al menos 9 de 10 en menos de 3 s. | ✅ **19 de 19** en menos de 3 s (mín. 0.285 s, mediana 0.338 s, máx. 0.392 s) [12]. La primera invocación después del despliegue (arranque en frío) tardó 6.07 s en la Lambda [17][18]; el criterio no la cuenta. |
| RNF-04 | 5 compañeros registran su día con cronómetro. Revisar la página a 360 px. | Todos en menos de 60 s; la página se ve completa en 360 px. | ✅ 360 px: Acceso, Mi día y Mi semana con `scrollWidth = 360` y ningún elemento fuera de la pantalla, en Chrome y Edge [10][14][15]. Cronómetro con 5 compañeros: _pendiente (tabla abajo)_. |
| RNF-05 | Revisar AWS Billing y el plan de Cloudant. | $0 MXN; Cloudant en plan Lite. | ✅ AWS: plan `FREE`, estado `ACTIVE`, créditos sin usar (119.99 USD) [2]. Cloudant `miritmo-cloudant`: plan **lite**, us-south, activo [20]. |
| RNF-06 | Flujo completo (cuenta, registro, editar y gráfica) en Chrome, Safari y Edge. | Funciona en los tres navegadores. | ✅ Chrome 158: 22/22 pasos, sin errores de consola [14]. ✅ Edge 158: 22/22 pasos, sin errores de consola [15]. Safari (iPhone): _pendiente_. |
| RNF-07 | Un integrante distinto despliega siguiendo el README. | La aplicación queda desplegada y funcionando. | ✅ Código en GitHub (ver `DESPLIEGUE_E2_MiRitmo.md`). El [README](../../README.md) se siguió al pie de la letra desde un clon limpio en una carpeta temporal: la sección 6, *Publicar una nueva versión* (unitarias 36/36, empaquetar, `update-function-code`, `publicar_frontend.py --esperar`, verificación), contra los recursos existentes; todo funcionó sin cambios [25] y la app siguió funcionando después [26]. Los bloques de la sección 7 (primera vez) se revisaron con el analizador de PowerShell (0 errores) y las plantillas se probaron sin crear recursos. |
| Regresión | Script de curl del Entregable 1 + `GET /registros`. Pruebas unitarias. CloudWatch. | Todo como se espera; sin errores. | ✅ curl 18/18 [11]. Unitarias 36/36 [19]. CloudWatch: 0 eventos con `Traceback`, `ERROR`, `Task timed out` o `Exception` desde el despliegue [16]. |

## Tiempos de registro (RNF-04)

| Compañero | Dispositivo | Tiempo (s) |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
