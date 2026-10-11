# Modelo de riesgo: entrenamiento y prueba

Paquetes 1.3.1 y 1.3.3 de la EDT. Las cifras salen de `backend/data/red_neuronal_report.json` y `backend/data/aplicacion_colegio.json`, que escriben los propios programas de entrenamiento y de comprobación. Entrenado el 10/10/2026. Este documento no contiene datos de ningún estudiante.

## 1. Enfoque

El modelo se entrena y se prueba con una base pública. Después, el archivo ya entrenado se aplica a los datos del colegio, que no participan del entrenamiento.

Se eligió así porque el colegio todavía tiene pocos casos propios para entrenar una red neuronal: 44 con mal resultado, frente a 230 en la base pública.

## 2. Base de entrenamiento

*Student Performance* (P. Cortez y A. Silva, 2008), del repositorio UCI de Machine Learning, con licencia CC BY 4.0. Los archivos están en `backend/data/publica/`, sin modificar.

| Medida | Valor |
|---|---|
| Registros | 1 044 (395 de Matemática y 649 de Lenguaje) |
| Estudiantes | 662, de secundaria, de dos colegios de Portugal |
| Escala de notas | 0 a 20; se aprueba con 10 |
| Registros con mal resultado (nota final menor de 10) | 230 (22 %) |

**Qué predice:** si al estudiante le irá mal en el curso.

## 3. Variables

De las 32 columnas de entrada de la base se usan 25. No se consideran: `school`, `address`, `higher`, `reason`, `nursery`, `Dalc` y `Walc`.

| Grupo | Variables |
|---|---|
| Notas | Nota del periodo anterior (`G1`) y del periodo actual (`G2`) |
| Historial y colegio | Edad, inasistencias, cursos desaprobados antes, horas de estudio, apoyo escolar, clases particulares, tiempo de viaje |
| Familia | Sexo, tamaño de la familia, si los padres viven juntos, estudios y ocupación de la madre y del padre, apoderado, apoyo familiar, internet, relación familiar |
| Hábitos | Actividades extracurriculares, relación sentimental, tiempo libre, salidas con amigos, salud |

En el sistema, estas variables están en la tabla `perfiles` (ver [arquitectura.md](arquitectura.md)); `backend/etl/perfil.py` describe cada una.

## 4. Modelo

Red neuronal densa (`MLPClassifier` de scikit-learn).

| Elemento | Valor |
|---|---|
| Arquitectura | 35-32-16-8-1: 35 entradas (las 25 variables, con las categorías separadas), tres capas ocultas y una salida con la probabilidad |
| Activación | ReLU |
| Optimizador | Adam |
| Preparación | StandardScaler sobre todas las entradas |
| Regularización | `alpha` = 1,0 y detención temprana (se detuvo en la época 27) |
| Clases | Los casos con mal resultado se repiten en el entrenamiento hasta igualar las clases |

Se compararon dos niveles de regularización. Con `alpha` = 0,01 la exactitud en la prueba es mayor (89,5 %), pero la red memoriza (99 % en el entrenamiento) y responde casi siempre 0 o 1, lo que no permite separar tres niveles. Con `alpha` = 1,0 las probabilidades son graduales. Se usa esta.

No se usa TensorFlow porque el servidor de la demostración no tiene memoria suficiente; la red de scikit-learn es equivalente para este tamaño.

## 5. Prueba

80 % de los registros para entrenar (835) y 20 % para probar (209). Un mismo estudiante, que aparece en Matemática y en Lenguaje, queda siempre en un solo lado.

**Matriz de confusión, con los 209 registros que la red no vio:**

| | Predijo que bien | Predijo que mal |
|---|---|---|
| **Le fue bien** (163) | 135 | 28 |
| **Le fue mal** (46) | 6 | 40 |

| Medida | Valor |
|---|---|
| Exactitud (accuracy) | 83,7 % |
| AUC | 0,95 |
| Detecta (recall de «le va mal») | 87 % |
| Aciertos de sus alertas (precisión de «le va mal») | 59 % |
| F1 de «le va mal» | 0,70 |
| Exactitud en el entrenamiento | 90,2 % |
| Validación cruzada de 5 partes, dentro del entrenamiento | 87,8 % ± 2,7 de exactitud; AUC 0,96 |

Para comparar: decir que a nadie le irá mal acierta 78 %. Y la regla más simple, «le fue mal en el periodo anterior», acierta 89,5 % en esta misma prueba: en esta base, la nota del periodo anterior ya explica casi todo. Lo que la red agrega es una probabilidad, que permite ordenar a los estudiantes y definir niveles.

