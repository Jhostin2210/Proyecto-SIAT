"""
SIA-T: nivel de riesgo de cada estudiante.

Para cada curso, la red neuronal estima la probabilidad de que al estudiante le vaya mal y la
probabilidad se lleva a tres niveles: bajo, medio y alto. El riesgo general del estudiante junta
sus cursos (ver etl/informe.py).

Si no existe el archivo del modelo, se usa una regla por nota y queda rotulado como tal.
"""

import json
import os

import joblib
import pandas as pd
from sqlalchemy import delete, insert, select

from etl.informe import ALTO, BAJO, MEDIO, armar_informe, nivel_de
from etl.modelo_datos import cargas, clasificaciones, crear_tablas, periodos, predicciones
from etl.perfil import completar_perfiles, leer_perfiles
from etl.variables import entradas_del_modelo, leer_notas, rendimiento_por_curso
from etl.hora import ahora

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_MODELO = os.path.join(BASE, "models", "red_neuronal_riesgo.joblib")
# Cortes de nivel ajustados con los datos del colegio (ml/ajustar_cortes.py, SC-14). Si no existe, se usan los del modelo.
RUTA_UMBRALES = os.path.join(BASE, "data", "umbrales_colegio.json")
VERSION_REGLA = "regla_por_nota_v1"
# Sin modelo: probabilidad fija por rango de nota, solo para ordenar.
UMBRALES_REGLA = {"medio": 0.3, "alto": 0.7}
_modelo = {}


def cargar_modelo():
    """Devuelve el paquete del modelo (pipeline, variables, umbrales, versión) o None si no hay archivo."""
    if not os.path.exists(RUTA_MODELO):
        return None
    fecha = os.path.getmtime(RUTA_MODELO)
    if _modelo.get("fecha") != fecha:
        _modelo.update(fecha=fecha, paquete=joblib.load(RUTA_MODELO))
    return _modelo["paquete"]


def _tipo_datos(engine):
    """«reales» o «practica», según la última carga de la base."""
    with engine.connect() as cx:
        return cx.execute(select(cargas.c.tipo_datos).order_by(cargas.c.id.desc()).limit(1)).scalar()


def evaluar_cursos(engine) -> tuple:
    """Devuelve (casos, origen): una fila por estudiante, curso y periodo con «probabilidad» y «nivel»."""
    casos = rendimiento_por_curso(leer_notas(engine))
    if casos.empty:
        return casos, {"origen": None, "version": None, "umbrales": UMBRALES_REGLA}
    modelo = cargar_modelo()
    if modelo:
        X = entradas_del_modelo(casos, leer_perfiles(engine), modelo["variables"], modelo["aprobatoria"])
        casos["probabilidad"] = modelo["pipeline"].predict_proba(X)[:, 1]
        origen = {"origen": "modelo", "version": modelo["version"], "umbrales": modelo["umbrales"]}
        # Los cortes del colegio se ajustaron con su población real: no se aplican a los datos de práctica.
        if os.path.exists(RUTA_UMBRALES) and _tipo_datos(engine) == "reales":
            with open(RUTA_UMBRALES, encoding="utf-8") as f:
                cortes = json.load(f)
            origen = {**origen, "version": f"{modelo['version']}+{cortes['version']}", "umbrales": cortes["umbrales"], "cortes": "colegio"}
    else:
        casos["probabilidad"] = casos["nota"].map(lambda n: 0.85 if n < 10 else 0.4 if n < 15 else 0.05)
        origen = {"origen": "regla_provisional", "version": VERSION_REGLA, "umbrales": UMBRALES_REGLA}
    casos["nivel"] = casos["probabilidad"].map(lambda p: nivel_de(p, origen["umbrales"]))
    return casos, origen


def _nulo(valor):
    return None if pd.isna(valor) else round(float(valor), 1)


def cursos_del_periodo(grupo: pd.DataFrame) -> list:
    return [
        {"curso": f.curso, "area": f.area, "nota": round(float(f.nota), 1), "examen": _nulo(f.examen), "trabajos": _nulo(f.trabajos), "nota_previa": _nulo(f.nota_previa), "cambio": _nulo(f.cambio), "probabilidad": round(float(f.probabilidad), 3), "nivel": f.nivel, "por_validar": bool(f.por_validar)}
        for f in grupo.itertuples()
    ]


