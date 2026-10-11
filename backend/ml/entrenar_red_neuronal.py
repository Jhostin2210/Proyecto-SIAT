"""
SIA-T: entrenamiento y prueba de la red neuronal (paquetes 1.3.1 y 1.3.3 de la EDT).

Uso, desde la carpeta backend:  python -m ml.entrenar_red_neuronal

Base de entrenamiento: «Student Performance» (Cortez y Silva, 2008; repositorio UCI), en
data/publica/. Son 1 044 registros de estudiantes de secundaria de Portugal, con notas de 0 a 20.

Qué predice: si al estudiante le irá mal en el curso (nota final menor de 10, la aprobatoria allá).
Con qué: 25 variables. Las notas de los dos periodos anteriores (G1 y G2), inasistencias, historial,
familia y hábitos. No se consideran: school, address, higher, reason, nursery, Dalc y Walc.

Modelo: red neuronal densa 32-16-8 con activación ReLU y optimizador Adam, sobre variables
estandarizadas (StandardScaler). Las 25 variables son 35 entradas al separar las categorías
(ocupación de los padres, apoderado); la salida es una neurona con la probabilidad de que le vaya mal.

Cómo se prueba: 80 % de los estudiantes para entrenar y 20 % para probar. La matriz de confusión
sale de ese 20 %, que la red no vio. El mismo estudiante (aparece en Matemática y en Lenguaje)
queda siempre en un solo lado. Además, validación cruzada de 5 partes dentro del 80 %.

Niveles de riesgo: la probabilidad se divide en tres niveles. Los cortes son la probabilidad que
la red da, en un estudiante típico, a las notas 9,5 y 14,5 de la escala del colegio:
alto por debajo de 10, medio de 10 a 14 y bajo desde 15.

Salidas: models/red_neuronal_riesgo.joblib (preparación de datos, escalador, red y cortes, en un
solo archivo) y data/red_neuronal_report.json.
"""

import json
import os
import sys
import warnings
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.perfil import leer_base_publica

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_MODELO = os.path.join(BASE, "models", "red_neuronal_riesgo.joblib")
RUTA_REPORTE = os.path.join(BASE, "data", "red_neuronal_report.json")
APROBATORIA = 10  # en la base pública; en el colegio es 11
APROBATORIA_COLEGIO = 11
SEMILLA = 42

NO_CONSIDERADAS = ["school", "address", "higher", "reason", "nursery", "Dalc", "Walc"]
NUMERICAS = ["age", "Medu", "Fedu", "traveltime", "studytime", "failures", "famrel", "freetime", "goout", "health", "absences", "G1", "G2"]
CATEGORICAS = ["sex", "famsize", "Pstatus", "Mjob", "Fjob", "guardian", "schoolsup", "famsup", "paid", "activities", "internet", "romantic"]
VARIABLES = NUMERICAS + CATEGORICAS
CAPAS = (32, 16, 8)
# Notas del colegio que separan los niveles: alto por debajo de 10, medio de 10 a 14, bajo desde 15.
LIMITE_ALTO, LIMITE_MEDIO = 9.5, 14.5


def leer_publica() -> pd.DataFrame:
    d = leer_base_publica()
    # La base no trae identificador: se reconoce al mismo estudiante en los dos cursos por sus datos de contexto.
    llave = ["school", "sex", "age", "address", "famsize", "Pstatus", "Medu", "Fedu", "Mjob", "Fjob", "reason", "nursery", "internet"]
    d["est"] = d[llave].astype(str).agg("|".join, axis=1).factorize()[0]
    return d


def nueva_red() -> Pipeline:
    preparar = ColumnTransformer(
        [("num", "passthrough", NUMERICAS), ("cat", OneHotEncoder(drop="if_binary", handle_unknown="ignore", sparse_output=False), CATEGORICAS)]
    )
    # alpha (regularización) alto: la red memoriza menos y da probabilidades graduales, necesarias para los tres niveles.
    red = MLPClassifier(hidden_layer_sizes=CAPAS, activation="relu", solver="adam", alpha=1.0, batch_size=16, max_iter=300, early_stopping=True, validation_fraction=0.15, n_iter_no_change=20, random_state=SEMILLA)
    return Pipeline([("preparar", preparar), ("escalar", StandardScaler()), ("red", red)])


