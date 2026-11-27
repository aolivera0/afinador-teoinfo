"""Procesa un conjunto de WAV con la cadena provisional (librosa.yin) y escribe el CSV por tramo.

El CSV sigue docs/contratos.md, sección 5.5, con implementacion = "librosa" y
metodo = "yin". Cuando el frente B entregue sus estimadores, el notebook de
evaluación lee sus CSV sin cambios.

Uso:
    python analisis/evaluacion/procesar_librosa.py --conjunto nsynth \
        --indice datos/indice_nsynth.csv --audio datos/nsynth/48k \
        --N 2048 4096 8192 16384
"""

from __future__ import annotations

import argparse
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
import soundfile as sf

from comun import RESULTADOS, cargar_parametros, f_min_efectiva
from provisional import compuerta, preprocesar, tiempos, tramos

COLUMNAS = [
    "implementacion", "conjunto", "archivo", "metodo", "N", "tramo",
    "t_s", "activa", "rms_dbfs", "entropia", "f0_hz", "claridad",
]


def procesar_archivo(ruta: Path, conjunto: str, Ns: list[int]) -> pd.DataFrame:
    # f_min,ef = 2 fs / N cae justo en el límite que librosa acepta y avisa en cada archivo.
    warnings.filterwarnings("ignore", message="With fmin=.*less than two periods", category=UserWarning)
    p = cargar_parametros()
    x, fs = sf.read(ruta, dtype="float64")
    if x.ndim > 1:
        x = x.mean(axis=1)
    x = preprocesar(x, fs, p)
    salto = p["tramo"]["salto"]
    partes = []
    for N in Ns:
        m = tramos(x, N, salto, p["preprocesado"]["quitar_media"])
        if len(m) == 0:
            continue
        g = compuerta(m, fs, p)
        f0 = librosa.yin(
            x, fmin=f_min_efectiva(fs, N), fmax=p["rango"]["f_max_hz"], sr=fs,
            frame_length=N, hop_length=salto, trough_threshold=p["yin"]["umbral"], center=False,
        )[: len(m)]
        partes.append(pd.DataFrame({
            "implementacion": "librosa",
            "conjunto": conjunto,
            "archivo": ruta.stem,
            "metodo": "yin",
            "N": N,
            "tramo": np.arange(len(m)),
            "t_s": np.round(tiempos(len(m), N, salto, fs), 6),
            "activa": g["activa"].astype(int),
            "rms_dbfs": np.round(g["rms_dbfs"], 3),
            "entropia": np.round(g["entropia"], 5),
            "f0_hz": np.where(g["activa"], np.round(f0, 5), np.nan),
            "claridad": np.where(g["activa"], np.round(1 - g["entropia"], 5), np.nan),
        }))
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLUMNAS)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conjunto", required=True, choices=["sinteticos", "nsynth", "grabaciones"])
    ap.add_argument("--indice", type=Path, required=True, help="CSV con la columna 'archivo' (sin extensión)")
    ap.add_argument("--audio", type=Path, required=True, help="Carpeta con los WAV")
    ap.add_argument("--N", type=int, nargs="+", default=None, help="Tamaños de tramo (por defecto, el de parametros.json)")
    ap.add_argument("--salida", type=Path, default=None)
    ap.add_argument("--procesos", type=int, default=None)
    args = ap.parse_args()

    Ns = args.N or [cargar_parametros()["tramo"]["N"]]
    salida = args.salida or RESULTADOS / "tramos" / f"librosa_{args.conjunto}.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    rutas = [args.audio / f"{a}.wav" for a in pd.read_csv(args.indice)["archivo"]]

    with ProcessPoolExecutor(max_workers=args.procesos) as ex:
        partes = list(ex.map(procesar_archivo, rutas, [args.conjunto] * len(rutas), [Ns] * len(rutas), chunksize=8))
    df = pd.concat(partes, ignore_index=True)[COLUMNAS]
    df.to_csv(salida, index=False)
    print(f"{len(rutas)} archivos, {len(df)} tramos -> {salida}")


if __name__ == "__main__":
    main()
