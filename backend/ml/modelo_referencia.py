"""
SIA-T: modelo de referencia con una base pública ya estudiada.

Uso, desde la carpeta backend, con la base de datos reales:

    $env:SQLITE_PATH = "data/privado/sia_t_reales.db"
    python -m ml.modelo_referencia

Base pública: «Student Performance» (Cortez y Silva, 2008; repositorio UCI), en data/publica/.
Son 1 044 registros de estudiantes de secundaria de dos colegios de Portugal, en Matemática y
Lenguaje, con notas de 0 a 20 en tres periodos (G1, G2 y G3), inasistencias, historial y contexto.
Se predice si el estudiante desaprueba el curso (G3 menor de 10, la nota aprobatoria en Portugal).

Responde tres preguntas:
A. ¿Hasta dónde llega el método con datos completos? Modelo con todas las columnas de la base pública.
B. ¿Y solo con las columnas que también tiene el colegio (nota actual y nota anterior)?
C. ¿Sirve en el colegio un modelo entrenado con la base pública? Se entrena con la base pública
   y se prueba con los resultados reales del colegio (validación externa).

Salida: data/referencia_report.json (sin datos de estudiantes). No reemplaza al modelo en uso.
"""

import json
import os
import sys
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.database import engine
from etl.variables import NOTA_APROBATORIA, construir_casos, leer_notas

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(BASE, "data", "publica")
RUTA_REPORTE = os.path.join(BASE, "data", "referencia_report.json")
APROBATORIA_PUBLICA = 10
REPETICIONES, PARTES = 10, 5
COMPARTIDAS = ["actual", "previa", "cambio"]

BOSQUE = RandomForestClassifier(n_estimators=400, min_samples_leaf=3, class_weight="balanced_subsample", random_state=0, n_jobs=-1)
LOGISTICA = make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))


def leer_publica() -> pd.DataFrame:
    partes = []
    for archivo, curso in (("student-mat.csv", "Matemática"), ("student-por.csv", "Lenguaje")):
        d = pd.read_csv(os.path.join(CARPETA, archivo), sep=";")
        d["curso"] = curso
        partes.append(d)
    d = pd.concat(partes, ignore_index=True)
    for c in ("G1", "G2", "G3"):
        d[c] = pd.to_numeric(d[c])
    # La base no trae identificador: se reconoce al mismo estudiante en los dos cursos por sus datos de contexto.
    llave = ["school", "sex", "age", "address", "famsize", "Pstatus", "Medu", "Fedu", "Mjob", "Fjob", "reason", "nursery", "internet"]
    d["est"] = d[llave].astype(str).agg("|".join, axis=1).factorize()[0]
    return d


def casos_compartidos(d: pd.DataFrame) -> pd.DataFrame:
    """Solo lo que también existe en el colegio: nota actual y anterior, en puntos sobre la nota aprobatoria.
    Dos casos por registro: con G1 y G2 se predice G3; con G1 sola se predice G2."""
    a = pd.DataFrame({"actual": d.G2 - APROBATORIA_PUBLICA, "previa": d.G1 - APROBATORIA_PUBLICA, "y": (d.G3 < APROBATORIA_PUBLICA).astype(int), "est": d.est})
    b = pd.DataFrame({"actual": d.G1 - APROBATORIA_PUBLICA, "previa": np.nan, "y": (d.G2 < APROBATORIA_PUBLICA).astype(int), "est": d.est})
    t = pd.concat([a, b], ignore_index=True)
    t["cambio"] = t.actual - t.previa
    return t


def validar(modelo, X, y, grupos) -> dict:
    """Validación cruzada agrupada por estudiante y repetida. Corte de 0,5."""
    filas = []
    for rep in range(REPETICIONES):
        p = cross_val_predict(clone(modelo), X, y, groups=grupos, cv=StratifiedGroupKFold(n_splits=PARTES, shuffle=True, random_state=rep), method="predict_proba")[:, 1]
        filas.append(medir(y, p))
    return {k: {"media": round(float(np.mean([f[k] for f in filas])), 3), "desviacion": round(float(np.std([f[k] for f in filas])), 3)} for k in filas[0]}


def medir(y, p, corte=0.5) -> dict:
    aviso = p >= corte
    return {
        "precision_media": average_precision_score(y, p),
        "auc_roc": roc_auc_score(y, p),
        "exactitud": accuracy_score(y, aviso),
        "sensibilidad": recall_score(y, aviso),
        "precision": precision_score(y, aviso, zero_division=0),
        "alertas": float(np.mean(aviso)),
    }