def equilibrar(X, y, semilla=SEMILLA):
    """Repite casos de la clase menos frecuente en el entrenamiento hasta igualar las clases (equivale a darles más peso)."""
    azar = np.random.RandomState(semilla)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    extra = azar.choice(pos, size=len(neg) - len(pos), replace=True)
    orden = azar.permutation(np.concatenate([neg, pos, extra]))
    return X.iloc[orden], y[orden]


def medir(y, p) -> dict:
    aviso = (p >= 0.5).astype(int)
    vn, fp, fn, vp = confusion_matrix(y, aviso, labels=[0, 1]).ravel()
    return {
        "matriz": {"verdaderos_negativos": int(vn), "falsos_positivos": int(fp), "falsos_negativos": int(fn), "verdaderos_positivos": int(vp)},
        "exactitud": round(float(accuracy_score(y, aviso)), 3),
        "auc_roc": round(float(roc_auc_score(y, p)), 3),
        "le_va_mal": {"precision": round(float(precision_score(y, aviso)), 3), "recall": round(float(recall_score(y, aviso)), 3), "f1": round(float(f1_score(y, aviso)), 3)},
        "le_va_bien": {"precision": round(float(precision_score(y, aviso, pos_label=0)), 3), "recall": round(float(recall_score(y, aviso, pos_label=0)), 3), "f1": round(float(f1_score(y, aviso, pos_label=0)), 3)},
    }


def probabilidad_tipica(modelo, contexto: pd.DataFrame, nota_colegio: float) -> float:
    """Probabilidad que da la red, en un estudiante típico, a una nota del colegio que no cambia entre periodos."""
    X = contexto.copy()
    X["G1"] = X["G2"] = nota_colegio - (APROBATORIA_COLEGIO - APROBATORIA)
    return float(np.median(modelo.predict_proba(X[VARIABLES])[:, 1]))


