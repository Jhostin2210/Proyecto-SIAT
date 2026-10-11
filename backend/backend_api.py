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
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from etl.cargar_notas import cargar_archivo
from etl.database import engine
from etl.informe import ALTO, BAJO, MEDIO, nivel_de
from etl.modelo_datos import NIVELES_RIESGO, calidad_datos, cargas, crear_tablas, cursos, estudiantes, matriculas, notas, perfiles, periodos, predicciones
from etl.perfil import COLUMNAS, DESCRIPCION, leer_base_publica, para_el_modelo
from etl.reporte_pdf import reporte_estudiante
from etl.riesgo import calcular_riesgo, cargar_modelo, evaluar_cursos, informes
from etl.validar_datos import validar
from etl.variables import NOTA_APROBATORIA

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_REPORTE = os.path.join(BASE_DIR, "data", "red_neuronal_report.json")
RUTA_APLICACION = os.path.join(BASE_DIR, "data", "aplicacion_colegio.json")
DATOS_PRACTICA = os.path.join(BASE_DIR, "data", "notas_practica.csv")
ORDEN_NIVEL = {ALTO: 0, MEDIO: 1, BAJO: 2}


def preparar_base():
    """Crea las tablas. Si la base está vacía y hay datos de práctica, los carga para la demostración."""
    crear_tablas(engine)
    with engine.connect() as cx:
        vacia = (cx.execute(select(func.count()).select_from(estudiantes)).scalar() or 0) == 0
    if vacia and os.path.exists(DATOS_PRACTICA) and os.getenv("CARGAR_DATOS_PRACTICA", "true").lower() == "true":
        cargar_archivo(DATOS_PRACTICA, engine)
        validar(engine)
        return
    # Si el modelo cambió desde el último cálculo, se recalcula el nivel de riesgo.
    modelo = cargar_modelo()
    with engine.connect() as cx:
        version = cx.execute(select(predicciones.c.version).limit(1)).scalar()
    if not vacia and version != (modelo["version"] if modelo else None):
        calcular_riesgo(engine)


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
    version="4.0.0",
    lifespan=ciclo_de_vida,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


def _json(ruta):
    if not os.path.exists(ruta):
        return None
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


# ───────────────────────── Resultados en memoria ─────────────────────────
# Los informes se calculan con el modelo sobre toda la base; se guardan mientras la base no cambie.
_memoria = {"clave": None}


def _nombre(fila) -> str:
    return f"{fila['nombres']} {fila['apellido']}" if fila["apellido"] else fila["nombres"]


def _resultados() -> dict:
    """{'estudiantes': [...], 'informes': {id: informe}, 'origen': {...}, 'casos': DataFrame}"""
    with engine.connect() as cx:
        clave = (
            cx.execute(select(func.count()).select_from(notas)).scalar(),
            cx.execute(select(func.count()).select_from(perfiles)).scalar(),
            str(cx.execute(select(func.max(predicciones.c.fecha))).scalar()),
            os.path.getmtime(RUTA_REPORTE) if os.path.exists(RUTA_REPORTE) else 0,
        )
        if _memoria["clave"] == clave:
            return _memoria["valor"]
        personas = {f["id"]: dict(f) for f in cx.execute(select(estudiantes)).mappings()}
    nombres = {i: _nombre(p) for i, p in personas.items()}
    por_estudiante, origen = informes(engine, nombres)
    casos, _ = evaluar_cursos(engine)
    lista = []
    for est, inf in por_estudiante.items():
        p = personas[est]
        notas_curso = [c["nota"] for c in inf["cursos"]]
        lista.append(
            {
                "id": est,
                "codigo": p["codigo"],
                "nombre": nombres[est],
                "nombres": p["nombres"],
                "apellido": p["apellido"],
                "grado": inf["grado"],
                "nivel_educativo": inf["nivel_educativo"],
                "periodo": inf["periodo"],
                "periodo_nombre": inf["periodo_nombre"],
                "promedio": round(sum(notas_curso) / len(notas_curso), 1),
                "nivel": inf["nivel"],
                "probabilidad": inf["probabilidad"],
                "resumen": inf["resumen"],
                "cursos": len(inf["cursos"]),
                "cursos_alto": sum(1 for c in inf["cursos"] if c["nivel"] == ALTO),
                "cursos_medio": sum(1 for c in inf["cursos"] if c["nivel"] == MEDIO),
            }
        )
    lista.sort(key=lambda e: (ORDEN_NIVEL[e["nivel"]], -e["probabilidad"]))
    _memoria.update(clave=clave, valor={"estudiantes": lista, "informes": por_estudiante, "origen": origen, "casos": casos, "personas": personas})
    return _memoria["valor"]


