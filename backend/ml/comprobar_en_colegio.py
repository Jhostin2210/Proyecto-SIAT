"""
SIA-T: comprobación del modelo con los datos reales del colegio (paquete 1.3.3 de la EDT).

Uso, desde la carpeta backend, con la base de datos reales:

    $env:SQLITE_PATH = "data/privado/sia_t_reales.db"
    python -m ml.comprobar_en_colegio

El modelo no se entrena con estos datos: solo se le aplican. Para cada estudiante y curso se toma
el nivel que dio el modelo en un periodo y se compara con lo que pasó en el periodo siguiente
(si la nota del curso fue menor de 11).

Criterio desde el 15/11/2026 (SC-14): Cubicol guarda el promedio del curso después de la recuperación,
que nunca baja de 11. Por eso «le fue mal» se mide por competencias: si alguna competencia del curso
tuvo promedio menor de 11 en el periodo siguiente. Si no hay datos por competencia, se usa la nota.

Salida: data/aplicacion_colegio.json, con cifras agregadas y sin datos de ningún estudiante.
"""

import json
import os
import sys

import pandas as pd
from sklearn.metrics import roc_auc_score
from sqlalchemy import func, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.database import engine
from etl.informe import ALTO, BAJO, MEDIO
from etl.modelo_datos import cargas, competencias, cursos, periodos
from etl.riesgo import calcular_riesgo, evaluar_cursos
from etl.variables import NOTA_APROBATORIA
from etl.hora import ahora

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(BASE, "data", "aplicacion_colegio.json")


def _alerta(d, niveles) -> dict:
    aviso, mal = d["nivel"].isin(niveles), d["mal"] == 1
    vp, fp, fn, vn = int((aviso & mal).sum()), int((aviso & ~mal).sum()), int((~aviso & mal).sum()), int((~aviso & ~mal).sum())
    return {
        "matriz": {"verdaderos_negativos": vn, "falsos_positivos": fp, "falsos_negativos": fn, "verdaderos_positivos": vp},
        "exactitud": round((vp + vn) / len(d), 3),
        "detecta": round(vp / max(1, vp + fn), 3),
        "aciertos": round(vp / max(1, vp + fp), 3),
    }


def casos_con_resultado(engine) -> tuple:
    """Casos (estudiante, curso y periodo) con el nivel que dio el modelo y si «le fue mal» en el periodo siguiente.

    Devuelve (casos, origen, criterio, con_competencias). Lo usan esta comprobación y el ajuste de los cortes.
    """
    casos, origen = evaluar_cursos(engine)
    # Peor competencia de cada estudiante, curso y periodo; se compara la del periodo siguiente.
    with engine.connect() as cx:
        peor = pd.DataFrame(
            cx.execute(
                select(competencias.c.estudiante_id, cursos.c.nombre, periodos.c.codigo, func.min(competencias.c.nota))
                .select_from(competencias.join(cursos).join(periodos))
                .group_by(competencias.c.estudiante_id, cursos.c.nombre, periodos.c.codigo)
            ).all(),
            columns=["est", "curso", "periodo", "peor"],
        )
    casos = casos.sort_values(["est", "curso", "orden"]).merge(peor, on=["est", "curso", "periodo"], how="left")
    casos["peor_siguiente"] = casos.groupby(["est", "curso"])["peor"].shift(-1)
    d = casos.dropna(subset=["nota_siguiente"]).copy()
    con_competencias = d["peor_siguiente"].notna()
    d["mal"] = ((con_competencias & (d["peor_siguiente"] < NOTA_APROBATORIA)) | (~con_competencias & (d["nota_siguiente"] < NOTA_APROBATORIA))).astype(int)
    criterio = (
        "alguna competencia del curso tuvo promedio menor de 11 en el periodo siguiente (SC-14); "
        f"en {int((~con_competencias).sum())} de {len(d)} casos sin datos por competencia se usa la nota del curso"
    )
    return d, origen, criterio, con_competencias


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    with engine.connect() as cx:
        tipo = cx.execute(cargas.select().order_by(cargas.c.id.desc())).mappings().first()
    if not tipo or tipo["tipo_datos"] != "reales":
        sys.exit("La base no tiene datos reales del colegio: la comprobación no se hace con datos de práctica.")
    resumen = calcular_riesgo(engine, "comprobación del modelo")
    d, origen, criterio, con_competencias = casos_con_resultado(engine)
    niveles = {}
    for clave, nivel in (("alto", ALTO), ("medio", MEDIO), ("bajo", BAJO)):
        g = d[d["nivel"] == nivel]
        niveles[clave] = {"casos": int(len(g)), "les_fue_mal": int(g["mal"].sum())}
    reporte = {
        "fecha": ahora().strftime("%Y-%m-%d %H:%M"),
        "version_modelo": origen["version"],
        "como": "El modelo no se entrenó con estos datos. Se compara el nivel que dio en un periodo con lo que pasó en el periodo siguiente.",
        "criterio": criterio,
        "casos_por_competencia": int(con_competencias.sum()),
        "casos": int(len(d)),
        "estudiantes": int(d["est"].nunique()),
        "les_fue_mal": int(d["mal"].sum()),
        "proporcion": round(float(d["mal"].mean()), 3),
        # Sin casos desaprobados (o sin aprobados) el AUC no se puede calcular: se guarda vacío.
        "auc_roc": round(float(roc_auc_score(d["mal"], d["probabilidad"])), 3) if d["mal"].nunique() == 2 else None,
        "niveles": niveles,
        "alerta_solo_alto": _alerta(d, [ALTO]),
        "alerta_medio_y_alto": _alerta(d, [ALTO, MEDIO]),
        "exactitud_sin_modelo": round(float(1 - d["mal"].mean()), 3),
        "estudiantes_por_nivel": resumen.get("niveles"),
    }
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=1)
    print(json.dumps(reporte, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
