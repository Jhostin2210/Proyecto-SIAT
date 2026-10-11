# Datos disponibles y variables del modelo

Actividades A-0.1.1.2 (calidad y disponibilidad de los datos) y A-0.1.1.3 (variables) del cronograma. Las cifras salen de cargar la base consolidada de notas del colegio en un equipo del proyecto, el 10/10/2026. Este documento no contiene datos de ningún estudiante.

## 1. Qué datos hay

La fuente es un libro de Excel que consolida todo lo entregado por el colegio, con una fila por nota (3 937 filas) y, en cada fila, de qué archivo u hoja salió.

| Origen | Contenido | Filas | Situación |
|---|---|---|---|
| Registro de notas en Excel, 2025 | Noviembre y diciembre de 2025, de 3.° de primaria a 2.° de secundaria | 968 | Validadas |
| Registro de notas en Excel, 2026 | Marzo a mayo de 2026 | 1 528 | Validadas |
| 36 fotografías de cuadernos de registro | Exámenes mensuales de marzo y abril, y del primer trimestre de 2026 | 1 441 | **Por validar**: transcritas, falta cotejarlas con el original |
| Asistencia e incidencias | — | — | No existen en formato digital |
| Exportaciones de Cubicol | — | — | Pendientes de solicitar al colegio |

El libro trae además una hoja con DNI y otros datos personales. **Esa hoja no se lee ni se carga.**

Supuesto por confirmar con el colegio: el registro de marzo a mayo y las fotografías no indican el año; se cargaron como 2026.

## 2. Qué quedó en la base

| Medida | Valor |
|---|---|
| Notas válidas cargadas | 3 878 de 3 937 filas |
| Estudiantes | 173 |
| Matrículas (estudiante y año) | 187: 48 en 2025 y 139 en 2026; 14 estudiantes están en los dos años |
| Cursos | 16, en 4 áreas |
| Periodos | 6: noviembre y diciembre de 2025; marzo, abril, mayo y primer trimestre de 2026 |
| Reconciliación entre el archivo y la base | Correcta, sin duplicados |

| Periodo | Notas | Estudiantes | Cursos |
|---|---|---|---|
| Noviembre de 2025 | 463 | 48 | 7 |
| Diciembre de 2025 | 490 | 48 | 7 |
| Marzo de 2026 | 961 | 118 | 11 |
| Abril de 2026 | 958 | 113 | 11 |
| Mayo de 2026 | 517 | 57 | 7 |
| Primer trimestre de 2026 | 489 | 68 | 4 |

| Tipo de nota | Notas | Promedio | Menores de 11 |
|---|---|---|---|
| Cuaderno | 925 | 15,0 | 6 % |
| Examen | 897 | 14,6 | 15 % |
| Oral | 674 | 14,8 | 5 % |
| Libro | 659 | 14,9 | 6 % |
| Práctica | 287 | 16,3 | 0 % |
| Promedio que anota el docente | 225 | 14,9 | 8 % |
| Conducta | 130 | 15,1 | 5 % |
| Exposición | 52 | 13,9 | 12 % |
| Trabajo | 29 | 12,3 | 21 % |

El examen es la nota que más separa a los estudiantes: los trabajos casi siempre se aprueban.

## 3. Calidad

Lo que la carga no acepta, y lo dice:

| Observación | Casos | Qué hace la carga |
|---|---|---|
| Más de una nota del mismo tipo para el mismo estudiante, curso y periodo | 33 | Conserva la primera |
| Nota sin mes ni tipo de evaluación reconocible | 15 | No la carga |
| Casilla sin nota o con texto («no vino», «?») | 7 | No la carga; no asume cero |
| Actividad fuera del catálogo de cursos | 4 | No la carga |

Lo que la validación automática avisa sobre la base ya cargada (ninguna regla crítica falla):

| Aviso | Casos | Qué significa |
|---|---|---|
| Notas por validar | 1 426 | Transcritas de cuadernos; falta cotejarlas |
| Estudiantes de los que solo se conoce el nombre de pila | 78 | En los cuadernos fotografiados figura solo el nombre; no se pueden enlazar con seguridad con otros años |
| Cursos sin nota de examen en un periodo | 62 | El modelo usa entonces los trabajos |
| Notas en cero | 56 | Conviene confirmar si son inasistencias a la evaluación |
| Estudiantes con un solo periodo | 24 | No sirven para entrenar: el modelo necesita dos periodos seguidos |

**Conclusión.** La base alcanza para aplicar el modelo y comprobar sus resultados (558 casos de 146 estudiantes con dos periodos seguidos en un mismo curso). No alcanza todavía para entrenar una red neuronal con datos propios: faltan las exportaciones completas de Cubicol y cotejar las notas transcritas.

## 4. Identidad de los estudiantes

- Cada estudiante tiene un **código único** (`E-0001`…), asignado en orden aleatorio. Es lo que usa el sistema para identificarlo.
- La base guarda **nombres, un apellido, año, nivel y grado**, y el **perfil** que usa el modelo (historial, familia y hábitos). No guarda DNI, fecha de nacimiento, dirección ni teléfonos.
- El perfil incluye datos de la familia y del estado de salud, que son datos personales sensibles: su tratamiento requiere el consentimiento de los apoderados (Ley N.° 29733).
- La relación entre el nombre completo del registro y el código queda en `backend/data/privado/`, que no se sube al repositorio.
- Este repositorio y la API de la demostración son públicos: **los datos reales solo se cargan en local**. La demostración usa datos de práctica.

## 5. Datos de práctica

`python -m etl.generar_datos_practica` crea un colegio ficticio completo: 135 estudiantes con nombres inventados, 9 grados, 4 cursos por nivel, 3 meses y 7 907 notas, generadas al azar con un comportamiento parecido al real (los trabajos tienen notas más altas que los exámenes; a quien le va mal un mes le suele ir mal el siguiente).

Sirven para mostrar el sistema funcionando sin exponer a ningún estudiante. **No se usan para entrenar ni para comprobar el modelo**: un modelo entrenado con notas inventadas solo aprendería la fórmula con que se inventaron.

## 6. Variables y qué se predice

Se predice si al estudiante le irá mal en un curso. El modelo es una red neuronal entrenada con una base pública; el método y los resultados están en [modelo-y-validacion.md](modelo-y-validacion.md).

| Variable | De dónde sale en el sistema |
|---|---|
| Nota del curso en el periodo actual y en el anterior | Tabla `notas`: promedio del examen y de los trabajos del periodo |
| Historial y colegio: edad, inasistencias, cursos desaprobados antes, horas de estudio, apoyo escolar, clases particulares, tiempo de viaje | Tabla `perfiles` |
| Familia: sexo, tamaño de la familia, padres, estudios y ocupación de los padres, apoderado, apoyo familiar, internet, relación familiar | Tabla `perfiles` |
| Hábitos: actividades extracurriculares, relación sentimental, tiempo libre, salidas, salud | Tabla `perfiles` |
| Estado de pago de pensiones | **Retirada**: es un dato sensible y el tutor no puede actuar sobre él |

La asistencia y las incidencias por periodo tienen sus propias tablas, que están vacías: el colegio aún las lleva en papel.
