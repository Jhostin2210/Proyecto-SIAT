# Modelo de riesgo: entrenamiento y validación

Las cifras salen de `backend/data/metrics_report.json`, que escribe el propio entrenamiento (`python -m ml.entrenar_modelo`). Entrenado el 10/10/2026 con los datos reales del colegio, en un equipo del proyecto. Este documento no contiene datos de ningún estudiante.

## 1. Qué predice

Para cada estudiante, curso y periodo: **si desaprobará (menos de 11) el examen del periodo siguiente en ese curso**, usando solo las notas que ya se conocen en el periodo actual.

Se eligió el examen del periodo siguiente porque es el dato más objetivo y el que más se repite en la base, y porque da al tutor un mes para actuar.

## 2. Con qué datos

| Medida | Valor |
|---|---|
| Casos (estudiante, curso y periodo con examen en el periodo siguiente) | 519 |
| Estudiantes | 146 |
| Casos que desaprobaron el examen siguiente | 64 (12,3 %) |
| Casos que incluyen notas por validar (transcritas de cuadernos) | 177 |

| Periodo actual → periodo que se predice | Casos | Desaprobaron |
|---|---|---|
| Noviembre → diciembre de 2025 | 113 | 17 |
| Marzo → abril de 2026 | 185 | 16 |
| Marzo → primer trimestre de 2026 | 4 | 2 |
| Abril → mayo de 2026 | 118 | 10 |
| Abril → primer trimestre de 2026 | 99 | 19 |

Los datos de práctica de la demostración **no participan** del entrenamiento ni de la validación.

## 3. Variables

Todas salen de las notas. Las calcula `backend/etl/variables.py`, que usan por igual el entrenamiento y el cálculo del riesgo.

| Variable | Qué es |
|---|---|
| `examen` | Nota de examen del periodo en el curso |
| `trabajos` | Promedio de cuaderno, libro, oral, prácticas y exposiciones |
| `cuaderno`, `libro`, `oral`, `conducta` | Cada nota por separado |
| `minimo` | Nota más baja del periodo en el curso |
| `n_notas` | Cantidad de notas registradas |
| `examen_previo`, `cambio_examen` | Examen del periodo anterior y diferencia con el actual |
| `examen_otros_cursos`, `trabajos_otros_cursos` | Cómo le va al estudiante en sus otros cursos ese periodo |
| `secundaria`, `area_*` | Nivel educativo y área del curso |

No se usan la asistencia ni las incidencias (el colegio las lleva en papel) ni el pago de pensiones (se retiró: es un dato sensible y el tutor no puede actuar sobre él).

## 4. Cómo se validó

- **Validación cruzada estratificada y agrupada por estudiante**, en 5 partes y repetida 10 veces. Agrupar por estudiante impide que el mismo estudiante esté a la vez en el entrenamiento y en la prueba, que es la forma más común de obtener resultados inflados.
- **Todo el preparado de los datos va dentro del modelo** (valores faltantes, escalas), de modo que se ajusta solo con los datos de entrenamiento de cada parte.
- **Clases desbalanceadas:** solo 12 % desaprueba, así que los modelos pesan más esos casos. No se usa la exactitud, que con este desbalance se obtiene prediciendo que nadie desaprueba (88 %).
- **El corte se elige dentro de cada entrenamiento**, buscando detectar al menos 75 % de los que desaprueban, y se mide en la parte que el modelo no vio.
- **Referencias obligatorias:** una regla simple y una regresión logística. El bosque aleatorio solo se justifica si las supera.
- **Parámetros fijos**, sin búsqueda: con tan pocos datos, ajustarlos produciría resultados optimistas.

## 5. Resultados

Media y desviación entre las 10 repeticiones.

| Modelo | Precisión media | AUC | Detecta (sensibilidad) | Aciertos de sus alertas (precisión) | Casos que alerta |
|---|---|---|---|---|---|
| Regla simple (ordena por la nota de examen) | 0,27 | 0,71 | 76 % | 16 % | 57 % |
| Regresión logística | 0,38 ± 0,02 | 0,74 ± 0,02 | 76 % | 19 % | 51 % |
| **Bosque aleatorio (en uso)** | **0,40 ± 0,02** | **0,75 ± 0,02** | 75 % | 20 % | 47 % |

Para comparar: la regla más natural, «alertar a quien desaprobó el examen de este mes», detecta solo 33 % de los que desaprueban el siguiente, con 32 % de aciertos.

**Lectura.** Si se alertara al azar, la precisión media sería 0,12; el modelo llega a 0,40. Supera a la regla simple y a la regresión logística, pero por un margen moderado. Para detectar a tres de cada cuatro estudiantes que desaprobarán, hay que alertar casi a la mitad de los casos, y de cada cinco alertas una acierta. Con estos datos el modelo sirve para **ordenar a quién mirar primero**, no para afirmar quién va a desaprobar.

### Los tres niveles

Los cortes se fijaron con las predicciones sobre datos que el modelo no vio: riesgo medio desde una probabilidad de 0,25 y riesgo alto desde 0,57.

| Nivel | Casos | Desaprobaron el examen siguiente |
|---|---|---|
| Riesgo alto | 50 | 25 (50 %) |
| Riesgo medio | 176 | 23 (13 %) |
| Riesgo bajo | 293 | 16 (5 %) |

