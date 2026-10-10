"""
SIA-T: carga de notas a la base de datos (paquete 1.2.1 de la EDT, requisito REQ-01).

Uso, desde la carpeta backend:

    python -m etl.cargar_notas "ruta/al/registro.xlsx"          # registro del colegio (datos reales)
    python -m etl.cargar_notas data/notas_practica.csv           # datos de práctica

Con un Excel del colegio, los nombres se reemplazan por códigos antes de tocar la base.
La tabla que relaciona cada nombre con su código se guarda en data/privado/claves.csv,
una carpeta que no se sube al repositorio. Al terminar muestra la reconciliación entre
el archivo de origen y la base, y deja la carga anotada en la tabla «cargas».
"""

import argparse
import csv
import os
import random
import sys
from collections import Counter
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, insert, select, update

from etl.database import engine as engine_por_defecto
from etl.modelo_datos import cargas, crear_tablas, cursos, estudiantes, notas, periodos
from etl.riesgo import calcular_riesgo_provisional

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CLAVES = os.path.join(BASE, "data", "privado", "claves.csv")
REGLAS_DE_RECHAZO = ("nota_no_numerica", "nota_fuera_de_rango")


def asignar_codigos(claves, ruta=RUTA_CLAVES) -> dict:
    """Devuelve {clave: código}. Los códigos nuevos se reparten al azar para que no sigan el orden de la lista."""
    tabla = {}
    if os.path.exists(ruta):
        with open(ruta, newline="", encoding="utf-8") as f:
            tabla = {fila["clave"]: fila["codigo"] for fila in csv.DictReader(f, delimiter=";")}
    nuevas = sorted(set(claves) - set(tabla))
    random.shuffle(nuevas)
    siguiente = len(tabla) + 1
    for clave in nuevas:
        tabla[clave] = f"E-{siguiente:04d}"
        siguiente += 1
    if nuevas:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["clave", "codigo"])
            w.writerows(sorted(tabla.items(), key=lambda x: x[1]))
    return tabla


def leer_csv(ruta: str) -> list:
    """Formato largo: codigo, grado, nivel, curso, periodo, componente, nota."""
    with open(ruta, newline="", encoding="utf-8") as f:
        return [{**fila, "nota": float(fila["nota"])} for fila in csv.DictReader(f)]


def cargar(registros, archivo, tipo_datos, filas_origen, rechazadas=0, engine=engine_por_defecto) -> dict:
    """Inserta las notas que aún no están en la base. Cada registro trae 'codigo' en lugar de nombre."""
    from etl.leer_registro import nombre_periodo

    crear_tablas(engine)
    with engine.begin() as cx:
        carga_id = cx.execute(
            insert(cargas).values(fecha=datetime.now(), archivo=os.path.basename(archivo), tipo_datos=tipo_datos, filas_origen=filas_origen, notas_leidas=len(registros), notas_cargadas=0, notas_repetidas=0, notas_rechazadas=rechazadas)
        ).inserted_primary_key[0]

        def catalogo(tabla, columna):
            return {fila[1]: fila[0] for fila in cx.execute(select(tabla.c.id, columna))}

        ids_periodo, ids_curso, ids_est = catalogo(periodos, periodos.c.codigo), catalogo(cursos, cursos.c.nombre), catalogo(estudiantes, estudiantes.c.codigo)
        existentes = {tuple(f) for f in cx.execute(select(notas.c.estudiante_id, notas.c.curso_id, notas.c.periodo_id, notas.c.componente))}
        cargadas = repetidas = 0
        for r in registros:
            if r["periodo"] not in ids_periodo:
                ids_periodo[r["periodo"]] = cx.execute(insert(periodos).values(codigo=r["periodo"], nombre=nombre_periodo(r["periodo"]))).inserted_primary_key[0]
            if r["curso"] not in ids_curso:
                ids_curso[r["curso"]] = cx.execute(insert(cursos).values(nombre=r["curso"])).inserted_primary_key[0]
            if r["codigo"] not in ids_est:
                ids_est[r["codigo"]] = cx.execute(insert(estudiantes).values(codigo=r["codigo"], grado=r["grado"], nivel_educativo=r["nivel"])).inserted_primary_key[0]
            llave = (ids_est[r["codigo"]], ids_curso[r["curso"]], ids_periodo[r["periodo"]], r["componente"])
            if llave in existentes:
                repetidas += 1
                continue
            existentes.add(llave)
            cx.execute(insert(notas).values(estudiante_id=llave[0], curso_id=llave[1], periodo_id=llave[2], componente=llave[3], nota=r["nota"], carga_id=carga_id))
            cargadas += 1
        cx.execute(update(cargas).where(cargas.c.id == carga_id).values(notas_cargadas=cargadas, notas_repetidas=repetidas))
    calcular_riesgo_provisional(engine)
    return {"carga_id": carga_id, "leidas": len(registros), "cargadas": cargadas, "repetidas": repetidas, "rechazadas": rechazadas}


