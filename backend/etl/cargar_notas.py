"""
SIA-T: carga de notas a la base de datos (paquete 1.2.1 de la EDT, requisito REQ-01).

Uso, desde la carpeta backend:

    python -m etl.cargar_notas data/privado/consolidado.xlsx    # base consolidada del colegio (datos reales)
    python -m etl.cargar_notas data/notas_practica.csv           # datos de práctica

Con la base consolidada, cada estudiante recibe un identificador único. La tabla que relaciona
cada persona con su identificador se guarda en data/privado/claves.csv, que no se sube al
repositorio. Al terminar muestra la reconciliación entre el archivo y la base, deja la carga
anotada en la tabla «cargas» y recalcula el nivel de riesgo.
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
from etl.modelo_datos import cargas, crear_tablas, cursos, estudiantes, matriculas, notas, periodos
from etl.riesgo import calcular_riesgo

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CLAVES = os.path.join(BASE, "data", "privado", "claves.csv")


def asignar_codigos(claves, ruta=RUTA_CLAVES) -> dict:
    """Devuelve {clave: código}. Los códigos nuevos se reparten al azar para que no sigan el orden de la lista."""
    tabla = {}
    if os.path.exists(ruta):
        with open(ruta, newline="", encoding="utf-8") as f:
            tabla = {fila["clave"]: fila["codigo"] for fila in csv.DictReader(f, delimiter=";")}
    nuevas = sorted(set(claves) - set(tabla))
    random.shuffle(nuevas)
    for i, clave in enumerate(nuevas, start=len(tabla) + 1):
        tabla[clave] = f"E-{i:04d}"
    if nuevas:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["clave", "codigo"])
            w.writerows(sorted(tabla.items(), key=lambda x: x[1]))
    return tabla


def leer_csv(ruta: str):
    """Datos de práctica: una fila por nota, con los datos del estudiante repetidos."""
    registros, fichas = [], {}
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            ficha = fichas.setdefault(fila["codigo"], {"nombres": fila["nombres"], "apellido": fila["apellido"] or None, "identidad": "completa", "matriculas": {}})
            ficha["matriculas"][int(fila["anio"])] = (fila["nivel"], fila["grado"])
            registros.append({**fila, "anio": int(fila["anio"]), "nota": float(fila["nota"]), "periodo_orden": float(fila["periodo_orden"]), "validada": 1, "confianza": "alta", "fuente": "PRACTICA"})
    return registros, fichas


def cargar(registros, fichas, archivo, tipo_datos, filas_origen, rechazadas=0, engine=engine_por_defecto) -> dict:
    """Inserta estudiantes, matrículas y las notas que aún no están en la base. Cada registro trae 'codigo'."""
    crear_tablas(engine)
    with engine.begin() as cx:
        carga_id = cx.execute(
            insert(cargas).values(fecha=datetime.now(), archivo=os.path.basename(archivo), tipo_datos=tipo_datos, filas_origen=filas_origen, notas_leidas=len(registros), notas_cargadas=0, notas_repetidas=0, notas_rechazadas=rechazadas)
        ).inserted_primary_key[0]

        def catalogo(tabla, columna):
            return {fila[1]: fila[0] for fila in cx.execute(select(tabla.c.id, columna))}

        ids_periodo, ids_curso, ids_est = catalogo(periodos, periodos.c.codigo), catalogo(cursos, cursos.c.nombre), catalogo(estudiantes, estudiantes.c.codigo)
        con_matricula = {(e, a) for e, a in cx.execute(select(matriculas.c.estudiante_id, matriculas.c.anio))}
        for codigo, ficha in fichas.items():
            if codigo not in ids_est:
                ids_est[codigo] = cx.execute(insert(estudiantes).values(codigo=codigo, nombres=ficha["nombres"], apellido=ficha["apellido"], identidad=ficha["identidad"])).inserted_primary_key[0]
            for anio, (nivel, grado) in ficha["matriculas"].items():
                if (ids_est[codigo], anio) not in con_matricula:
                    cx.execute(insert(matriculas).values(estudiante_id=ids_est[codigo], anio=anio, nivel_educativo=nivel, grado=grado))
                    con_matricula.add((ids_est[codigo], anio))

        existentes = {tuple(f) for f in cx.execute(select(notas.c.estudiante_id, notas.c.curso_id, notas.c.periodo_id, notas.c.tipo_evaluacion, notas.c.componente))}
        nuevas, repetidas = [], 0
        for r in registros:
            if r["periodo"] not in ids_periodo:
                ids_periodo[r["periodo"]] = cx.execute(insert(periodos).values(codigo=r["periodo"], nombre=r["periodo_nombre"], anio=r["anio"], orden=r["periodo_orden"])).inserted_primary_key[0]
            if r["curso"] not in ids_curso:
                ids_curso[r["curso"]] = cx.execute(insert(cursos).values(nombre=r["curso"], area=r["area"])).inserted_primary_key[0]
            llave = (ids_est[r["codigo"]], ids_curso[r["curso"]], ids_periodo[r["periodo"]], r["tipo"], r["componente"])
            if llave in existentes:
                repetidas += 1
                continue
            existentes.add(llave)
            nuevas.append({"estudiante_id": llave[0], "curso_id": llave[1], "periodo_id": llave[2], "tipo_evaluacion": llave[3], "componente": llave[4], "nota": r["nota"], "fuente": r["fuente"], "confianza": r["confianza"], "validada": r["validada"], "carga_id": carga_id})
        if nuevas:
            cx.execute(insert(notas), nuevas)
        cx.execute(update(cargas).where(cargas.c.id == carga_id).values(notas_cargadas=len(nuevas), notas_repetidas=repetidas))
    riesgo = calcular_riesgo(engine)
    return {"carga_id": carga_id, "leidas": len(registros), "cargadas": len(nuevas), "repetidas": repetidas, "rechazadas": rechazadas, "riesgo": riesgo}


def reconciliar(registros, engine=engine_por_defecto) -> list:
    """Compara, por curso y periodo, las notas del archivo con las de la base. Devuelve las diferencias."""
    origen = Counter((r["curso"], r["periodo"]) for r in registros)
    with engine.connect() as cx:
        consulta = select(cursos.c.nombre, periodos.c.codigo, func.count()).select_from(notas.join(cursos).join(periodos)).group_by(cursos.c.nombre, periodos.c.codigo)
        en_base = {(c, p): n for c, p, n in cx.execute(consulta)}
    return [(llave, n, en_base.get(llave, 0)) for llave, n in sorted(origen.items()) if en_base.get(llave, 0) < n]


def cargar_archivo(ruta: str, engine=engine_por_defecto, ruta_claves=RUTA_CLAVES) -> dict:
    """Carga la base consolidada del colegio (.xlsx) o los datos de práctica (.csv). Devuelve el resumen."""
    if ruta.lower().endswith((".xlsx", ".xlsm")):
        from etl.leer_consolidado import leer_consolidado

        leido = leer_consolidado(ruta)
        codigos = asignar_codigos(leido["estudiantes"].keys(), ruta_claves)
        registros = [{**n, "codigo": codigos[n["clave"]]} for n in leido["notas"]]
        fichas = {codigos[clave]: ficha for clave, ficha in leido["estudiantes"].items()}
        rechazadas = sum(h["cantidad"] for h in leido["hallazgos"])
        resumen = cargar(registros, fichas, ruta, "reales", leido["filas_origen"], rechazadas, engine)
        resumen.update(hallazgos=leido["hallazgos"], filas_origen=leido["filas_origen"])
    else:
        registros, fichas = leer_csv(ruta)
        resumen = cargar(registros, fichas, ruta, "practica", len(registros), 0, engine)
        resumen.update(hallazgos=[], filas_origen=len(registros))
    resumen["diferencias"] = reconciliar(registros, engine)
    resumen["estudiantes"] = len(fichas)
    return resumen


def main():
    parser = argparse.ArgumentParser(description="Carga notas a la base de datos de SIA-T.")
    parser.add_argument("archivo", help="Base consolidada del colegio (.xlsx) o datos de práctica (.csv)")
    parser.add_argument("--claves", default=RUTA_CLAVES, help="Archivo local con la relación persona-identificador (no se sube al repositorio)")
    args = parser.parse_args()

    r = cargar_archivo(args.archivo, ruta_claves=args.claves)
    print(f"Archivo: {os.path.basename(args.archivo)}")
    print(f"Filas leídas: {r['filas_origen']} | Estudiantes: {r['estudiantes']}")
    print(f"Notas válidas: {r['leidas']} | cargadas: {r['cargadas']} | ya estaban: {r['repetidas']} | no cargadas: {r['rechazadas']}")
    for h in r["hallazgos"]:
        print(f"  - {h['regla']}: {h['cantidad']}. {h['detalle']}")
    print(f"Nivel de riesgo ({r['riesgo'].get('origen')}): {r['riesgo'].get('niveles')}")
    if r["diferencias"]:
        print("RECONCILIACIÓN: HAY DIFERENCIAS entre el archivo y la base:")
        for (curso, periodo), origen, base in r["diferencias"]:
            print(f"  - {curso}, {periodo}: {origen} en el archivo, {base} en la base")
        sys.exit(1)
    print("RECONCILIACIÓN: correcta. Todas las notas válidas del archivo están en la base, sin duplicados.")


if __name__ == "__main__":
    main()
