"""
SIA-T: nivel de riesgo de cada estudiante.

Si existe un modelo entrenado (models/modelo_riesgo.joblib), el nivel sale de él: para cada curso se
estima la probabilidad de desaprobar el próximo examen, y el riesgo del estudiante es el promedio de
sus cursos. Si un solo curso está en riesgo alto, el estudiante queda como mínimo en riesgo medio. Si no hay modelo, se usa una regla simple y visible, que es además la referencia contra la
que se compara el modelo.

Tres niveles: bajo, medio y alto. Los cortes del modelo se fijan al entrenarlo.
"""

import os
from datetime import datetime

import joblib
from sqlalchemy import delete, insert, select

from etl.modelo_datos import periodos, predicciones
from etl.variables import NOTA_APROBATORIA, VARIABLES, construir_casos, leer_notas

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_MODELO = os.path.join(BASE, "models", "modelo_riesgo.joblib")
VERSION_REGLA = "regla_provisional_v2"
ORDEN_NIVEL = {"Riesgo bajo": 0, "Riesgo medio": 1, "Riesgo alto": 2}


def cargar_modelo():
    return joblib.load(RUTA_MODELO) if os.path.exists(RUTA_MODELO) else None


def regla(caso) -> tuple:
    """Regla de referencia sobre un curso: devuelve (nivel, motivo)."""
    examen, trabajos, cambio = caso.get("examen"), caso.get("trabajos"), caso.get("cambio_examen")
    referencia = examen if examen == examen else trabajos  # un valor vacío (NaN) no es igual a sí mismo
    if referencia != referencia:
        return "Riesgo bajo", "sin notas suficientes"
    if referencia < NOTA_APROBATORIA:
        return "Riesgo alto", f"nota de {referencia:.0f}"
    baja = cambio == cambio and cambio <= -3
    if referencia < 13 or baja:
        return "Riesgo medio", f"nota de {referencia:.0f}" + (f", bajó {abs(cambio):.0f} puntos" if baja else "")
    return "Riesgo bajo", "sin señales"


def calcular_riesgo(engine) -> dict:
    """Recalcula el nivel de riesgo de cada estudiante en su último periodo. Devuelve un resumen."""
    casos = construir_casos(leer_notas(engine))
    if casos.empty:
        return {"origen": None, "estudiantes": 0}
    # Último periodo de cada estudiante y, dentro de él, todos sus cursos.
    actuales = casos[casos["orden"] == casos.groupby("est")["orden"].transform("max")].copy()

    modelo = cargar_modelo()
    if modelo:
        actuales["prob"] = modelo["pipeline"].predict_proba(actuales[VARIABLES])[:, 1]
        t_medio, t_alto = modelo["umbrales"]["medio"], modelo["umbrales"]["alto"]
        actuales["nivel"] = actuales["prob"].map(lambda p: "Riesgo alto" if p >= t_alto else "Riesgo medio" if p >= t_medio else "Riesgo bajo")
        actuales["detalle"] = actuales["prob"].map(lambda p: f"{p:.0%}")
        origen, version = "modelo", modelo["version"]
    else:
        resultado = [regla(f) for f in actuales.to_dict("records")]
        actuales["nivel"], actuales["detalle"] = [r[0] for r in resultado], [r[1] for r in resultado]
        actuales["prob"] = 0.0
        origen, version = "regla_provisional", VERSION_REGLA

    actuales["rango"] = actuales["nivel"].map(ORDEN_NIVEL)
    filas = []
    for est, grupo in actuales.groupby("est"):
        grupo = grupo.sort_values(["rango", "prob"], ascending=False)
        peor, en_riesgo = grupo.iloc[0], grupo[grupo["rango"] > 0]
        nivel, prob = peor["nivel"], None
        if modelo:
            # Riesgo general del estudiante: promedio de sus cursos. Un solo curso en alto lo deja, como mínimo, en medio.
            prob = float(grupo["prob"].mean())
            nivel = "Riesgo alto" if prob >= t_alto else "Riesgo medio" if prob >= t_medio or peor["rango"] == 2 else "Riesgo bajo"
        if en_riesgo.empty:
            motivo = "Ningún curso con señales de riesgo."
        elif modelo:
            motivo = "Probabilidad de desaprobar el próximo examen: " + ", ".join(f"{f.curso} ({f.detalle})" for f in en_riesgo.head(3).itertuples()) + "."
        else:
            motivo = "Cursos con señales: " + ", ".join(f"{f.curso} ({f.detalle})" for f in en_riesgo.head(3).itertuples()) + "."
        filas.append({"est": int(est), "periodo": peor["periodo"], "nivel": nivel, "prob": prob, "motivo": motivo})

    with engine.begin() as cx:
        ids_periodo = {codigo: pid for pid, codigo in cx.execute(select(periodos.c.id, periodos.c.codigo))}
        cx.execute(delete(predicciones))
        ahora = datetime.now()
        cx.execute(
            insert(predicciones),
            [{"estudiante_id": f["est"], "periodo_id": ids_periodo[f["periodo"]], "nivel_riesgo": f["nivel"], "probabilidad": f["prob"], "origen": origen, "version": version, "motivo": f["motivo"], "fecha": ahora} for f in filas],
        )
    return {"origen": origen, "version": version, "estudiantes": len(filas), "niveles": {n: sum(1 for f in filas if f["nivel"] == n) for n in ORDEN_NIVEL}}
