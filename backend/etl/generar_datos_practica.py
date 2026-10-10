"""
SIA-T: datos de práctica.

Genera data/notas_practica.csv: notas inventadas con la misma estructura que el registro real
del colegio (grados, tamaño de cada aula, cursos, componentes y dos periodos consecutivos).
Sirven para la demostración pública, porque los datos reales no pueden publicarse sin el
consentimiento de los apoderados. Ninguna nota de este archivo pertenece a un estudiante real.

Uso, desde la carpeta backend:  python -m etl.generar_datos_practica
"""

import csv
import os
import random

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(BASE, "data", "notas_practica.csv")
PERIODOS = ["2025-11", "2025-12"]
ACADEMICOS = ["libro", "cuaderno", "examen"]
TODOS = ["libro", "cuaderno", "conducta", "examen"]

# Estructura tomada del registro de noviembre y diciembre de 2025: (grado, nivel, estudiantes, {curso: componentes}).
ESTRUCTURA = [
    ("3° Primaria", "primaria", 5, {"Álgebra": TODOS, "Geometría": TODOS, "Razonamiento matemático": TODOS}),
    ("4° Primaria", "primaria", 7, {"Aritmética": TODOS, "Razonamiento matemático": TODOS, "Álgebra": ACADEMICOS, "Razonamiento verbal": ACADEMICOS, "Geometría": ACADEMICOS}),
    ("5° Primaria", "primaria", 10, {"Aritmética": ACADEMICOS, "Geometría": ACADEMICOS, "Álgebra": ACADEMICOS, "Razonamiento matemático": ACADEMICOS}),
    ("6° Primaria", "primaria", 7, {"Álgebra": TODOS, "Geometría": ACADEMICOS}),
    ("1° Secundaria", "secundaria", 8, {"Historia": ["cuaderno", "conducta", "examen"]}),
    ("2° Secundaria", "secundaria", 8, {"Economía": ["cuaderno", "conducta", "examen"]}),
]
# Diferencia típica de cada componente respecto del nivel del estudiante: el examen es más exigente.
AJUSTE = {"libro": 1.3, "cuaderno": 1.2, "conducta": 1.4, "examen": -1.2}
DISPERSION = {"libro": 1.2, "cuaderno": 1.3, "conducta": 1.0, "examen": 2.6}


def generar(semilla=2026) -> list:
    azar = random.Random(semilla)
    filas, numero = [], 0
    for grado, nivel, cantidad, cursos in ESTRUCTURA:
        for _ in range(cantidad):
            numero += 1
            codigo = f"P-{numero:04d}"
            capacidad = azar.gauss(14.6, 2.2)
            cambio = azar.gauss(0, 0.9) - (3.0 if azar.random() < 0.12 else 0)  # algunos estudiantes bajan en el segundo periodo
            for i, periodo in enumerate(PERIODOS):
                base = capacidad + (cambio if i == 1 else 0)
                for curso, componentes in cursos.items():
                    del_curso = azar.gauss(0, 0.8)
                    for componente in componentes:
                        nota = round(base + del_curso + AJUSTE[componente] + azar.gauss(0, DISPERSION[componente]))
                        filas.append({"codigo": codigo, "grado": grado, "nivel": nivel, "curso": curso, "periodo": periodo, "componente": componente, "nota": max(5, min(20, nota))})
    return filas


def main():
    filas = generar()
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["codigo", "grado", "nivel", "curso", "periodo", "componente", "nota"])
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} notas de práctica de {len({x['codigo'] for x in filas})} estudiantes ficticios en {DESTINO}")


if __name__ == "__main__":
    main()
