"""
SIA-T: nivel de riesgo de cada estudiante.

Para cada curso, la red neuronal estima la probabilidad de que al estudiante le vaya mal y la
probabilidad se lleva a tres niveles: bajo, medio y alto. El riesgo general del estudiante junta
sus cursos (ver etl/informe.py).

Si no existe el archivo del modelo, se usa una regla por nota y queda rotulado como tal.
"""

import os
from datetime import datetime

import joblib
import pandas as pd
from sqlalchemy import delete, insert, select

from etl.informe import ALTO, BAJO, MEDIO, armar_informe, nivel_de
from etl.modelo_datos import crear_tablas, periodos, predicciones
from etl.perfil import completar_perfiles, leer_perfiles
from etl.variables import entradas_del_modelo, leer_notas, rendimiento_por_curso

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_MODELO = os.path.join(BASE, "models", "red_neuronal_riesgo.joblib")
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


def informes(engine, nombres: dict = None) -> tuple:
    """Informe de cada estudiante en su último periodo. Devuelve ({id: informe}, origen)."""
    casos, origen = evaluar_cursos(engine)
    if casos.empty:
        return {}, origen
    actuales = casos[casos["orden"] == casos.groupby("est")["orden"].transform("max")]
    resultado = {}
    for est, grupo in actuales.groupby("est"):
        primero = grupo.iloc[0]
        informe = armar_informe((nombres or {}).get(int(est), "el estudiante"), primero["grado"], primero["periodo_nombre"], cursos_del_periodo(grupo), origen["umbrales"])
        resultado[int(est)] = {**informe, "periodo": primero["periodo"], "periodo_nombre": primero["periodo_nombre"], "grado": primero["grado"], "nivel_educativo": primero["nivel_educativo"]}
    return resultado, origen


def calcular_riesgo(engine) -> dict:
    """Recalcula y guarda el nivel de riesgo general de cada estudiante en su último periodo. Devuelve un resumen."""
    crear_tablas(engine)
    completar_perfiles(engine)
    por_estudiante, origen = informes(engine)
    if not por_estudiante:
        return {"origen": None, "estudiantes": 0}
    with engine.begin() as cx:
        ids_periodo = {codigo: pid for pid, codigo in cx.execute(select(periodos.c.id, periodos.c.codigo))}
        cx.execute(delete(predicciones))
        ahora = datetime.now()
        cx.execute(
            insert(predicciones),
            [{"estudiante_id": est, "periodo_id": ids_periodo[i["periodo"]], "nivel_riesgo": i["nivel"], "probabilidad": i["probabilidad"], "origen": origen["origen"], "version": origen["version"], "motivo": i["resumen"], "fecha": ahora} for est, i in por_estudiante.items()],
        )
    niveles = {n: sum(1 for i in por_estudiante.values() if i["nivel"] == n) for n in (BAJO, MEDIO, ALTO)}
    return {"origen": origen["origen"], "version": origen["version"], "estudiantes": len(por_estudiante), "niveles": niveles}
