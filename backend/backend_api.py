"""
SIA-T: API del Sistema Inteligente de Alerta Temprana.

Lee los datos de la base (PostgreSQL en producción, SQLite en pruebas y demostración).
No devuelve datos de relleno: si la base está vacía, lo dice. El endpoint /api/estado
informa siempre qué datos se están mostrando y de dónde sale el nivel de riesgo.
"""

import csv
import io
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from etl.cargar_notas import cargar_archivo
from etl.database import engine
from etl.modelo_datos import NIVELES_RIESGO, calidad_datos, cargas, crear_tablas, cursos, estudiantes, notas, periodos, predicciones
from etl.riesgo import ORIGEN as ORIGEN_REGLA
from etl.riesgo import VERSION_REGLA, promedios_por_periodo
from etl.validar_datos import validar

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "random_forest_riesgo.pkl")
REPORT_PATH = os.path.join(BASE_DIR, "data", "metrics_report.json")
DATOS_PRACTICA = os.path.join(BASE_DIR, "data", "notas_practica.csv")


def preparar_base():
    """Crea las tablas. Si la base está vacía y hay datos de práctica, los carga para la demostración."""
    crear_tablas(engine)
    with engine.connect() as cx:
        vacia = (cx.execute(select(func.count()).select_from(estudiantes)).scalar() or 0) == 0
    if vacia and os.path.exists(DATOS_PRACTICA) and os.getenv("CARGAR_DATOS_PRACTICA", "true").lower() == "true":
        cargar_archivo(DATOS_PRACTICA, engine)
        validar(engine)


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    try:
        preparar_base()
    except Exception as e:  # la API debe poder arrancar y explicar el problema en /api/estado
        print(f"[SIA-T] No se pudo preparar la base de datos: {e}")
    yield


