"""
SIA-T: modelo de datos (versión 2).

Las tablas se definen una sola vez aquí y sirven tanto para PostgreSQL (producción)
como para SQLite (pruebas locales y demostración). El archivo database/schema.sql
documenta el mismo esquema en SQL de PostgreSQL.

Decisiones del alcance del proyecto que este modelo refleja:
- Los estudiantes se identifican con un código; la base no guarda nombres.
- Tres niveles de riesgo: bajo, medio y alto.
- Cuatro roles de usuario más un administrador técnico.
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

COMPONENTES = ("libro", "cuaderno", "conducta", "examen")
NIVELES_RIESGO = ("Riesgo bajo", "Riesgo medio", "Riesgo alto")
ROLES = ("docente", "coordinacion", "psicologia", "direccion", "administrador")


def _en(columna: str, valores) -> str:
    return f"{columna} IN (" + ", ".join(f"'{v}'" for v in valores) + ")"


periodos = Table(
    "periodos",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("codigo", String(7), nullable=False, unique=True),  # '2025-11'
    Column("nombre", String(40), nullable=False),  # 'Noviembre de 2025'
)

estudiantes = Table(
    "estudiantes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("codigo", String(20), nullable=False, unique=True),  # código anónimo: 'E-0042'
    Column("grado", String(30), nullable=False),  # '3° Primaria'
    Column("nivel_educativo", String(12), nullable=False),
    CheckConstraint(_en("nivel_educativo", ("inicial", "primaria", "secundaria")), name="chk_nivel_educativo"),
)

cursos = Table(
    "cursos",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", String(60), nullable=False, unique=True),
)

notas = Table(
    "notas",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("estudiante_id", Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False),
    Column("curso_id", Integer, ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False),
    Column("periodo_id", Integer, ForeignKey("periodos.id", ondelete="CASCADE"), nullable=False),
    Column("componente", String(12), nullable=False),
    Column("nota", Float, nullable=False),
    Column("carga_id", Integer, ForeignKey("cargas.id")),
    UniqueConstraint("estudiante_id", "curso_id", "periodo_id", "componente", name="uq_nota"),
    CheckConstraint("nota >= 0 AND nota <= 20", name="chk_nota_rango"),
    CheckConstraint(_en("componente", COMPONENTES), name="chk_componente"),
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

predicciones = Table(
    "predicciones",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("estudiante_id", Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False),
    Column("periodo_id", Integer, ForeignKey("periodos.id", ondelete="CASCADE"), nullable=False),
    Column("nivel_riesgo", String(20), nullable=False),
    Column("probabilidad", Float),  # vacío cuando el nivel sale de la regla provisional
    Column("origen", String(20), nullable=False),  # 'regla_provisional' o 'modelo'
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
