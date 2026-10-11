# SIA-T — Sistema Inteligente de Alerta Temprana

Prototipo del sistema de alerta temprana del bajo rendimiento académico para la I.E.P. Peruano Francés (Villa El Salvador, Lima). Proyecto del curso Gestión de Proyecto de TI, UNTELS.

- Página: https://proyecto-siat.vercel.app
- API: https://proyecto-siat.onrender.com (documentación en `/docs`; al estar en un plan gratuito, la primera respuesta puede tardar cerca de un minuto)
- Documentación de gestión del proyecto: https://peruano-frances-gti.vercel.app

## Estado

El sistema carga la base de notas del colegio, valida los datos cada noche y calcula el nivel de riesgo de cada estudiante con un modelo de Machine Learning entrenado y validado con datos reales.

| Qué | Estado |
|---|---|
| Base de datos (12 tablas) y carga de la base consolidada de notas | Construidas y probadas con los datos reales, en local: 3 878 notas de 173 estudiantes |
| Validación automática de los datos (10 reglas) | Construida; se ejecuta cada noche |
| Modelo de riesgo | **Entrenado y validado con datos reales** (519 casos de 146 estudiantes). Resultados y límites en [docs/modelo-y-validacion.md](docs/modelo-y-validacion.md) |
| Pantallas (inicio, estudiantes, ficha, riesgos y simulador) | Funcionan con los datos de la base y con el modelo |
| Datos de la demostración pública | **De práctica**: 135 estudiantes ficticios con la misma estructura que la base real. Los datos reales no se publican sin el consentimiento de los apoderados |
| Alertas por correo, usuarios y roles | Pendientes (Sprint 4) |

`GET /api/estado` informa en todo momento qué datos se muestran y de dónde sale el nivel de riesgo.

Más detalle en [docs/arquitectura.md](docs/arquitectura.md), [docs/datos-y-variables.md](docs/datos-y-variables.md), [docs/modelo-y-validacion.md](docs/modelo-y-validacion.md) y [docs/pruebas-sprint-2.md](docs/pruebas-sprint-2.md).

## El modelo, en corto

Predice si un estudiante desaprobará (menos de 11) el examen del periodo siguiente en un curso, con sus notas del periodo actual. Se validó con validación cruzada agrupada por estudiante, repetida 10 veces, y se comparó con una regla simple y una regresión logística.

| Modelo | Precisión media | AUC | Detecta | Aciertos de sus alertas |
|---|---|---|---|---|
| Regla simple | 0,27 | 0,71 | 76 % | 16 % |
| Regresión logística | 0,38 | 0,74 | 76 % | 19 % |
| **Bosque aleatorio (en uso)** | **0,40** | **0,75** | 75 % | 20 % |

Supera a las referencias por un margen moderado. Detecta a tres de cada cuatro estudiantes que desaprobarán, pero de cada cinco alertas una acierta: sirve para ordenar a quién mirar primero, no para afirmar quién va a desaprobar. Los datos son pocos (64 casos desaprobados) y la validación debe repetirse con más.

## Niveles de riesgo

Tres niveles, como define el alcance del proyecto: bajo (verde), medio (amarillo) y alto (rojo). Los cortes se fijaron con predicciones sobre datos que el modelo no vio:

| Nivel | Probabilidad | Qué pasó en la validación |
|---|---|---|
| Riesgo alto | 0,57 o más | Desaprobó 50 % (25 de 50 casos) |
| Riesgo medio | de 0,25 a 0,57 | Desaprobó 13 % (23 de 176) |
| Riesgo bajo | menos de 0,25 | Desaprobó 5 % (16 de 293) |

El riesgo de un estudiante es el promedio de sus cursos; con un curso en riesgo alto queda como mínimo en riesgo medio.

## Estructura

| Carpeta | Contenido |
|---|---|
| `src/` | Página web (Vite + React + Tailwind). Es la que está publicada. |
| `backend/backend_api.py` | API (FastAPI). |
| `backend/etl/modelo_datos.py` | Definición de las tablas. |
| `backend/etl/leer_consolidado.py`, `cargar_notas.py` | Lectura de la base consolidada, asignación de códigos y carga. |
| `backend/etl/validar_datos.py` | Reglas de calidad de los datos. |
| `backend/etl/variables.py` | Variables del modelo, a partir de las notas. |
| `backend/ml/entrenar_modelo.py` | Entrenamiento y validación del modelo. |
| `backend/etl/riesgo.py` | Nivel de riesgo de cada estudiante, con el modelo. |
| `backend/models/modelo_riesgo.joblib`, `backend/data/metrics_report.json` | Modelo entrenado y reporte de su validación. |
| `backend/etl/generar_datos_practica.py`, `backend/data/notas_practica.csv` | Datos de práctica de la demostración. |
| `backend/database/schema.sql` | El mismo esquema en SQL de PostgreSQL. |
| `.github/workflows/` | Validación nocturna de los datos. |
| `docs/` | Arquitectura, datos y variables, modelo y pruebas. |
| `frontend/` | Borrador anterior en Next.js; no está en uso. |

## Ejecutarlo en tu equipo

**API** (Python 3.12):

```powershell
cd backend
py -V:3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend_api:app --reload --port 8000
```

Queda en http://localhost:8000 (documentación en http://localhost:8000/docs).

**Página** (Node.js 20 o superior):

```powershell
npm install
npm run dev
```

Queda en http://localhost:3000. Por defecto consulta la API en línea. Para usar la API de tu equipo, crea un archivo `.env.local` con:

```
VITE_API_URL=http://localhost:8000
```

## Cargar datos, validar y entrenar

Desde `backend`, con el entorno activo:

```powershell
$env:SQLITE_PATH = "data/privado/sia_t_reales.db"            # base local con los datos reales; no se sube
python -m etl.cargar_notas "ruta\a\la base consolidada.xlsx"  # carga y calcula el nivel de riesgo
python -m etl.validar_datos                                   # reglas de calidad
python -m ml.entrenar_modelo                                  # entrena y valida el modelo (unos 10 minutos)
python -m etl.generar_datos_practica                          # vuelve a crear los datos de práctica
```

Sin `SQLITE_PATH` se usa `sia_t_local.db`. Para PostgreSQL, las variables descritas en [docs/arquitectura.md](docs/arquitectura.md).

## Endpoints de la API

| Método y ruta | Qué hace |
|---|---|
| `GET /api/estado` | Qué datos hay, periodos y origen del nivel de riesgo |
| `GET /api/estudiantes` | Estudiantes con promedios, nivel de riesgo, probabilidad y motivo |
| `GET /api/estudiantes/{codigo}` | Ficha: notas por curso y periodo |
| `GET /api/cargas` | Bitácora de cargas |
| `GET /api/calidad` | Última validación de los datos |
| `POST /api/calidad/ejecutar` | Ejecuta la validación |
| `GET /api/exportar-csv` | Exporta las notas por código |
| `POST /api/predecir` | Simulador: estima el riesgo de un caso con el modelo |
| `GET /api/reporte-metricas` | Reporte de la validación del modelo |

## Cuidado con los datos

El repositorio y la API son públicos. No subas listas de alumnos, notas reales, DNI, correos ni archivos `.env`.

- Cada estudiante se identifica por un código único. La base guarda nombres, un apellido y grado; nunca DNI, fecha de nacimiento ni datos de los apoderados.
- Los datos reales y la relación entre nombres y códigos viven solo en `backend/data/privado/`, que git ignora.
- La demostración pública usa datos de práctica. El modelo publicado se entrenó con datos reales, pero el archivo contiene los árboles del modelo, no las notas.
