# Arquitectura del sistema

Actividad A-0.1.1.4 del cronograma (Sprint 1). Describe las piezas del sistema, cómo circulan los datos y qué está construido.

## Vista general

```
 Registro de notas del colegio (Excel)
            │  python -m etl.cargar_notas        ← anonimiza: nombre → código
            ▼
 ┌──────────────────────┐   cada noche    ┌─────────────────────────┐
 │   Base de datos      │◄───────────────│ Validación automática    │
 │ PostgreSQL / SQLite  │                 │ (GitHub Actions)         │
 └──────────┬───────────┘                 └─────────────────────────┘
            │ nivel de riesgo: regla provisional hoy; modelo en el Sprint 3
            ▼
 ┌──────────────────────┐                 ┌─────────────────────────┐
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
| Nivel de riesgo | Regla provisional; después, modelo de Scikit-learn | API y tarea programada | Regla construida; modelo en el Sprint 3 |
| API | FastAPI | Render | Construida |
| Página web | Vite, React, Tailwind | Vercel | Construida |
| Alertas por correo, usuarios y roles | Por definir | — | Sprint 4 |

## Decisiones

- **Por lotes, no en tiempo real.** El riesgo se calcula al cargar datos y, más adelante, una vez por semana. La página solo lee resultados ya calculados, así que no depende de un servidor de cálculo siempre encendido.
- **Una sola definición del modelo de datos.** `backend/etl/modelo_datos.py` crea las tablas en PostgreSQL y en SQLite; `database/schema.sql` se genera a partir de él.
- **Sin nombres en la base.** El nombre se reemplaza por un código antes de cargar. La relación nombre–código queda en `backend/data/privado/`, que no se sube al repositorio.
- **Sin datos de relleno.** Si la base está vacía, la API lo dice. `GET /api/estado` informa siempre qué datos se muestran y de dónde sale el nivel de riesgo.
- **Datos de práctica para la demostración pública.** Los datos reales no se publican sin el consentimiento de los apoderados; la demostración usa notas inventadas con la misma estructura.

## Modelo de datos

Once tablas. Las principales:

| Tabla | Contenido |
|---|---|
| `estudiantes` | Código, grado y nivel educativo |
| `cursos`, `periodos` | Catálogos |
| `notas` | Una fila por estudiante, curso, periodo y componente (libro, cuaderno, conducta, examen) |
| `predicciones` | Nivel de riesgo por estudiante y periodo, con su origen (regla o modelo) y el motivo |
| `cargas` | Bitácora de cada carga, para reconciliar el archivo con la base |
| `calidad_datos` | Resultado de cada validación |
| `asistencia`, `incidencias` | Listas, pero vacías: el colegio aún las lleva en papel |
| `alertas`, `usuarios` | Para el Sprint 4; `usuarios` admite los cuatro roles y un administrador |

## Pasar a la base gestionada

1. Crear el proyecto de PostgreSQL y ejecutar `backend/database/schema.sql`.
2. En Render, definir `USE_SQLITE_FALLBACK=false`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` y `CARGAR_DATOS_PRACTICA=false`.
3. Definir los mismos secretos en GitHub para que la validación nocturna revise esa base.
4. Cargar los datos reales con `python -m etl.cargar_notas`, una vez resuelto el consentimiento de los apoderados.

Las claves nunca van en el repositorio.
