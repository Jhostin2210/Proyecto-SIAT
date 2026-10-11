"""
SIA-T: rendimiento por curso y entradas del modelo.

Convierte las notas de la base en una fila por estudiante, curso y periodo con su nota del curso
(promedio del examen y de los trabajos), la del periodo anterior y, cuando existe, la del periodo
siguiente, que sirve para comprobar después si el modelo acertó.
"""

import numpy as np
import pandas as pd
from sqlalchemy import select

from etl.modelo_datos import cursos, estudiantes, matriculas, notas, periodos

NOTA_APROBATORIA = 11
TRABAJOS = ["cuaderno", "libro", "oral", "practica", "exposicion", "trabajo"]


def leer_notas(engine) -> pd.DataFrame:
    """Notas de la base con estudiante, curso, área, periodo y nivel educativo del año de la nota."""
    consulta = (
        select(
            notas.c.estudiante_id.label("est"), estudiantes.c.codigo, cursos.c.nombre.label("curso"), cursos.c.area,
            periodos.c.codigo.label("periodo"), periodos.c.nombre.label("periodo_nombre"), periodos.c.orden, periodos.c.anio,
            notas.c.componente, notas.c.nota, notas.c.validada, matriculas.c.nivel_educativo.label("nivel"), matriculas.c.grado,
        )
        .select_from(
            notas.join(estudiantes).join(cursos).join(periodos).outerjoin(matriculas, (matriculas.c.estudiante_id == notas.c.estudiante_id) & (matriculas.c.anio == periodos.c.anio))
        )
    )
    with engine.connect() as cx:
        return pd.DataFrame(cx.execute(consulta).mappings().all())


def rendimiento_por_curso(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por estudiante, curso y periodo. «nota» es el promedio del examen y de los trabajos."""
    if df.empty:
        return pd.DataFrame()
    df = df[~df["componente"].isin(["promedio", "conducta"])].copy()  # el promedio del docente se deriva de las otras notas
    llave = ["est", "curso", "periodo"]
    base = df.groupby(llave).agg(
        codigo=("codigo", "first"), periodo_nombre=("periodo_nombre", "first"), orden=("orden", "first"), anio=("anio", "first"), area=("area", "first"),
        nivel_educativo=("nivel", "first"), grado=("grado", "first"), n_notas=("nota", "size"), por_validar=("validada", lambda v: bool((v == 0).any())),
    )
    por_componente = df.pivot_table(index=llave, columns="componente", values="nota", aggfunc="mean")
    for c in ["examen", *TRABAJOS]:
        if c not in por_componente:
            por_componente[c] = np.nan
    base["examen"] = por_componente["examen"]
    base["trabajos"] = por_componente[TRABAJOS].mean(axis=1)
    base["nota"] = base[["examen", "trabajos"]].mean(axis=1)
    base = base[base["nota"].notna()].reset_index().sort_values(["est", "curso", "orden"]).reset_index(drop=True)

    # Periodo anterior y siguiente del mismo curso, dentro del mismo año escolar.
    g = base.groupby(["est", "curso", "anio"])
    base["nota_previa"] = g["nota"].shift(1)
    base["cambio"] = base["nota"] - base["nota_previa"]
    base["nota_siguiente"] = g["nota"].shift(-1)
    return base


def entradas_del_modelo(casos: pd.DataFrame, perfiles: pd.DataFrame, variables: list, aprobatoria_modelo: int = 10) -> pd.DataFrame:
    """Une cada caso con el perfil del estudiante y lleva las notas a la escala del modelo.
    El modelo se entrenó con una nota aprobatoria de 10; en el colegio es 11."""
    ajuste = NOTA_APROBATORIA - aprobatoria_modelo
    X = casos[["est"]].merge(perfiles, on="est", how="left")
    actual = (casos["nota"] - ajuste).clip(0, 20).to_numpy()
    previa = (casos["nota_previa"] - ajuste).clip(0, 20).to_numpy()
    X["G2"] = actual
    X["G1"] = np.where(np.isnan(previa), actual, previa)  # sin periodo anterior: la misma nota
    return X[variables]