app = FastAPI(
    title="SIA-T Backend API",
    description="API del Sistema Inteligente de Alerta Temprana del bajo rendimiento académico",
    version="2.0.0",
    lifespan=ciclo_de_vida,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


# ───────────────────────── Estado ─────────────────────────
@app.get("/")
def raiz():
    return {"app": "SIA-T - Sistema Inteligente de Alerta Temprana", "estado": "Servidor funcionando", "fecha_servidor": datetime.now().isoformat(), "documentacion": "/docs"}


@app.get("/api/estado", summary="Qué datos se muestran y de dónde sale el nivel de riesgo")
def obtener_estado():
    try:
        with engine.connect() as cx:
            n_est = cx.execute(select(func.count()).select_from(estudiantes)).scalar() or 0
            n_notas = cx.execute(select(func.count()).select_from(notas)).scalar() or 0
            lista_periodos = [{"codigo": c, "nombre": n} for c, n in cx.execute(select(periodos.c.codigo, periodos.c.nombre).order_by(periodos.c.codigo))]
            ultima = cx.execute(select(cargas).order_by(cargas.c.id.desc())).mappings().first()
        base = {"conectada": True}
    except Exception as e:
        n_est = n_notas = 0
        lista_periodos, ultima = [], None
        base = {"conectada": False, "error": str(e)}
    return {
        "base_de_datos": base,
        "origen_datos": "base_de_datos" if n_est else "sin_datos",
        "tipo_datos": ultima["tipo_datos"] if ultima else None,
        "estudiantes": n_est,
        "notas": n_notas,
        "periodos": lista_periodos,
        "periodo_actual": lista_periodos[-1] if lista_periodos else None,
        "ultima_carga": {"fecha": str(ultima["fecha"]), "archivo": ultima["archivo"], "notas_cargadas": ultima["notas_cargadas"]} if ultima else None,
        "nivel_de_riesgo": {
            "origen": ORIGEN_REGLA,
            "version": VERSION_REGLA,
            "explicacion": "Regla provisional y transparente. El modelo de Machine Learning se entrena y valida con datos reales en el Sprint 3.",
        },
        "modelo_demostracion_cargado": os.path.exists(MODEL_PATH),
        "metricas_disponibles": os.path.exists(REPORT_PATH),
        "niveles_riesgo": list(NIVELES_RIESGO),
    }


# ───────────────────────── Estudiantes ─────────────────────────
def _redondear(valor):
    return None if valor is None else round(valor, 1)


@app.get("/api/estudiantes", summary="Estudiantes (por código) con sus promedios y su nivel de riesgo en el último periodo")
def listar_estudiantes(grado: Optional[str] = None, nivel_riesgo: Optional[str] = None):
    with engine.connect() as cx:
        codigos_periodo = [c for (c,) in cx.execute(select(periodos.c.codigo).order_by(periodos.c.codigo))]
        if not codigos_periodo:
            return []
        actual = codigos_periodo[-1]
        anterior = codigos_periodo[-2] if len(codigos_periodo) > 1 else None
        promedios = promedios_por_periodo(cx)
        niveles = {
            fila.estudiante_id: fila
            for fila in cx.execute(
                select(predicciones.c.estudiante_id, predicciones.c.nivel_riesgo, predicciones.c.probabilidad, predicciones.c.origen, predicciones.c.motivo, predicciones.c.fecha)
                .select_from(predicciones.join(periodos))
                .where(periodos.c.codigo == actual)
            )
        }
        resultado = []
        for est in cx.execute(select(estudiantes).order_by(estudiantes.c.grado, estudiantes.c.codigo)).mappings():
            p = promedios.get(est["id"], {}).get(actual)
            nivel = niveles.get(est["id"])
            if not p or not nivel:
                continue
            previo = promedios.get(est["id"], {}).get(anterior) if anterior else None
            resultado.append(
                {
                    "id": est["id"],
                    "codigo_anonimizado": est["codigo"],
                    # La base no guarda nombres: la interfaz muestra el código.
                    "nombres": "Estudiante",
                    "apellidos": est["codigo"],
                    "grado": est["grado"],
                    "seccion": "Única",
                    "nivel_educativo": est["nivel_educativo"],
                    "periodo": actual,
                    "notas": {
                        "nota_libro": _redondear(p["libro"]),
                        "nota_cuaderno": _redondear(p["cuaderno"]),
                        "nota_examen": _redondear(p["examen"]),
                        "conducta": _redondear(p["conducta"]),
                        "nota_final": _redondear(p["promedio"]),
                    },
                    "nota_final": _redondear(p["promedio"]),
                    "promedio_anterior": _redondear(previo["promedio"]) if previo else None,
                    "inasistencias": None,  # la asistencia aún no se registra en formato digital
                    "estado_pension": "no_registrado",  # variable retirada de los datos
                    "ultima_prediccion": {
                        "probabilidad": nivel.probabilidad,
                        "nivel": nivel.nivel_riesgo,
                        "origen": nivel.origen,
                        "motivo": nivel.motivo,
                        "fecha": str(nivel.fecha),
                    },
                }
            )
    if grado:
        resultado = [e for e in resultado if e["grado"].lower() == grado.lower()]
    if nivel_riesgo:
        resultado = [e for e in resultado if e["ultima_prediccion"]["nivel"].lower() == nivel_riesgo.lower()]
    return resultado


@app.get("/api/estudiantes/{codigo}", summary="Ficha de un estudiante: notas por curso y periodo")
def ficha_estudiante(codigo: str):
    with engine.connect() as cx:
        est = cx.execute(select(estudiantes).where(estudiantes.c.codigo == codigo)).mappings().first()
        if not est:
            raise HTTPException(status_code=404, detail="No existe un estudiante con ese código.")
        filas = cx.execute(
            select(periodos.c.codigo, cursos.c.nombre, notas.c.componente, notas.c.nota)
            .select_from(notas.join(periodos).join(cursos))
            .where(notas.c.estudiante_id == est["id"])
            .order_by(periodos.c.codigo, cursos.c.nombre)
        ).all()
        historial = cx.execute(
            select(periodos.c.codigo, predicciones.c.nivel_riesgo, predicciones.c.origen, predicciones.c.motivo)
            .select_from(predicciones.join(periodos))
            .where(predicciones.c.estudiante_id == est["id"])
            .order_by(periodos.c.codigo)
        ).all()
    por_curso = {}
    for periodo, curso, componente, nota in filas:
        por_curso.setdefault((periodo, curso), {"periodo": periodo, "curso": curso})[componente] = nota
    return {
        "codigo": est["codigo"],
        "grado": est["grado"],
        "nivel_educativo": est["nivel_educativo"],
        "notas": list(por_curso.values()),
        "riesgo": [{"periodo": p, "nivel": n, "origen": o, "motivo": m} for p, n, o, m in historial],
    }


# ───────────────────────── Datos: cargas, calidad y exportación ─────────────────────────
@app.get("/api/cargas", summary="Bitácora de cargas de datos")
def listar_cargas():
    with engine.connect() as cx:
        return [{**fila, "fecha": str(fila["fecha"])} for fila in cx.execute(select(cargas).order_by(cargas.c.id.desc())).mappings()]


@app.get("/api/calidad", summary="Resultado de la última validación automática de los datos")
def ultima_validacion():
    with engine.connect() as cx:
        ultima = cx.execute(select(func.max(calidad_datos.c.fecha))).scalar()
        if ultima is None:
            return {"disponible": False, "mensaje": "Todavía no se ha ejecutado la validación."}
        reglas = [dict(f) for f in cx.execute(select(calidad_datos.c.regla, calidad_datos.c.severidad, calidad_datos.c.cantidad, calidad_datos.c.detalle).where(calidad_datos.c.fecha == ultima)).mappings()]
        ejecuciones = cx.execute(select(func.count(func.distinct(calidad_datos.c.fecha)))).scalar()
    return {
        "disponible": True,
        "fecha": str(ultima),
        "ejecuciones": ejecuciones,
        "criticas": sum(1 for r in reglas if r["severidad"] == "critica"),
        "avisos": sum(1 for r in reglas if r["severidad"] == "aviso"),
        "reglas": reglas,
    }


@app.post("/api/calidad/ejecutar", summary="Ejecuta ahora la validación de los datos")
def ejecutar_validacion():
    return validar(engine)


@app.get("/api/exportar-csv", summary="Exporta las notas de la base (por código, sin nombres) para entrenar el modelo")
def exportar_csv():
    salida = io.StringIO()
    w = csv.writer(salida)
    w.writerow(["codigo", "grado", "nivel", "curso", "periodo", "componente", "nota"])
    with engine.connect() as cx:
        consulta = (
            select(estudiantes.c.codigo, estudiantes.c.grado, estudiantes.c.nivel_educativo, cursos.c.nombre, periodos.c.codigo, notas.c.componente, notas.c.nota)
            .select_from(notas.join(estudiantes).join(cursos).join(periodos))
            .order_by(estudiantes.c.codigo, periodos.c.codigo, cursos.c.nombre)
        )
        w.writerows(cx.execute(consulta).all())
    respuesta = StreamingResponse(io.BytesIO(salida.getvalue().encode("utf-8")), media_type="text/csv")
    respuesta.headers["Content-Disposition"] = "attachment; filename=notas_sia_t.csv"
    return respuesta


@app.get("/api/reporte-metricas", summary="Métricas del último entrenamiento del modelo, si existen")
def obtener_reporte_metricas():
    """No devuelve valores por defecto: si no hay reporte de un entrenamiento real, lo indica."""
    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as archivo:
                reporte = json.load(archivo)
            reporte["disponible"] = True
            return reporte
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"No se pudo leer el reporte de métricas: {str(e)}")
    return {
        "disponible": False,
        "mensaje": "Todavía no hay un reporte de métricas. El modelo se entrenará y validará con datos reales del colegio en el Sprint 3.",
    }


