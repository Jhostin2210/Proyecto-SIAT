-- ==========================================
-- SIA-T: Sistema Inteligente de Alerta Temprana del Rendimiento Académico Estudiantil
-- ESQUEMA DE BASE DE DATOS - PostgreSQL
-- ==========================================

-- Tabla 1: Periodos académicos / Trimestres
CREATE TABLE IF NOT EXISTS periodos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE, -- Ej: '2024-I', '2024-II'
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    CONSTRAINT chk_fechas CHECK (fecha_fin >= fecha_inicio)
);

-- Tabla 2: Estudiantes
CREATE TABLE IF NOT EXISTS estudiantes (
    id SERIAL PRIMARY KEY,
    codigo_anonimizado VARCHAR(50) NOT NULL UNIQUE, -- Ej: 'A001', 'A002' para exportación y anonimización
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    grado VARCHAR(50) NOT NULL, -- Ej: '3° Secundaria'
    nivel_educativo VARCHAR(20) NOT NULL, -- 'primaria' o 'secundaria'
    seccion VARCHAR(5) NOT NULL, -- Ej: 'A', 'B'
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_nivel CHECK (nivel_educativo IN ('primaria', 'secundaria'))
);

-- Tabla 3: Notas académicas por periodo y estudiante
CREATE TABLE IF NOT EXISTS notas (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE CASCADE,
    nota_libro NUMERIC(4,2) NOT NULL, -- Rango 0.00 a 20.00
    nota_cuaderno NUMERIC(4,2) NOT NULL, -- Rango 0.00 a 20.00
    nota_examen NUMERIC(4,2) NOT NULL, -- Rango 0.00 a 20.00
    conducta NUMERIC(4,2) NOT NULL, -- Rango 0.00 a 20.00
    nota_final NUMERIC(4,2) NOT NULL, -- Calculada (promedio de notas)
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_nota_libro CHECK (nota_libro >= 0 AND nota_libro <= 20),
    CONSTRAINT chk_nota_cuaderno CHECK (nota_cuaderno >= 0 AND nota_cuaderno <= 20),
    CONSTRAINT chk_nota_examen CHECK (nota_examen >= 0 AND nota_examen <= 20),
    CONSTRAINT chk_conducta CHECK (conducta >= 0 AND conducta <= 20),
    CONSTRAINT chk_nota_final CHECK (nota_final >= 0 AND nota_final <= 20),
    CONSTRAINT uq_estudiante_periodo_nota UNIQUE (estudiante_id, periodo_id)
);

-- Tabla 4: Asistencia (Inasistencias acumuladas en el periodo)
CREATE TABLE IF NOT EXISTS asistencia (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE CASCADE,
    inasistencias INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT chk_inasistencias CHECK (inasistencias >= 0),
    CONSTRAINT uq_estudiante_periodo_asistencia UNIQUE (estudiante_id, periodo_id)
);

-- Tabla 5: Pensiones (Estado de pago de pensiones en el periodo)
CREATE TABLE IF NOT EXISTS pensiones (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE CASCADE,
    estado_pension VARCHAR(20) NOT NULL, -- 'al_dia', 'atraso_leve', 'deuda'
    CONSTRAINT chk_estado_pension CHECK (estado_pension IN ('al_dia', 'atraso_leve', 'deuda')),
    CONSTRAINT uq_estudiante_periodo_pension UNIQUE (estudiante_id, periodo_id)
);

-- Tabla 6: Predicciones generadas por el modelo de ML
CREATE TABLE IF NOT EXISTS predicciones (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE CASCADE,
    probabilidad_riesgo NUMERIC(5,4) NOT NULL, -- Rango 0.0000 a 1.0000 (Salida de predict_proba)
    nivel_riesgo VARCHAR(20) NOT NULL, -- 'Sin riesgo', 'Riesgo bajo', 'Riesgo medio', 'Riesgo alto'
    version_modelo VARCHAR(50) NOT NULL, -- Ej: 'random_forest_v1.0' o referencia al .pkl
    fecha_prediccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    origen VARCHAR(20) NOT NULL, -- 'automatico' (ejecución programada) o 'simulador' (hipotético)
    CONSTRAINT chk_probabilidad CHECK (probabilidad_riesgo >= 0 AND probabilidad_riesgo <= 1),
    CONSTRAINT chk_nivel_riesgo CHECK (nivel_riesgo IN ('Sin riesgo', 'Riesgo bajo', 'Riesgo medio', 'Riesgo alto')),
    CONSTRAINT chk_origen CHECK (origen IN ('automatico', 'simulador'))
);

-- Tabla 7: Alertas generadas automáticamente ante riesgo detectado
CREATE TABLE IF NOT EXISTS alertas (
    id SERIAL PRIMARY KEY,
    prediccion_id INTEGER NOT NULL REFERENCES predicciones(id) ON DELETE CASCADE,
    mensaje TEXT NOT NULL,
    atendida BOOLEAN NOT NULL DEFAULT FALSE,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla 8: Usuarios del sistema (Docentes, Coordinadores, Administradores)
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    rol VARCHAR(30) NOT NULL, -- 'docente', 'coordinador', 'administrador'
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_rol CHECK (rol IN ('docente', 'coordinador', 'administrador'))
);

-- Índices recomendados para optimización de lectura analítica
CREATE INDEX IF NOT EXISTS idx_notas_estudiante ON notas(estudiante_id);
CREATE INDEX IF NOT EXISTS idx_notas_periodo ON notas(periodo_id);
CREATE INDEX IF NOT EXISTS idx_predicciones_estudiante ON predicciones(estudiante_id);
CREATE INDEX IF NOT EXISTS idx_predicciones_periodo ON predicciones(periodo_id);
CREATE INDEX IF NOT EXISTS idx_alertas_atendida ON alertas(atendida);