def _conteo(lista) -> dict:
    return {"alto": sum(1 for e in lista if e["nivel"] == ALTO), "medio": sum(1 for e in lista if e["nivel"] == MEDIO), "bajo": sum(1 for e in lista if e["nivel"] == BAJO)}


def _orden_grado(grado: str) -> tuple:
    return (0 if "Primaria" in grado else 1 if "Secundaria" in grado else -1, grado)


# ───────────────────────── Estado ─────────────────────────
@app.get("/")
def raiz():
    return {"app": "SIA-T - Sistema Inteligente de Alerta Temprana", "estado": "Servidor funcionando", "version": app.version, "fecha_servidor": datetime.now().isoformat(), "documentacion": "/docs"}


@app.get("/api/estado", summary="Qué datos se muestran y de dónde sale el nivel de riesgo")
def obtener_estado():
    try:
        with engine.connect() as cx:
            n_est = cx.execute(select(func.count()).select_from(estudiantes)).scalar() or 0
            n_notas = cx.execute(select(func.count()).select_from(notas)).scalar() or 0
            lista_periodos = [{"codigo": c, "nombre": n} for c, n in cx.execute(select(periodos.c.codigo, periodos.c.nombre).order_by(periodos.c.orden))]
            ultima = cx.execute(select(cargas).order_by(cargas.c.id.desc())).mappings().first()
            prediccion = cx.execute(select(predicciones.c.origen, predicciones.c.version, predicciones.c.fecha).limit(1)).first()
        base = {"conectada": True}
    except Exception as e:
        n_est = n_notas = 0
        lista_periodos, ultima, prediccion = [], None, None
        base = {"conectada": False, "error": str(e)}
    reporte = _json(RUTA_REPORTE)
    con_modelo = bool(prediccion and prediccion.origen == "modelo")
    return {
        "base_de_datos": base,
        "tipo_datos": ultima["tipo_datos"] if ultima else None,
        "estudiantes": n_est,
        "notas": n_notas,
        "periodos": lista_periodos,
        "periodo_actual": lista_periodos[-1] if lista_periodos else None,
        "ultima_carga": {"fecha": str(ultima["fecha"]), "archivo": ultima["archivo"], "notas_cargadas": ultima["notas_cargadas"]} if ultima else None,
        "nivel_de_riesgo": {
            "origen": prediccion.origen if prediccion else None,
            "version": prediccion.version if prediccion else None,
            "fecha": str(prediccion.fecha) if prediccion else None,
            "explicacion": "Red neuronal que estima, para cada curso, la probabilidad de que al estudiante le vaya mal." if con_modelo else "Regla por nota. Se usa cuando no hay un modelo entrenado.",
        },
        "modelo": {"nombre": reporte["nombre"], "arquitectura": reporte["red"]["arquitectura"], "base": reporte["base"]["nombre"], "exactitud": reporte["prueba"]["exactitud"], "fecha_entrenamiento": reporte["fecha_entrenamiento"]} if reporte else None,
        "niveles_riesgo": list(NIVELES_RIESGO),
    }


# ───────────────────────── Estudiantes y aulas ─────────────────────────
@app.get("/api/estudiantes", summary="Estudiantes con su nivel de riesgo general en su último periodo")
def listar_estudiantes(grado: Optional[str] = None, nivel: Optional[str] = None):
    lista = _resultados()["estudiantes"]
    if grado:
        lista = [e for e in lista if e["grado"] == grado]
    if nivel:
        lista = [e for e in lista if e["nivel"] == nivel]
    return lista


def _est_por_codigo(codigo: str):
    r = _resultados()
    est = next((e for e in r["estudiantes"] if e["codigo"] == codigo), None)
    if not est:
        raise HTTPException(status_code=404, detail="No existe un estudiante con ese código o no tiene notas.")
    return r, est