## 6. Los tres niveles

La probabilidad de la red se divide en tres niveles. Los cortes son la probabilidad que la red da, en un estudiante típico, a las notas 9,5 y 14,5 del colegio.

| Nivel | Probabilidad | Equivale, en un estudiante típico, a una nota |
|---|---|---|
| Riesgo alto | 0,69 o más | menor de 10 |
| Riesgo medio | de 0,05 a 0,69 | de 10 a 14 |
| Riesgo bajo | menos de 0,05 | de 15 a 20 |

No es un corte por nota: los demás datos del estudiante pueden moverlo de nivel.

En el colegio se aprueba con 11 y en la base pública con 10, así que a las notas del colegio se les resta un punto antes de pasarlas a la red. La nota del curso es el promedio del examen y de los trabajos del periodo. Si no hay periodo anterior, se toma la misma nota actual. La red se entrenó con estudiantes de 15 a 22 años; la edad se lleva a ese rango.

**Riesgo general del estudiante.** Se juntan sus cursos: la probabilidad general es el promedio de sus cursos, y basta un curso en riesgo alto para que el estudiante quede en riesgo alto. `backend/etl/informe.py` reconoce además el patrón (un curso o varios, exámenes frente a trabajos, caída reciente), propone acciones y redacta el comunicado al apoderado.

## 7. Aplicación en el colegio

`python -m ml.comprobar_en_colegio`, con la base de datos reales en local. La red no se entrena con estos datos. Para cada estudiante y curso se toma el nivel que dio la red en un periodo y se compara con lo que pasó en el periodo siguiente: si la nota del curso fue menor de 11.

Son 558 casos de 146 estudiantes; en 44 (7,9 %) la nota del periodo siguiente fue desaprobatoria.

| Nivel que dio la red | Casos | Les fue mal después |
|---|---|---|
| Riesgo alto | 20 | 11 (55 %) |
| Riesgo medio | 159 | 23 (14 %) |
| Riesgo bajo | 379 | 10 (3 %) |

| Si se alerta… | Exactitud | Detecta | Aciertos de sus alertas |
|---|---|---|---|
| Solo el nivel alto | 92,5 % | 25 % (11 de 44) | 55 % |
| Los niveles medio y alto | 72,2 % | 77 % (34 de 44) | 19 % |

AUC en el colegio: 0,83. Sin modelo, decir que a nadie le irá mal acierta 92,1 %; por eso la exactitud sola no sirve para juzgar las alertas.

**Lectura.** Los niveles ordenan bien: en riesgo alto le va mal a uno de cada dos, y en riesgo bajo a tres de cada cien. El nivel alto es una alerta razonable. El nivel medio acierta poco y sirve como lista de seguimiento. Separar por rangos de nota da un resultado muy parecido: hoy la red aporta sobre todo la probabilidad y un procedimiento entrenado y probado.

**Frente al criterio del proyecto** (detectar al menos 75 % de los estudiantes en riesgo): se cumple usando los niveles medio y alto (77 %), al costo de muchas alertas que no se confirman. La forma de medir este criterio sigue en evaluación (SC-08).

## 8. Límites

- La red se entrenó con estudiantes de secundaria de otro país. Lo que mejor se traslada es la relación entre la nota y el riesgo; lo demás no está comprobado para el colegio.
- En el colegio hay pocos casos con mal resultado (44): los porcentajes pueden cambiar con más datos. El 55 % del nivel alto sale de 20 casos.
- No predicen lo mismo: la base pública predice la nota final del curso; en el colegio se aplica periodo a periodo.
- Falta comprobar las alertas en un periodo nuevo y contrastarlas con el criterio de los docentes, en el piloto.
- Las acciones recomendadas son una propuesta del equipo: deben validarse con los docentes y con psicología.
- Cuando el colegio acumule uno o dos años completos de datos, conviene volver a entrenar con ellos.

## 9. Cómo repetirlo

Desde `backend`, con el entorno activo:

```powershell
python -m ml.entrenar_red_neuronal            # entrena, prueba y guarda la red (un minuto)

$env:SQLITE_PATH = "data/privado/sia_t_reales.db"
python -m ml.comprobar_en_colegio             # aplica la red a los datos reales y compara
```

El primero escribe `models/red_neuronal_riesgo.joblib` (preparación de los datos, escalador, red y cortes, en un solo archivo) y `data/red_neuronal_report.json`. El segundo, `data/aplicacion_colegio.json`.
