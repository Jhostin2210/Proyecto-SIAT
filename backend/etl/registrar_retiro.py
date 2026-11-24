"""
SIA-T: registro de un estudiante que dejó el colegio (traslado o retiro).

Uso, desde la carpeta backend, con la base de datos reales:

    $env:SQLITE_PATH = "data/privado/sia_t_reales.db"
    python -m etl.registrar_retiro E-0036 traslado --confirmado "Product Owner, 24/11/2026"
    python -m etl.registrar_retiro E-0036 traslado --ultimo-periodo 2026-06 --confirmado "..."

Solo se registra con la confirmación del Product Owner. Las notas del estudiante se conservan y siguen
contando en los meses pasados; desde el registro no aparece en la clasificación actual ni recibe alertas.
Después del registro se recalcula el nivel de riesgo.
"""

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import insert, select

from etl.database import engine
from etl.hora import ahora
from etl.modelo_datos import crear_tablas, estudiantes, retiros
from etl.riesgo import calcular_riesgo


def registrar(engine, codigo: str, motivo: str, confirmado_por: str, ultimo_periodo: str = None) -> bool:
    """Registra el retiro. Devuelve False si ya estaba registrado."""
    crear_tablas(engine)
    with engine.begin() as cx:
        est = cx.execute(select(estudiantes.c.id).where(estudiantes.c.codigo == codigo)).scalar()
        if est is None:
            sys.exit(f"No existe el estudiante {codigo}.")
        if cx.execute(select(retiros.c.id).where(retiros.c.estudiante_id == est)).first():
            return False
        cx.execute(insert(retiros).values(estudiante_id=est, motivo=motivo, ultimo_periodo=ultimo_periodo, confirmado_por=confirmado_por, fecha=ahora()))
    return True


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Registra a un estudiante que dejó el colegio.")
    parser.add_argument("codigo", help="Código del estudiante, por ejemplo E-0036")
    parser.add_argument("motivo", choices=["traslado", "retiro"])
    parser.add_argument("--confirmado", required=True, help="Quién lo confirmó y cuándo")
    parser.add_argument("--ultimo-periodo", help="Último mes en el colegio (AAAA-MM), si se conoce")
    args = parser.parse_args()
    if registrar(engine, args.codigo, args.motivo, args.confirmado, args.ultimo_periodo):
        print(f"{args.codigo}: {args.motivo} registrado.")
    else:
        print(f"{args.codigo} ya estaba registrado.")
    r = calcular_riesgo(engine, "registro de retiro")
    print(f"Nivel de riesgo ({r.get('origen')}): {r.get('niveles')} | estudiantes clasificados: {r.get('estudiantes')}")


if __name__ == "__main__":
    main()