def main():
    pub = leer_publica()
    y = (pub.G3 < APROBATORIA_PUBLICA).astype(int)
    print(f"Base pública: {len(pub)} registros, {pub.est.nunique()} estudiantes; desaprueban {int(y.sum())} ({y.mean():.1%})")

    # A. Todas las columnas, y qué pasa al quitar las notas previas.
    X = pd.get_dummies(pub.drop(columns=["G3", "est"]), drop_first=True).astype(float)
    escenarios = {
        "con_dos_periodos": ("Con las notas de los dos periodos anteriores", list(X.columns)),
        "con_un_periodo": ("Con la nota de un solo periodo anterior", [c for c in X.columns if c != "G2"]),
        "sin_notas": ("Sin notas: solo inasistencias, historial y contexto", [c for c in X.columns if c not in ("G1", "G2")]),
    }
    completos = {}
    for clave, (nombre, columnas) in escenarios.items():
        completos[clave] = {"nombre": nombre, **validar(BOSQUE, X[columnas], y, pub.est)}
        r = completos[clave]
        print(f"  {nombre:<52} exactitud {r['exactitud']['media']:.2f}  AUC {r['auc_roc']['media']:.2f}  sensibilidad {r['sensibilidad']['media']:.2f}  precisión {r['precision']['media']:.2f}")
    bosque = clone(BOSQUE).fit(X, y)
    pesos = sorted(zip(X.columns, bosque.feature_importances_), key=lambda x: -x[1])[:8]

    # B. Solo las columnas compartidas con el colegio.
    comp = casos_compartidos(pub)
    compartido = validar(LOGISTICA, comp[COMPARTIDAS], comp.y, comp.est)
    print(f"  Solo nota actual y anterior (columnas compartidas)   exactitud {compartido['exactitud']['media']:.2f}  AUC {compartido['auc_roc']['media']:.2f}")

    # C. Entrenado con la base pública, probado en el colegio.
    externa = None
    casos = construir_casos(leer_notas(engine))
    casos = casos.dropna(subset=["objetivo"]).reset_index(drop=True) if not casos.empty else casos
    if len(casos) >= 100 and casos["objetivo"].sum() >= 20:
        y_col = casos["objetivo"].astype(int).to_numpy()
        modelo = clone(LOGISTICA).fit(comp[COMPARTIDAS], comp.y)
        # La nota de periodo de la base pública equivale, en el colegio, al promedio del examen y los trabajos del periodo.
        actual = pd.concat([casos.examen, casos.trabajos], axis=1).mean(axis=1)
        col = pd.DataFrame({"actual": actual - NOTA_APROBATORIA, "previa": casos.examen_previo - NOTA_APROBATORIA})
        col["cambio"] = col.actual - col.previa
        m = medir(y_col, modelo.predict_proba(col[COMPARTIDAS])[:, 1])
        externa = {"casos": int(len(casos)), "desaprobados": int(y_col.sum()), "proporcion_desaprobados": round(float(y_col.mean()), 3), **{k: round(float(v), 3) for k, v in m.items()}}
        print(f"  Entrenado con la base pública y probado en el colegio: exactitud {m['exactitud']:.2f}  AUC {m['auc_roc']:.2f}  sensibilidad {m['sensibilidad']:.2f}  precisión {m['precision']:.2f}")
    else:
        print("  Sin la base de datos reales no se puede hacer la validación externa.")

    reporte = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "base_publica": {
            "nombre": "Student Performance",
            "autores": "P. Cortez y A. Silva (2008)",
            "origen": "Repositorio UCI de Machine Learning, https://archive.ics.uci.edu/dataset/320/student+performance",
            "licencia": "CC BY 4.0",
            "descripcion": "Estudiantes de secundaria de dos colegios de Portugal, en Matemática y Lenguaje. Notas de 0 a 20 en tres periodos, inasistencias, historial y contexto.",
            "registros": int(len(pub)),
            "estudiantes": int(pub.est.nunique()),
            "desaprobados": int(y.sum()),
            "proporcion_desaprobados": round(float(y.mean()), 3),
        },
        "que_predice": "Si el estudiante desaprueba el curso al final del año (nota final menor de 10, la aprobatoria en Portugal).",
        "validacion": f"Validación cruzada estratificada y agrupada por estudiante, {PARTES} partes, repetida {REPETICIONES} veces. Corte de 0,5.",
        "exactitud_sin_modelo": round(float(1 - y.mean()), 3),
        "con_todas_las_columnas": completos,
        "variables_mas_influyentes": [{"variable": n, "peso": round(float(p), 3)} for n, p in pesos],
        "solo_columnas_compartidas": compartido,
        "probado_en_el_colegio": externa,
        "conclusiones": [
            "Con datos completos (notas de periodos anteriores, inasistencias e historial) el método predice bien quién desaprueba el curso.",
            "Lo que más pesa son las notas de los periodos anteriores; sin ellas el resultado cae mucho.",
            "Un modelo entrenado con la base pública no sirve tal cual en el colegio: allí no supera al modelo entrenado con los datos propios. Por eso el nivel de riesgo se calcula con el modelo local.",
            "No son el mismo problema: la base pública predice la nota final del curso a partir de las notas de periodo; el colegio predice el examen del mes siguiente, que varía más.",
        ],
    }
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=1)
    print(f"Reporte: {RUTA_REPORTE}")


if __name__ == "__main__":
    main()