Los niveles ordenan bien: en riesgo alto desaprueba uno de cada dos; en riesgo bajo, uno de cada veinte.

Una advertencia: el corte de riesgo alto se eligió, con estas mismas predicciones, como el punto desde el cual desaprueba al menos la mitad. El 50 % del nivel alto es entonces el criterio con que se fijó el corte, no una medición independiente; hay que confirmarlo con datos nuevos.

El riesgo de un **estudiante** es el promedio de sus cursos; si un solo curso está en riesgo alto, el estudiante queda como mínimo en riesgo medio.

### Solo con notas validadas

Al repetir la validación sin las notas transcritas de cuadernos (342 casos, 30 desaprobados), el bosque aleatorio obtiene una precisión media de 0,40 y un AUC de 0,75: el resultado no depende de las notas por validar.

### Variables que más pesan

Trabajos del curso (0,17), examen en los otros cursos (0,11), trabajos en los otros cursos (0,11), nota oral (0,09), nota más baja (0,09) y examen del curso (0,08).

## 6. Frente al criterio del proyecto

El criterio de aceptación pide detectar al menos 75 % de los estudiantes en riesgo. Se cumple (75 %), pero al costo descrito arriba: muchas alertas que no se confirman. Antes del piloto conviene decidir con el colegio cuántas alertas por tutor son manejables y, si hace falta, usar solo el nivel alto para las alertas por correo.

## 7. Límites

- **Pocos datos.** 64 casos desaprobados; por eso se informa la media y la desviación, y los resultados pueden cambiar con más datos.
- **Notas por validar.** Las transcritas de fotografías de cuadernos faltan cotejarse con el original.
- **Solo notas.** Sin asistencia ni incidencias en formato digital.
- **Pocos docentes y cursos.** La validación debe repetirse con las exportaciones completas de Cubicol.
- **Sin prueba en el tiempo.** Todavía no hay periodos suficientes para entrenar con un trimestre y probar con el siguiente; es el paso que sigue.
- **Falta la validación en campo:** comparar las alertas con el juicio de los docentes y con el resultado real del bimestre, durante el piloto.

## 8. Cómo repetirlo

Desde `backend`, con el entorno activo y la base real en local:

```powershell
$env:SQLITE_PATH = "data/privado/sia_t_reales.db"
python -m etl.cargar_notas "ruta\a\la base consolidada.xlsx"
python -m ml.entrenar_modelo
```

Tarda unos diez minutos. Escribe `models/modelo_riesgo.joblib` y `data/metrics_report.json`. El archivo del modelo contiene los árboles y los cortes, no las notas de ningún estudiante.

## 9. Modelo de referencia con una base pública

Para saber hasta dónde llega el método con datos completos, se repitió con una base pública ya estudiada: *Student Performance* (Cortez y Silva, 2008; repositorio UCI, licencia CC BY 4.0). Son 1 044 registros de 662 estudiantes de secundaria de dos colegios de Portugal, en Matemática y Lenguaje, con notas de 0 a 20 en tres periodos, inasistencias, cursos desaprobados antes y datos de contexto. Se predice si el estudiante desaprueba el curso (nota final menor de 10); desaprueba 22 %. Los archivos están en `backend/data/publica/` y el reporte en `backend/data/referencia_report.json` (`python -m ml.modelo_referencia`).

Misma validación: cruzada, agrupada por estudiante, 5 partes, 10 repeticiones. Corte de 0,5.

| Con qué datos | Exactitud | AUC | Detecta | Aciertos de sus alertas |
|---|---|---|---|---|
| Base pública, con las notas de los dos periodos anteriores | 92 % | 0,97 | 88 % | 79 % |
| Base pública, con la nota de un solo periodo anterior | 87 % | 0,93 | 79 % | 67 % |
| Base pública, sin notas: solo inasistencias, historial y contexto | 80 % | 0,79 | 40 % | 56 % |
| **Entrenado con la base pública y probado con los resultados reales del colegio** | 87 % | 0,71 | 30 % | 46 % |

Sin modelo, decir que nadie desaprueba acierta 78 % en la base pública y 88 % en el colegio.

**Qué se concluye**

- Con datos completos, el método funciona bien: 92 % de exactitud y detecta a 88 % de los que desaprueban.
- Lo que más pesa son las notas de los periodos anteriores (G2 y G1 suman dos tercios del peso); después, los cursos desaprobados antes y las inasistencias.
- **Un modelo entrenado con la base pública no sirve tal cual en el colegio.** Para aplicarlo solo puede usar las columnas que el colegio también tiene (nota actual y anterior). Probado con los 519 casos reales, obtiene un AUC de 0,71 y detecta a 30 % de los que desaprueban: igual que la regla simple y por debajo del modelo entrenado con los datos del colegio (AUC 0,75). Su 87 % de exactitud es menor que el 88 % de no alertar a nadie.
- La razón es que no son el mismo problema: la base pública predice la nota final del curso a partir de notas de periodo, que se parecen mucho entre sí; el colegio predice el examen del mes siguiente, que varía más.

Por eso el nivel de riesgo del sistema lo sigue calculando el modelo entrenado con los datos del colegio. La base pública queda como referencia del método y como argumento para pedir al colegio lo que falta: notas de cierre de periodo de todos los cursos, inasistencias e historial.
