# Pruebas de aceptación · MiRitmo

Cada requerimiento se prueba con su criterio de aceptación en la URL pública de CloudFront.
Llena la columna **Resultado obtenido** con lo que pasó (✅ / ❌ y una nota breve).

- URL probada: `https://__________.cloudfront.net`
- Fecha de las pruebas: ____________
- Participantes (5 compañeros): ____________________________________________

## Requerimientos funcionales

| ID | Pasos | Resultado esperado | Resultado obtenido |
|---|---|---|---|
| RF-01 | Crear cuenta con nombre, correo y contraseña de 8+ caracteres. Repetir con el mismo correo. Revisar `usuarios` en Cloudant. | La cuenta se crea; el segundo intento muestra "Este correo ya está registrado"; el documento tiene `hash` y `sal`, no la contraseña. | |
| RF-02 | Iniciar sesión con datos correctos, luego con contraseña incorrecta. Cerrar sesión y abrir `/dia.html` y `/semana.html` directamente. | Con datos correctos entra a "Mi día"; con incorrectos muestra "Correo o contraseña incorrectos"; sin sesión regresa a Acceso. | |
| RF-03 | Registrar el día de hoy y uno de hace 6 días. Revisar las opciones de fecha. Guardar dos veces el mismo día. | Solo se ofrecen hoy y los 6 días anteriores; los registros aparecen en `registros`; un solo documento por fecha. | |
| RF-04 | Registrar 6 h de estudio, 4 tareas, 7.5 h de sueño y energía 4. | La calificación es **84**. | |
| RF-05 | Elegir una fecha ya registrada, cambiar un dato y guardar. | El formulario muestra los datos guardados; al guardar se actualiza el mismo registro y se recalcula la calificación. | |
| RF-06 | Abrir "Mi semana" con algunos días sin registrar. | Gráfica de barras de los últimos 7 días; los días vacíos dicen "Sin registro". | |
| RF-07 | Revisar el resumen de "Mi semana". | Muestra el promedio de los días registrados y el mejor día. | |

## Requerimientos no funcionales

| ID | Pasos | Resultado esperado | Resultado obtenido |
|---|---|---|---|
| RNF-01 | Abrir la URL desde un celular con datos móviles y desde una computadora. | Abre con HTTPS sin instalar nada y funciona en ambos. | |
| RNF-02 | Llamar `GET /registros` sin token y con un token alterado. Revisar el repositorio y las variables de Lambda. | Responde 401; las credenciales solo están en variables de entorno de Lambda. | |
| RNF-03 | Medir 10 peticiones a la API en *DevTools → Network*. | Al menos 9 de 10 en menos de 3 s (sin contar la primera tras inactividad). | |
| RNF-04 | 5 compañeros registran su día con cronómetro. Revisar la página a 360 px. | Todos en menos de 60 s; la página se ve completa en 360 px. | |
| RNF-05 | Revisar AWS Billing y el plan de Cloudant. | $0 MXN; Cloudant en plan Lite. | |
| RNF-06 | Flujo completo (cuenta, registro y gráfica) en Chrome, Safari y Edge. | Funciona en los tres navegadores. | |
| RNF-07 | Un integrante distinto despliega siguiendo el README. | La aplicación queda desplegada y funcionando. | |

## Tiempos de registro (RNF-04)

| Compañero | Dispositivo | Tiempo (s) |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
