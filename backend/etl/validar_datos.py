"""
SIA-T: limpieza y validación automática de los datos (paquete 1.2.2 de la EDT, requisito REQ-02).

Uso, desde la carpeta backend:

    python -m etl.validar_datos                         # valida la base configurada
    python -m etl.validar_datos --reporte ../docs/reporte-calidad.md

Revisa la base, anota el resultado de cada regla en la tabla «calidad_datos» y termina con
código 1 si alguna regla crítica falla. Una tarea programada lo ejecuta cada noche
(.github/workflows/validacion-nocturna.yml).
"""

import argparse
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import case, func, insert, select

from etl.database import engine as engine_por_defecto
from etl.modelo_datos import calidad_datos, cargas, crear_tablas, cursos, estudiantes, matriculas, notas, periodos


def _reglas(cx) -> list:
    """Cada regla devuelve (nombre, severidad si falla, cantidad, descripción)."""
    contar = lambda consulta: cx.execute(consulta).scalar() or 0
    total_notas = contar(select(func.count()).select_from(notas))
    llave = [notas.c.estudiante_id, notas.c.curso_id, notas.c.periodo_id, notas.c.tipo_evaluacion, notas.c.componente]

    fuera = contar(select(func.count()).select_from(notas).where((notas.c.nota < 0) | (notas.c.nota > 20)))
    repetidas = len(cx.execute(select(notas.c.estudiante_id).group_by(*llave).having(func.count() > 1)).all())
    huerfanas = contar(
        select(func.count())
        .select_from(notas.outerjoin(estudiantes).outerjoin(cursos).outerjoin(periodos))
        .where((estudiantes.c.id.is_(None)) | (cursos.c.id.is_(None)) | (periodos.c.id.is_(None)))
    )
    sin_matricula = contar(select(func.count()).select_from(estudiantes).where(estudiantes.c.id.not_in(select(matriculas.c.estudiante_id))))
    en_cero = contar(select(func.count()).select_from(notas).where(notas.c.nota == 0))
    por_validar = contar(select(func.count()).select_from(notas).where(notas.c.validada == 0))
    sin_apellido = contar(select(func.count()).select_from(estudiantes).where(estudiantes.c.identidad == "solo_nombre"))
    por_estudiante = cx.execute(select(notas.c.estudiante_id, func.count(func.distinct(notas.c.periodo_id))).group_by(notas.c.estudiante_id)).all()
    un_periodo = sum(1 for _, n in por_estudiante if n < 2)
    sin_examen = len(
        cx.execute(
            select(notas.c.estudiante_id, notas.c.curso_id, notas.c.periodo_id)
            .group_by(notas.c.estudiante_id, notas.c.curso_id, notas.c.periodo_id)
            .having(func.sum(case((notas.c.componente == "examen", 1), else_=0)) == 0)
        ).all()
    )

    return [
        ("base_con_datos", "critica", 0 if total_notas else 1, "La base tiene notas cargadas."),
        ("notas_fuera_de_rango", "critica", fuera, "Notas menores de 0 o mayores de 20."),
        ("notas_duplicadas", "critica", repetidas, "Misma nota registrada más de una vez (estudiante, curso, periodo, tipo y componente)."),
        ("referencias_huerfanas", "critica", huerfanas, "Notas sin estudiante, curso o periodo."),
        ("estudiantes_sin_matricula", "critica", sin_matricula, "Estudiantes sin año, nivel y grado."),
        ("notas_por_validar", "aviso", por_validar, "Notas transcritas de cuadernos que falta cotejar con el original."),
        ("notas_en_cero", "aviso", en_cero, "Notas en cero: conviene confirmar si son inasistencias a la evaluación."),
        ("identidad_incompleta", "aviso", sin_apellido, "Estudiantes de los que solo se conoce el nombre de pila."),
        ("cursos_sin_examen", "aviso", sin_examen, "Cursos de un estudiante en un periodo sin nota de examen."),
        ("un_solo_periodo", "aviso", un_periodo, "Estudiantes con un solo periodo: no hay periodo anterior con que comparar."),
    ]


def validar(engine=engine_por_defecto) -> dict:
    """Ejecuta las reglas, guarda el resultado y lo devuelve."""
    crear_tablas(engine)
    momento = datetime.now()
    with engine.begin() as cx:
        resultados = [
            {"regla": nombre, "severidad": severidad if cantidad else "correcta", "cantidad": int(cantidad or 0), "detalle": descripcion}
            for nombre, severidad, cantidad, descripcion in _reglas(cx)
        ]
        cx.execute(insert(calidad_datos), [{**r, "fecha": momento} for r in resultados])
        resumen = {
            "estudiantes": cx.execute(select(func.count()).select_from(estudiantes)).scalar(),
            "cursos": cx.execute(select(func.count()).select_from(cursos)).scalar(),
            "periodos": [c for (c,) in cx.execute(select(periodos.c.codigo).order_by(periodos.c.codigo))],
            "notas": cx.execute(select(func.count()).select_from(notas)).scalar(),
            "cargas": cx.execute(select(func.count()).select_from(cargas)).scalar(),
        }
    return {
        "fecha": momento.strftime("%Y-%m-%d %H:%M"),
        "resumen": resumen,
        "reglas": resultados,
        "criticas": sum(1 for r in resultados if r["severidad"] == "critica"),
        "avisos": sum(1 for r in resultados if r["severidad"] == "aviso"),
    }


def a_markdown(resultado: dict, titulo="Reporte de calidad de datos") -> str:
    r = resultado["resumen"]
    lineas = [
        f"# {titulo}",
        "",
        f"Generado el {resultado['fecha']} por `python -m etl.validar_datos`.",
        "",
        f"- Estudiantes: {r['estudiantes']}",
        f"- Cursos: {r['cursos']}",
        f"- Periodos: {', '.join(r['periodos']) or 'ninguno'}",
        f"- Notas: {r['notas']}",
        "",
        "| Regla | Resultado | Cantidad | Qué revisa |",
        "|---|---|---|---|",
    ]
    etiqueta = {"correcta": "Correcta", "aviso": "Aviso", "critica": "CRÍTICA"}
    lineas += [f"| `{x['regla']}` | {etiqueta[x['severidad']]} | {x['cantidad']} | {x['detalle']} |" for x in resultado["reglas"]]
    lineas += ["", f"Reglas críticas con fallas: {resultado['criticas']}. Avisos: {resultado['avisos']}.", ""]
    return "\n".join(lineas)


def main():
    parser = argparse.ArgumentParser(description="Valida los datos de la base de SIA-T.")
    parser.add_argument("--reporte", help="Ruta donde guardar el reporte en Markdown")
    args = parser.parse_args()
    resultado = validar()
    texto = a_markdown(resultado)
    print(texto)
    if args.reporte:
        with open(args.reporte, "w", encoding="utf-8") as f:
            f.write(texto)
    sys.exit(1 if resultado["criticas"] else 0)


if __name__ == "__main__":
    main()