def main():
    datos = leer_publica()
    X, y, grupos = datos[VARIABLES], (datos.G3 < APROBATORIA).astype(int).to_numpy(), datos.est.to_numpy()
    print(f"Base pública: {len(datos)} registros de {datos.est.nunique()} estudiantes; les va mal a {y.sum()} ({y.mean():.1%}). Variables: {len(VARIABLES)}")

    # 80 % para entrenar, 20 % para probar, sin repartir a un mismo estudiante entre los dos lados.
    ent, pru = next(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEMILLA).split(X, y, grupos))
    X_ent, y_ent, X_pru, y_pru = X.iloc[ent], y[ent], X.iloc[pru], y[pru]
    print(f"Entrenamiento: {len(ent)} registros ({y_ent.sum()} con mal resultado) | Prueba: {len(pru)} registros ({y_pru.sum()} con mal resultado)")

    # Validación cruzada dentro del entrenamiento: cuánto varía el resultado.
    cruzada = []
    for a, b in StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=0).split(X_ent, y_ent, grupos[ent]):
        m = clone(nueva_red()).fit(*equilibrar(X_ent.iloc[a], y_ent[a]))
        p = m.predict_proba(X_ent.iloc[b])[:, 1]
        cruzada.append((accuracy_score(y_ent[b], p >= 0.5), recall_score(y_ent[b], p >= 0.5), precision_score(y_ent[b], p >= 0.5), roc_auc_score(y_ent[b], p)))
    cruzada = np.array(cruzada)
    print(f"Validación cruzada en el entrenamiento: exactitud {cruzada[:, 0].mean():.3f} ± {cruzada[:, 0].std():.3f} | recall {cruzada[:, 1].mean():.3f} | precisión {cruzada[:, 2].mean():.3f} | AUC {cruzada[:, 3].mean():.3f}")

    # Entrenamiento final y prueba.
    modelo = nueva_red().fit(*equilibrar(X_ent, y_ent))
    red = modelo.named_steps["red"]
    entradas = int(modelo.named_steps["escalar"].n_features_in_)
    arquitectura = f"{entradas}-{'-'.join(str(c) for c in CAPAS)}-1"
    en_entrenamiento = medir(y_ent, modelo.predict_proba(X_ent)[:, 1])
    en_prueba = medir(y_pru, modelo.predict_proba(X_pru)[:, 1])
    m = en_prueba["matriz"]
    print(f"\nRed {arquitectura} | épocas: {red.n_iter_} | pérdida final: {red.loss_:.4f}")
    print(f"Exactitud en entrenamiento: {en_entrenamiento['exactitud']:.3f} | en prueba: {en_prueba['exactitud']:.3f} | AUC en prueba: {en_prueba['auc_roc']:.3f}")
    print("\nMatriz de confusión (20 % de prueba)")
    print(f"{'':<22}{'Predijo bien':>18}{'Predijo mal':>20}")
    print(f"{'Le fue bien':<22}{m['verdaderos_negativos']:>18}{m['falsos_positivos']:>20}")
    print(f"{'Le fue mal':<22}{m['falsos_negativos']:>18}{m['verdaderos_positivos']:>20}")
    for clase in ("le_va_bien", "le_va_mal"):
        c = en_prueba[clase]
        print(f"  {clase:<11} precisión {c['precision']:.2f} | recall {c['recall']:.2f} | F1 {c['f1']:.2f}")

    # Cortes de los tres niveles.
    contexto = datos[[v for v in VARIABLES if v not in ("G1", "G2")]]
    corte_alto, corte_medio = probabilidad_tipica(modelo, contexto, LIMITE_ALTO), probabilidad_tipica(modelo, contexto, LIMITE_MEDIO)
    curva = [{"nota": n, "probabilidad": round(probabilidad_tipica(modelo, contexto, n), 3)} for n in range(5, 21)]
    print(f"\nNiveles: alto desde {corte_alto:.3f} (nota menor de 10) | medio desde {corte_medio:.3f} (nota de 10 a 14) | bajo por debajo")

    version = f"red_neuronal_{datetime.now():%Y%m%d}"
    os.makedirs(os.path.dirname(RUTA_MODELO), exist_ok=True)
    joblib.dump(
        {"pipeline": modelo, "variables": VARIABLES, "numericas": NUMERICAS, "categoricas": CATEGORICAS, "aprobatoria": APROBATORIA, "umbrales": {"medio": corte_medio, "alto": corte_alto}, "version": version, "sklearn": sklearn.__version__},
        RUTA_MODELO,
    )
    reporte = {
        "fecha_entrenamiento": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": version,
        "nombre": "Red neuronal",
        "base": {"nombre": "Student Performance", "autores": "P. Cortez y A. Silva (2008)", "origen": "Repositorio UCI de Machine Learning", "enlace": "https://archive.ics.uci.edu/dataset/320/student+performance", "descripcion": "Estudiantes de secundaria de dos colegios de Portugal, en Matemática y Lenguaje, con notas de 0 a 20.", "registros": int(len(datos)), "estudiantes": int(datos.est.nunique()), "con_mal_resultado": int(y.sum())},
        "que_predice": "Si al estudiante le irá mal en el curso (nota final desaprobatoria).",
        "variables": VARIABLES,
        "no_consideradas": NO_CONSIDERADAS,
        "red": {"arquitectura": arquitectura, "capas_ocultas": list(CAPAS), "entradas": entradas, "activacion": "ReLU", "optimizador": "Adam", "escalado": "StandardScaler", "epocas": int(red.n_iter_), "perdida_final": round(float(red.loss_), 4), "curva_de_perdida": [round(float(v), 4) for v in red.loss_curve_]},
        "particion": {"entrenamiento": int(len(ent)), "prueba": int(len(pru)), "metodo": "80 % para entrenar y 20 % para probar, sin repartir a un mismo estudiante entre los dos lados."},
        "validacion_cruzada": {k: {"media": round(float(cruzada[:, i].mean()), 3), "desviacion": round(float(cruzada[:, i].std()), 3)} for i, k in enumerate(["exactitud", "recall", "precision", "auc_roc"])},
        "entrenamiento": en_entrenamiento,
        "prueba": en_prueba,
        "exactitud_sin_modelo": round(float(1 - y_pru.mean()), 3),
        "niveles": {"alto_desde": round(corte_alto, 3), "medio_desde": round(corte_medio, 3), "equivalencia": "En un estudiante típico: riesgo alto con nota menor de 10, medio de 10 a 14 y bajo desde 15.", "curva": curva},
        "sklearn_version": sklearn.__version__,
    }
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=1)
    print(f"\nModelo: {os.path.relpath(RUTA_MODELO, BASE)} | Reporte: {os.path.relpath(RUTA_REPORTE, BASE)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
