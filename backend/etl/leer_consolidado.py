"""
SIA-T: lectura de la base escolar consolidada (Excel con las hojas BASE_NOTAS y ALUMNOS).

La base consolidada reúne los registros de notas de los docentes y la transcripción de sus
cuadernos. Cada fila de BASE_NOTAS es una calificación. Este módulo la ordena:

- unifica a cada estudiante (el archivo repite un identificador provisional por cada lista);
- normaliza los cursos (30 formas de escribirlos) y las actividades (49 etiquetas) con catálogos;
- convierte mes y tipo de evaluación en un periodo;
- conserva la fuente, la confianza y si la nota está pendiente de validar.

Solo toma nombre, apellido, nivel y grado. No lee la hoja de datos personales (DNI y fechas).
"""

import re
import unicodedata

import pandas as pd

MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8, "setiembre": 9, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
NOMBRE_MES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
# El archivo solo acredita 2025 para una fuente; el resto corresponde al año escolar siguiente.
ANIO_POR_DEFECTO = 2026

# Curso oficial y área, según el inicio del nombre escrito en el registro (sin tildes ni mayúsculas).
CURSOS = [
    ("geometria", "Geometría", "Matemática"),
    ("algebra", "Álgebra", "Matemática"),
    ("aritm", "Aritmética", "Matemática"),
    ("r.m", "Razonamiento matemático", "Matemática"),
    ("r.v", "Razonamiento verbal", "Comunicación"),
    ("lenguaje", "Lenguaje", "Comunicación"),
    ("literatura", "Literatura", "Comunicación"),
    ("comunicacion", "Comunicación", "Comunicación"),
    ("historia", "Historia", "Ciencias Sociales"),
    ("civica", "Cívica", "Ciencias Sociales"),
    ("geografia", "Geografía", "Ciencias Sociales"),
    ("economia", "Economía", "Ciencias Sociales"),
    ("personal social", "Personal Social", "Ciencias Sociales"),
    ("cultura general", "Cultura General", "Ciencias Sociales"),
    ("ciencia y tecnologia", "Ciencia y Tecnología", "Ciencia y Tecnología"),
    ("ciencia y ambiente", "Ciencia y Ambiente", "Ciencia y Tecnología"),
]

# Tipo de nota según la etiqueta de la columna. El orden importa: gana la primera regla que coincide.
COMPONENTES = [
    (r"^(nota final|promedio|p)$", "promedio"),
    (r"^(examen|exm|extrim|ex\.? ?m|ex\.? ?trim)", "examen"),
    (r"(^exo$|oral|interv)", "oral"),
    (r"(^r\.?c\.?$|cuad)", "cuaderno"),
    (r"(^r\.?l\.?$|libro)", "libro"),
    (r"pract", "practica"),
    (r"(^exp|exposic)", "exposicion"),
    (r"(papelografo|trabajo|proyecto|maqueta)", "trabajo"),
    (r"(conducta|convivencia|comparte|cmparte|puntualidad|respons)", "conducta"),
]
TIPOS = {"registro mensual": "registro_mensual", "examen mensual": "examen_mensual", "examen trimestral": "examen_trimestral"}


def plano(valor) -> str:
    """Minúsculas, sin tildes y sin espacios repetidos."""
    t = unicodedata.normalize("NFD", "" if valor is None or (isinstance(valor, float) and pd.isna(valor)) else str(valor).lower())
    return re.sub(r"\s+", " ", "".join(c for c in t if unicodedata.category(c) != "Mn")).strip()


def curso_oficial(texto):
    p = plano(texto)
    for inicio, nombre, area in CURSOS:
        if p.startswith(inicio):
            return nombre, area
    return None


def componente_de(etiqueta):
    p = plano(etiqueta)
    for patron, componente in COMPONENTES:
        if re.search(patron, p):
            return componente
    return None


def periodo_de(mes, tipo, anio):
    """Devuelve (código, nombre, orden). El examen trimestral cierra el primer trimestre (después de mayo)."""
    if tipo == "examen_trimestral":
        return f"{anio}-T1", f"Examen del primer trimestre de {anio}", anio + 0.055
    m = MESES.get(plano(mes))
    return (f"{anio}-{m:02d}", f"{NOMBRE_MES[m]} de {anio}", anio + m / 100) if m else None


def _capital(texto: str) -> str:
    return " ".join(p.capitalize() for p in str(texto).split())


