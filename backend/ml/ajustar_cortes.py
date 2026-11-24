"""
SIA-T: ajuste de los cortes de nivel del modelo con los datos del colegio (paquete 1.3.3, actividad A-3.2.1.2).

Uso, desde la carpeta backend, con la base de datos reales:

    $env:SQLITE_PATH = "data/privado/sia_t_reales.db"
    python -m ml.ajustar_cortes            # ajusta los cortes (cambia la configuración: requiere aprobación)
    python -m ml.ajustar_cortes --medir    # conserva los cortes vigentes y solo vuelve a medir con los datos nuevos

La red neuronal no se vuelve a entrenar: solo se eligen los dos cortes que llevan su probabilidad a los
niveles medio y alto. Para no medir con los mismos datos con que se ajusta:
- los cortes se ajustan con los casos de marzo y abril de 2026 (el resultado es el mes siguiente);
- el resultado se mide con los casos de mayo a agosto, que el ajuste no vio.

Reglas fijas (decididas antes de mirar la prueba):
- corte medio: el más alto que, en el ajuste, detecta al menos el 75 % de los casos con dificultad (meta del proyecto);
- corte alto: el más bajo con el que, en el ajuste, al menos el 45 % de las alertas acierta y hay 10 alertas o más.

También compara el modelo con una regla simple que no necesita modelo: alertar si la nota actual del curso es
baja, con su corte elegido de la misma manera. «Le fue mal» sigue el criterio de la SC-14 (competencias).

Salida: data/umbrales_colegio.json (cifras agregadas, sin datos de ningún estudiante). Si existe, la red usa
estos cortes en lugar de los de la base pública (etl/riesgo.py).
"""

import json
import os
import sys

import numpy as np
from sklearn.metrics import roc_auc_score

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.database import engine
from etl.hora import ahora
from ml.comprobar_en_colegio import casos_con_resultado

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(BASE, "data", "umbrales_colegio.json")
FIN_AJUSTE = "2026-04"  # casos de marzo y abril
META_DETECCION = 0.75
META_ACIERTO_ALTO = 0.45
MIN_ALERTAS_ALTO = 10


def _medidas(y, alerta) -> dict:
    vp, fp, fn = int((alerta & (y == 1)).sum()), int((alerta & (y == 0)).sum()), int((~alerta & (y == 1)).sum())
    return {"alertas": vp + fp, "detecta": round(vp / max(1, vp + fn), 3), "aciertos": round(vp / max(1, vp + fp), 3), "verdaderos_positivos": vp, "casos_con_dificultad": vp + fn}


def _corte_deteccion(puntaje, y):
    """El corte más alto cuyo «puntaje ≥ corte» detecta al menos la meta."""
    for c in sorted(set(np.round(puntaje, 4)), reverse=True):
        if _medidas(y, puntaje >= c)["detecta"] >= META_DETECCION:
            return float(c)
    return float(min(puntaje))


def _corte_acierto(puntaje, y):
    """El corte más bajo con al menos MIN_ALERTAS_ALTO alertas y aciertos ≥ META_ACIERTO_ALTO."""
    for c in sorted(set(np.round(puntaje, 4))):
        m = _medidas(y, puntaje >= c)
        if m["alertas"] >= MIN_ALERTAS_ALTO and m["aciertos"] >= META_ACIERTO_ALTO:
            return float(c)
    return None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    medir = "--medir" in sys.argv[1:]
    vigente = None
    if os.path.exists(RUTA):
        with open(RUTA, encoding="utf-8") as f:
            vigente = json.load(f)
        os.remove(RUTA)  # se mide siempre sobre la probabilidad de la red, no sobre cortes anteriores
    if medir and not vigente:
        sys.exit("No hay cortes vigentes que medir: ejecute primero el ajuste.")
    try:
        d, origen, criterio, _ = casos_con_resultado(engine)
    except BaseException:
        if vigente:
            with open(RUTA, "w", encoding="utf-8") as f:
                json.dump(vigente, f, ensure_ascii=False, indent=1)
        raise
    ajuste, prueba = d[d["periodo"] <= FIN_AJUSTE], d[d["periodo"] > FIN_AJUSTE]
    y_a, y_p = ajuste["mal"].values, prueba["mal"].values

    if medir:
        medio, alto = vigente["umbrales"]["medio"], vigente["umbrales"]["alto"]
    else:
        medio = _corte_deteccion(ajuste["probabilidad"].values, y_a)
        alto = _corte_acierto(ajuste["probabilidad"].values, y_a)
    # La regla simple usa la nota actual: más baja, más riesgo (puntaje = −nota).
    corte_nota = -_corte_deteccion(-ajuste["nota"].values, y_a)

    def resultado(datos, y):
        p = datos["probabilidad"].values
        return {
            "casos": int(len(datos)),
            "casos_con_dificultad": int(y.sum()),
            "auc_modelo": round(float(roc_auc_score(y, p)), 3),
            "auc_regla_simple": round(float(roc_auc_score(y, -datos["nota"].values)), 3),
            "modelo_medio_y_alto": _medidas(y, p >= medio),
            "modelo_solo_alto": _medidas(y, p >= alto) if alto is not None else None,
            "regla_simple": _medidas(y, datos["nota"].values <= corte_nota),
            "cortes_anteriores_medio_y_alto": _medidas(y, p >= origen["umbrales"]["medio"]),
        }

    reporte = {
        "fecha": ahora().strftime("%Y-%m-%d %H:%M"),
        "version": vigente["version"] if medir else f"cortes_{ahora():%Y%m%d}",
        "fecha_ajuste": (vigente.get("fecha_ajuste") or vigente["fecha"]) if medir else ahora().strftime("%Y-%m-%d %H:%M"),
        "medicion": "cortes vigentes, medidos de nuevo con los datos actuales" if medir else "cortes ajustados en esta ejecución",
        "umbrales": {"medio": round(medio, 4), "alto": round(alto, 4) if alto is not None else 1.0},
        "umbrales_anteriores": {k: round(v, 4) for k, v in origen["umbrales"].items()},
        "como": "La red no se vuelve a entrenar. Los cortes se ajustan con los casos de marzo y abril de 2026 y se miden con los de mayo a agosto, que el ajuste no vio.",
        "reglas": {
            "medio": f"el corte más alto que detecta al menos el {int(META_DETECCION * 100)} % de los casos con dificultad en el ajuste",
            "alto": f"el corte más bajo con el que al menos el {int(META_ACIERTO_ALTO * 100)} % de las alertas acierta en el ajuste ({MIN_ALERTAS_ALTO} alertas o más)",
            "regla_simple": f"alertar si la nota actual del curso es {corte_nota:g} o menos (corte elegido con la misma meta de detección)",
        },
        "criterio": criterio,
        "ajuste": resultado(ajuste, y_a),
        "prueba": resultado(prueba, y_p),
    }
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=1)
    print(json.dumps(reporte, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
