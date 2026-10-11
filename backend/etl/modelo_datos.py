"""
SIA-T: modelo de datos (versión 3).

Las tablas se definen una sola vez aquí y sirven tanto para PostgreSQL (producción)
como para SQLite (pruebas locales y demostración). database/schema.sql documenta el
mismo esquema en SQL de PostgreSQL y se genera desde este archivo.

Criterios:
- Cada estudiante tiene un identificador único (código). Se guardan su nombre y un apellido;
  no se guardan DNI, fecha de nacimiento ni datos de contacto.
- La matrícula (año, nivel y grado) va aparte, porque un estudiante cambia de grado cada año.
- Cada nota conserva de dónde salió, qué tan confiable es y si ya fue validada.
- Tres niveles de riesgo: bajo, medio y alto. Cuatro roles de usuario más un administrador.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)

metadata = MetaData()

# Tipos de nota. «promedio» es un valor calculado por el docente: se guarda, pero el modelo no lo usa.
COMPONENTES = ("examen", "cuaderno", "libro", "oral", "practica", "exposicion", "trabajo", "conducta", "promedio")
TIPOS_EVALUACION = ("registro_mensual", "examen_mensual", "examen_trimestral")
NIVELES_RIESGO = ("Riesgo bajo", "Riesgo medio", "Riesgo alto")
ROLES = ("docente", "coordinacion", "psicologia", "direccion", "administrador")


def _en(columna: str, valores) -> str:
    return f"{columna} IN (" + ", ".join(f"'{v}'" for v in valores) + ")"


estudiantes = Table(
    "estudiantes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("codigo", String(20), nullable=False, unique=True),  # identificador único: 'E-0042'
    Column("nombres", String(60), nullable=False),
    Column("apellido", String(60)),  # vacío cuando la fuente solo trae el nombre de pila
    Column("identidad", String(12), nullable=False, default="completa"),
    CheckConstraint(_en("identidad", ("completa", "solo_nombre")), name="chk_identidad"),
)

matriculas = Table(
    "matriculas",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("estudiante_id", Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False),
    Column("anio", Integer, nullable=False),
    Column("nivel_educativo", String(12), nullable=False),
    Column("grado", String(20), nullable=False),  # '3° Primaria'
    UniqueConstraint("estudiante_id", "anio", name="uq_matricula"),
    CheckConstraint(_en("nivel_educativo", ("inicial", "primaria", "secundaria")), name="chk_nivel_educativo"),
)

cursos = Table(
    "cursos",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", String(60), nullable=False, unique=True),
    Column("area", String(40), nullable=False),
)

periodos = Table(
    "periodos",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("codigo", String(8), nullable=False, unique=True),  # '2026-03' o '2026-T1'
    Column("nombre", String(40), nullable=False),
    Column("anio", Integer, nullable=False),
    Column("orden", Float, nullable=False),  # para ordenar: 2026.03, 2026.055 (trimestral)...
)

notas = Table(
    "notas",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("estudiante_id", Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False),
    Column("curso_id", Integer, ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False),
    Column("periodo_id", Integer, ForeignKey("periodos.id", ondelete="CASCADE"), nullable=False),
    Column("tipo_evaluacion", String(20), nullable=False),
    Column("componente", String(12), nullable=False),
    Column("nota", Float, nullable=False),
    Column("fuente", String(12), nullable=False),  # 'XLS01', 'IMG07', 'PRACTICA'...
    Column("confianza", String(6), nullable=False, default="alta"),
    Column("validada", Integer, nullable=False, default=1),  # 0: transcripción pendiente de cotejar
    Column("carga_id", Integer, ForeignKey("cargas.id")),
    UniqueConstraint("estudiante_id", "curso_id", "periodo_id", "tipo_evaluacion", "componente", name="uq_nota"),
    CheckConstraint("nota >= 0 AND nota <= 20", name="chk_nota_rango"),
    CheckConstraint(_en("componente", COMPONENTES), name="chk_componente"),
    CheckConstraint(_en("tipo_evaluacion", TIPOS_EVALUACION), name="chk_tipo_evaluacion"),
    CheckConstraint(_en("confianza", ("alta", "media")), name="chk_confianza"),
)

# Perfil del estudiante: lo que el modelo usa además de las notas (historial, familia y hábitos).
# Los valores usan los códigos de la base con que se entrenó el modelo; etl/perfil.py los describe.
perfiles = Table(
    "perfiles",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("estudiante_id", Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False, unique=True),
    Column("sexo", String(1)),
    Column("edad", Integer),
    Column("tam_familia", String(3)),
    Column("padres_juntos", String(1)),
    Column("educ_madre", Integer),
    Column("educ_padre", Integer),
    Column("ocup_madre", String(10)),
    Column("ocup_padre", String(10)),
    Column("apoderado", String(10)),
    Column("tiempo_viaje", Integer),
    Column("horas_estudio", Integer),
    Column("cursos_desaprobados", Integer),
    Column("apoyo_escolar", String(3)),
    Column("apoyo_familiar", String(3)),
    Column("clases_pagadas", String(3)),
    Column("actividades", String(3)),
    Column("internet", String(3)),
    Column("pareja", String(3)),
    Column("relacion_familiar", Integer),
    Column("tiempo_libre", Integer),
    Column("salidas", Integer),
    Column("salud", Integer),
    Column("inasistencias", Integer),
    Column("origen", String(10), nullable=False, default="colegio"),
    Column("actualizado", DateTime, server_default=func.now()),
    CheckConstraint(_en("origen", ("colegio", "generado")), name="chk_origen_perfil"),
)

# Asistencia e incidencias: el colegio todavía las lleva en papel; las tablas quedan listas.
asistencia = Table(
    "asistencia",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("estudiante_id", Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False),
    Column("periodo_id", Integer, ForeignKey("periodos.id", ondelete="CASCADE"), nullable=False),
    Column("inasistencias", Integer, nullable=False, default=0),
    UniqueConstraint("estudiante_id", "periodo_id", name="uq_asistencia"),
    CheckConstraint("inasistencias >= 0", name="chk_inasistencias"),
)

incidencias = Table(
    "incidencias",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("estudiante_id", Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False),
    Column("periodo_id", Integer, ForeignKey("periodos.id", ondelete="CASCADE"), nullable=False),
    Column("fecha", DateTime),
    Column("tipo", String(40), nullable=False),
    Column("descripcion", Text),
)

# Nivel de riesgo general por estudiante y periodo. «probabilidad» es el promedio de sus cursos.
predicciones = Table(
    "predicciones",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("estudiante_id", Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False),
    Column("periodo_id", Integer, ForeignKey("periodos.id", ondelete="CASCADE"), nullable=False),
    Column("nivel_riesgo", String(20), nullable=False),
    Column("probabilidad", Float),
    Column("origen", String(20), nullable=False),  # 'modelo' o 'regla_provisional'
    Column("version", String(50), nullable=False),
    Column("motivo", Text),
    Column("fecha", DateTime, server_default=func.now()),
    UniqueConstraint("estudiante_id", "periodo_id", "origen", name="uq_prediccion"),
    CheckConstraint(_en("nivel_riesgo", NIVELES_RIESGO), name="chk_nivel_riesgo"),
    CheckConstraint(_en("origen", ("regla_provisional", "modelo")), name="chk_origen"),
)

alertas = Table(
    "alertas",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("prediccion_id", Integer, ForeignKey("predicciones.id", ondelete="CASCADE"), nullable=False),
    Column("mensaje", Text, nullable=False),
    Column("atendida", Integer, nullable=False, default=0),
    Column("fecha", DateTime, server_default=func.now()),
)

usuarios = Table(
    "usuarios",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", String(100), nullable=False),
    Column("email", String(100), nullable=False, unique=True),
    Column("rol", String(20), nullable=False),
    Column("password_hash", String(255), nullable=False),
    CheckConstraint(_en("rol", ROLES), name="chk_rol"),
)

# Bitácora de cada carga de datos: permite reconciliar el origen con la base.
cargas = Table(
    "cargas",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fecha", DateTime, server_default=func.now()),
    Column("archivo", String(200), nullable=False),
    Column("tipo_datos", String(12), nullable=False),  # 'reales' o 'practica'
    Column("filas_origen", Integer, nullable=False),
    Column("notas_leidas", Integer, nullable=False),
    Column("notas_cargadas", Integer, nullable=False),
    Column("notas_repetidas", Integer, nullable=False),
    Column("notas_rechazadas", Integer, nullable=False),
    CheckConstraint(_en("tipo_datos", ("reales", "practica")), name="chk_tipo_datos"),
)

# Resultado de cada ejecución de la validación automática.
calidad_datos = Table(
    "calidad_datos",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fecha", DateTime, server_default=func.now()),
    Column("regla", String(60), nullable=False),
    Column("severidad", String(10), nullable=False),  # 'critica', 'aviso' o 'correcta'
    Column("cantidad", Integer, nullable=False),
    Column("detalle", Text),
)


def crear_tablas(engine) -> None:
    """Crea las tablas que falten. No borra datos."""
    metadata.create_all(engine)
