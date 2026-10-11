# Base pública: Student Performance

- **Archivos:** `student-mat.csv` (Matemática, 395 registros) y `student-por.csv` (Lenguaje, 649 registros). Separador: punto y coma.
- **Origen:** Repositorio UCI de Machine Learning, https://archive.ics.uci.edu/dataset/320/student+performance. Descargados el 10/10/2026, sin modificar.
- **Autores:** P. Cortez y A. Silva. *Using Data Mining to Predict Secondary School Student Performance.* Proceedings of 5th FUture BUsiness TEChnology Conference (FUBUTEC 2008), pp. 5-12, Porto, Portugal, 2008.
- **Licencia:** Creative Commons Atribución 4.0 (CC BY 4.0).
- **Contenido:** estudiantes de secundaria de dos colegios de Portugal. Notas de 0 a 20 en tres periodos (`G1`, `G2`, `G3`; se aprueba con 10), inasistencias (`absences`), cursos desaprobados antes (`failures`), horas de estudio, apoyo escolar y datos de contexto. Es una base anónima.

No son datos del colegio Peruano Francés. Con ellos se entrena y se prueba la red neuronal (`python -m ml.entrenar_red_neuronal`).
