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
         │                    python -m ml.entrenar_modelo
         │  notas reales  ───────────────────────────────►  modelo_riesgo.joblib
         │                                                   metrics_report.json
         │  al cargar: variables → modelo → nivel de riesgo        │
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
| Modelo de riesgo | Scikit-learn (bosque aleatorio) | Se entrena en local con los datos reales; el archivo del modelo viaja con la API | Entrenado y validado; ver [modelo-y-validacion.md](modelo-y-validacion.md) |
| API | FastAPI | Render | Construida |
| Página web | Vite, React, Tailwind | Vercel | Construida |
| Alertas por correo, usuarios y roles | Por definir | — | Sprint 4 |

## Decisiones

- **Por lotes, no en tiempo real.** El riesgo se calcula al cargar datos y queda guardado en la tabla `predicciones`. La página solo lee resultados ya calculados.
- **Una sola definición del modelo de datos.** `backend/etl/modelo_datos.py` crea las tablas en PostgreSQL y en SQLite; `database/schema.sql` se genera a partir de él.
- **Una sola definición de las variables.** `backend/etl/variables.py` las calcula para el entrenamiento y para el cálculo del riesgo, de modo que el modelo recibe siempre lo mismo.
- **Código único por estudiante y mínimos datos personales.** Nombres, un apellido y grado; nunca DNI, fecha de nacimiento ni datos de los apoderados.
- **Los datos reales no salen del equipo del proyecto.** El repositorio y la API son públicos y aún no hay consentimiento de los apoderados; la demostración usa datos de práctica. El modelo sí se entrena con datos reales: el archivo publicado contiene los árboles del modelo, no las notas.
- **Sin datos de relleno ni métricas escritas a mano.** `GET /api/estado` informa qué datos se muestran y de dónde sale el nivel de riesgo; `GET /api/reporte-metricas` devuelve el archivo que escribió el entrenamiento.
- **Si no hay modelo, se dice.** Sin el archivo del modelo, el sistema usa una regla simple y lo rotula como tal.

## Modelo de datos

Doce tablas (`backend/database/schema.sql`):

| Tabla | Contenido |
|---|---|
| `estudiantes` | Código único, nombres, un apellido y si la identidad está completa |
| `matriculas` | Año, nivel y grado de cada estudiante; una fila por año, así el mismo estudiante puede pasar de grado |
| `cursos` | Catálogo de cursos, cada uno con su área |
| `periodos` | Meses y trimestres, con un orden que permite saber cuál sigue a cuál |
| `notas` | Una fila por estudiante, curso, periodo, tipo de evaluación y tipo de nota. Guarda de qué fuente salió, la confianza y si está validada |
| `predicciones` | Nivel de riesgo por estudiante y periodo, con la probabilidad, el origen (modelo o regla), la versión y el motivo |
| `cargas` | Bitácora de cada carga, para reconciliar el archivo con la base |
| `calidad_datos` | Resultado de cada validación |
| `asistencia`, `incidencias` | Listas, pero vacías: el colegio aún las lleva en papel |
| `alertas`, `usuarios` | Para el Sprint 4; `usuarios` admite los cuatro roles y un administrador |

```
 estudiantes ──< matriculas
      │
      ├──< notas >── cursos
      │      └────── periodos
      ├──< asistencia, incidencias
      └──< predicciones ──< alertas

 cargas ──< notas          calidad_datos y usuarios (independientes)
```

Restricciones que la base hace cumplir: nota entre 0 y 20; una sola nota por estudiante, curso, periodo, tipo de evaluación y tipo de nota; una sola matrícula por estudiante y año; nivel de riesgo solo bajo, medio o alto.

## Pasar a la base gestionada

1. Crear el proyecto de PostgreSQL y ejecutar `backend/database/schema.sql`.
2. En Render, definir `USE_SQLITE_FALLBACK=false`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` y `CARGAR_DATOS_PRACTICA=false`.
3. Definir los mismos secretos en GitHub para que la validación nocturna revise esa base.
4. Cargar los datos reales con `python -m etl.cargar_notas`, una vez resuelto el consentimiento de los apoderados y restringido el acceso a la API con usuarios y roles.

Las claves nunca van en el repositorio.