# ───────────────────────── Simulador (modelo de demostración) ─────────────────────────
class StudentPredictInput(BaseModel):
    nivel_educativo: str = Field(..., description="'primaria' o 'secundaria'")
    nota_libro: float = Field(..., ge=0, le=20)
    nota_cuaderno: float = Field(..., ge=0, le=20)
    nota_examen: float = Field(..., ge=0, le=20)
    conducta: float = Field(..., ge=0, le=20)
    inasistencias: int = Field(..., ge=0)
    estado_pension: str = Field("al_dia", description="El modelo de demostración aún la requiere; se retirará al reentrenar")


class PredictionOutput(BaseModel):
    probabilidad_riesgo: float
    nivel_riesgo: str
    mensaje_alerta: str
    factores_criticos: List[str]
    modelo_usado: str


MENSAJES = {
    "Riesgo bajo": "Desempeño estable. Continuar con el seguimiento regular.",
    "Riesgo medio": "Se recomienda que el tutor revise el caso.",
    "Riesgo alto": "Alerta: riesgo alto de bajo rendimiento. Requiere atención del tutor esta semana.",
}


def clasificar_riesgo(prob: float) -> str:
    """Cortes provisionales del modelo de demostración: menos de 0.50, bajo; de 0.50 a 0.75, medio; 0.75 o más, alto."""
    return "Riesgo bajo" if prob < 0.50 else "Riesgo medio" if prob < 0.75 else "Riesgo alto"


