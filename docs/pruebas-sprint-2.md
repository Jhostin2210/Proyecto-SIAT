# Pruebas del entregable E-01: integración y limpieza de datos

Paquetes 1.2.1 y 1.2.2 de la EDT, requisitos REQ-01 y REQ-02, casos de prueba CP-01 a CP-08 de la matriz de trazabilidad. Ejecutadas el 10/10/2026 en un equipo del proyecto, con la base consolidada de notas del colegio.

## Cómo repetirlas

Desde la carpeta `backend`, con el entorno de Python activo:

```powershell
# Carga de la base consolidada en una base local que no se sube al repositorio
$env:SQLITE_PATH = "data/privado/sia_t_reales.db"
python -m etl.cargar_notas "ruta\a\la base consolidada.xlsx"
python -m etl.cargar_notas "ruta\a\la base consolidada.xlsx"   # segunda vez: no debe cargar nada nuevo
python -m etl.validar_datos
```

## Resultados

| Caso | Qué comprueba | Resultado | Evidencia |
|---|---|---|---|
| CP-01 | Se consolidan todos los registros válidos | **Aprobado** | 3 878 notas válidas leídas y 3 878 cargadas, de 3 937 filas de 173 estudiantes. Las 59 restantes se reportan con su motivo |
| CP-02 | No se generan duplicados | **Aprobado** | Segunda carga del mismo archivo: 0 cargadas, 3 878 «ya estaban»; regla `notas_duplicadas` correcta |
| CP-03 | Reconciliación entre el origen y la base en tres fechas | **Aprobado en parte** | La reconciliación es correcta. Falta repetirla en tres fechas con cargas reales sucesivas |
| CP-04 | Integridad referencial | **Aprobado** | Reglas `referencias_huerfanas` y `estudiantes_sin_matricula` correctas |
| CP-05 | La validación corre cada noche 15 días seguidos sin fallas | **En curso** | Una ejecución programada por noche desde el 11/10/2026: 6 seguidas sin fallas al 17/10/2026 (pestaña Actions del repositorio). Se cumple el 25/10/2026 si no hay fallas |
| CP-06 | Detecta duplicados | **Aprobado** | 33 notas repetidas en el origen: la carga conserva la primera y las cuenta; la validación revisa la base |
| CP-07 | Detecta vacíos críticos | **Aprobado** | 7 casillas vacías o con texto y 15 notas sin periodo identificable detectadas y no cargadas; 56 notas en cero y 62 cursos sin examen avisados |
| CP-08 | El resultado queda disponible para el responsable de TI | **Aprobado** | Pantalla «Datos» del administrador (cargas, reconciliación, reglas e historial), `GET /api/calidad`, `GET /api/calidad/historial` y reporte de cada ejecución nocturna |

La validación tiene diez reglas: cinco críticas (detienen la tarea nocturna) y cinco avisos. Con la base real: ninguna crítica falla y hay cinco avisos, detallados en [datos-y-variables.md](datos-y-variables.md). Con los datos de práctica: ninguna falla y ningún aviso.

## Lo que estas pruebas no cubren

- La base consolidada reúne registros de pocos docentes. Las exportaciones de Cubicol pueden tener otro formato y requerir su propio lector.
- 1 426 notas vienen de fotografías de cuadernos y están marcadas «por validar» hasta cotejarlas con el original.
- En la demostración pública la base tiene datos de práctica. La carga de datos reales a la nube espera la base gestionada, el control de acceso y el consentimiento de los apoderados.
- El criterio de 15 noches seguidas (CP-05) y la reconciliación en tres fechas (CP-03) necesitan tiempo real de operación.
