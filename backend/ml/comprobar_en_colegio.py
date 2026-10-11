"""
SIA-T: comprobación del modelo con los datos reales del colegio (paquete 1.3.3 de la EDT).

Uso, desde la carpeta backend, con la base de datos reales:

    $env:SQLITE_PATH = "data/privado/sia_t_reales.db"
    python -m ml.comprobar_en_colegio

El modelo no se entrena con estos datos: solo se le aplican. Para cada estudiante y curso se toma
el nivel que dio el modelo en un periodo y se compara con lo que pasó en el periodo siguiente
(si la nota del curso fue menor de 11).

Salida: data/aplicacion_colegio.json, con cifras agregadas y sin datos de ningún estudiante.
"""

import json
import os
import sys
from datetime import datetime

from sklearn.metrics import roc_auc_score

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.database import engine
from etl.informe import ALTO, BAJO, MEDIO
from etl.modelo_datos import cargas
from etl.riesgo import calcular_riesgo, evaluar_cursos
from etl.variables import NOTA_APROBATORIA

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


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    with engine.connect() as cx:
        tipo = cx.execute(cargas.select().order_by(cargas.c.id.desc())).mappings().first()
    if not tipo or tipo["tipo_datos"] != "reales":
        sys.exit("La base no tiene datos reales del colegio: la comprobación no se hace con datos de práctica.")
    resumen = calcular_riesgo(engine)
    casos, origen = evaluar_cursos(engine)
    d = casos.dropna(subset=["nota_siguiente"]).copy()
    d["mal"] = (d["nota_siguiente"] < NOTA_APROBATORIA).astype(int)
    niveles = {}
    for clave, nivel in (("alto", ALTO), ("medio", MEDIO), ("bajo", BAJO)):
        g = d[d["nivel"] == nivel]
        niveles[clave] = {"casos": int(len(g)), "les_fue_mal": int(g["mal"].sum())}
    reporte = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version_modelo": origen["version"],
        "como": "El modelo no se entrenó con estos datos. Se compara el nivel que dio en un periodo con la nota del curso en el periodo siguiente.",
        "casos": int(len(d)),
        "estudiantes": int(d["est"].nunique()),
        "les_fue_mal": int(d["mal"].sum()),
        "proporcion": round(float(d["mal"].mean()), 3),
        "auc_roc": round(float(roc_auc_score(d["mal"], d["probabilidad"])), 3),
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
