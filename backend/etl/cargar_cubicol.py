"""
SIA-T: carga de las exportaciones de Cubicol (paquete 1.2.1 de la EDT, requisito REQ-01).

Uso, desde la carpeta backend, con la base de datos reales:

    $env:SQLITE_PATH = "data/privado/sia_t_reales.db"
    python -m etl.cargar_cubicol "<carpeta con los .xls de Cubicol>"

Lee todos los .xls de la carpeta (y sus subcarpetas), enlaza cada estudiante con su código ya
existente (ver etl/leer_cubicol.py), carga los promedios que aún no están en la base, anota la carga
en la tabla «cargas», recalcula el nivel de riesgo y muestra la reconciliación entre los archivos y
la base. Los estudiantes que no se enlazan con certeza quedan en data/privado/cubicol_por_revisar.csv
para que el equipo indique su código en data/privado/cubicol_equivalencias.csv.
"""

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select

from etl.cargar_notas import RUTA_CLAVES, cargar, reconciliar
from etl.database import engine as engine_por_defecto
from etl.leer_cubicol import leer_cubicol
from etl.modelo_datos import estudiantes, matriculas

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_EQUIVALENCIAS = os.path.join(BASE, "data", "privado", "cubicol_equivalencias.csv")
RUTA_POR_REVISAR = os.path.join(BASE, "data", "privado", "cubicol_por_revisar.csv")


def _claves(ruta) -> dict:
    with open(ruta, newline="", encoding="utf-8") as f:
        return {fila["clave"]: fila["codigo"] for fila in csv.DictReader(f, delimiter=";")}


def _grados(engine) -> dict:
    """Código del estudiante → grado de su matrícula más reciente."""
    with engine.connect() as cx:
        ultima = select(matriculas.c.estudiante_id, func.max(matriculas.c.anio).label("anio")).group_by(matriculas.c.estudiante_id).subquery()
        consulta = select(estudiantes.c.codigo, matriculas.c.grado).select_from(
            estudiantes.join(ultima, ultima.c.estudiante_id == estudiantes.c.id).join(matriculas, (matriculas.c.estudiante_id == estudiantes.c.id) & (matriculas.c.anio == ultima.c.anio))
        )
        return dict(cx.execute(consulta).all())


def cargar_carpeta(carpeta, engine=engine_por_defecto, ruta_claves=RUTA_CLAVES, ruta_equivalencias=RUTA_EQUIVALENCIAS) -> dict:
    archivos = [p for p in Path(carpeta).rglob("*.xls") if not p.name.startswith("~$")]
    leido = leer_cubicol(archivos, _claves(ruta_claves), _grados(engine), ruta_equivalencias)
    rechazadas = sum(h["cantidad"] for h in leido["hallazgos"])
    etiqueta = f"Cubicol: {Path(carpeta).name} ({leido['archivos']} archivos)"
    resumen = cargar(leido["notas"], {}, etiqueta, "reales", leido["filas_origen"], rechazadas, engine)
    resumen.update(hallazgos=leido["hallazgos"], filas_origen=leido["filas_origen"], archivos=leido["archivos"], sin_identificar=leido["sin_identificar"])
    resumen["diferencias"] = reconciliar(leido["notas"], engine)
    resumen["estudiantes"] = len({n["codigo"] for n in leido["notas"]})
    resumen["enlaces"] = {c: len({n["codigo"] for n in leido["notas"] if n["criterio_enlace"] == c}) for c in sorted({n["criterio_enlace"] for n in leido["notas"]})}
    # Lista privada para revisar a mano los estudiantes que no se pudieron enlazar.
    with open(RUTA_POR_REVISAR, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["nombre_cubicol", "salon", "motivo", "notas_sin_cargar"])
        w.writerows([s["nombre"], s["salon"], s["motivo"], s["notas"]] for s in leido["sin_identificar"])
    return resumen


def main():
    parser = argparse.ArgumentParser(description="Carga a SIA-T las exportaciones de Cubicol (.xls).")
    parser.add_argument("carpeta", help="Carpeta con los archivos .xls exportados de Cubicol")
    args = parser.parse_args()

    r = cargar_carpeta(args.carpeta)
    print(f"Archivos: {r['archivos']} | filas de estudiantes: {r['filas_origen']} | estudiantes enlazados: {r['estudiantes']}")
    for criterio, n in r["enlaces"].items():
        print(f"  - enlazados por {criterio}: {n}")
    print(f"Notas válidas: {r['leidas']} | cargadas: {r['cargadas']} | ya estaban: {r['repetidas']} | no cargadas: {r['rechazadas']}")
    for h in r["hallazgos"]:
        print(f"  - {h['regla']}: {h['cantidad']}. {h['detalle']}")
    if r["sin_identificar"]:
        print(f"Por revisar: {len(r['sin_identificar'])} estudiantes (lista en data/privado/cubicol_por_revisar.csv)")
        for s in r["sin_identificar"]:
            print(f"  - {s['salon']}: {s['motivo']} ({s['notas']} notas)")
    print(f"Nivel de riesgo ({r['riesgo'].get('origen')}): {r['riesgo'].get('niveles')}")
    if r["diferencias"]:
        print("RECONCILIACIÓN: HAY DIFERENCIAS entre los archivos y la base:")
        for (curso, periodo), origen, base in r["diferencias"]:
            print(f"  - {curso}, {periodo}: {origen} en los archivos, {base} en la base")
        sys.exit(1)
    print("RECONCILIACIÓN: correcta. Todas las notas enlazadas de los archivos están en la base, sin duplicados.")


if __name__ == "__main__":
    main()