@app.get("/api/estudiantes/{codigo}", summary="Ficha del estudiante: informe, cursos, historial y perfil")
def ficha_estudiante(codigo: str):
    r, est = _est_por_codigo(codigo)
    casos = r["casos"]
    propios = casos[casos["est"] == est["id"]].sort_values(["orden", "curso"])
    historial = [
        {"periodo": f.periodo, "periodo_nombre": f.periodo_nombre, "curso": f.curso, "nota": round(float(f.nota), 1), "examen": None if pd.isna(f.examen) else round(float(f.examen), 1), "trabajos": None if pd.isna(f.trabajos) else round(float(f.trabajos), 1), "nivel": f.nivel, "probabilidad": round(float(f.probabilidad), 3), "por_validar": bool(f.por_validar)}
        for f in propios.itertuples()
    ]
    with engine.connect() as cx:
        perfil = cx.execute(select(perfiles).where(perfiles.c.estudiante_id == est["id"])).mappings().first()
        anios = [dict(m) for m in cx.execute(select(matriculas.c.anio, matriculas.c.nivel_educativo, matriculas.c.grado).where(matriculas.c.estudiante_id == est["id"]).order_by(matriculas.c.anio)).mappings()]
    datos_perfil = []
    if perfil:
        for clave, d in DESCRIPCION.items():
            valor = perfil[clave]
            datos_perfil.append({"clave": clave, "etiqueta": d["etiqueta"], "grupo": d["grupo"], "valor": valor, "texto": d["opciones"].get(valor, str(valor)) if "opciones" in d else str(valor)})
    return {**est, "matriculas": anios, "informe": r["informes"][est["id"]], "historial": historial, "perfil": datos_perfil}


