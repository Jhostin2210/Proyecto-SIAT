"""
SIA-T: entrenamiento y validación del modelo de riesgo (paquetes 1.3.1 y 1.3.3 de la EDT).

Uso, desde la carpeta backend, con la base de datos reales:

    $env:SQLITE_PATH = "data/privado/sia_t_reales.db"
    python -m ml.entrenar_modelo

Qué predice: con las notas de un estudiante en un curso y un periodo, si desaprobará (menos de 11)
el examen del periodo siguiente en ese curso.

Cómo se valida, pensando en que hay pocos datos:
- Solo con datos reales. Los datos de práctica nunca entran al entrenamiento ni a la validación.
- Validación cruzada agrupada por estudiante: nadie aparece a la vez en entrenamiento y en prueba.
- Repetida 10 veces con distintas particiones, para medir cuánto varía el resultado.
- Comparación contra una regla simple («tiene menos de 11 en el examen actual»).
- Modelos sencillos y regularizados, con peso mayor para la clase minoritaria.
- El punto de corte se elige dentro de cada entrenamiento, nunca mirando los datos de prueba.
- Se repite todo sin las notas pendientes de validar, para ver cuánto dependen los resultados de ellas.

Salidas: models/modelo_riesgo.joblib (el modelo) y data/metrics_report.json (el reporte, sin datos
de estudiantes).
"""

import json
import os
import sys
import warnings
from datetime import datetime

import joblib
import numpy as np
import sklearn
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.database import engine
from etl.variables import DESCRIPCION, VARIABLES, construir_casos, leer_notas

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_MODELO = os.path.join(BASE, "models", "modelo_riesgo.joblib")
RUTA_REPORTE = os.path.join(BASE, "data", "metrics_report.json")
META_SENSIBILIDAD = 0.75  # detectar al menos 75 % de quienes luego desaprueban
REPETICIONES, PARTES = 10, 5

MODELOS = {
    "regresion_logistica": make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), LogisticRegression(C=0.3, class_weight="balanced", max_iter=3000)),
    "bosque_aleatorio": make_pipeline(SimpleImputer(strategy="median", add_indicator=True), RandomForestClassifier(n_estimators=400, min_samples_leaf=5, class_weight="balanced_subsample", random_state=0)),
}
NOMBRES = {"regla_simple": "Regla simple", "regresion_logistica": "Regresión logística", "bosque_aleatorio": "Bosque aleatorio (Random Forest)"}


def puntaje_regla(X):
    """Regla de referencia: a menor nota de examen (o de trabajos, si no hay examen), mayor riesgo."""
    referencia = X["examen"].fillna(X["trabajos"]).fillna(14)
    return (20 - referencia).to_numpy()


def corte_para_meta(y, puntajes, meta=META_SENSIBILIDAD):
    """El corte más alto que todavía detecta al menos la meta de desaprobados."""
    for t in np.unique(puntajes)[::-1]:
        if recall_score(y, puntajes >= t) >= meta:
            return float(t)
    return float(np.min(puntajes))


def puntajes_de(nombre, X_ent, y_ent, g_ent, X_pru, semilla):
    """Devuelve (puntajes de prueba, corte elegido solo con el entrenamiento)."""
    if nombre == "regla_simple":
        return puntaje_regla(X_pru), corte_para_meta(y_ent, puntaje_regla(X_ent))
    modelo = clone(MODELOS[nombre])
    interno = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=semilla)
    dentro = cross_val_predict(modelo, X_ent, y_ent, groups=g_ent, cv=interno, method="predict_proba")[:, 1]
    return modelo.fit(X_ent, y_ent).predict_proba(X_pru)[:, 1], corte_para_meta(y_ent, dentro)


def validar(casos, modelos):
    """Validación cruzada agrupada y repetida. Devuelve métricas por modelo (media y desviación entre repeticiones)."""
    X, y, grupos = casos[VARIABLES], casos["objetivo"].astype(int).to_numpy(), casos["est"].to_numpy()
    por_modelo = {m: [] for m in modelos}
    regla_natural = []
    for rep in range(REPETICIONES):
        puntos = {m: np.zeros(len(y)) for m in modelos}
        avisos = {m: np.zeros(len(y), dtype=bool) for m in modelos}
        for ent, pru in StratifiedGroupKFold(n_splits=PARTES, shuffle=True, random_state=rep).split(X, y, grupos):
            for m in modelos:
                p, corte = puntajes_de(m, X.iloc[ent], y[ent], grupos[ent], X.iloc[pru], rep)
                puntos[m][pru], avisos[m][pru] = p, p >= corte
        for m in modelos:
            por_modelo[m].append(
                {
                    "precision_media": average_precision_score(y, puntos[m]),
                    "auc_roc": roc_auc_score(y, puntos[m]),
                    "sensibilidad": recall_score(y, avisos[m]),
                    "precision": precision_score(y, avisos[m], zero_division=0),
                    "alertas": float(avisos[m].mean()),
                }
            )
        natural = (casos["examen"].fillna(casos["trabajos"]) < 11).to_numpy()
        regla_natural.append({"sensibilidad": recall_score(y, natural), "precision": precision_score(y, natural, zero_division=0), "alertas": float(natural.mean())})
    resumen = lambda lista: {k: {"media": round(float(np.mean([x[k] for x in lista])), 3), "desviacion": round(float(np.std([x[k] for x in lista])), 3)} for k in lista[0]}
    return {m: resumen(v) for m, v in por_modelo.items()}, resumen(regla_natural)


