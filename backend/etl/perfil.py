"""
SIA-T: perfil del estudiante.

Además de las notas, el modelo usa 23 datos de cada estudiante: historial, familia y hábitos. Este
módulo define esos datos, los lee de la tabla «perfiles» y completa los perfiles que falten.

Los nombres de la izquierda son las columnas de la base de datos; los de la derecha, las columnas
de la base pública con que se entrenó el modelo. Los valores se guardan con los códigos de esa base.
"""

import os
import re
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy import func, insert, select

from etl.generar_datos_practica import NOMBRES, NOMBRES_FEMENINOS
from etl.modelo_datos import estudiantes, matriculas, perfiles

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_PUBLICA = os.path.join(BASE, "data", "publica")

COLUMNAS = {
    "sexo": "sex",
    "edad": "age",
    "tam_familia": "famsize",
    "padres_juntos": "Pstatus",
    "educ_madre": "Medu",
    "educ_padre": "Fedu",
    "ocup_madre": "Mjob",
    "ocup_padre": "Fjob",
    "apoderado": "guardian",
    "tiempo_viaje": "traveltime",
    "horas_estudio": "studytime",
    "cursos_desaprobados": "failures",
    "apoyo_escolar": "schoolsup",
    "apoyo_familiar": "famsup",
    "clases_pagadas": "paid",
    "actividades": "activities",
    "internet": "internet",
    "pareja": "romantic",
    "relacion_familiar": "famrel",
    "tiempo_libre": "freetime",
    "salidas": "goout",
    "salud": "health",
    "inasistencias": "absences",
}
# El modelo se entrenó con estudiantes de 15 a 22 años: la edad se lleva a ese rango antes de usarla.
EDAD_MINIMA_MODELO, EDAD_MAXIMA_MODELO = 15, 22

# Qué significa cada dato y sus valores, para el formulario y la ficha.
DESCRIPCION = {
    "sexo": {"etiqueta": "Sexo", "grupo": "familia", "opciones": {"F": "Femenino", "M": "Masculino"}},
    "edad": {"etiqueta": "Edad", "grupo": "historial", "minimo": 6, "maximo": 22},
    "tam_familia": {"etiqueta": "Tamaño de la familia", "grupo": "familia", "opciones": {"LE3": "Hasta 3 personas", "GT3": "Más de 3 personas"}},
    "padres_juntos": {"etiqueta": "Padres", "grupo": "familia", "opciones": {"T": "Viven juntos", "A": "Viven separados"}},
    "educ_madre": {"etiqueta": "Estudios de la madre", "grupo": "familia", "opciones": {0: "Ninguno", 1: "Primaria", 2: "Secundaria incompleta", 3: "Secundaria completa", 4: "Superior"}},
    "educ_padre": {"etiqueta": "Estudios del padre", "grupo": "familia", "opciones": {0: "Ninguno", 1: "Primaria", 2: "Secundaria incompleta", 3: "Secundaria completa", 4: "Superior"}},
    "ocup_madre": {"etiqueta": "Ocupación de la madre", "grupo": "familia", "opciones": {"teacher": "Docente", "health": "Salud", "services": "Servicios", "at_home": "En casa", "other": "Otra"}},
    "ocup_padre": {"etiqueta": "Ocupación del padre", "grupo": "familia", "opciones": {"teacher": "Docente", "health": "Salud", "services": "Servicios", "at_home": "En casa", "other": "Otra"}},
    "apoderado": {"etiqueta": "Apoderado", "grupo": "familia", "opciones": {"mother": "Madre", "father": "Padre", "other": "Otro familiar"}},
    "tiempo_viaje": {"etiqueta": "Tiempo de casa al colegio", "grupo": "historial", "opciones": {1: "Menos de 15 minutos", 2: "De 15 a 30 minutos", 3: "De 30 minutos a 1 hora", 4: "Más de 1 hora"}},
    "horas_estudio": {"etiqueta": "Estudio por semana", "grupo": "historial", "opciones": {1: "Menos de 2 horas", 2: "De 2 a 5 horas", 3: "De 5 a 10 horas", 4: "Más de 10 horas"}},
    "cursos_desaprobados": {"etiqueta": "Cursos desaprobados antes", "grupo": "historial", "opciones": {0: "Ninguno", 1: "Uno", 2: "Dos", 3: "Tres o más"}},
    "apoyo_escolar": {"etiqueta": "Apoyo escolar adicional", "grupo": "historial", "opciones": {"no": "No", "yes": "Sí"}},
    "apoyo_familiar": {"etiqueta": "Apoyo de la familia para estudiar", "grupo": "familia", "opciones": {"no": "No", "yes": "Sí"}},
    "clases_pagadas": {"etiqueta": "Clases particulares", "grupo": "historial", "opciones": {"no": "No", "yes": "Sí"}},
    "actividades": {"etiqueta": "Actividades extracurriculares", "grupo": "habitos", "opciones": {"no": "No", "yes": "Sí"}},
    "internet": {"etiqueta": "Internet en casa", "grupo": "familia", "opciones": {"no": "No", "yes": "Sí"}},
    "pareja": {"etiqueta": "Relación sentimental", "grupo": "habitos", "opciones": {"no": "No", "yes": "Sí"}},
    "relacion_familiar": {"etiqueta": "Relación familiar", "grupo": "familia", "opciones": {1: "Muy mala", 2: "Mala", 3: "Regular", 4: "Buena", 5: "Muy buena"}},
    "tiempo_libre": {"etiqueta": "Tiempo libre después del colegio", "grupo": "habitos", "opciones": {1: "Muy poco", 2: "Poco", 3: "Regular", 4: "Bastante", 5: "Mucho"}},
    "salidas": {"etiqueta": "Salidas con amigos", "grupo": "habitos", "opciones": {1: "Muy pocas", 2: "Pocas", 3: "Regular", 4: "Bastantes", 5: "Muchas"}},
    "salud": {"etiqueta": "Estado de salud", "grupo": "habitos", "opciones": {1: "Muy malo", 2: "Malo", 3: "Regular", 4: "Bueno", 5: "Muy bueno"}},
    "inasistencias": {"etiqueta": "Inasistencias en el año", "grupo": "historial", "minimo": 0, "maximo": 93},
}


