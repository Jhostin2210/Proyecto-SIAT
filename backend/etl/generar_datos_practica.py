"""
SIA-T: datos de práctica para la demostración.

Genera data/notas_practica.csv: un colegio ficticio completo, con la misma estructura que la base
real (grados, cursos, tipos de nota y periodos) y notas con un comportamiento parecido al real:
los trabajos tienen notas más altas que los exámenes y a quien le va mal un mes le suele ir mal el
siguiente. Los nombres son inventados. Ningún estudiante ni nota de este archivo es real.

Estos datos alimentan el sistema público. Nunca se usan para entrenar ni para validar el modelo.

Uso, desde la carpeta backend:  python -m etl.generar_datos_practica
"""

import csv
import os
import random
import unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(BASE, "data", "notas_practica.csv")
RUTA_CLAVES = os.path.join(BASE, "data", "privado", "claves.csv")
ANIO = 2026
PERIODOS = [("2026-03", "Marzo de 2026", 2026.03), ("2026-04", "Abril de 2026", 2026.04), ("2026-05", "Mayo de 2026", 2026.05)]
GRADOS = [("3° Primaria", "primaria", 14), ("4° Primaria", "primaria", 15), ("5° Primaria", "primaria", 16), ("6° Primaria", "primaria", 15), ("1° Secundaria", "secundaria", 17), ("2° Secundaria", "secundaria", 16), ("3° Secundaria", "secundaria", 15), ("4° Secundaria", "secundaria", 14), ("5° Secundaria", "secundaria", 13)]
CURSOS = {
    "primaria": [("Aritmética", "Matemática"), ("Comunicación", "Comunicación"), ("Personal Social", "Ciencias Sociales"), ("Ciencia y Ambiente", "Ciencia y Tecnología")],
    "secundaria": [("Álgebra", "Matemática"), ("Lenguaje", "Comunicación"), ("Historia", "Ciencias Sociales"), ("Ciencia y Tecnología", "Ciencia y Tecnología")],
}
# Diferencia típica de cada tipo de nota respecto del nivel del estudiante, y cuánto varía.
COMPONENTES = {"cuaderno": (0.6, 1.4), "libro": (0.4, 1.5), "oral": (0.0, 1.8), "practica": (-0.6, 2.2), "examen": (-0.4, 3.0), "conducta": (1.2, 1.2)}
NOMBRES = ["Camila", "Mateo", "Valentina", "Thiago", "Luciana", "Liam", "Mía", "Gael", "Ariana", "Dylan", "Zoe", "Ian", "Antonella", "Adrián", "Fabiana", "Joaquín", "Renata", "Sebastián", "Daniela", "Rodrigo", "Alessia", "Nicolás", "Brianna", "Emilio", "Samantha", "Bruno", "Kiara", "Leonardo", "Abigail", "Santiago", "Paula", "Marcelo", "Ximena", "Álvaro", "Micaela", "Iker", "Alondra", "Franco", "Nahia", "Piero"]
NOMBRES_FEMENINOS = {"Camila", "Valentina", "Luciana", "Mía", "Ariana", "Zoe", "Antonella", "Fabiana", "Renata", "Daniela", "Alessia", "Brianna", "Samantha", "Kiara", "Abigail", "Paula", "Ximena", "Micaela", "Alondra", "Nahia"}
APELLIDOS = ["Quispe", "Flores", "Rojas", "Huamán", "Mamani", "Torres", "Vargas", "Ramos", "Castillo", "Chávez", "Mendoza", "Salazar", "Espinoza", "Paredes", "Cárdenas", "Aguilar", "Medina", "Palomino", "Yupanqui", "Villanueva", "Cabrera", "Poma", "Reyes", "Ccori", "Delgado", "Ñahui", "Campos", "Tello", "Gutarra", "Lozano"]


def _sin_tildes(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def _personas_reales() -> list:
    """Palabras del nombre de cada estudiante real, si la relación privada está en este equipo.
    Sirve para que ningún estudiante ficticio se llame igual que uno real."""
    if not os.path.exists(RUTA_CLAVES):
        return []
    with open(RUTA_CLAVES, encoding="utf-8") as f:
        return [set(_sin_tildes(fila["clave"]).replace("|", " ").split()) for fila in csv.DictReader(f, delimiter=";")]


def generar(semilla=2026) -> list:
    azar = random.Random(semilla)
    filas, numero, usados = [], 0, set()
    reales = _personas_reales()
    for grado, nivel, cantidad in GRADOS:
        for _ in range(cantidad):
            numero += 1
            while True:  # nombre y apellido que no se repitan ni coincidan con un estudiante real
                persona = (azar.choice(NOMBRES), azar.choice(APELLIDOS))
                if any({_sin_tildes(persona[0]), _sin_tildes(persona[1])} <= real for real in reales):
                    continue
                if persona not in usados:
                    usados.add(persona)
                    break
            capacidad = azar.gauss(15.1, 2.3)
            tendencia = azar.gauss(0, 0.5) - (1.3 if azar.random() < 0.15 else 0)  # algunos van bajando mes a mes
            por_curso = {curso: azar.gauss(0, 1.3) for curso, _ in CURSOS[nivel]}
            for i, (periodo, nombre_periodo, orden) in enumerate(PERIODOS):
                del_mes = azar.gauss(0, 0.6)
                for curso, area in CURSOS[nivel]:
                    base = capacidad + tendencia * i + por_curso[curso] + del_mes
                    for componente, (ajuste, variacion) in COMPONENTES.items():
                        if componente == "conducta" and curso not in ("Personal Social", "Historia"):
                            continue  # la conducta se registra en un solo curso, como en el colegio
                        if componente == "practica" and azar.random() < 0.35:
                            continue  # no todos los meses hay práctica calificada
                        nota = max(4, min(20, round(base + ajuste + azar.gauss(0, variacion))))
                        filas.append(
                            {"codigo": f"P-{numero:04d}", "nombres": persona[0], "apellido": persona[1], "anio": ANIO, "nivel": nivel, "grado": grado, "curso": curso, "area": area, "periodo": periodo, "periodo_nombre": nombre_periodo, "periodo_orden": orden, "tipo": "registro_mensual", "componente": componente, "nota": nota}
                        )
    return filas


def main():
    filas = generar()
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} notas de práctica de {len({x['codigo'] for x in filas})} estudiantes ficticios en {DESTINO}")


if __name__ == "__main__":
    main()