@app.get("/api/estudiantes/{codigo}/reporte.pdf", summary="Reporte del estudiante en PDF")
def reporte_pdf(codigo: str):
    r, est = _est_por_codigo(codigo)
    modelo = _json(RUTA_REPORTE)
    with engine.connect() as cx:
        ultima = cx.execute(select(cargas.c.tipo_datos).order_by(cargas.c.id.desc())).scalar()
    contenido = reporte_estudiante(est, r["informes"][est["id"]], f"red neuronal {modelo['red']['arquitectura']}" if modelo and r["origen"]["origen"] == "modelo" else "regla por nota", ultima == "practica")
    return Response(content=contenido, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="reporte_{codigo}_{datetime.now():%Y%m%d}.pdf"'})


def _aulas(lista) -> list:
    grados = {}
    for e in lista:
        grados.setdefault(e["grado"], []).append(e)
    return [
        {"grado": g, "nivel_educativo": grupo[0]["nivel_educativo"], "estudiantes": len(grupo), **_conteo(grupo), "promedio": round(sum(e["promedio"] for e in grupo) / len(grupo), 1)}
        for g, grupo in sorted(grados.items(), key=lambda x: _orden_grado(x[0]))
    ]


@app.get("/api/aulas", summary="Resumen por aula: estudiantes y niveles de riesgo")
def listar_aulas():
    return _aulas(_resultados()["estudiantes"])


@app.post("/api/aulas/evaluar", summary="Vuelve a evaluar con el modelo a todos los estudiantes, o a un aula")
def evaluar_aula(grado: Optional[str] = None):
    inicio = time.perf_counter()
    resumen = calcular_riesgo(engine)
    _memoria["clave"] = None
    lista = _resultados()["estudiantes"]
    if grado:
        lista = [e for e in lista if e["grado"] == grado]
    return {"grado": grado, "evaluados": len(lista), "niveles": _conteo(lista), "origen": resumen.get("origen"), "version": resumen.get("version"), "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "milisegundos": round((time.perf_counter() - inicio) * 1000), "estudiantes": lista}


@app.get("/api/aulas/exportar.csv", summary="Exporta el resultado de un aula, o de todas")
def exportar_aula(grado: Optional[str] = None):
    lista = [e for e in _resultados()["estudiantes"] if not grado or e["grado"] == grado]
    salida = io.StringIO()
    w = csv.writer(salida)
    w.writerow(["codigo", "estudiante", "grado", "periodo", "promedio", "nivel_de_riesgo", "probabilidad", "cursos_en_riesgo_alto", "cursos_en_riesgo_medio", "resumen"])
    w.writerows([[e["codigo"], e["nombre"], e["grado"], e["periodo_nombre"], e["promedio"], e["nivel"], e["probabilidad"], e["cursos_alto"], e["cursos_medio"], e["resumen"]] for e in lista])
    return Response(content="﻿" + salida.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="riesgo_por_aula.csv"'})


# ───────────────────────── Modelo ─────────────────────────
@app.get("/api/modelo", summary="Cómo se entrenó y probó el modelo, y qué pasó al aplicarlo en el colegio")
def obtener_modelo():
    reporte = _json(RUTA_REPORTE)
    if not reporte:
        return {"disponible": False, "mensaje": "Todavía no hay un modelo entrenado. El nivel de riesgo sale de una regla por nota."}
    return {"disponible": True, **reporte, "aplicacion_colegio": _json(RUTA_APLICACION)}


_tipico = {}


def _valores_tipicos() -> dict:
    """Valor más frecuente de cada dato del perfil en la base de entrenamiento: punto de partida del formulario."""
    if not _tipico:
        publica = leer_base_publica()
        for clave, columna in COLUMNAS.items():
            serie = publica[columna]
            valor = int(serie.median()) if clave in ("edad", "inasistencias") else serie.mode().iloc[0]
            _tipico[clave] = valor.item() if hasattr(valor, "item") else valor
    return _tipico


@app.get("/api/formulario", summary="Campos del formulario «Evaluar estudiante» con sus opciones y valores de partida")
def formulario():
    tipicos = _valores_tipicos()
    campos = []
    for clave, d in DESCRIPCION.items():
        campo = {"clave": clave, "etiqueta": d["etiqueta"], "grupo": d["grupo"], "valor": tipicos[clave]}
        if "opciones" in d:
            campo["opciones"] = [{"valor": v, "texto": t} for v, t in d["opciones"].items()]
        else:
            campo.update(minimo=d["minimo"], maximo=d["maximo"])
        campos.append(campo)
    return {"nota_aprobatoria": NOTA_APROBATORIA, "campos": campos}


class EntradaEvaluacion(BaseModel):
    nota_actual: float = Field(..., ge=0, le=20, description="Nota del curso en el periodo actual")
    nota_anterior: Optional[float] = Field(None, ge=0, le=20, description="Nota del curso en el periodo anterior, si se conoce")
    perfil: dict = Field(default_factory=dict, description="Datos del perfil; los que falten toman el valor más frecuente")


@app.post("/api/evaluar", summary="Evalúa un caso con el modelo. No guarda nada.")
def evaluar(entrada: EntradaEvaluacion):
    modelo = cargar_modelo()
    if not modelo:
        raise HTTPException(status_code=503, detail="No hay un modelo entrenado.")
    perfil = {**_valores_tipicos(), **{k: v for k, v in entrada.perfil.items() if k in COLUMNAS and v not in (None, "")}}
    for clave, d in DESCRIPCION.items():
        if "opciones" in d:
            opciones = {str(k): k for k in d["opciones"]}
            if str(perfil[clave]) not in opciones:
                raise HTTPException(status_code=422, detail=f"Valor no válido en «{d['etiqueta']}».")
            perfil[clave] = opciones[str(perfil[clave])]
        else:
            try:
                perfil[clave] = min(d["maximo"], max(d["minimo"], int(perfil[clave])))
            except (TypeError, ValueError):
                raise HTTPException(status_code=422, detail=f"Valor no válido en «{d['etiqueta']}».")
    ajuste = NOTA_APROBATORIA - modelo["aprobatoria"]
    fila = {COLUMNAS[k]: v for k, v in perfil.items()}
    fila["G2"] = min(20, max(0, entrada.nota_actual - ajuste))
    fila["G1"] = min(20, max(0, (entrada.nota_anterior if entrada.nota_anterior is not None else entrada.nota_actual) - ajuste))
    X = para_el_modelo(pd.DataFrame([fila]))[modelo["variables"]]
    probabilidad = float(modelo["pipeline"].predict_proba(X)[0, 1])
    nivel = nivel_de(probabilidad, modelo["umbrales"])
    mensajes = {
        ALTO: "Riesgo alto de que le vaya mal en el curso. Conviene que el tutor intervenga esta semana.",
        MEDIO: "Riesgo medio. Conviene hacerle seguimiento en el próximo periodo.",
        BAJO: "Riesgo bajo. Continuar con el seguimiento regular.",
    }
    return {"probabilidad": round(probabilidad, 3), "nivel": nivel, "mensaje": mensajes[nivel], "umbrales": {k: round(v, 3) for k, v in modelo["umbrales"].items()}, "modelo": modelo["version"]}


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
