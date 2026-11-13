"""Regla de calificación del día (RF-04).

Cada dato aporta hasta 25 puntos y la suma se redondea al entero más cercano.

| Dato                       | Puntos (máximo 25)                                        |
|----------------------------|-----------------------------------------------------------|
| Horas de estudio o trabajo | horas ÷ 8 × 25 (8 h o más = 25)                           |
| Tareas completadas         | tareas ÷ 5 × 25 (5 o más = 25)                            |
| Horas de sueño             | 7 a 9 h = 25; 6 a 6.5 h o 9.5 a 10 h = 15; otro valor = 5 |
| Nivel de energía           | energía × 5                                               |

Ejemplo: 6 h (18.75) + 4 tareas (20) + 7.5 h de sueño (25) + energía 4 (20) = 83.75 -> 84.
"""

import math


def puntos_trabajo(horas: float) -> float:
    return min(horas, 8) / 8 * 25


def puntos_tareas(tareas: int) -> float:
    return min(tareas, 5) / 5 * 25


def puntos_sueno(horas: float) -> float:
    if 7 <= horas <= 9:
        return 25
    if 6 <= horas <= 6.5 or 9.5 <= horas <= 10:
        return 15
    return 5


def puntos_energia(energia: int) -> float:
    return energia * 5


def calcular_calificacion(horas_trabajo: float, tareas: int, horas_sueno: float, energia: int) -> int:
    """Devuelve la calificación del día de 0 a 100."""
    total = (
        puntos_trabajo(horas_trabajo)
        + puntos_tareas(tareas)
        + puntos_sueno(horas_sueno)
        + puntos_energia(energia)
    )
    # Redondeo al entero más cercano (x.5 hacia arriba), igual que Math.round en el navegador.
    return int(math.floor(total + 0.5))
