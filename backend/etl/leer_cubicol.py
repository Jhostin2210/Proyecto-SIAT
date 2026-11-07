"""
SIA-T: lectura de las exportaciones de Cubicol («Registro auxiliar», archivos .xls).

Cada archivo es un curso de un salón en una unidad (mes): trae el salón, el curso, el periodo, la
unidad y el profesor en la cabecera, y luego una fila por estudiante con su promedio y la nota de
cada criterio de evaluación. Se toma el promedio de la unidad, que es el promedio de sus criterios.

Los estudiantes se enlazan con su código ya existente, dentro de su grado:
1. con la tabla de equivalencias revisada a mano (data/privado/cubicol_equivalencias.csv), si existe;
2. si las palabras del nombre son las mismas que las de un solo estudiante del grado;
3. si las palabras del nombre están todas dentro del nombre de un solo estudiante del grado.
Los que no se enlazan con certeza no se cargan: quedan en una lista para revisarlos.
Este módulo no crea estudiantes ni guarda nombres fuera de la carpeta privada.
"""

import csv
import os
import re
from pathlib import Path

from etl.leer_consolidado import curso_oficial, periodo_de, plano

GRADOS = {"primero": 1, "segundo": 2, "tercer": 3, "tercero": 3, "cuarto": 4, "quinto": 5, "sexto": 6}
# El promedio de los criterios de la unidad es la evaluación continua del mes: se guarda como «trabajo»
# (catálogo de la base) y se distingue por su fuente, «CUBICOL».
COMPONENTE = "trabajo"
TIPO = "registro_mensual"


def _palabras(texto) -> frozenset:
    return frozenset(plano(texto).replace(",", " ").replace("|", " ").replace(".", " ").split())


def _cabecera(hoja) -> dict:
    """Valor que sigue a cada etiqueta de la fila de cabecera (Salón, Curso, Periodo, Unidad)."""
    fila = [str(hoja.cell_value(3, c)).strip() for c in range(hoja.ncols)]
    datos = {}
    for etiqueta in ("salon", "curso", "periodo", "unidad", "profesor"):
        i = next((i for i, v in enumerate(fila) if plano(v).rstrip(":") == etiqueta), None)
        datos[etiqueta] = next((v for v in fila[i + 1 :] if v), "") if i is not None else ""
    return datos


def grado_de(salon: str):
    """«Primaria Cuarto Grado» → ("primaria", 4)."""
    p = plano(salon).split()
    nivel = p[0] if p else ""
    numero = next((GRADOS[x] for x in p if x in GRADOS), None)
    return nivel, numero


def leer_equivalencias(ruta) -> dict:
    if not ruta or not os.path.exists(ruta):
        return {}
    with open(ruta, newline="", encoding="utf-8") as f:
        return {_palabras(fila["nombre_cubicol"]): fila["codigo"].strip() for fila in csv.DictReader(f, delimiter=";") if fila.get("codigo", "").strip()}


def enlazar(nombre, nivel, numero, claves: dict, grado_por_codigo: dict, equivalencias: dict):
    """Devuelve (código, criterio) o (None, motivo)."""
    palabras = _palabras(nombre)
    if palabras in equivalencias:
        return equivalencias[palabras], "equivalencia revisada"
    del_grado = {
        clave: codigo
        for clave, codigo in claves.items()
        if (g := grado_por_codigo.get(codigo, "")) and g.startswith(str(numero)) and nivel in plano(g)
    }
    iguales = [c for k, c in del_grado.items() if _palabras(k.split("|")[0]) == palabras]
    if len(iguales) == 1:
        return iguales[0], "mismo nombre"
    contenidos = [c for k, c in del_grado.items() if palabras < _palabras(k.split("|")[0])]
    if len(contenidos) == 1 and not iguales:
        return contenidos[0], "nombre más corto que el de la base"
    if len(iguales) > 1 or len(contenidos) > 1:
        return None, "coincide con más de un estudiante del grado"
    return None, "sin coincidencia segura en el grado"


