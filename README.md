# MiRitmo

Medidor de rendimiento diario para estudiantes y jóvenes profesionistas: un registro de menos de un minuto, una calificación del día de 0 a 100 y una gráfica semanal.

Infraestructura y Cómputo en la Nube · Universidad Anáhuac Querétaro

## Entregables

El producto se construye en dos incrementos. Cada carpeta es independiente y se despliega por su cuenta.

| Carpeta | Entrega | Contenido |
|---|---|---|
| [`entregable-1/`](entregable-1/README.md) | Práctica: Entregable uno | Crear cuenta, iniciar/cerrar sesión, registrar el día y ver la calificación (RF-01 a RF-04) |
| [`entregable-2/`](entregable-2/README.md) | Examen final | MVP completo: + editar días, gráfica semanal y resumen (RF-01 a RF-07, RNF-01 a RNF-07) |

## Arquitectura

```
Navegador ──HTTPS──▶ CloudFront ──▶ S3 (bucket privado: HTML, CSS, JS, Chart.js)
    │
    └──HTTPS + token──▶ Lambda (Python 3.12, URL de función) ──▶ IBM Cloudant (usuarios, registros)
                              │
                              └──▶ CloudWatch Logs
```

Todos los servicios se usan dentro de su capa gratuita.

## Prueba rápida (sin AWS)

```bash
cd entregable-2
python3 scripts/servidor_local.py
```

Abre http://localhost:8080.

## Desplegar en AWS

Cada entregable se despliega con un comando (`scripts/desplegar_aws.sh`). Los pasos están en la sección *Despliegue automático* del README de cada entregable. El Entregable 2 actualiza la misma infraestructura que el 1.