@app.post("/api/predecir", response_model=PredictionOutput, summary="Simulador: calcula el riesgo de un caso con el modelo de demostración")
def predecir_riesgo(entrada: StudentPredictInput):
    """
    Usa el Random Forest de demostración, entrenado con un conjunto de datos sintético. Sirve para mostrar
    el flujo de predicción; no es el modelo definitivo ni se usa para el nivel de riesgo de los estudiantes.
    """
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=503, detail="El modelo de demostración no está disponible en este servidor.")
    try:
        paquete = joblib.load(MODEL_PATH)
        codificacion = paquete.get("encoding", {})
        fila = {
            "nivel_educativo": codificacion.get("nivel_educativo", {"primaria": 0, "secundaria": 1}).get(entrada.nivel_educativo.lower(), 1),
            "nota_libro": entrada.nota_libro,
            "nota_cuaderno": entrada.nota_cuaderno,
            "nota_examen": entrada.nota_examen,
            "conducta": entrada.conducta,
            "inasistencias": entrada.inasistencias,
            "estado_pension": codificacion.get("estado_pension", {"al_dia": 0, "atraso_leve": 1, "deuda": 2}).get(entrada.estado_pension.lower(), 0),
        }
        prob = float(paquete["model"].predict_proba(pd.DataFrame([fila])[paquete["features"]])[0][1])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo ejecutar el modelo de demostración: {str(e)}")

    factores = []
    promedio = (entrada.nota_libro + entrada.nota_cuaderno + entrada.nota_examen) / 3
    if promedio < 11:
        factores.append(f"Bajo promedio académico ({promedio:.1f})")
    if entrada.conducta < 11:
        factores.append(f"Baja nota de conducta ({entrada.conducta:.1f})")
    if entrada.inasistencias >= 3:
        factores.append(f"Frecuencia de inasistencias ({entrada.inasistencias})")
    nivel = clasificar_riesgo(prob)
    return PredictionOutput(
        probabilidad_riesgo=round(prob, 3),
        nivel_riesgo=nivel,
        mensaje_alerta=MENSAJES[nivel],
        factores_criticos=factores or ["Ninguno detectado"],
        modelo_usado="Random Forest de demostración (datos sintéticos)",
    )
