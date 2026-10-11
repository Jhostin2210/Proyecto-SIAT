"""
SIA-T: informe del estudiante.

Junta los resultados de sus cursos, reconoce el patrón (un curso o varios, exámenes frente a
trabajos, caída reciente), propone acciones y redacta el comunicado para el apoderado (REQ-12).

Las acciones son un borrador del equipo del proyecto: deben validarse con los docentes y con el
responsable de psicología antes del piloto.
"""

from etl.variables import NOTA_APROBATORIA

ALTO, MEDIO, BAJO = "Riesgo alto", "Riesgo medio", "Riesgo bajo"
ORDEN = {BAJO: 0, MEDIO: 1, ALTO: 2}
CAIDA_FUERTE = 2  # puntos que baja la nota de un periodo al siguiente
BRECHA_EXAMEN = 3  # puntos en que el examen queda por debajo de los trabajos


def nivel_de(probabilidad: float, umbrales: dict) -> str:
    return ALTO if probabilidad >= umbrales["alto"] else MEDIO if probabilidad >= umbrales["medio"] else BAJO


def nivel_general(cursos: list, umbrales: dict):
    """Riesgo general del estudiante: (nivel, probabilidad).
    La probabilidad es el promedio de sus cursos. Un curso en riesgo alto basta para que el estudiante
    esté en riesgo alto: es el caso en que el colegio debe actuar aunque los demás cursos vayan bien."""
    probabilidad = sum(c["probabilidad"] for c in cursos) / len(cursos)
    nivel = nivel_de(probabilidad, umbrales)
    if any(c["nivel"] == ALTO for c in cursos):
        nivel = ALTO
    return nivel, probabilidad


def _lista(nombres: list) -> str:
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]


def patrones_de(cursos: list) -> list:
    """Patrones que se observan en las notas. Cada uno: {clave, texto}."""
    altos = [c for c in cursos if c["nivel"] == ALTO]
    medios = [c for c in cursos if c["nivel"] == MEDIO]
    en_riesgo = altos + medios
    hallados = []
    if len(altos) >= 2 or (altos and len(en_riesgo) >= 3):
        hallados.append({"clave": "varios_cursos", "texto": f"Dificultad en varios cursos: {_lista([c['curso'] for c in en_riesgo[:4]])}."})
    elif len(altos) == 1:
        hallados.append({"clave": "un_curso", "texto": f"La dificultad se concentra en {altos[0]['curso']}."})
    elif len(medios) >= 3:
        hallados.append({"clave": "rendimiento_justo", "texto": f"Rendimiento justo en {len(medios)} cursos, sin ninguno en riesgo alto."})

    brecha = [c for c in en_riesgo if c.get("examen") is not None and c.get("trabajos") is not None and c["trabajos"] - c["examen"] >= BRECHA_EXAMEN]
    if brecha:
        hallados.append({"clave": "examenes_bajos", "texto": f"Rinde menos en los exámenes que en los trabajos en {_lista([c['curso'] for c in brecha[:3]])}."})
    todo_bajo = [c for c in altos if c.get("examen") is not None and c.get("trabajos") is not None and c["examen"] < NOTA_APROBATORIA and c["trabajos"] < NOTA_APROBATORIA]
    if todo_bajo:
        hallados.append({"clave": "todo_bajo", "texto": f"Exámenes y trabajos desaprobados en {_lista([c['curso'] for c in todo_bajo[:3]])}."})
    caida = [c for c in cursos if c.get("cambio") is not None and c["cambio"] <= -CAIDA_FUERTE]
    if caida:
        peor = min(caida, key=lambda c: c["cambio"])
        hallados.append({"clave": "caida", "texto": f"Bajó {abs(peor['cambio']):.0f} puntos en {peor['curso']} respecto del periodo anterior." + (f" También bajó en {_lista([c['curso'] for c in caida if c is not peor][:2])}." if len(caida) > 1 else "")})
    if not hallados:
        hallados.append({"clave": "sin_senales", "texto": "Sin señales de riesgo en sus cursos."})
    return hallados