def leer_consolidado(ruta: str) -> dict:
    """Devuelve {"notas": [...], "estudiantes": {clave: {...}}, "hallazgos": [...], "filas_origen": n}."""
    base = pd.read_excel(ruta, sheet_name="BASE_NOTAS")
    alumnos = pd.read_excel(ruta, sheet_name="ALUMNOS").set_index("ID_ALUMNO")
    hallazgos = {}

    def hallazgo(regla, severidad, detalle):
        h = hallazgos.setdefault(regla, {"regla": regla, "severidad": severidad, "detalle": detalle, "cantidad": 0})
        h["cantidad"] += 1

    estudiantes, notas, vistas = {}, [], set()
    for f in base.itertuples(index=False):
        nivel = plano(f.NIVEL)
        grado = f"{str(f.GRADO).strip()} {nivel.capitalize()}"
        ficha = alumnos.loc[f.ID_ALUMNO] if f.ID_ALUMNO in alumnos.index else None
        clave_nombre = plano(ficha["CLAVE_NORMALIZADA"] if ficha is not None else f.ALUMNO_ORIGINAL)
        completa = len(clave_nombre.split()) >= 2
        anio = int(f.ANO_LECTIVO) if not pd.isna(f.ANO_LECTIVO) else ANIO_POR_DEFECTO
        # Con nombre completo, la persona es la misma en cualquier año. Con solo el nombre de pila,
        # únicamente se puede distinguir dentro de su grado y año.
        clave = clave_nombre if completa else f"{clave_nombre}|{grado}|{anio}"
        if clave not in estudiantes:
            if completa and ficha is not None and not pd.isna(ficha.get("APELLIDOS")) and not pd.isna(ficha.get("NOMBRES")):
                nombres, apellido = _capital(str(ficha["NOMBRES"]).split()[0]), _capital(str(ficha["APELLIDOS"]).split()[0])
            elif completa:
                partes = _capital(clave_nombre).split()
                nombres, apellido = (partes[2] if len(partes) >= 3 else partes[-1]), partes[0]
            else:
                nombres, apellido = _capital(clave_nombre), None
            estudiantes[clave] = {"nombres": nombres, "apellido": apellido, "identidad": "completa" if completa else "solo_nombre", "matriculas": {}}
        estudiantes[clave]["matriculas"].setdefault(anio, (nivel, grado))

        tipo = TIPOS.get(plano(f.PERIODO_EVALUACION))
        periodo = periodo_de(f.MES, tipo, anio) if tipo else None
        curso = curso_oficial(f.ASIGNATURA)
        componente = componente_de(f.ACTIVIDAD)
        if pd.isna(f.NOTA):
            hallazgo("nota_vacia_o_textual", "aviso", "Casillas sin nota o con texto («no vino», «?»): no se cargan ni se asume cero.")
            continue
        if not periodo:
            hallazgo("periodo_no_identificado", "aviso", "Notas sin mes ni tipo de evaluación reconocible: no se cargan.")
            continue
        if not curso:
            hallazgo("curso_no_catalogado", "aviso", f"Curso fuera del catálogo («{str(f.ASIGNATURA)[:30]}»): no se carga.")
            continue
        if not componente:
            hallazgo("actividad_no_catalogada", "aviso", f"Actividad fuera del catálogo («{str(f.ACTIVIDAD)[:30]}»): no se carga.")
            continue
        if not 0 <= float(f.NOTA) <= 20:
            hallazgo("nota_fuera_de_rango", "critica", "Notas fuera de 0 a 20: no se cargan.")
            continue
        llave = (clave, curso[0], periodo[0], tipo, componente)
        if llave in vistas:
            hallazgo("nota_repetida_en_origen", "aviso", "Más de una nota del mismo tipo para el mismo estudiante, curso y periodo: se conserva la primera.")
            continue
        vistas.add(llave)
        fuente = str(f.FUENTE_ID)
        notas.append(
            {
                "clave": clave,
                "curso": curso[0],
                "area": curso[1],
                "periodo": periodo[0],
                "periodo_nombre": periodo[1],
                "periodo_orden": periodo[2],
                "anio": anio,
                "tipo": tipo,
                "componente": componente,
                "nota": float(f.NOTA),
                "fuente": fuente,
                "confianza": plano(f.CONFIANZA) if plano(f.CONFIANZA) in ("alta", "media") else "media",
                "validada": 0 if fuente.startswith("IMG") else 1,
            }
        )
    usados = {n["clave"] for n in notas}
    return {"notas": notas, "estudiantes": {k: v for k, v in estudiantes.items() if k in usados}, "hallazgos": list(hallazgos.values()), "filas_origen": len(base)}