def reconciliar(registros, engine=engine_por_defecto) -> list:
    """Compara, por grado, curso y periodo, las notas del archivo con las de la base. Devuelve las diferencias."""
    origen = Counter((r["grado"], r["curso"], r["periodo"]) for r in {(r["codigo"], r["curso"], r["periodo"], r["componente"]): r for r in registros}.values())
    with engine.connect() as cx:
        consulta = (
            select(estudiantes.c.grado, cursos.c.nombre, periodos.c.codigo, func.count())
            .select_from(notas.join(estudiantes).join(cursos).join(periodos))
            .group_by(estudiantes.c.grado, cursos.c.nombre, periodos.c.codigo)
        )
        en_base = {(g, c, p): n for g, c, p, n in cx.execute(consulta)}
    return [(llave, n, en_base.get(llave, 0)) for llave, n in sorted(origen.items()) if en_base.get(llave, 0) < n]


def cargar_archivo(ruta: str, engine=engine_por_defecto, ruta_claves=RUTA_CLAVES) -> dict:
    """Carga un Excel del colegio (datos reales, se anonimizan) o un CSV de práctica. Devuelve el resumen."""
    if ruta.lower().endswith((".xlsx", ".xlsm")):
        from etl.leer_registro import leer_registro

        leido = leer_registro(ruta)
        codigos = asignar_codigos([n["clave"] for n in leido["notas"]], ruta_claves)
        registros = [{**{k: v for k, v in n.items() if k != "clave"}, "codigo": codigos[n["clave"]]} for n in leido["notas"]]
        rechazadas = sum(1 for h in leido["hallazgos"] if h["regla"] in REGLAS_DE_RECHAZO)
        resumen = cargar(registros, ruta, "reales", leido["filas_origen"], rechazadas, engine)
        resumen.update(hallazgos=leido["hallazgos"], filas_origen=leido["filas_origen"], bloques=leido["bloques"])
    else:
        registros = leer_csv(ruta)
        resumen = cargar(registros, ruta, "practica", len(registros), 0, engine)
        resumen.update(hallazgos=[], filas_origen=len(registros), bloques=0)
    resumen["diferencias"] = reconciliar(registros, engine)
    resumen["estudiantes"] = len({r["codigo"] for r in registros})
    return resumen


def main():
    parser = argparse.ArgumentParser(description="Carga notas a la base de datos de SIA-T.")
    parser.add_argument("archivo", help="Registro del colegio (.xlsx) o datos de práctica (.csv)")
    parser.add_argument("--claves", default=RUTA_CLAVES, help="Archivo local con la relación nombre-código (no se sube al repositorio)")
    args = parser.parse_args()

    r = cargar_archivo(args.archivo, ruta_claves=args.claves)
    print(f"Archivo: {os.path.basename(args.archivo)}")
    print(f"Filas de estudiantes leídas: {r['filas_origen']} | Estudiantes: {r['estudiantes']}")
    print(f"Notas leídas: {r['leidas']} | cargadas: {r['cargadas']} | ya estaban: {r['repetidas']} | rechazadas: {r['rechazadas']}")
    if r["hallazgos"]:
        print("Observaciones del archivo de origen:")
        for regla, n in sorted(Counter(h["regla"] for h in r["hallazgos"]).items()):
            print(f"  - {regla}: {n}")
    if r["diferencias"]:
        print("RECONCILIACIÓN: HAY DIFERENCIAS entre el archivo y la base:")
        for (grado, curso, periodo), origen, base in r["diferencias"]:
            print(f"  - {grado}, {curso}, {periodo}: {origen} en el archivo, {base} en la base")
        sys.exit(1)
    print("RECONCILIACIÓN: correcta. Todas las notas válidas del archivo están en la base, sin duplicados.")


if __name__ == "__main__":
    main()