def nombres_de_variables(pipeline):
    imputador = pipeline.steps[0][1]
    faltantes = [f"sin_dato_{VARIABLES[i]}" for i in imputador.indicator_.features_] if imputador.indicator_ is not None else []
    return list(VARIABLES) + faltantes


def main():
    casos = construir_casos(leer_notas(engine))
    casos = casos.dropna(subset=["objetivo"]).reset_index(drop=True)
    if len(casos) < 100 or casos["objetivo"].sum() < 20:
        sys.exit("No hay suficientes casos para entrenar. ¿Está cargada la base con los datos reales?")
    y = casos["objetivo"].astype(int)
    print(f"Casos: {len(casos)} | estudiantes: {casos['est'].nunique()} | desaprueban el examen siguiente: {int(y.sum())} ({y.mean():.1%})")

    todos = ["regla_simple", *MODELOS]
    metricas, regla_natural = validar(casos, todos)
    validados = casos[casos["sin_validar"] == 0].reset_index(drop=True)
    metricas_validados, _ = validar(validados, todos) if validados["objetivo"].sum() >= 20 else ({}, None)

    print(f"\n{'Modelo':<34}{'Prec. media':>12}{'AUC':>8}{'Sensib.':>9}{'Precisión':>11}{'Alertas':>9}")
    for m in todos:
        r = metricas[m]
        print(f"{NOMBRES[m]:<34}{r['precision_media']['media']:>8.2f}±{r['precision_media']['desviacion']:.2f}{r['auc_roc']['media']:>8.2f}{r['sensibilidad']['media']:>9.2f}{r['precision']['media']:>11.2f}{r['alertas']['media']:>9.0%}")
    print(f"Regla «examen menor de 11», tal cual: sensibilidad {regla_natural['sensibilidad']['media']:.2f}, precisión {regla_natural['precision']['media']:.2f}")

    # Modelo elegido: el de mayor precisión media; si la diferencia es mínima, el más simple.
    ap = {m: metricas[m]["precision_media"]["media"] for m in MODELOS}
    elegido = "regresion_logistica" if ap["regresion_logistica"] >= ap["bosque_aleatorio"] - 0.02 else "bosque_aleatorio"
    supera_regla = metricas[elegido]["precision_media"]["media"] > metricas["regla_simple"]["precision_media"]["media"]

    # Entrenamiento final con todos los casos y cortes de los tres niveles con predicciones fuera de muestra.
    X, grupos = casos[VARIABLES], casos["est"].to_numpy()
    fuera = cross_val_predict(clone(MODELOS[elegido]), X, y, groups=grupos, cv=StratifiedGroupKFold(n_splits=PARTES, shuffle=True, random_state=0), method="predict_proba")[:, 1]
    corte_medio = corte_para_meta(y, fuera)
    candidatos = [t for t in np.unique(fuera) if t >= corte_medio and (fuera >= t).sum() >= 10 and precision_score(y, fuera >= t) >= 0.5]
    corte_alto = float(min(candidatos)) if candidatos else float(np.quantile(fuera[fuera >= corte_medio], 0.6))
    pipeline = clone(MODELOS[elegido]).fit(X, y)

    nombres = nombres_de_variables(pipeline)
    estimador = pipeline.steps[-1][1]
    pesos = estimador.coef_[0] if hasattr(estimador, "coef_") else estimador.feature_importances_
    importancia = sorted(({"variable": n, "descripcion": DESCRIPCION.get(n, n.replace("sin_dato_", "Falta el dato: ").replace("area_", "Área: ")), "peso": round(float(p), 3)} for n, p in zip(nombres, pesos)), key=lambda x: -abs(x["peso"]))

    version = f"{elegido}_{datetime.now():%Y%m%d}"
    os.makedirs(os.path.dirname(RUTA_MODELO), exist_ok=True)
    joblib.dump({"pipeline": pipeline, "variables": VARIABLES, "umbrales": {"medio": corte_medio, "alto": corte_alto}, "version": version, "sklearn": sklearn.__version__}, RUTA_MODELO)

    en = lambda mascara: {"casos": int(mascara.sum()), "desaprobados": int(y[mascara].sum())}
    reporte = {
        "fecha_entrenamiento": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": version,
        "que_predice": "Si el estudiante desaprobará (menos de 11) el examen del periodo siguiente en un curso, con sus notas del periodo actual.",
        "datos": {
            "casos": len(casos),
            "estudiantes": int(casos["est"].nunique()),
            "desaprobados": int(y.sum()),
            "proporcion_desaprobados": round(float(y.mean()), 3),
            "con_notas_por_validar": int(casos["sin_validar"].sum()),
            "por_transicion": {f"{a} → {b}": en(((casos["periodo"] == a) & (casos["periodo_siguiente"] == b)).to_numpy()) for a, b in sorted(set(zip(casos["periodo"], casos["periodo_siguiente"])))},
            "origen": "Datos reales del colegio. Los datos de práctica no participan del entrenamiento ni de la validación.",
        },
        "validacion": {
            "metodo": f"Validación cruzada estratificada y agrupada por estudiante, {PARTES} partes, repetida {REPETICIONES} veces.",
            "meta_sensibilidad": META_SENSIBILIDAD,
            "corte": "Elegido dentro de cada entrenamiento para detectar al menos 75 % de los desaprobados.",
        },
        "modelos": {m: {"nombre": NOMBRES[m], **metricas[m]} for m in todos},
        "regla_examen_menor_de_11": regla_natural,
        "solo_notas_validadas": {"casos": len(validados), "desaprobados": int(validados["objetivo"].sum()), "modelos": {m: {"nombre": NOMBRES[m], **metricas_validados[m]} for m in metricas_validados}},
        "modelo_elegido": {"clave": elegido, "nombre": NOMBRES[elegido], "supera_a_la_regla": bool(supera_regla), "cumple_meta_sensibilidad": bool(round(metricas[elegido]["sensibilidad"]["media"], 2) >= META_SENSIBILIDAD)},
        "niveles": {
            "medio_desde": round(corte_medio, 3),
            "alto_desde": round(corte_alto, 3),
            "fuera_de_muestra": {
                "riesgo_alto": {"casos": int((fuera >= corte_alto).sum()), "desaprueban": int(y[fuera >= corte_alto].sum())},
                "riesgo_medio": {"casos": int(((fuera >= corte_medio) & (fuera < corte_alto)).sum()), "desaprueban": int(y[(fuera >= corte_medio) & (fuera < corte_alto)].sum())},
                "riesgo_bajo": {"casos": int((fuera < corte_medio).sum()), "desaprueban": int(y[fuera < corte_medio].sum())},
            },
        },
        "variables_mas_influyentes": importancia[:10],
        "limitaciones": [
            "Pocos datos: los resultados varían entre particiones; por eso se informa la media y la desviación.",
            "Las notas transcritas de cuadernos están pendientes de validar contra el original.",
            "No hay asistencia ni incidencias en formato digital: el modelo solo usa notas.",
            "Los datos son de pocos docentes y cursos; hay que repetir la validación con las exportaciones completas de Cubicol.",
            "El corte de riesgo alto se fijó como el punto desde el cual desaprueba al menos la mitad: ese porcentaje es el criterio del corte, no una medición independiente.",
        ],
        "sklearn_version": sklearn.__version__,
    }
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=1)

    n = reporte["niveles"]["fuera_de_muestra"]
    print(f"\nModelo elegido: {NOMBRES[elegido]} | supera a la regla: {supera_regla} | cumple la meta de sensibilidad: {reporte['modelo_elegido']['cumple_meta_sensibilidad']}")
    print(f"Cortes: medio desde {corte_medio:.2f}, alto desde {corte_alto:.2f}")
    for k, v in n.items():
        print(f"  {k}: {v['casos']} casos, {v['desaprueban']} desaprueban ({v['desaprueban'] / max(1, v['casos']):.0%})")
    if metricas_validados:
        r = metricas_validados[elegido]
        print(f"Solo notas validadas ({len(validados)} casos): precisión media {r['precision_media']['media']:.2f}, AUC {r['auc_roc']['media']:.2f}, sensibilidad {r['sensibilidad']['media']:.2f}, precisión {r['precision']['media']:.2f}")
    print("Variables más influyentes:", ", ".join(f"{x['variable']} ({x['peso']:+.2f})" for x in importancia[:6]))
    print(f"\nModelo: {RUTA_MODELO}\nReporte: {RUTA_REPORTE}")


if __name__ == "__main__":
    main()
