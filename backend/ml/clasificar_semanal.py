"""
SIA-T: clasificación semanal automática de los estudiantes (requisito REQ-04, paquete 1.3.2, actividad A-3.2.1.4).

Uso, desde la carpeta backend:

    python -m ml.clasificar_semanal            # clasifica si pasaron 7 días o más desde la última clasificación
    python -m ml.clasificar_semanal --forzar   # clasifica igual

La red neuronal no se vuelve a entrenar: se aplica a las notas que hay en la base y se guarda el nivel de riesgo
de cada estudiante. Cada clasificación queda en la bitácora (tabla «clasificaciones») con su motivo. La ejecutan
la tarea programada de GitHub Actions (cada lunes) y la propia API, que revisa cada hora si ya toca.
"""

import argparse
import os
import sys
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.database import engine as engine_por_defecto
from etl.hora import ahora
from etl.riesgo import calcular_riesgo, ultima_clasificacion

DIAS = 7
MOTIVO = "semanal automática"


def clasificar_si_toca(engine=engine_por_defecto, forzar: bool = False):
    """Clasifica si la última clasificación tiene 7 días o más (o no hay ninguna). Devuelve el resumen o None."""
    ultima = ultima_clasificacion(engine)
    if not forzar and ultima and ahora().replace(tzinfo=None) - ultima["fecha"].replace(tzinfo=None) < timedelta(days=DIAS):
        return None
    return calcular_riesgo(engine, MOTIVO)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Clasificación semanal automática del riesgo de los estudiantes.")
    parser.add_argument("--forzar", action="store_true", help="Clasificar aunque no hayan pasado 7 días")
    args = parser.parse_args()
    r = clasificar_si_toca(forzar=args.forzar)
    if r is None:
        u = ultima_clasificacion(engine_por_defecto)
        print(f"Todavía no toca: la última clasificación fue el {u['fecha']:%d/%m/%Y %H:%M} ({u['motivo']}).")
        return
    print(f"Clasificación {MOTIVO} del {r['fecha']:%d/%m/%Y %H:%M}: {r['estudiantes']} estudiantes · {r['niveles']} · modelo {r['version']}")


if __name__ == "__main__":
    main()
