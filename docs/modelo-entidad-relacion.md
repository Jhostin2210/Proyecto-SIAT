# Modelo entidad-relación de la base de datos

Actividad A-2.1.1.2 del cronograma (paquete 1.2.1, entregable E-01). El diagrama sale de la definición de las tablas en `backend/etl/modelo_datos.py`, que sirve igual para PostgreSQL (producción) y SQLite (pruebas locales). Versión del 15/11/2026, con la tabla `competencias` (SC-14). Este documento no contiene datos de ningún estudiante.

## Diagrama

```mermaid
erDiagram
    estudiantes ||--o{ matriculas : "tiene"
    estudiantes ||--o{ notas : "obtiene"
    estudiantes ||--o{ competencias : "obtiene"
    estudiantes ||--o| perfiles : "tiene"
    estudiantes ||--o{ predicciones : "recibe"
    estudiantes ||--o{ asistencia : "registra"
    estudiantes ||--o{ incidencias : "registra"
    cursos ||--o{ notas : "califica"
    cursos ||--o{ competencias : "califica"
    periodos ||--o{ notas : "agrupa"
    periodos ||--o{ competencias : "agrupa"
    periodos ||--o{ predicciones : "agrupa"
    periodos ||--o{ asistencia : "agrupa"
    periodos ||--o{ incidencias : "agrupa"
    cargas ||--o{ notas : "trae"
    cargas ||--o{ competencias : "trae"
    predicciones ||--o{ alertas : "genera"

    estudiantes {
        int id PK
        string codigo "E-0001, único"
        string nombres
        string apellido "uno solo; sin DNI"
        string identidad "completa o solo_nombre"
    }
    matriculas {
        int id PK
        int estudiante_id FK
        int anio
        string nivel_educativo
        string grado
    }
    cursos {
        int id PK
        string nombre
        string area
    }
    periodos {
        int id PK
        string codigo "2026-03"
        string nombre
        int anio
        float orden
    }
    notas {
        int id PK
        int estudiante_id FK
        int curso_id FK
        int periodo_id FK
        string tipo_evaluacion
        string componente
        float nota "0 a 20"
        string fuente "CUBICOL"
        string confianza
        int validada
        int carga_id FK
    }
    competencias {
        int id PK
        int estudiante_id FK
        int curso_id FK
        int periodo_id FK
        string competencia
        float nota "0 a 20"
        int carga_id FK
    }
    cargas {
        int id PK
        datetime fecha
        string archivo
        string tipo_datos "reales o practica"
        int filas_origen
        int notas_leidas
        int notas_cargadas
        int notas_repetidas
        int notas_rechazadas
    }
    perfiles {
        int id PK
        int estudiante_id FK
        string variables "25 variables del modelo"
        string origen
    }
    predicciones {
        int id PK
        int estudiante_id FK
        int periodo_id FK
        string nivel_riesgo
        float probabilidad
        string version
        text motivo
    }
    alertas {
        int id PK
        int prediccion_id FK
        text mensaje
        int atendida
        datetime fecha
    }
    asistencia {
        int id PK
        int estudiante_id FK
        int periodo_id FK
        int inasistencias
    }
    incidencias {
        int id PK
        int estudiante_id FK
        int periodo_id FK
        datetime fecha
        string tipo
        text descripcion
    }
    usuarios {
        int id PK
        string nombre
        string email
        string rol
        string password_hash
    }
    calidad_datos {
        int id PK
        datetime fecha
        string regla
        string severidad
        int cantidad
        text detalle
    }
```

`perfiles` tiene en realidad 25 columnas, una por variable del modelo (sexo, edad, familia, hábitos, inasistencias…); en el diagrama se resumen en una.

## Tablas

| Tabla | Para qué | Filas en la base real al 15/11/2026 |
|---|---|---|
| `estudiantes` | Un registro por estudiante con su código único. Los nombres solo existen en la base privada. | 50 |
| `matriculas` | Año, nivel y grado de cada estudiante (cambia cada año). | 50 |
| `cursos` | Catálogo de cursos con su área. | 7 |
| `periodos` | Meses del año escolar, ordenados. | 6 (marzo a agosto de 2026) |
| `notas` | Promedio de cada curso en cada mes, con su fuente y su carga. | 807 |
| `competencias` | Promedio de cada competencia del curso en el mes (SC-14). | 2 892 |
| `cargas` | Bitácora de cada carga de datos: archivos, filas, notas cargadas, repetidas y rechazadas. | 5 |
| `calidad_datos` | Resultado de cada regla en cada ejecución de la validación. | 40 |
| `perfiles` | Variables del modelo que no son notas. | 50 |
| `predicciones` | Nivel de riesgo y probabilidad de cada estudiante en su último periodo. | 49 |
| `alertas` | Alertas generadas a partir de las predicciones (Sprint 4). | 0 |
| `asistencia` | Inasistencias por periodo (sin datos digitales todavía). | 0 |
| `incidencias` | Incidencias de conducta (sin datos digitales todavía). | 0 |
| `usuarios` | Cuentas con su rol: administrador, dirección, coordinación y docente (Sprint 4). | 0 |

## Reglas de integridad

- Un estudiante no puede tener dos notas del mismo curso, periodo, tipo y componente (`uq_nota`), ni dos promedios de la misma competencia en el mismo curso y periodo (`uq_competencia`).
- Las notas y competencias van de 0 a 20; los componentes, tipos de evaluación y niveles de riesgo solo aceptan los valores del catálogo.
- Al borrar un estudiante se borran sus notas, competencias, matrículas, perfil y predicciones (borrado en cascada).
