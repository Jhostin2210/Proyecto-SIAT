# Pruebas del entregable E-01: integración y limpieza de datos

Paquetes 1.2.1 y 1.2.2 de la EDT, requisitos REQ-01 y REQ-02, casos de prueba CP-01 a CP-08 de la matriz de trazabilidad. Ejecutadas el 10/10/2026 en un equipo del proyecto.

## Cómo repetirlas

Desde la carpeta `backend`, con el entorno de Python activo:

```powershell
# Carga del registro real en una base local que no se sube al repositorio
$env:SQLITE_PATH = "data/privado/sia_t_reales.db"
python -m etl.cargar_notas "ruta\al\registro de notas.xlsx"
python -m etl.cargar_notas "ruta\al\registro de notas.xlsx"   # segunda vez: no debe cargar nada nuevo
python -m etl.validar_datos
```

## Resultados

| Caso | Qué comprueba | Resultado | Evidencia |
|---|---|---|---|
| CP-01 | Se consolidan todos los registros válidos | **Aprobado** | 715 notas válidas leídas y 715 cargadas, de 230 filas de 44 estudiantes |
| CP-02 | No se generan duplicados | **Aprobado** | Segunda carga del mismo archivo: 0 cargadas, 715 «ya estaban»; regla `notas_duplicadas` correcta |
| CP-03 | Reconciliación entre el origen y la base en tres fechas | **Aprobado en parte** | La reconciliación por grado, curso y periodo es correcta. Falta repetirla en tres fechas con cargas reales sucesivas |
| CP-04 | Integridad referencial | **Aprobado** | Regla `referencias_huerfanas` correcta: ninguna nota sin estudiante, curso o periodo |
| CP-05 | La validación corre cada noche 15 días seguidos sin fallas | **En curso** | Tarea programada creada; el historial queda en la pestaña Actions del repositorio. Se cumple al completar 15 ejecuciones |
| CP-06 | Detecta duplicados | **Aprobado** | La carga los omite y los cuenta; la validación revisa la base |
| CP-07 | Detecta vacíos críticos | **Aprobado** | 13 notas vacías, 9 filas en cero y 2 valores no numéricos detectados en el registro real |
| CP-08 | El resultado queda disponible para el responsable de TI | **Aprobado** | Tabla `calidad_datos`, `GET /api/calidad`, tarjeta «Datos y calidad» de la página y reporte de cada ejecución nocturna |

## Lo que estas pruebas no cubren

- La carga se probó con el registro de un docente (noviembre y diciembre de 2025). Las exportaciones de Cubicol pueden tener otro formato y requerir su propio lector.
- En la demostración pública la base tiene datos de práctica. La carga de datos reales a la nube espera la base gestionada y el consentimiento de los apoderados.
- El criterio de 15 noches seguidas (CP-05) y la reconciliación en tres fechas (CP-03) necesitan tiempo real de operación.
