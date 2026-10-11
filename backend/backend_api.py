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

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from etl.cargar_notas import cargar_archivo
from etl.database import engine
from etl.modelo_datos import NIVELES_RIESGO, calidad_datos, cargas, crear_tablas, cursos, estudiantes, matriculas, notas, periodos, predicciones
from etl.riesgo import cargar_modelo
from etl.validar_datos import validar
from etl.variables import AREAS, VARIABLES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(BASE_DIR, "data", "metrics_report.json")
DATOS_PRACTICA = os.path.join(BASE_DIR, "data", "notas_practica.csv")
TRABAJOS = ("cuaderno", "libro", "oral", "practica", "exposicion", "trabajo")


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
    version="3.0.0",
    lifespan=ciclo_de_vida,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


def _reporte():
    if not os.path.exists(REPORT_PATH):
        return None
    with open(REPORT_PATH, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def _media(valores):
    valores = [v for v in valores if v is not None]
    return round(sum(valores) / len(valores), 1) if valores else None


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
            lista_periodos = [{"codigo": c, "nombre": n} for c, n in cx.execute(select(periodos.c.codigo, periodos.c.nombre).order_by(periodos.c.orden))]
            ultima = cx.execute(select(cargas).order_by(cargas.c.id.desc())).mappings().first()
            prediccion = cx.execute(select(predicciones.c.origen, predicciones.c.version).limit(1)).first()
        base = {"conectada": True}
    except Exception as e:
        n_est = n_notas = 0
        lista_periodos, ultima, prediccion = [], None, None
        base = {"conectada": False, "error": str(e)}
    reporte = _reporte()
    con_modelo = bool(prediccion and prediccion.origen == "modelo")
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
            "origen": prediccion.origen if prediccion else None,
            "version": prediccion.version if prediccion else None,
            "explicacion": (
                "Modelo de Machine Learning entrenado y validado con datos reales del colegio. Estima la probabilidad de desaprobar el próximo examen en cada curso."
                if con_modelo
                else "Regla simple y visible. Se usa cuando no hay un modelo entrenado."
            ),
        },
        "modelo": {"nombre": reporte["modelo_elegido"]["nombre"], "fecha_entrenamiento": reporte["fecha_entrenamiento"], "casos": reporte["datos"]["casos"]} if reporte else None,
        "metricas_disponibles": bool(reporte),
        "niveles_riesgo": list(NIVELES_RIESGO),
    }


