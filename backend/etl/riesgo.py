"""
SIA-T: nivel de riesgo provisional.

Mientras no exista un modelo entrenado y validado con datos reales (Sprint 3), el nivel de riesgo
se calcula con una regla simple y transparente. No es Machine Learning: es la referencia contra la
que se comparará el modelo, y se muestra siempre como «regla provisional».

Regla, versión 1 (por estudiante y periodo, con sus notas de libro, cuaderno y examen):
- Riesgo alto: promedio general menor de 11, o promedio de exámenes menor de 9.
- Riesgo medio: promedio de exámenes menor de 11, o caída de 2 puntos o más frente al periodo anterior.
- Riesgo bajo: los demás casos.
"""

from collections import defaultdict
from datetime import datetime

from sqlalchemy import delete, insert, select

from etl.modelo_datos import notas, periodos, predicciones

VERSION_REGLA = "regla_provisional_v1"
ORIGEN = "regla_provisional"


def clasificar(promedio, promedio_examen, promedio_anterior):
    """Devuelve (nivel, motivo)."""
    if promedio < 11:
        return "Riesgo alto", f"Promedio general de {promedio:.1f}, menor de 11."
    if promedio_examen is not None and promedio_examen < 9:
        return "Riesgo alto", f"Promedio de exámenes de {promedio_examen:.1f}, menor de 9."
    if promedio_examen is not None and promedio_examen < 11:
        return "Riesgo medio", f"Promedio de exámenes de {promedio_examen:.1f}, menor de 11."
    if promedio_anterior is not None and promedio_anterior - promedio >= 2:
        return "Riesgo medio", f"Bajó {promedio_anterior - promedio:.1f} puntos frente al periodo anterior."
    return "Riesgo bajo", "Sin señales de riesgo con la regla provisional."


def promedios_por_periodo(cx) -> dict:
    """{estudiante_id: {periodo_codigo: {"promedio": x, "examen": y, "conducta": z, "libro": .., "cuaderno": ..}}}"""
    consulta = select(notas.c.estudiante_id, periodos.c.codigo, notas.c.componente, notas.c.nota).select_from(notas.join(periodos))
    acumulado = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for est, periodo, componente, nota in cx.execute(consulta):
        acumulado[est][periodo][componente].append(nota)
    media = lambda v: sum(v) / len(v) if v else None
    resultado = {}
    for est, por_periodo in acumulado.items():
        resultado[est] = {}
        for periodo, comp in por_periodo.items():
            academicas = comp["libro"] + comp["cuaderno"] + comp["examen"]
            resultado[est][periodo] = {
                "promedio": media(academicas),
                "examen": media(comp["examen"]),
                "libro": media(comp["libro"]),
                "cuaderno": media(comp["cuaderno"]),
                "conducta": media(comp["conducta"]),
            }
    return resultado


def calcular_riesgo_provisional(engine) -> int:
    """Recalcula el nivel provisional de todos los estudiantes en todos sus periodos. Devuelve cuántos calculó."""
    with engine.begin() as cx:
        ids_periodo = {codigo: pid for pid, codigo in cx.execute(select(periodos.c.id, periodos.c.codigo))}
        cx.execute(delete(predicciones).where(predicciones.c.origen == ORIGEN))
        filas = []
        for est, por_periodo in promedios_por_periodo(cx).items():
            anterior = None
            for periodo in sorted(por_periodo):
                p = por_periodo[periodo]
                if p["promedio"] is None:
                    continue
                nivel, motivo = clasificar(p["promedio"], p["examen"], anterior)
                filas.append({"estudiante_id": est, "periodo_id": ids_periodo[periodo], "nivel_riesgo": nivel, "probabilidad": None, "origen": ORIGEN, "version": VERSION_REGLA, "motivo": motivo, "fecha": datetime.now()})
                anterior = p["promedio"]
        if filas:
            cx.execute(insert(predicciones), filas)
    return len(filas)
