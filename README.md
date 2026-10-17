# SIA-T — Sistema Inteligente de Alerta Temprana

Prototipo del sistema de alerta temprana del bajo rendimiento académico para la I.E.P. Peruano Francés (Villa El Salvador, Lima). Proyecto del curso Gestión de Proyecto de TI, UNTELS.

- Página: https://proyecto-siat.vercel.app
- API: https://proyecto-siat.onrender.com (documentación en `/docs`; al estar en un plan gratuito, la primera respuesta puede tardar cerca de un minuto)
- Documentación de gestión del proyecto: https://peruano-frances-gti.vercel.app

## Estado

El sistema carga la base de notas del colegio, valida los datos cada noche y calcula el nivel de riesgo de cada estudiante con una red neuronal.

| Qué | Estado |
|---|---|
| Base de datos (13 tablas) y carga de la base consolidada de notas | Construidas y probadas con los datos reales, en local: 3 878 notas de 173 estudiantes |
| Validación automática de los datos (10 reglas) | Construida; se ejecuta cada noche |
| Modelo de riesgo | **Red neuronal** entrenada y probada con una base pública, y aplicada después a los datos del colegio. Resultados y límites en [docs/modelo-y-validacion.md](docs/modelo-y-validacion.md) |
| Página | Inicio con indicadores, aulas, estudiantes, ficha con informe y acciones, evaluación de un caso, vista del modelo y pantalla «Datos» con la evidencia del entregable E-01 |
| Reporte del estudiante en PDF y exportación por aula | Construidos |
| Comunicado al apoderado | El sistema lo redacta y abre WhatsApp; el tutor lo revisa y lo envía. Solo en riesgo alto |
| Datos de la demostración pública | **De práctica**: 135 estudiantes ficticios con la misma estructura que la base real. Los datos reales no se publican sin el consentimiento de los apoderados |
| Alertas por correo, registro de seguimiento, usuarios y roles | Pendientes (Sprint 4) |

`GET /api/estado` informa en todo momento qué datos se muestran y de dónde sale el nivel de riesgo.

Más detalle en [docs/arquitectura.md](docs/arquitectura.md), [docs/datos-y-variables.md](docs/datos-y-variables.md), [docs/modelo-y-validacion.md](docs/modelo-y-validacion.md) y [docs/pruebas-sprint-2.md](docs/pruebas-sprint-2.md).

## El modelo, en corto

Una red neuronal (35-32-16-8-1, ReLU, Adam) que estima, para cada curso, la probabilidad de que al estudiante le vaya mal. Se entrena con la base pública *Student Performance* (UCI; 1 044 registros de secundaria de Portugal, con notas de 0 a 20) y usa 25 variables: las notas de los dos periodos anteriores, inasistencias, historial, familia y hábitos.

| Dónde se mide | Exactitud | AUC | Detecta | Aciertos de sus alertas |
|---|---|---|---|---|
| Prueba con 209 registros de la base pública que la red no vio | 83,7 % | 0,95 | 87 % | 59 % |

El archivo ya entrenado se aplica a los datos del colegio, que no participan del entrenamiento.

## Niveles de riesgo

Tres niveles, como define el alcance del proyecto: bajo (verde), medio (amarillo) y alto (rojo). La probabilidad de la red se divide con dos cortes, que en un estudiante típico equivalen a estas notas:

| Nivel | Probabilidad | Nota equivalente | Qué pasó en el colegio en el periodo siguiente |
|---|---|---|---|
| Riesgo alto | 0,69 o más | menor de 10 | Le fue mal a 55 % (11 de 20 casos) |
| Riesgo medio | de 0,05 a 0,69 | de 10 a 14 | Le fue mal a 14 % (23 de 159) |
| Riesgo bajo | menos de 0,05 | de 15 a 20 | Le fue mal a 3 % (10 de 379) |

El riesgo general de un estudiante junta sus cursos: basta un curso en riesgo alto para que quede en riesgo alto. El nivel alto es una alerta razonable; el nivel medio acierta poco y sirve como lista de seguimiento. Es una estimación de apoyo para el tutor: no reemplaza el criterio del docente.

## Estructura

