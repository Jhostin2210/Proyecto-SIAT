-- ==========================================
-- SIA-T: esquema de la base de datos (versión 3) - PostgreSQL
-- Generado desde backend/etl/modelo_datos.py, que es la definición vigente.
-- Cada estudiante tiene un código único. La base no guarda DNI, fecha de nacimiento,
-- dirección ni datos de los apoderados.
-- ==========================================

CREATE TABLE calidad_datos (
	id SERIAL NOT NULL, 
	fecha TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	regla VARCHAR(60) NOT NULL, 
	severidad VARCHAR(10) NOT NULL, 
	cantidad INTEGER NOT NULL, 
	detalle TEXT, 
	PRIMARY KEY (id)
);

CREATE TABLE cargas (
	id SERIAL NOT NULL, 
	fecha TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	archivo VARCHAR(200) NOT NULL, 
	tipo_datos VARCHAR(12) NOT NULL, 
	filas_origen INTEGER NOT NULL, 
	notas_leidas INTEGER NOT NULL, 
	notas_cargadas INTEGER NOT NULL, 
	notas_repetidas INTEGER NOT NULL, 
	notas_rechazadas INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT chk_tipo_datos CHECK (tipo_datos IN ('reales', 'practica'))
);

CREATE TABLE cursos (
	id SERIAL NOT NULL, 
	nombre VARCHAR(60) NOT NULL, 
	area VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE estudiantes (
	id SERIAL NOT NULL, 
	codigo VARCHAR(20) NOT NULL, 
	nombres VARCHAR(60) NOT NULL, 
	apellido VARCHAR(60), 
	identidad VARCHAR(12) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT chk_identidad CHECK (identidad IN ('completa', 'solo_nombre')), 
	UNIQUE (codigo)
);

CREATE TABLE periodos (
	id SERIAL NOT NULL, 
	codigo VARCHAR(8) NOT NULL, 
	nombre VARCHAR(40) NOT NULL, 
	anio INTEGER NOT NULL, 
	orden FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo)
);

CREATE TABLE usuarios (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	email VARCHAR(100) NOT NULL, 
	rol VARCHAR(20) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT chk_rol CHECK (rol IN ('docente', 'coordinacion', 'psicologia', 'direccion', 'administrador')), 
	UNIQUE (email)
);

CREATE TABLE asistencia (
	id SERIAL NOT NULL, 
	estudiante_id INTEGER NOT NULL, 
	periodo_id INTEGER NOT NULL, 
	inasistencias INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_asistencia UNIQUE (estudiante_id, periodo_id), 
	CONSTRAINT chk_inasistencias CHECK (inasistencias >= 0), 
	FOREIGN KEY(estudiante_id) REFERENCES estudiantes (id) ON DELETE CASCADE, 
	FOREIGN KEY(periodo_id) REFERENCES periodos (id) ON DELETE CASCADE
);

CREATE TABLE incidencias (
	id SERIAL NOT NULL, 
	estudiante_id INTEGER NOT NULL, 
	periodo_id INTEGER NOT NULL, 
	fecha TIMESTAMP WITHOUT TIME ZONE, 
	tipo VARCHAR(40) NOT NULL, 
	descripcion TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(estudiante_id) REFERENCES estudiantes (id) ON DELETE CASCADE, 
	FOREIGN KEY(periodo_id) REFERENCES periodos (id) ON DELETE CASCADE
);

CREATE TABLE matriculas (
	id SERIAL NOT NULL, 
	estudiante_id INTEGER NOT NULL, 
	anio INTEGER NOT NULL, 
	nivel_educativo VARCHAR(12) NOT NULL, 
	grado VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_matricula UNIQUE (estudiante_id, anio), 
	CONSTRAINT chk_nivel_educativo CHECK (nivel_educativo IN ('inicial', 'primaria', 'secundaria')), 
	FOREIGN KEY(estudiante_id) REFERENCES estudiantes (id) ON DELETE CASCADE
);

CREATE TABLE notas (
	id SERIAL NOT NULL, 
	estudiante_id INTEGER NOT NULL, 
	curso_id INTEGER NOT NULL, 
	periodo_id INTEGER NOT NULL, 
	tipo_evaluacion VARCHAR(20) NOT NULL, 
	componente VARCHAR(12) NOT NULL, 
	nota FLOAT NOT NULL, 
	fuente VARCHAR(12) NOT NULL, 
	confianza VARCHAR(6) NOT NULL, 
	validada INTEGER NOT NULL, 
	carga_id INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_nota UNIQUE (estudiante_id, curso_id, periodo_id, tipo_evaluacion, componente), 
	CONSTRAINT chk_nota_rango CHECK (nota >= 0 AND nota <= 20), 
	CONSTRAINT chk_componente CHECK (componente IN ('examen', 'cuaderno', 'libro', 'oral', 'practica', 'exposicion', 'trabajo', 'conducta', 'promedio')), 
	CONSTRAINT chk_tipo_evaluacion CHECK (tipo_evaluacion IN ('registro_mensual', 'examen_mensual', 'examen_trimestral')), 
	CONSTRAINT chk_confianza CHECK (confianza IN ('alta', 'media')), 
	FOREIGN KEY(estudiante_id) REFERENCES estudiantes (id) ON DELETE CASCADE, 
	FOREIGN KEY(curso_id) REFERENCES cursos (id) ON DELETE CASCADE, 
	FOREIGN KEY(periodo_id) REFERENCES periodos (id) ON DELETE CASCADE, 
	FOREIGN KEY(carga_id) REFERENCES cargas (id)
);

CREATE TABLE predicciones (
	id SERIAL NOT NULL, 
	estudiante_id INTEGER NOT NULL, 
	periodo_id INTEGER NOT NULL, 
	nivel_riesgo VARCHAR(20) NOT NULL, 
	probabilidad FLOAT, 
	origen VARCHAR(20) NOT NULL, 
	version VARCHAR(50) NOT NULL, 
	motivo TEXT, 
	fecha TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_prediccion UNIQUE (estudiante_id, periodo_id, origen), 
	CONSTRAINT chk_nivel_riesgo CHECK (nivel_riesgo IN ('Riesgo bajo', 'Riesgo medio', 'Riesgo alto')), 
	CONSTRAINT chk_origen CHECK (origen IN ('regla_provisional', 'modelo')), 
	FOREIGN KEY(estudiante_id) REFERENCES estudiantes (id) ON DELETE CASCADE, 
	FOREIGN KEY(periodo_id) REFERENCES periodos (id) ON DELETE CASCADE
);

CREATE TABLE alertas (
	id SERIAL NOT NULL, 
	prediccion_id INTEGER NOT NULL, 
	mensaje TEXT NOT NULL, 
	atendida INTEGER NOT NULL, 
	fecha TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(prediccion_id) REFERENCES predicciones (id) ON DELETE CASCADE
);