ACCIONES = {
    "varios_cursos": ["Reunión del tutor con el apoderado dentro de la semana.", "Derivación a psicología para descartar una causa que no sea académica.", "Plan de reforzamiento coordinado entre los docentes de los cursos en riesgo."],
    "un_curso": ["Reforzamiento con el docente del curso antes de la próxima evaluación.", "Revisión de los temas pendientes y entrega de material de práctica."],
    "rendimiento_justo": ["Seguimiento del tutor en el próximo periodo.", "Conversación breve con el estudiante sobre sus hábitos de estudio."],
    "examenes_bajos": ["Práctica con evaluaciones anteriores y repaso antes de cada examen.", "Revisar con el estudiante cómo se prepara para los exámenes."],
    "todo_bajo": ["Verificar si entrega las tareas y lleva el cuaderno al día.", "Acordar con el apoderado un horario de estudio en casa."],
    "caida": ["Entrevista del tutor con el estudiante esta semana para conocer qué cambió."],
}


def acciones_de(patrones: list, nivel: str) -> list:
    acciones = []
    for p in patrones:
        for a in ACCIONES.get(p["clave"], []):
            if a not in acciones:
                acciones.append(a)
    if not acciones:
        acciones.append("Seguimiento del tutor en el próximo periodo." if nivel == MEDIO else "Continuar con el seguimiento regular.")
    return acciones[:5]


def comunicado_apoderado(nombre: str, grado: str, periodo: str, nivel: str, cursos: list, colegio: str = "I.E.P. Peruano Francés") -> str:
    """Mensaje para el apoderado, sin tecnicismos: en qué cursos hay dificultad y cómo apoyar en casa."""
    dificultad = [c for c in cursos if c["nivel"] == ALTO] or [c for c in cursos if c["nivel"] == MEDIO]
    lineas = [f"Estimado(a) apoderado(a) de {nombre}:", "", f"Le escribimos de la {colegio}. Al revisar las notas de {periodo[:1].lower() + periodo[1:]}, vemos que {nombre.split()[0]} necesita apoyo" + (f" en {_lista([c['curso'] for c in dificultad[:3]])}." if dificultad else ".")]
    if dificultad:
        lineas += ["", "Notas del periodo:"] + [f"- {c['curso']}: {c['nota']:.0f}" for c in dificultad[:3]]
    lineas += [
        "",
        "Cómo puede ayudar en casa:",
        "- Acordar un horario fijo de estudio todos los días.",
        "- Revisar que tenga el cuaderno y las tareas al día.",
        "- Conversar con su hijo(a) sobre lo que le resulta difícil.",
        "",
        "Queremos coordinar una reunión con usted. Por favor indíquenos qué día puede acercarse al colegio.",
        "",
        "Atentamente,",
        "Tutoría",
    ]
    return "\n".join(lineas)


def armar_informe(nombre: str, grado: str, periodo: str, cursos: list, umbrales: dict) -> dict:
    """Informe completo de un estudiante a partir de los resultados de sus cursos en un periodo."""
    cursos = sorted(cursos, key=lambda c: -c["probabilidad"])
    nivel, probabilidad = nivel_general(cursos, umbrales)
    patrones = patrones_de(cursos)
    en_alto, en_medio = [c["curso"] for c in cursos if c["nivel"] == ALTO], [c["curso"] for c in cursos if c["nivel"] == MEDIO]
    if en_alto:
        resumen = f"Riesgo alto en {_lista(en_alto)}" + (f"; riesgo medio en {_lista(en_medio[:3])}." if en_medio else ".")
    elif en_medio:
        resumen = f"Riesgo medio en {_lista(en_medio[:4])}."
    else:
        resumen = "Ningún curso con señales de riesgo."
    return {
        "nivel": nivel,
        "probabilidad": round(probabilidad, 3),
        "resumen": resumen,
        "cursos": cursos,
        "patrones": patrones,
        "acciones": acciones_de(patrones, nivel),
        "comunicado": comunicado_apoderado(nombre, grado, periodo, nivel, cursos) if nivel == ALTO else None,
    }