def leer_base_publica() -> pd.DataFrame:
    partes = []
    for archivo, curso in (("student-mat.csv", "Matemática"), ("student-por.csv", "Lenguaje")):
        d = pd.read_csv(os.path.join(CARPETA_PUBLICA, archivo), sep=";")
        d["curso"] = curso
        partes.append(d)
    d = pd.concat(partes, ignore_index=True)
    for c in ("G1", "G2", "G3"):
        d[c] = pd.to_numeric(d[c])
    return d


def edad_por_grado(grado: str, nivel: str) -> int:
    """Edad habitual al terminar el grado: 3.° de primaria, 9 años; 1.° de secundaria, 13."""
    numero = re.search(r"\d", grado or "")
    numero = int(numero.group()) if numero else 1
    return {"inicial": 2, "primaria": 6, "secundaria": 12}.get(nivel, 6) + numero


def completar_perfiles(engine, semilla: int = 2026) -> int:
    """Crea el perfil de los estudiantes que todavía no lo tienen. Devuelve cuántos creó."""
    with engine.connect() as cx:
        ultima = select(matriculas.c.estudiante_id, func.max(matriculas.c.anio).label("anio")).group_by(matriculas.c.estudiante_id).subquery()
        consulta = (
            select(estudiantes.c.id, estudiantes.c.nombres, matriculas.c.nivel_educativo, matriculas.c.grado)
            .select_from(estudiantes.join(ultima, ultima.c.estudiante_id == estudiantes.c.id).join(matriculas, (matriculas.c.estudiante_id == estudiantes.c.id) & (matriculas.c.anio == ultima.c.anio)))
            .where(estudiantes.c.id.not_in(select(perfiles.c.estudiante_id)))
            .order_by(estudiantes.c.codigo)
        )
        pendientes = cx.execute(consulta).all()
    if not pendientes:
        return 0
    publica = leer_base_publica()
    elegidos = publica.iloc[np.random.RandomState(semilla).randint(0, len(publica), size=len(pendientes))]
    ahora, filas = datetime.now(), []
    for (est_id, nombres, nivel, grado), (_, origen) in zip(pendientes, elegidos.iterrows()):
        fila = {columna: (origen[publica_col].item() if hasattr(origen[publica_col], "item") else origen[publica_col]) for columna, publica_col in COLUMNAS.items()}
        fila["edad"] = edad_por_grado(grado, nivel)
        primer_nombre = (nombres or "").split(" ")[0]
        if primer_nombre in NOMBRES:  # nombres de los datos de práctica: el sexo acompaña al nombre
            fila["sexo"] = "F" if primer_nombre in NOMBRES_FEMENINOS else "M"
        if nivel != "secundaria":
            fila["pareja"] = "no"
        filas.append({**fila, "estudiante_id": est_id, "origen": "generado", "actualizado": ahora})
    with engine.begin() as cx:
        cx.execute(insert(perfiles), filas)
    return len(filas)


def leer_perfiles(engine) -> pd.DataFrame:
    """Perfiles con los nombres de columna que espera el modelo, más «est» (id del estudiante)."""
    with engine.connect() as cx:
        d = pd.DataFrame(cx.execute(select(perfiles)).mappings().all())
    if d.empty:
        return pd.DataFrame(columns=["est", *COLUMNAS.values()])
    d = d.rename(columns={"estudiante_id": "est", **COLUMNAS})[["est", *COLUMNAS.values()]]
    return para_el_modelo(d)


def para_el_modelo(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["age"] = pd.to_numeric(d["age"]).clip(EDAD_MINIMA_MODELO, EDAD_MAXIMA_MODELO)
    return d
