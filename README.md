# SIA-T — Sistema Inteligente de Alerta Temprana

Prototipo del sistema de alerta temprana del bajo rendimiento académico para la I.E.P. Peruano Francés (Villa El Salvador, Lima). Proyecto del curso Gestión de Proyecto de TI, UNTELS.

- Página: https://proyecto-siat.vercel.app
- API: https://proyecto-siat.onrender.com (documentación en `/docs`; al estar en un plan gratuito, la primera respuesta puede tardar cerca de un minuto)
- Documentación de gestión del proyecto: https://peruano-frances-gti.vercel.app

## Estado

El sistema lee una base de datos, carga el registro de notas del colegio, valida los datos cada noche y muestra el nivel de riesgo de cada estudiante.

| Qué | Estado |
|---|---|
| Base de datos (11 tablas) y carga del registro de notas | Construidas y probadas con el registro real, en local |
| Validación automática de los datos | Construida; se ejecuta cada noche |
| Pantallas (inicio, estudiantes, ficha, riesgos y simulador) | Funcionan con los datos de la base |
| Datos de la demostración pública | **De práctica**: notas inventadas con la estructura del registro real. Los datos reales no se publican sin el consentimiento de los apoderados |
| Nivel de riesgo | **Regla provisional**, visible como tal. El modelo se entrena y valida con datos reales en el Sprint 3 |
| Simulador | Usa un modelo de demostración entrenado con datos sintéticos |
| Alertas por correo, usuarios y roles | Pendientes (Sprint 4) |

`GET /api/estado` informa en todo momento qué datos se muestran y de dónde sale el nivel de riesgo.

Más detalle en [docs/arquitectura.md](docs/arquitectura.md), [docs/datos-y-variables.md](docs/datos-y-variables.md) y [docs/pruebas-sprint-2.md](docs/pruebas-sprint-2.md).

## Niveles de riesgo

Tres niveles, como define el alcance del proyecto: bajo (verde), medio (amarillo) y alto (rojo).

Mientras no haya un modelo validado se usa esta regla provisional, con las notas de libro, cuaderno y examen del periodo:

| Nivel | Regla |
|---|---|
| Riesgo alto | Promedio general menor de 11, o promedio de exámenes menor de 9 |
| Riesgo medio | Promedio de exámenes menor de 11, o caída de 2 puntos o más frente al periodo anterior |
| Riesgo bajo | Los demás casos |

## Estructura

| Carpeta | Contenido |
|---|---|
| `src/` | Página web (Vite + React + Tailwind). Es la que está publicada. |
| `backend/backend_api.py` | API (FastAPI). |
| `backend/etl/modelo_datos.py` | Definición de las tablas. |
| `backend/etl/leer_registro.py`, `cargar_notas.py` | Lectura del registro de notas, anonimización y carga. |
| `backend/etl/validar_datos.py` | Reglas de calidad de los datos. |
| `backend/etl/riesgo.py` | Regla provisional del nivel de riesgo. |
| `backend/etl/generar_datos_practica.py`, `backend/data/notas_practica.csv` | Datos de práctica de la demostración. |
| `backend/database/schema.sql` | El mismo esquema en SQL de PostgreSQL. |
| `backend/models/` | Modelo de demostración del simulador. |
| `.github/workflows/` | Validación nocturna de los datos. |
| `docs/` | Arquitectura, datos y variables, y pruebas. |
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

## Cargar y validar datos

Desde `backend`, con el entorno activo:

```powershell
python -m etl.cargar_notas "rutaalegistro de notas.xlsx"   # registro del colegio: reemplaza nombres por códigos
python -m etl.validar_datos                                   # reglas de calidad
python -m etl.generar_datos_practica                          # vuelve a crear los datos de práctica
```

La relación entre nombres y códigos se guarda en `backend/data/privado/`, que no se sube al repositorio. Para cargar en una base aparte, define antes `SQLITE_PATH`; para usar PostgreSQL, las variables descritas en [docs/arquitectura.md](docs/arquitectura.md).

## Endpoints de la API

| Método y ruta | Qué hace |
|---|---|
| `GET /api/estado` | Qué datos hay, periodo actual y origen del nivel de riesgo |
| `GET /api/estudiantes` | Estudiantes (por código) con promedios y nivel de riesgo |
| `GET /api/estudiantes/{codigo}` | Ficha: notas por curso y periodo |
| `GET /api/cargas` | Bitácora de cargas |
| `GET /api/calidad` | Última validación de los datos |
| `POST /api/calidad/ejecutar` | Ejecuta la validación |
| `GET /api/exportar-csv` | Exporta las notas por código |
| `POST /api/predecir` | Simulador con el modelo de demostración |
| `GET /api/reporte-metricas` | Métricas del modelo, cuando existan |

## Cuidado con los datos

El repositorio es público. No subas listas de alumnos, notas reales, correos ni archivos `.env`.