def informes(engine, nombres: dict = None, periodo: str = None, casos_y_origen: tuple = None) -> tuple:
    """Informe de cada estudiante en su último periodo, o en el periodo indicado. Devuelve ({id: informe}, origen)."""
    casos, origen = casos_y_origen or evaluar_cursos(engine)
    if casos.empty:
        return {}, origen
    if periodo:
        actuales = casos[casos["periodo"] == periodo]
    else:
        actuales = casos[casos["orden"] == casos.groupby("est")["orden"].transform("max")]
    resultado = {}
    for est, grupo in actuales.groupby("est"):
        primero = grupo.iloc[0]
        informe = armar_informe((nombres or {}).get(int(est), "el estudiante"), primero["grado"], primero["periodo_nombre"], cursos_del_periodo(grupo), origen["umbrales"])
        resultado[int(est)] = {**informe, "periodo": primero["periodo"], "periodo_nombre": primero["periodo_nombre"], "grado": primero["grado"], "nivel_educativo": primero["nivel_educativo"]}
    return resultado, origen


def calcular_riesgo(engine, motivo: str = "carga de datos") -> dict:
    """Recalcula y guarda el nivel de riesgo general de cada estudiante en su último periodo y lo anota en la
    bitácora de clasificaciones con su motivo. Devuelve un resumen."""
    crear_tablas(engine)
    completar_perfiles(engine)
    por_estudiante, origen = informes(engine)
    if not por_estudiante:
        return {"origen": None, "estudiantes": 0}
    with engine.begin() as cx:
        ids_periodo = {codigo: pid for pid, codigo in cx.execute(select(periodos.c.id, periodos.c.codigo))}
        cx.execute(delete(predicciones))
        momento = ahora()
        cx.execute(
            insert(predicciones),
            [{"estudiante_id": est, "periodo_id": ids_periodo[i["periodo"]], "nivel_riesgo": i["nivel"], "probabilidad": i["probabilidad"], "origen": origen["origen"], "version": origen["version"], "motivo": i["resumen"], "fecha": momento} for est, i in por_estudiante.items()],
        )
    niveles = {n: sum(1 for i in por_estudiante.values() if i["nivel"] == n) for n in (BAJO, MEDIO, ALTO)}
    with engine.begin() as cx:
        cx.execute(insert(clasificaciones).values(fecha=momento, motivo=motivo[:30], version=(origen["version"] or "")[:60], estudiantes=len(por_estudiante), bajo=niveles[BAJO], medio=niveles[MEDIO], alto=niveles[ALTO]))
    return {"origen": origen["origen"], "version": origen["version"], "estudiantes": len(por_estudiante), "niveles": niveles, "fecha": momento, "motivo": motivo}


def ultima_clasificacion(engine):
    """Fecha y motivo de la última clasificación, o None."""
    crear_tablas(engine)
    with engine.connect() as cx:
        fila = cx.execute(select(clasificaciones).order_by(clasificaciones.c.id.desc()).limit(1)).mappings().first()
    return dict(fila) if fila else None


def resumen_por_periodo(engine) -> list:
    """Para el tablero: niveles de riesgo y promedio de cada periodo, en total y por aula, con el cambio respecto
    del periodo anterior. Cada estudiante cuenta en los periodos en que tiene notas."""
    casos, origen = evaluar_cursos(engine)
    if casos.empty:
        return []
    salida = []
    for (codigo, nombre, orden), _ in casos.groupby(["periodo", "periodo_nombre", "orden"]):
        por_est, _o = informes(engine, periodo=codigo, casos_y_origen=(casos, origen))
        filas = [{"grado": i["grado"], "nivel": i["nivel"], "promedio": sum(c["nota"] for c in i["cursos"]) / len(i["cursos"])} for i in por_est.values()]

        def resumen(lista):
            return {
                "estudiantes": len(lista),
                "alto": sum(1 for x in lista if x["nivel"] == ALTO),
                "medio": sum(1 for x in lista if x["nivel"] == MEDIO),
                "bajo": sum(1 for x in lista if x["nivel"] == BAJO),
                "promedio": round(sum(x["promedio"] for x in lista) / len(lista), 1) if lista else None,
            }

        aulas = {}
        for x in filas:
            aulas.setdefault(x["grado"], []).append(x)
        salida.append({"periodo": codigo, "periodo_nombre": nombre, "orden": float(orden), **resumen(filas), "aulas": [{"grado": g, **resumen(l)} for g, l in sorted(aulas.items())]})
    salida.sort(key=lambda p: p["orden"])
    for anterior, actual in zip(salida, salida[1:]):
        actual["anterior"] = anterior["periodo"]
    return salida
