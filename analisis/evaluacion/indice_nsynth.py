"""Construye el subconjunto de NSynth para la evaluación y su índice.

Filtra el conjunto de prueba de NSynth (familias bass, guitar y string, fuentes
acoustic y electronic, MIDI dentro del rango de compartido/afinaciones.json), remuestrea cada
nota de 16 kHz a 48 kHz y escribe datos/indice_nsynth.csv con las columnas de
docs/contratos.md, sección 5.4.

Uso:
    python analisis/evaluacion/indice_nsynth.py \
        --origen datos/nsynth/original/nsynth-test \
        --destino datos/nsynth/48k \
        --indice datos/indice_nsynth.csv
"""

from __future__ import annotations

import argparse
import json
from math import gcd
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf
from scipy.signal import resample_poly

from comun import f_de_midi, rango_midi_afinaciones

FAMILIAS = ("bass", "guitar", "string")
# El conjunto de prueba no tiene bajo acústico: el bajo solo aparece como
# "electronic" (instrumento eléctrico grabado en directo, como un bajo por línea)
# o "synthetic". Se excluyen solo los sintéticos.
FUENTES = ("acoustic", "electronic")
FS_DESTINO = 48000
COLUMNAS = ["archivo", "instrumento_nsynth", "familia", "fuente", "midi", "f_ref_hz", "velocidad"]


def filtrar(ejemplos: dict, midi_min: int, midi_max: int) -> list[dict]:
    """Notas de las familias elegidas, fuente acústica o eléctrica y MIDI en [midi_min, midi_max]."""
    return sorted(
        (
            e
            for e in ejemplos.values()
            if e["instrument_family_str"] in FAMILIAS
            and e["instrument_source_str"] in FUENTES
            and midi_min <= e["pitch"] <= midi_max
        ),
        key=lambda e: e["note_str"],
    )


def remuestrear(x: np.ndarray, fs_origen: int, fs_destino: int) -> np.ndarray:
    """Remuestreo polifásico (filtro antialiasing incluido) de fs_origen a fs_destino."""
    g = gcd(fs_origen, fs_destino)
    y = resample_poly(x, fs_destino // g, fs_origen // g)
    return np.clip(y, -1.0, 1.0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--origen", type=Path, required=True, help="Carpeta nsynth-test (con examples.json y audio/)")
    ap.add_argument("--destino", type=Path, required=True, help="Carpeta para los WAV remuestreados")
    ap.add_argument("--indice", type=Path, required=True, help="CSV de salida")
    args = ap.parse_args()

    ejemplos = json.loads((args.origen / "examples.json").read_text(encoding="utf-8"))
    midi_min, midi_max = rango_midi_afinaciones()
    seleccion = filtrar(ejemplos, midi_min, midi_max)
    args.destino.mkdir(parents=True, exist_ok=True)

    filas = []
    for e in seleccion:
        x, fs = sf.read(args.origen / "audio" / f"{e['note_str']}.wav", dtype="float64")
        if x.ndim > 1:
            x = x.mean(axis=1)
        sf.write(args.destino / f"{e['note_str']}.wav", remuestrear(x, fs, FS_DESTINO), FS_DESTINO, subtype="PCM_16")
        filas.append(
            {
                "archivo": e["note_str"],
                "instrumento_nsynth": e["instrument_str"],
                "familia": e["instrument_family_str"],
                "fuente": e["instrument_source_str"],
                "midi": e["pitch"],
                "f_ref_hz": round(float(f_de_midi(e["pitch"])), 4),
                "velocidad": e["velocity"],
            }
        )

    indice = pd.DataFrame(filas, columns=COLUMNAS)
    indice.to_csv(args.indice, index=False)
    resumen = indice.groupby("familia").agg(notas=("archivo", "size"), instrumentos=("instrumento_nsynth", "nunique"))
    print(f"{len(indice)} notas (MIDI {midi_min}-{midi_max}) escritas en {args.indice}")
    print(resumen.to_string())


if __name__ == "__main__":
    main()
