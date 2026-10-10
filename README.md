# SIA-T — Sistema Inteligente de Alerta Temprana

Prototipo del sistema de alerta temprana del bajo rendimiento académico para la I.E.P. Peruano Francés (Villa El Salvador, Lima). Proyecto del curso Gestión de Proyecto de TI, UNTELS.

- Página: https://proyecto-siat.vercel.app
- API: https://proyecto-siat.onrender.com (documentación en `/docs`; al estar en un plan gratuito, la primera respuesta puede tardar cerca de un minuto)
- Documentación de gestión del proyecto: https://peruano-frances-gti.vercel.app

## Estado: demostración

Este repositorio muestra el flujo completo del sistema —datos, modelo, nivel de riesgo y pantalla—, pero todavía con datos de ejemplo.

| Qué | Estado |
|---|---|
| Pantallas (inicio, estudiantes, riesgos y simulador) | Funcionan |
| API y carga del modelo | Funcionan |
| Estudiantes y notas | **De ejemplo** (ficticios); la base de datos está vacía |
| Modelo | **De demostración**: Random Forest entrenado con un conjunto de datos sintético |
| Métricas del modelo | No hay: se publicarán cuando se entrene con datos reales |
| Carga de datos del colegio, alertas por correo, usuarios y roles | Pendientes |

El modelo definitivo se entrena y valida con datos reales del colegio en el Sprint 3 del cronograma. `GET /api/estado` informa en todo momento de dónde salen los datos.

## Niveles de riesgo

Tres niveles, como define el alcance del proyecto. Los cortes son provisionales.

| Nivel | Probabilidad del modelo | Color |
|---|---|---|
| Riesgo bajo | menos de 0.50 | Verde |
| Riesgo medio | de 0.50 a 0.75 | Amarillo |
| Riesgo alto | 0.75 o más | Rojo |

## Estructura

| Carpeta | Contenido |
|---|---|
| `src/` | Página web (Vite + React + Tailwind). Es la que está publicada. |
| `backend/backend_api.py` | API (FastAPI): estudiantes, predicción, estado y métricas. |
| `backend/models/` | Modelo entrenado (`.pkl`). |
| `backend/data/` | Conjunto de datos sintético usado para el modelo de demostración. |
| `backend/database/schema.sql` | Esquema de la base de datos (PostgreSQL). |
| `backend/etl/` | Conexión a la base y borradores de los procesos de carga. |
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

## Endpoints de la API

| Método y ruta | Qué hace |
|---|---|
| `GET /api/estado` | Origen de los datos, si el modelo está cargado y niveles de riesgo |
| `GET /api/estudiantes` | Lista de estudiantes con su último nivel de riesgo |
| `POST /api/predecir` | Calcula el riesgo de un caso con el modelo |
| `GET /api/reporte-metricas` | Métricas del último entrenamiento, si existen |
| `GET /api/exportar-csv` | Exporta los datos de ejemplo en CSV |

## Cuidado con los datos

El repositorio es público. No subas listas de alumnos, notas reales, correos ni archivos `.env`.
