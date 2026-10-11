"""
SIA-T: variables del modelo.

Convierte las notas de la base en «casos»: una fila por estudiante, curso y periodo, con lo que se
sabía en ese periodo y, cuando existe, el resultado del examen del periodo siguiente (lo que se predice).

El entrenamiento y el cálculo semanal usan esta misma función, para que el modelo reciba siempre
las variables calculadas de la misma manera.
"""

import numpy as np
import pandas as pd
from sqlalchemy import select

from etl.modelo_datos import cursos, estudiantes, matriculas, notas, periodos

NOTA_APROBATORIA = 11
TRABAJOS = ["cuaderno", "libro", "oral", "practica", "exposicion", "trabajo"]
AREAS = ["Matemática", "Comunicación", "Ciencias Sociales", "Ciencia y Tecnología"]
VARIABLES = (
    ["examen", "trabajos", "cuaderno", "libro", "oral", "conducta", "minimo", "n_notas", "examen_previo", "cambio_examen", "examen_otros_cursos", "trabajos_otros_cursos", "secundaria"]
    + [f"area_{a}" for a in AREAS]
)
DESCRIPCION = {
    "examen": "Nota de examen del periodo en el curso",
    "trabajos": "Promedio de cuaderno, libro, oral, prácticas y exposiciones",
    "cuaderno": "Nota de cuaderno",
    "libro": "Nota de libro",
    "oral": "Nota de intervención o examen oral",
    "conducta": "Nota de conducta",
    "minimo": "Nota más baja del periodo en el curso",
    "n_notas": "Cantidad de notas registradas",
    "examen_previo": "Examen del periodo anterior en el curso",
    "cambio_examen": "Diferencia entre el examen actual y el anterior",
    "examen_otros_cursos": "Promedio de examen del estudiante en sus otros cursos",
    "trabajos_otros_cursos": "Promedio de trabajos del estudiante en sus otros cursos",
    "secundaria": "El estudiante es de secundaria",
}


def leer_notas(engine) -> pd.DataFrame:
    """Notas de la base con estudiante, curso, área, periodo y nivel educativo del año de la nota."""
    consulta = (
        select(
            notas.c.estudiante_id.label("est"), estudiantes.c.codigo, cursos.c.nombre.label("curso"), cursos.c.area,
            periodos.c.codigo.label("periodo"), periodos.c.orden, periodos.c.anio, notas.c.tipo_evaluacion.label("tipo"),
            notas.c.componente, notas.c.nota, notas.c.validada, matriculas.c.nivel_educativo.label("nivel"), matriculas.c.grado,
        )
        .select_from(
            notas.join(estudiantes).join(cursos).join(periodos).outerjoin(matriculas, (matriculas.c.estudiante_id == notas.c.estudiante_id) & (matriculas.c.anio == periodos.c.anio))
        )
    )
    with engine.connect() as cx:
        return pd.DataFrame(cx.execute(consulta).mappings().all())


def construir_casos(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por estudiante, curso y periodo. «objetivo» es 1 si desaprueba el examen del periodo siguiente."""
    if df.empty:
        return pd.DataFrame()
    df = df[df["componente"] != "promedio"].copy()  # los promedios del docente se derivan de las otras notas
    llave = ["est", "curso", "periodo"]
    base = df.groupby(llave).agg(orden=("orden", "first"), anio=("anio", "first"), area=("area", "first"), nivel=("nivel", "first"), minimo=("nota", "min"), n_notas=("nota", "size"), sin_validar=("validada", lambda v: int((v == 0).any())))
    por_componente = df.pivot_table(index=llave, columns="componente", values="nota", aggfunc="mean")
    for c in ["examen", "conducta", *TRABAJOS]:
        if c not in por_componente:
            por_componente[c] = np.nan
    base = base.join(por_componente[["examen", "cuaderno", "libro", "oral", "conducta"]])
    base["trabajos"] = por_componente[TRABAJOS].mean(axis=1)
    base = base.reset_index()

    # Desempeño del estudiante en sus otros cursos del mismo periodo.
    for origen, destino in [("examen", "examen_otros_cursos"), ("trabajos", "trabajos_otros_cursos")]:
        g = base.groupby(["est", "periodo"])[origen]
        suma, cuenta = g.transform("sum"), g.transform("count")
        propio = base[origen].notna().astype(int)
        base[destino] = (suma - base[origen].fillna(0)) / (cuenta - propio).replace(0, np.nan)

    # Periodo anterior y siguiente del mismo curso, dentro del mismo año escolar.
    base = base.sort_values(["est", "curso", "orden"]).reset_index(drop=True)
    g = base.groupby(["est", "curso", "anio"])
    base["examen_previo"] = g["examen"].shift(1)
    base["cambio_examen"] = base["examen"] - base["examen_previo"]
    base["examen_siguiente"] = g["examen"].shift(-1)
    base["periodo_siguiente"] = g["periodo"].shift(-1)
    base["objetivo"] = np.where(base["examen_siguiente"].notna(), (base["examen_siguiente"] < NOTA_APROBATORIA).astype(float), np.nan)

    base["secundaria"] = (base["nivel"] == "secundaria").astype(int)
    for a in AREAS:
        base[f"area_{a}"] = (base["area"] == a).astype(int)
    return base
