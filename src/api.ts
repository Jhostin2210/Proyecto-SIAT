/// <reference types="vite/client" />
// Acceso a la API de SIA-T y tipos de sus respuestas.

export const API_URL: string = (import.meta.env.VITE_API_URL as string | undefined) ?? "https://proyecto-siat.onrender.com";

export type Nivel = "Riesgo alto" | "Riesgo medio" | "Riesgo bajo";

export interface Estado {
  base_de_datos: { conectada: boolean; error?: string };
  tipo_datos: "practica" | "reales" | null;
  estudiantes: number;
  notas: number;
  periodos: { codigo: string; nombre: string }[];
  periodo_actual: { codigo: string; nombre: string } | null;
  ultima_carga: { fecha: string; archivo: string; notas_cargadas: number } | null;
  nivel_de_riesgo: { origen: string | null; version: string | null; fecha: string | null; explicacion: string };
  modelo: { nombre: string; arquitectura: string; base: string; exactitud: number; fecha_entrenamiento: string } | null;
}

export interface Estudiante {
  id: number;
  codigo: string;
  nombre: string;
  grado: string;
  nivel_educativo: string;
  periodo: string;
  periodo_nombre: string;
  promedio: number;
  nivel: Nivel;
  probabilidad: number;
  resumen: string;
  cursos: number;
  cursos_alto: number;
  cursos_medio: number;
}

export interface CursoEvaluado {
  curso: string;
  area: string;
  nota: number;
  examen: number | null;
  trabajos: number | null;
  nota_previa: number | null;
  cambio: number | null;
  probabilidad: number;
  nivel: Nivel;
  por_validar: boolean;
}

export interface Informe {
  nivel: Nivel;
  probabilidad: number;
  resumen: string;
  cursos: CursoEvaluado[];
  patrones: { clave: string; texto: string }[];
  acciones: string[];
  comunicado: string | null;
  periodo_nombre: string;
}

export interface Ficha extends Estudiante {
  matriculas: { anio: number; nivel_educativo: string; grado: string }[];
  informe: Informe;
  historial: { periodo: string; periodo_nombre: string; curso: string; nota: number; examen: number | null; trabajos: number | null; nivel: Nivel; probabilidad: number }[];
  perfil: { clave: string; etiqueta: string; grupo: string; valor: string | number; texto: string }[];
}

export interface Aula {
  grado: string;
  nivel_educativo: string;
  estudiantes: number;
  alto: number;
  medio: number;
  bajo: number;
  promedio: number;
}

export interface Campo {
  clave: string;
  etiqueta: string;
  grupo: "historial" | "familia" | "habitos";
  valor: string | number;
  opciones?: { valor: string | number; texto: string }[];
  minimo?: number;
  maximo?: number;
}

export interface ResultadoEvaluacion {
  probabilidad: number;
  nivel: Nivel;
  mensaje: string;
  umbrales: { medio: number; alto: number };
  modelo: string;
}

interface Medidas {
  matriz: { verdaderos_negativos: number; falsos_positivos: number; falsos_negativos: number; verdaderos_positivos: number };
  exactitud: number;
}

export interface Modelo {
  disponible: boolean;
  mensaje?: string;
  fecha_entrenamiento: string;
  version: string;
  nombre: string;
  base: { nombre: string; autores: string; origen: string; enlace: string; descripcion: string; registros: number; estudiantes: number; con_mal_resultado: number };
  que_predice: string;
  variables: string[];
  no_consideradas: string[];
  red: { arquitectura: string; capas_ocultas: number[]; entradas: number; activacion: string; optimizador: string; escalado: string; epocas: number; perdida_final: number; curva_de_perdida: number[] };
  particion: { entrenamiento: number; prueba: number; metodo: string };
  validacion_cruzada: Record<string, { media: number; desviacion: number }>;
  entrenamiento: Medidas;
  prueba: Medidas & { auc_roc: number; le_va_mal: { precision: number; recall: number; f1: number }; le_va_bien: { precision: number; recall: number; f1: number } };
  exactitud_sin_modelo: number;
  niveles: { alto_desde: number; medio_desde: number; equivalencia: string; curva: { nota: number; probabilidad: number }[] };
  aplicacion_colegio: null | {
    fecha: string;
    como: string;
    casos: number;
    estudiantes: number;
    les_fue_mal: number;
    proporcion: number;
    auc_roc: number;
    niveles: Record<"alto" | "medio" | "bajo", { casos: number; les_fue_mal: number }>;
    alerta_solo_alto: Medidas & { detecta: number; aciertos: number };
    alerta_medio_y_alto: Medidas & { detecta: number; aciertos: number };
    exactitud_sin_modelo: number;
  };
}

export interface Calidad {
  disponible: boolean;
  fecha?: string;
  ejecuciones?: number;
  criticas?: number;
  avisos?: number;
  reglas?: { regla: string; severidad: string; cantidad: number; detalle: string; tipo: "critica" | "aviso" }[];
}

export interface Carga {
  id: number;
  fecha: string;
  archivo: string;
  tipo_datos: "practica" | "reales";
  filas_origen: number;
  notas_leidas: number;
  notas_cargadas: number;
  notas_repetidas: number;
  notas_rechazadas: number;
}

export interface Ejecucion {
  fecha: string;
  criticas: number;
  avisos: number;
  correctas: number;
}

async function pedir<T>(ruta: string, opciones?: RequestInit): Promise<T> {
  const r = await fetch(`${API_URL}${ruta}`, opciones);
  if (!r.ok) {
    let detalle = `Error ${r.status}`;
    try {
      detalle = (await r.json()).detail ?? detalle;
    } catch {
      /* la respuesta no era JSON */
    }
    throw new Error(detalle);
  }
  return r.json();
}

export const api = {
  estado: () => pedir<Estado>("/api/estado"),
  estudiantes: () => pedir<Estudiante[]>("/api/estudiantes"),
  ficha: (codigo: string) => pedir<Ficha>(`/api/estudiantes/${encodeURIComponent(codigo)}`),
  aulas: () => pedir<Aula[]>("/api/aulas"),
  evaluarAula: (grado?: string) =>
    pedir<{ evaluados: number; niveles: { alto: number; medio: number; bajo: number }; milisegundos: number; fecha: string; estudiantes: Estudiante[] }>(
      `/api/aulas/evaluar${grado ? `?grado=${encodeURIComponent(grado)}` : ""}`,
      { method: "POST" },
    ),
  modelo: () => pedir<Modelo>("/api/modelo"),
  calidad: () => pedir<Calidad>("/api/calidad"),
  cargas: () => pedir<Carga[]>("/api/cargas"),
  historialCalidad: () => pedir<Ejecucion[]>("/api/calidad/historial"),
  ejecutarValidacion: () => pedir<{ criticas: number; avisos: number; fecha: string }>("/api/calidad/ejecutar", { method: "POST" }),
  urlExportarNotas: () => `${API_URL}/api/exportar-csv`,
  formulario: () => pedir<{ nota_aprobatoria: number; campos: Campo[] }>("/api/formulario"),
  evaluar: (cuerpo: { nota_actual: number; nota_anterior: number | null; perfil: Record<string, string | number> }) =>
    pedir<ResultadoEvaluacion>("/api/evaluar", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) }),
  urlReporte: (codigo: string) => `${API_URL}/api/estudiantes/${encodeURIComponent(codigo)}/reporte.pdf`,
  urlExportarAula: (grado?: string) => `${API_URL}/api/aulas/exportar.csv${grado ? `?grado=${encodeURIComponent(grado)}` : ""}`,
};