# ───────────────────────── Estudiantes ─────────────────────────
@app.get("/api/estudiantes", summary="Estudiantes con sus promedios y su nivel de riesgo en su último periodo")
def listar_estudiantes(grado: Optional[str] = None, nivel_riesgo: Optional[str] = None):
    with engine.connect() as cx:
        orden_periodo = {pid: (codigo, orden, nombre) for pid, codigo, orden, nombre in cx.execute(select(periodos.c.id, periodos.c.codigo, periodos.c.orden, periodos.c.nombre))}
        if not orden_periodo:
            return []
        matricula = {}
        for m in cx.execute(select(matriculas).order_by(matriculas.c.anio)).mappings():
            matricula[m["estudiante_id"]] = m  # queda la del año más reciente
        nivel_de = {p.estudiante_id: p for p in cx.execute(select(predicciones))}
        # Promedios por estudiante, periodo y tipo de nota.
        acumulado = {}
        for est, per, comp, nota in cx.execute(select(notas.c.estudiante_id, notas.c.periodo_id, notas.c.componente, notas.c.nota).where(notas.c.componente != "promedio")):
            acumulado.setdefault(est, {}).setdefault(per, {}).setdefault(comp, []).append(nota)
        resultado = []
        for est in cx.execute(select(estudiantes).order_by(estudiantes.c.codigo)).mappings():
            pred, m, por_periodo = nivel_de.get(est["id"]), matricula.get(est["id"]), acumulado.get(est["id"], {})
            if not pred or not m or pred.periodo_id not in por_periodo:
                continue
            actual = por_periodo[pred.periodo_id]
            academicas = [n for comp, lista in actual.items() if comp != "conducta" for n in lista]
            anteriores = sorted((p for p in por_periodo if orden_periodo[p][1] < orden_periodo[pred.periodo_id][1]), key=lambda p: orden_periodo[p][1])
            previo = [n for comp, lista in por_periodo[anteriores[-1]].items() if comp != "conducta" for n in lista] if anteriores else []
            trabajos = [n for comp in TRABAJOS for n in actual.get(comp, [])]
            resultado.append(
                {
                    "id": est["id"],
                    "codigo_anonimizado": est["codigo"],
                    "nombres": est["nombres"],
                    "apellidos": est["apellido"] or "",
                    "grado": m["grado"],
                    "seccion": "Única",
                    "nivel_educativo": m["nivel_educativo"],
                    "periodo": orden_periodo[pred.periodo_id][0],
                    "periodo_nombre": orden_periodo[pred.periodo_id][2],
                    "notas": {
                        "nota_libro": _media(actual.get("libro", [])),
                        "nota_cuaderno": _media(actual.get("cuaderno", [])),
                        "nota_examen": _media(actual.get("examen", [])),
                        "nota_trabajos": _media(trabajos),
                        "conducta": _media(actual.get("conducta", [])),
                        "nota_final": _media(academicas),
                    },
                    "nota_final": _media(academicas),
                    "promedio_anterior": _media(previo),
                    "inasistencias": None,  # la asistencia aún no se registra en formato digital
                    "estado_pension": "no_registrado",  # no forma parte de los datos del sistema
                    "ultima_prediccion": {"probabilidad": pred.probabilidad, "nivel": pred.nivel_riesgo, "origen": pred.origen, "motivo": pred.motivo, "fecha": str(pred.fecha)},
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
            select(periodos.c.codigo, cursos.c.nombre, notas.c.componente, notas.c.nota, notas.c.validada)
            .select_from(notas.join(periodos).join(cursos))
            .where(notas.c.estudiante_id == est["id"])
            .order_by(periodos.c.orden, cursos.c.nombre)
        ).all()
        historial = [dict(m) for m in cx.execute(select(matriculas.c.anio, matriculas.c.nivel_educativo, matriculas.c.grado).where(matriculas.c.estudiante_id == est["id"]).order_by(matriculas.c.anio)).mappings()]
        pred = cx.execute(select(predicciones).where(predicciones.c.estudiante_id == est["id"])).mappings().first()
    por_curso = {}
    for periodo, curso, componente, nota, validada in filas:
        fila = por_curso.setdefault((periodo, curso), {"periodo": periodo, "curso": curso, "por_validar": False})
        fila[componente] = nota
        fila["por_validar"] = fila["por_validar"] or not validada
    return {
        "codigo": est["codigo"],
        "nombres": est["nombres"],
        "apellido": est["apellido"],
        "matriculas": historial,
        "notas": list(por_curso.values()),
        "riesgo": {"nivel": pred["nivel_riesgo"], "probabilidad": pred["probabilidad"], "origen": pred["origen"], "motivo": pred["motivo"]} if pred else None,
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


@app.get("/api/exportar-csv", summary="Exporta las notas de la base por código de estudiante, sin nombres")
def exportar_csv():
    salida = io.StringIO()
    w = csv.writer(salida)
    w.writerow(["codigo", "curso", "area", "periodo", "tipo_evaluacion", "componente", "nota", "validada"])
    with engine.connect() as cx:
        consulta = (
            select(estudiantes.c.codigo, cursos.c.nombre, cursos.c.area, periodos.c.codigo, notas.c.tipo_evaluacion, notas.c.componente, notas.c.nota, notas.c.validada)
            .select_from(notas.join(estudiantes).join(cursos).join(periodos))
            .order_by(estudiantes.c.codigo, periodos.c.orden, cursos.c.nombre)
        )
        w.writerows(cx.execute(consulta).all())
    respuesta = StreamingResponse(io.BytesIO(salida.getvalue().encode("utf-8")), media_type="text/csv")
    respuesta.headers["Content-Disposition"] = "attachment; filename=notas_sia_t.csv"
    return respuesta


@app.get("/api/reporte-metricas", summary="Métricas de la validación del modelo")
def obtener_reporte_metricas():
    """Devuelve el reporte del último entrenamiento. No hay valores por defecto: si no existe, lo indica."""
    reporte = _reporte()
    if reporte:
        return {"disponible": True, **reporte}
    return {"disponible": False, "mensaje": "Todavía no hay un modelo entrenado. El nivel de riesgo sale de una regla simple."}


# ───────────────────────── Simulador ─────────────────────────
class StudentPredictInput(BaseModel):
    nivel_educativo: str = Field(..., description="'primaria' o 'secundaria'")
    nota_libro: float = Field(..., ge=0, le=20)
    nota_cuaderno: float = Field(..., ge=0, le=20)
    nota_examen: float = Field(..., ge=0, le=20)
    conducta: Optional[float] = Field(None, ge=0, le=20)
    examen_previo: Optional[float] = Field(None, ge=0, le=20, description="Examen del periodo anterior, si se conoce")
    area: Optional[str] = Field(None, description="Área del curso")
    # Campos de la versión anterior del simulador: se aceptan, pero el modelo no los usa.
    inasistencias: Optional[int] = None
    estado_pension: Optional[str] = None


class PredictionOutput(BaseModel):
    probabilidad_riesgo: float
    nivel_riesgo: str
    mensaje_alerta: str
    factores_criticos: List[str]
    modelo_usado: str


MENSAJES = {
    "Riesgo bajo": "Desempeño estable. Continuar con el seguimiento regular.",
    "Riesgo medio": "Se recomienda que el tutor revise el caso.",
    "Riesgo alto": "Alerta: riesgo alto de desaprobar el próximo examen. Requiere atención del tutor esta semana.",
}


@app.post("/api/predecir", response_model=PredictionOutput, summary="Simulador: probabilidad de desaprobar el próximo examen de un curso")
def predecir_riesgo(entrada: StudentPredictInput):
    """Aplica el modelo entrenado a un caso hipotético de un curso. Los datos que no se indican se tratan como desconocidos."""
    modelo = cargar_modelo()
    if not modelo:
        raise HTTPException(status_code=503, detail="No hay un modelo entrenado en este servidor.")
    trabajos = [entrada.nota_libro, entrada.nota_cuaderno]
    caso = {v: float("nan") for v in VARIABLES}
    caso.update(
        examen=entrada.nota_examen,
        libro=entrada.nota_libro,
        cuaderno=entrada.nota_cuaderno,
        trabajos=sum(trabajos) / len(trabajos),
        minimo=min([entrada.nota_examen, *trabajos]),
        n_notas=3 + (entrada.conducta is not None),
        secundaria=int(entrada.nivel_educativo.lower() == "secundaria"),
        **{f"area_{a}": int(entrada.area == a) for a in AREAS},
    )
    if entrada.conducta is not None:
        caso["conducta"] = entrada.conducta
    if entrada.examen_previo is not None:
        caso["examen_previo"], caso["cambio_examen"] = entrada.examen_previo, entrada.nota_examen - entrada.examen_previo
    try:
        prob = float(modelo["pipeline"].predict_proba(pd.DataFrame([caso])[VARIABLES])[0][1])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo ejecutar el modelo: {str(e)}")

    factores = []
    if entrada.nota_examen < 11:
        factores.append(f"Examen desaprobado ({entrada.nota_examen:g})")
    if caso["trabajos"] < 13:
        factores.append(f"Trabajos con promedio bajo ({caso['trabajos']:.1f})")
    if entrada.examen_previo is not None and entrada.nota_examen - entrada.examen_previo <= -3:
        factores.append(f"El examen bajó {entrada.examen_previo - entrada.nota_examen:g} puntos")
    if entrada.conducta is not None and entrada.conducta < 11:
        factores.append(f"Conducta baja ({entrada.conducta:g})")
    nivel = "Riesgo alto" if prob >= modelo["umbrales"]["alto"] else "Riesgo medio" if prob >= modelo["umbrales"]["medio"] else "Riesgo bajo"
    reporte = _reporte()
    return PredictionOutput(
        probabilidad_riesgo=round(prob, 3),
        nivel_riesgo=nivel,
        mensaje_alerta=MENSAJES[nivel],
        factores_criticos=factores or ["Ninguno detectado"],
        modelo_usado=f"{reporte['modelo_elegido']['nombre']}, entrenado con datos reales" if reporte else modelo["version"],
    )
