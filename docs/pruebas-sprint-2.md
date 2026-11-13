# Pruebas del entregable E-01: integración y limpieza de datos

Paquetes 1.2.1 y 1.2.2 de la EDT, requisitos REQ-01 y REQ-02, casos de prueba CP-01 a CP-08 de la matriz de trazabilidad. Ejecutadas el 10/10/2026 con la base consolidada de notas del colegio y repetidas el 13/11/2026, cuando la base se rearmó solo con las exportaciones de Cubicol (a pedido del Product Owner; la base anterior quedó como respaldo).

## Cómo repetirlas

Desde la carpeta `backend`, con el entorno de Python activo:

```powershell
# Carga de la base consolidada en una base local que no se sube al repositorio
$env:SQLITE_PATH = "data/privado/sia_t_reales.db"
python -m etl.cargar_notas "ruta\a\la base consolidada.xlsx"
python -m etl.cargar_notas "ruta\a\la base consolidada.xlsx"   # segunda vez: no debe cargar nada nuevo
python -m etl.validar_datos

# Exportaciones de Cubicol («Registro auxiliar», .xls): una carga por fecha de entrega
python -m etl.cargar_cubicol "ruta\a\la carpeta con los .xls" --como-base   # solo la primera vez, con la base vacía
python -m etl.cargar_cubicol "ruta\a\la carpeta con los .xls"               # cargas siguientes
```

## Resultados

| Caso | Qué comprueba | Resultado | Evidencia |
|---|---|---|---|
| CP-01 | Se consolidan todos los registros válidos | **Aprobado** | Base nueva (13/11/2026): 402 notas válidas leídas y 402 cargadas, de 411 filas de 60 exportaciones de Cubicol; los 9 promedios vacíos o con texto se reportan con su motivo. Antes, con la base consolidada: 3 878 de 3 937 filas |
| CP-02 | No se generan duplicados | **Aprobado** | Segunda carga de las mismas 60 exportaciones (13/11/2026): 0 cargadas, 402 «ya estaban»; regla `notas_duplicadas` correcta |
| CP-03 | Reconciliación entre el origen y la base en tres fechas | **En curso (2 de 3 fechas)** | Carga 2, 13/11/2026: base rearmada con 60 exportaciones (se suman 1.° a 3.° de secundaria), 402 notas de 48 estudiantes, reconciliación correcta. Carga 1, 07/11/2026, en la base anterior: 45 exportaciones de Cubicol (Matemática y Cultura General de 3.° a 6.° de primaria, marzo a mayo), 282 filas, 237 notas cargadas de 20 estudiantes, reconciliación correcta. 45 notas de 4 estudiantes sin enlazar con certeza quedan sin cargar hasta revisarlas. Faltan dos cargas en otras fechas |
| CP-04 | Integridad referencial | **Aprobado** | Reglas `referencias_huerfanas` y `estudiantes_sin_matricula` correctas |
| CP-05 | La validación corre cada noche 15 días seguidos sin fallas | **Aprobado** | Una ejecución programada por noche desde el 11/10/2026, sin fallas: 15 seguidas el 25/10/2026 y 28 al 07/11/2026 (pestaña Actions del repositorio) |
| CP-06 | Detecta duplicados | **Aprobado** | 33 notas repetidas en el origen: la carga conserva la primera y las cuenta; la validación revisa la base |
| CP-07 | Detecta vacíos críticos | **Aprobado** | 7 casillas vacías o con texto y 15 notas sin periodo identificable detectadas y no cargadas; 56 notas en cero y 62 cursos sin examen avisados |
| CP-08 | El resultado queda disponible para el responsable de TI | **Aprobado** | Pantalla «Datos» del administrador (cargas, reconciliación, reglas e historial), `GET /api/calidad`, `GET /api/calidad/historial` y reporte de cada ejecución nocturna |

La validación tiene diez reglas: cinco críticas (detienen la tarea nocturna) y cinco avisos. Con la base real: ninguna crítica falla y hay cinco avisos, detallados en [datos-y-variables.md](datos-y-variables.md). Con los datos de práctica: ninguna falla y ningún aviso.

## Lo que estas pruebas no cubren

- La base consolidada reúne registros de pocos docentes. Las exportaciones de Cubicol tienen su propio lector (`etl/leer_cubicol.py`): enlaza a cada estudiante con su código dentro de su grado y deja sin cargar, para revisarlos, a los que no coinciden con certeza.
- Con la base consolidada había estudiantes registrados dos veces (nombre completo y nombre de pila) y 1 426 notas de fotografías por validar. Al rearmar la base solo con Cubicol (13/11/2026) ambos problemas desaparecen.
- Las exportaciones de Cubicol traen el promedio mensual de cada curso, no una nota de examen aparte (aviso `cursos_sin_examen`), y aún no cubren 1.° y 2.° de primaria ni 4.° y 5.° de secundaria.
- En la demostración pública la base tiene datos de práctica. La carga de datos reales a la nube espera la base gestionada, el control de acceso y el consentimiento de los apoderados.
- El criterio de 15 noches seguidas (CP-05) y la reconciliación en tres fechas (CP-03) necesitan tiempo real de operación.