| Carpeta | Contenido |
|---|---|
| `src/` | Página web (Vite + React + Tailwind). `App.tsx` es la estructura; cada pantalla está en `src/vistas/`. |
| `backend/backend_api.py` | API (FastAPI). |
| `backend/etl/modelo_datos.py` | Definición de las tablas. |
| `backend/etl/leer_consolidado.py`, `cargar_notas.py` | Lectura de la base consolidada, asignación de códigos y carga. |
| `backend/etl/validar_datos.py` | Reglas de calidad de los datos. |
| `backend/etl/variables.py`, `perfil.py` | Entradas del modelo: nota por curso y perfil del estudiante. |
| `backend/ml/entrenar_red_neuronal.py` | Entrenamiento y prueba de la red neuronal. |
| `backend/ml/comprobar_en_colegio.py` | Aplica la red a los datos reales y compara con lo que pasó después. |
| `backend/etl/riesgo.py`, `informe.py` | Nivel de riesgo por curso y general, patrones, acciones y comunicado. |
| `backend/etl/reporte_pdf.py` | Reporte del estudiante en PDF. |
| `backend/models/red_neuronal_riesgo.joblib` | La red entrenada, con su escalador y sus cortes. |
| `backend/data/red_neuronal_report.json`, `aplicacion_colegio.json` | Resultados del entrenamiento y de la comprobación. |
| `backend/data/publica/` | Base pública de entrenamiento, con su fuente y licencia. |
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
python -m ml.entrenar_red_neuronal                            # entrena y prueba la red con la base pública

$env:SQLITE_PATH = "data/privado/sia_t_reales.db"            # base local con los datos reales; no se sube
python -m etl.cargar_notas "ruta\a\la base consolidada.xlsx"  # carga y calcula el nivel de riesgo
python -m etl.validar_datos                                   # reglas de calidad
python -m ml.comprobar_en_colegio                             # compara los niveles con lo que pasó después
python -m etl.generar_datos_practica                          # vuelve a crear los datos de práctica
```

Sin `SQLITE_PATH` se usa `sia_t_local.db`. Para PostgreSQL, las variables descritas en [docs/arquitectura.md](docs/arquitectura.md).

## Endpoints de la API

| Método y ruta | Qué hace |
|---|---|
| `GET /api/estado` | Qué datos hay, periodos y origen del nivel de riesgo |
| `GET /api/estudiantes` | Estudiantes con su nivel de riesgo general, de mayor a menor |
| `GET /api/estudiantes/{codigo}` | Ficha: informe, cursos, historial y perfil |
| `GET /api/estudiantes/{codigo}/reporte.pdf` | Reporte del estudiante en PDF |
| `GET /api/aulas` | Resumen por aula |
| `POST /api/aulas/evaluar` | Vuelve a evaluar con el modelo a un aula o a todas |
| `GET /api/aulas/exportar.csv` | Exporta el resultado de un aula o de todas |
| `GET /api/formulario` y `POST /api/evaluar` | Evalúa un caso con el modelo, sin guardar nada |
| `GET /api/modelo` | Cómo se entrenó y probó el modelo, y su aplicación en el colegio |
| `GET /api/cargas`, `GET /api/calidad`, `GET /api/calidad/historial`, `POST /api/calidad/ejecutar` | Bitácora de cargas, validación de los datos e historial de validaciones |
| `GET /api/exportar-csv` | Exporta las notas por código |

## Cuidado con los datos

El repositorio y la API son públicos. No subas listas de alumnos, notas reales, DNI, teléfonos, correos ni archivos `.env`.

- Cada estudiante se identifica por un código único. La base guarda nombres, un apellido, grado y el perfil que usa el modelo; nunca DNI ni teléfonos.
- El perfil incluye datos de la familia y de salud, que son datos sensibles: cargarlos del colegio requiere el consentimiento de los apoderados.
- Los datos reales y la relación entre nombres y códigos viven solo en `backend/data/privado/`, que git ignora.
- La demostración pública usa datos de práctica. Del colegio solo se publican cifras agregadas.
- El número de WhatsApp del apoderado se escribe al momento de enviar y no se guarda.
