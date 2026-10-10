# Datos disponibles y variables del modelo

Actividades A-0.1.1.2 (calidad y disponibilidad de los datos) y A-0.1.1.3 (variables) del cronograma, Sprint 1. Las cifras salen de ejecutar la carga sobre el registro real en un equipo del proyecto; este documento no contiene datos de ningún estudiante.

## 1. Qué datos hay

| Fuente | Contenido | Situación |
|---|---|---|
| Registro de notas de noviembre y diciembre de 2025 (Excel) | Matemática, Historia y Economía, de 3.° de primaria a 2.° de secundaria | **Se carga de forma automática** |
| Registro de notas de marzo a mayo de 2026 (Excel) | Personal Social e Historia por competencias | Otro formato; requiere un lector propio. Incluye una hoja con DNI y fechas de nacimiento que no debe cargarse |
| 36 fotografías de cuadernos de registro | Exámenes de marzo, abril y primer trimestre de 2026 | No son legibles por el sistema; habría que transcribirlas |
| Asistencia e incidencias | — | No existen en formato digital |
| Exportaciones de Cubicol | — | Pendientes de solicitar al colegio |

## 2. Calidad del registro de 2025

| Medida | Valor |
|---|---|
| Hojas (grados) | 6 |
| Bloques de curso y mes | 32 |
| Filas de estudiantes leídas | 230 |
| Estudiantes con notas válidas | 44 |
| Notas válidas cargadas | 715 |
| Periodos | 2 consecutivos (noviembre y diciembre de 2025) |
| Estudiantes con los dos periodos | 44 de 44 |
| Reconciliación entre el archivo y la base | Correcta, sin duplicados |

Observaciones que la carga detecta y reporta:

| Observación | Casos | Qué hace la carga |
|---|---|---|
| Nota vacía | 13 | No la carga y la reporta |
| Fila con todas las notas en cero | 9 | No la carga: se trata como estudiante sin evaluación |
| Título del bloque con otro grado que la hoja | 4 | Usa el grado de la hoja |
| Columna con notas pero sin encabezado | 3 | No la carga |
| Nota en cero aislada | 3 | La carga y pide confirmarla |
| Componente repetido en un bloque | 2 | Carga el primero |
| Valor no numérico | 2 | Lo rechaza |
| Nombre de curso mal escrito | 1 curso | Lo corrige con el catálogo de cursos |

**Conclusión.** El registro sirve para construir y probar la carga, y tiene dos periodos seguidos por estudiante, que es lo mínimo para predecir un periodo a partir del anterior. No alcanza para validar un modelo: son 44 estudiantes, pocos cursos por grado y un solo docente. Hacen falta las exportaciones de Cubicol de 2025 y 2026.

## 3. Variables propuestas

Pendiente de validar con los docentes en el taller del Sprint 1.

| Variable | De dónde sale | Situación |
|---|---|---|
| Promedio de exámenes del periodo | Notas | Disponible |
| Promedio de libro y cuaderno | Notas | Disponible |
| Nota de conducta | Notas | Disponible en parte: no todos los cursos la registran |
| Cambio del promedio frente al periodo anterior | Notas de dos periodos | Disponible |
| Número de cursos con examen desaprobado | Notas | Disponible |
| Grado y nivel educativo | Registro | Disponible |
| Inasistencias del periodo | Asistencia | No disponible: se lleva en papel |
| Incidencias del periodo | Incidencias | No disponible: se llevan en papel |

**Qué se predice:** si el estudiante desaprobará el periodo siguiente (promedio menor de 11).

**Variable retirada:** el estado de pago de pensiones. Era un dato simulado, es sensible y el tutor no puede actuar sobre él.

## 4. Nivel de riesgo mientras no hay modelo

Hasta que el modelo se entrene y valide con datos reales (Sprint 3), el sistema usa una regla provisional, visible como tal en la página:

- **Riesgo alto:** promedio general menor de 11, o promedio de exámenes menor de 9.
- **Riesgo medio:** promedio de exámenes menor de 11, o caída de 2 puntos o más frente al periodo anterior.
- **Riesgo bajo:** los demás casos.

Esta regla será además la referencia contra la que se compare el modelo: si el modelo no la supera, no se justifica.
