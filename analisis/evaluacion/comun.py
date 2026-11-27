"""Utilidades comunes del frente C: rutas, parámetros compartidos y conversiones.

Todo lo que dependa de un valor numérico lo lee de compartido/parametros.json
(ver docs/contratos.md, sección 3); nada se escribe a mano aquí.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
COMPARTIDO = RAIZ / "compartido"
DATOS = RAIZ / "datos"
RESULTADOS = RAIZ / "analisis" / "resultados"
FIGURAS = RAIZ / "analisis" / "evaluacion" / "figuras"


@lru_cache(maxsize=1)
def cargar_parametros() -> dict:
    return json.loads((COMPARTIDO / "parametros.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def cargar_afinaciones() -> dict:
    return json.loads((COMPARTIDO / "afinaciones.json").read_text(encoding="utf-8"))


def rango_midi_afinaciones() -> tuple[int, int]:
    """MIDI mínimo y máximo de todas las cuerdas de afinaciones.json."""
    midis = [
        c["midi"]
        for inst in cargar_afinaciones()["instrumentos"]
        for a in inst["afinaciones"]
        for c in a["cuerdas"]
    ]
    return min(midis), max(midis)


def f_de_midi(midi, la4: float | None = None):
    """Frecuencia en temperamento igual: f = la4 * 2^((midi - 69) / 12)."""
    la4 = cargar_parametros()["referencia_la4_hz"] if la4 is None else la4
    return la4 * 2.0 ** ((np.asarray(midi, dtype=float) - 69.0) / 12.0)


def cents(f, f_ref):
    """Desviación en cents de f respecto a f_ref: 1200 * log2(f / f_ref)."""
    return 1200.0 * np.log2(np.asarray(f, dtype=float) / np.asarray(f_ref, dtype=float))


def f_min_efectiva(fs: float, N: int) -> float:
    """f_min,ef = max(f_min, 2 fs / N) (docs/contratos.md, sección 4.4)."""
    return max(cargar_parametros()["rango"]["f_min_hz"], 2.0 * fs / N)