def leer_cubicol(archivos, claves: dict, grado_por_codigo: dict, ruta_equivalencias=None, anio: int = 2026) -> dict:
    """Devuelve {"notas": [...], "sin_identificar": [...], "hallazgos": [...], "filas_origen": n, "archivos": n}."""
    import xlrd  # solo hace falta para cargar exportaciones de Cubicol

    equivalencias = leer_equivalencias(ruta_equivalencias)
    notas, sin_identificar, hallazgos, vistas = [], {}, {}, set()
    filas_origen = 0

    def hallazgo(regla, detalle):
        h = hallazgos.setdefault(regla, {"regla": regla, "severidad": "aviso", "detalle": detalle, "cantidad": 0})
        h["cantidad"] += 1

    archivos = sorted(Path(a) for a in archivos)
    for archivo in archivos:
        # Cubicol genera .xls con una estructura interna irregular; se leen igual.
        hoja = xlrd.open_workbook(str(archivo), ignore_workbook_corruption=True).sheet_by_index(0)
        cab = _cabecera(hoja)
        nivel, numero = grado_de(cab["salon"])
        curso = curso_oficial(cab["curso"])
        periodo = periodo_de(cab["unidad"], TIPO, anio)
        for r in range(8, hoja.nrows):
            if str(hoja.cell_value(r, 0)).strip() == "":
                continue  # filas vacías y fila de totales
            filas_origen += 1
            nombre = hoja.cell_value(r, 1)
            if not curso:
                hallazgo("curso_no_catalogado", f"Curso fuera del catálogo («{cab['curso'][:30]}»): no se carga.")
                continue
            if not periodo:
                hallazgo("periodo_no_identificado", f"Unidad sin mes reconocible («{cab['unidad'][:20]}»): no se carga.")
                continue
            try:
                nota = float(str(hoja.cell_value(r, 3)).strip())
            except ValueError:
                hallazgo("nota_vacia_o_textual", "Promedio vacío o con texto: no se carga ni se asume cero.")
                continue
            if not 0 <= nota <= 20:
                hallazgo("nota_fuera_de_rango", "Promedios fuera de 0 a 20: no se cargan.")
                continue
            codigo, criterio = enlazar(nombre, nivel, numero, claves, grado_por_codigo, equivalencias)
            if not codigo:
                s = sin_identificar.setdefault(_palabras(nombre), {"nombre": plano(nombre), "salon": cab["salon"], "motivo": criterio, "notas": 0})
                s["notas"] += 1
                continue
            llave = (codigo, curso[0], periodo[0])
            if llave in vistas:
                hallazgo("nota_repetida_en_origen", "El mismo estudiante, curso y mes aparece en más de un archivo: se conserva el primero.")
                continue
            vistas.add(llave)
            notas.append(
                {
                    "codigo": codigo,
                    "criterio_enlace": criterio,
                    "curso": curso[0],
                    "area": curso[1],
                    "periodo": periodo[0],
                    "periodo_nombre": periodo[1],
                    "periodo_orden": periodo[2],
                    "anio": anio,
                    "tipo": TIPO,
                    "componente": COMPONENTE,
                    "nota": nota,
                    "fuente": "CUBICOL",
                    "confianza": "alta",
                    "validada": 1,
                }
            )
    if sin_identificar:
        hallazgos["estudiante_sin_identificar"] = {
            "regla": "estudiante_sin_identificar",
            "severidad": "aviso",
            "detalle": "Estudiantes que no se enlazan con certeza a un código: sus notas no se cargan hasta revisarlos.",
            "cantidad": sum(s["notas"] for s in sin_identificar.values()),
        }
    return {"notas": notas, "sin_identificar": list(sin_identificar.values()), "hallazgos": list(hallazgos.values()), "filas_origen": filas_origen, "archivos": len(archivos)}
