# Arquitectura del sistema

Actividad A-0.1.1.4 del cronograma. Describe las piezas del sistema, cómo circulan los datos y qué está construido.

## Vista general

```
 Base consolidada de notas (Excel)
            │  python -m etl.cargar_notas        ← asigna un código único; no lee el DNI
            ▼
 ┌──────────────────────┐   cada noche    ┌─────────────────────────┐
 │   Base de datos      │◄───────────────│ Validación automática    │
 │ PostgreSQL / SQLite  │                 │ (GitHub Actions)         │
 └───────┬──────────────┘                 └─────────────────────────┘
         │      base pública ──► python -m ml.entrenar_red_neuronal
         │                               └──► red_neuronal_riesgo.joblib
         │                                    red_neuronal_report.json
         │  al cargar: notas + perfil → red → nivel de riesgo      │
         ▼                                                         │
 ┌──────────────────────┐                 ┌────────────────────────▼┐
 │  API (FastAPI)       │────────────────►│ Página web (React)       │
 │  Render              │   JSON          │ Vercel                   │
 └──────────────────────┘                 └─────────────────────────┘
```

## Piezas

| Pieza | Tecnología | Dónde corre | Estado |
|---|---|---|---|
| Carga de datos | Python, openpyxl, SQLAlchemy | Equipo del responsable de datos | Construida |
| Base de datos | PostgreSQL en producción; SQLite en pruebas y demostración | Servicio gestionado (por contratar) | Esquema construido; hoy la demostración usa SQLite |
| Validación automática | Python, tarea programada de GitHub Actions | GitHub | Construida |
| Modelo de riesgo | Red neuronal de scikit-learn | Se entrena con una base pública; el archivo del modelo viaja con la API | Entrenado y probado; ver [modelo-y-validacion.md](modelo-y-validacion.md) |
| Informe, reporte PDF y comunicado | Python, ReportLab | API | Construidos |
| API | FastAPI | Render | Construida |
| Página web | Vite, React, Tailwind, Recharts | Vercel | Construida: inicio, aulas, estudiantes, ficha, evaluación y modelo |
| Alertas por correo, registro de seguimiento, usuarios y roles | Por definir | — | Sprint 4 |

## Decisiones

- **Por lotes, no en tiempo real.** El riesgo se calcula al cargar datos y queda guardado en la tabla `predicciones`. La página solo lee resultados ya calculados.
- **Una sola definición del modelo de datos.** `backend/etl/modelo_datos.py` crea las tablas en PostgreSQL y en SQLite; `database/schema.sql` se genera a partir de él.
- **El modelo se entrena fuera y se aplica dentro.** La red se entrena y se prueba con una base pública; el archivo entrenado es el que calcula el riesgo con los datos del colegio. `backend/etl/variables.py` y `backend/etl/perfil.py` preparan las entradas siempre de la misma manera.
- **Del curso al estudiante.** El modelo evalúa cada curso; `backend/etl/informe.py` junta los cursos, reconoce el patrón y propone acciones.
- **Código único por estudiante.** Nombres, un apellido y grado, más el perfil que usa el modelo; nunca DNI, fecha de nacimiento ni teléfonos.
- **Los datos reales no salen del equipo del proyecto.** El repositorio y la API son públicos y aún no hay consentimiento de los apoderados; la demostración usa datos de práctica. Del colegio solo se publican cifras agregadas de la comprobación del modelo.
- **El comunicado al apoderado lo envía una persona.** El sistema redacta el mensaje y abre WhatsApp; el tutor lo revisa y lo envía. Solo se ofrece en riesgo alto, y el número no se guarda.
- **Sin métricas escritas a mano.** `GET /api/estado` informa qué datos se muestran y de dónde sale el nivel de riesgo; `GET /api/modelo` devuelve los archivos que escribieron el entrenamiento y la comprobación.
- **Si no hay modelo, se dice.** Sin el archivo del modelo, el sistema usa una regla por nota y lo rotula como tal.

## Modelo de datos

Trece tablas (`backend/database/schema.sql`):

| Tabla | Contenido |
|---|---|
| `estudiantes` | Código único, nombres, un apellido y si la identidad está completa |
| `matriculas` | Año, nivel y grado de cada estudiante; una fila por año, así el mismo estudiante puede pasar de grado |
| `perfiles` | Lo que el modelo usa además de las notas: historial, familia y hábitos. Una fila por estudiante, con el origen de los datos |
| `cursos` | Catálogo de cursos, cada uno con su área |
| `periodos` | Meses y trimestres, con un orden que permite saber cuál sigue a cuál |
| `notas` | Una fila por estudiante, curso, periodo, tipo de evaluación y tipo de nota. Guarda de qué fuente salió, la confianza y si está validada |
| `predicciones` | Nivel de riesgo general por estudiante y periodo, con la probabilidad, el origen (modelo o regla), la versión y el resumen |
| `cargas` | Bitácora de cada carga, para reconciliar el archivo con la base |
| `calidad_datos` | Resultado de cada validación |
| `asistencia`, `incidencias` | Listas, pero vacías: el colegio aún las lleva en papel |
| `alertas`, `usuarios` | Para el Sprint 4; `usuarios` admite los cuatro roles y un administrador |

```
 estudiantes ──< matriculas
      ├─── perfiles (uno por estudiante)
      │
      ├──< notas >── cursos
      │      └────── periodos
      ├──< asistencia, incidencias
      └──< predicciones ──< alertas

 cargas ──< notas          calidad_datos y usuarios (independientes)
```

Restricciones que la base hace cumplir: nota entre 0 y 20; una sola nota por estudiante, curso, periodo, tipo de evaluación y tipo de nota; una sola matrícula por estudiante y año; un solo perfil por estudiante; nivel de riesgo solo bajo, medio o alto.

## Pasar a la base gestionada

1. Crear el proyecto de PostgreSQL y ejecutar `backend/database/schema.sql`.
2. En Render, definir `USE_SQLITE_FALLBACK=false`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` y `CARGAR_DATOS_PRACTICA=false`.
3. Definir los mismos secretos en GitHub para que la validación nocturna revise esa base.
4. Cargar los datos reales con `python -m etl.cargar_notas`, una vez resuelto el consentimiento de los apoderados y restringido el acceso a la API con usuarios y roles.

Las claves nunca van en el repositorio.
