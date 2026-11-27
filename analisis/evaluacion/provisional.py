"""Cadena provisional del frente C mientras no estén los estimadores del frente B.

Implementa, según docs/contratos.md, el preprocesado (4.1), los tramos (4.2) y la
compuerta (4.3), y usa librosa.yin como estimador de f0. Sirve para construir y
probar el pipeline de evaluación; los resultados se marcan con
implementacion = "librosa" y no reemplazan a los de Python (frente B) ni a los de
TypeScript (frente A).

Diferencias conocidas de librosa.yin frente al YIN del contrato (4.4):
  - siempre devuelve un f0: si ningún retardo baja del umbral, toma el mínimo
    global en lugar de dejar el tramo sin estimación;
  - su ventana de integración es N/2 y no N - tau_max;
  - no entrega la claridad 1 - d'(tau*); aquí se usa 1 - H de la compuerta.
"""

from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.signal import butter, sosfilt


def preprocesar(x: np.ndarray, fs: float, p: dict) -> np.ndarray:
    """Pasa altas Butterworth causal sobre la señal completa (contrato 4.1)."""
    pre = p["preprocesado"]
    sos = butter(pre["pasa_altas_orden"], pre["pasa_altas_hz"], "highpass", fs=fs, output="sos")
    return sosfilt(sos, x)


def tramos(x: np.ndarray, N: int, salto: int, quitar_media: bool = True) -> np.ndarray:
    """Matriz (n_tramos, N) con los tramos completos; el tramo k empieza en k*salto (contrato 4.2)."""
    if len(x) < N:
        return np.empty((0, N))
    m = sliding_window_view(x, N)[::salto].astype(float, copy=True)
    if quitar_media:
        m -= m.mean(axis=1, keepdims=True)
    return m


def tiempos(n_tramos: int, N: int, salto: int, fs: float) -> np.ndarray:
    """Tiempo del centro de cada tramo: (k*salto + N/2) / fs."""
    return (np.arange(n_tramos) * salto + N / 2) / fs


def hann_periodica(N: int) -> np.ndarray:
    n = np.arange(N)
    return 0.5 - 0.5 * np.cos(2 * np.pi * n / N)


def compuerta(m: np.ndarray, fs: float, p: dict) -> dict[str, np.ndarray]:
    """RMS en dBFS (sin ventana) y entropía espectral normalizada (con Hann, N_fft = N).

    Devuelve arreglos 'activa', 'rms_dbfs' y 'entropia', uno por tramo (contrato 4.3).
    """
    N = m.shape[1]
    with np.errstate(divide="ignore"):
        rms_dbfs = 20 * np.log10(np.sqrt(np.mean(m**2, axis=1)))

    P = np.abs(np.fft.rfft(m * hann_periodica(N), n=N, axis=1)) ** 2
    k_min = int(np.ceil(p["rango"]["f_min_hz"] * N / fs))
    k_max = int(np.floor(p["rango"]["f_max_hz"] * N / fs))
    P = P[:, k_min : k_max + 1]
    K = P.shape[1]
    total = P.sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        q = np.where(total > 0, P / total, 0.0)
        plogp = np.where(q > 0, q * np.log2(q), 0.0)
    entropia = np.where(total[:, 0] > 0, -plogp.sum(axis=1) / np.log2(K), 1.0)

    c = p["compuerta"]
    activa = (rms_dbfs >= c["rms_min_dbfs"]) & (entropia <= c["entropia_max"])
    return {"activa": activa, "rms_dbfs": rms_dbfs, "entropia": entropia}
