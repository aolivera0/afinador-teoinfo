"""Resumen por nota y métricas de evaluación, independientes del estimador.

Lee CSV por tramo con el formato de docs/contratos.md (sección 5.5), sin
importar si vienen de Python (frente B), de TypeScript (frente A) o de la cadena
provisional con librosa. Las métricas son las de la tabla del README.

Uso por línea de comandos (resumen por nota):
    python analisis/evaluacion/metricas.py \
        --tramos analisis/resultados/tramos/librosa_nsynth.csv \
        --referencias datos/indice_nsynth.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from comun import RESULTADOS, cargar_parametros, cents

CLAVES = ["implementacion", "conjunto", "archivo", "metodo", "N"]
COLUMNAS_NOTAS = CLAVES[:2] + ["archivo", "metodo", "N", "f_ref_hz", "f0_hz", "cents_error", "tramos_activos"]

# Errores "de octava o armónico": la estimación cae cerca de un múltiplo o
# submúltiplo entero de f_ref. Clave: desviación nominal en cents.
ERRORES_ARMONICOS = {
    -2400: "subarmonico_4",
    -1902: "subarmonico_3",
    -1200: "octava_abajo",
    1200: "octava_arriba",
    1902: "armonico_3",
    2400: "armonico_4",
}
CATEGORIAS = ["afinado", "nota_correcta", *ERRORES_ARMONICOS.values(), "otro", "sin_estimacion"]


def resumen_por_nota(tramos: pd.DataFrame, referencias: pd.DataFrame, p: dict | None = None) -> pd.DataFrame:
    """Una fila por (implementación, conjunto, archivo, método, N), como en el contrato 5.5.

    f0_hz es la mediana de los tramos activos con t entre ignorar_inicio_s e
    ignorar_inicio_s + duracion_max_s. `referencias` debe tener 'archivo' y 'f_ref_hz'.
    """
    p = p or cargar_parametros()
    t0 = p["evaluacion"]["ignorar_inicio_s"]
    t1 = t0 + p["evaluacion"]["duracion_max_s"]

    base = tramos[CLAVES].drop_duplicates()
    en_ventana = tramos[(tramos["t_s"] >= t0) & (tramos["t_s"] <= t1) & (tramos["activa"] == 1)]
    agregado = (
        en_ventana.groupby(CLAVES, as_index=False)
        .agg(f0_hz=("f0_hz", "median"), tramos_activos=("f0_hz", "count"))
    )
    notas = base.merge(agregado, on=CLAVES, how="left").merge(
        referencias[["archivo", "f_ref_hz"]], on="archivo", how="left", validate="many_to_one"
    )
    if notas["f_ref_hz"].isna().any():
        faltan = notas.loc[notas["f_ref_hz"].isna(), "archivo"].unique()[:5]
        raise ValueError(f"Archivos sin f_ref_hz en las referencias, por ejemplo: {list(faltan)}")
    notas["tramos_activos"] = notas["tramos_activos"].fillna(0).astype(int)
    notas["cents_error"] = cents(notas["f0_hz"], notas["f_ref_hz"])
    return notas[COLUMNAS_NOTAS].sort_values(CLAVES, ignore_index=True)


def clasificar(c: float, p: dict | None = None) -> str:
    """Categoría de una nota según su error en cents (NaN = sin estimación)."""
    if c is None or np.isnan(c):
        return "sin_estimacion"
    p = p or cargar_parametros()
    if abs(c) <= p["nota"]["afinado_cents"]:
        return "afinado"
    if abs(c) <= 50:
        return "nota_correcta"
    for nominal, nombre in ERRORES_ARMONICOS.items():
        if abs(c - nominal) <= 50:
            return nombre
    return "otro"


def tabla_metricas(notas: pd.DataFrame, por: list[str] | None = None) -> pd.DataFrame:
    """Métricas del README agrupadas por `por` (por defecto implementación, conjunto, método y N).

    Los porcentajes usan como denominador todas las notas: una nota sin
    estimación cuenta como fallo. Los errores medios solo usan las notas con estimación.
    """
    por = por or ["implementacion", "conjunto", "metodo", "N"]
    d = notas.copy()
    d["categoria"] = d["cents_error"].map(clasificar)
    d["abs_cents"] = d["cents_error"].abs()
    correcta = d["categoria"].isin(["afinado", "nota_correcta"])

    def agregar(g: pd.DataFrame) -> pd.Series:
        n = len(g)
        ok = correcta.loc[g.index]
        return pd.Series({
            "notas": n,
            "con_estimacion_pct": 100 * g["f0_hz"].notna().mean(),
            "acierto_afinacion_pct": 100 * (g["categoria"] == "afinado").sum() / n,
            "acierto_nota_pct": 100 * ok.sum() / n,
            "errores_octava_armonico_pct": 100 * g["categoria"].isin(ERRORES_ARMONICOS.values()).sum() / n,
            "error_abs_medio_cents": g["abs_cents"].mean(),
            "error_abs_medio_nota_correcta_cents": g.loc[ok, "abs_cents"].mean(),
            "error_abs_mediana_nota_correcta_cents": g.loc[ok, "abs_cents"].median(),
        })

    return d.groupby(por).apply(agregar, include_groups=False).reset_index()


def conteo_categorias(notas: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """Porcentaje de notas en cada categoría, con las columnas en el orden de CATEGORIAS."""
    d = notas.assign(categoria=notas["cents_error"].map(clasificar))
    t = pd.crosstab([d[c] for c in por], d["categoria"], normalize="index") * 100
    return t.reindex(columns=[c for c in CATEGORIAS if c in t.columns])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tramos", type=Path, required=True)
    ap.add_argument("--referencias", type=Path, required=True, help="CSV con 'archivo' y 'f_ref_hz'")
    ap.add_argument("--salida", type=Path, default=None)
    args = ap.parse_args()

    tramos = pd.read_csv(args.tramos)
    notas = resumen_por_nota(tramos, pd.read_csv(args.referencias))
    impl, conj = notas["implementacion"].iloc[0], notas["conjunto"].iloc[0]
    salida = args.salida or RESULTADOS / f"notas_{impl}_{conj}.csv"
    notas.to_csv(salida, index=False, float_format="%.5f")
    print(f"{len(notas)} filas -> {salida}")
    print(tabla_metricas(notas).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
