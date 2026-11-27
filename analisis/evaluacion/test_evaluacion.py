"""Pruebas del pipeline de evaluación del frente C.

Correr desde la raíz del repositorio:
    analisis/.venv/bin/python -m pytest analisis/evaluacion -q
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
import soundfile as sf

from comun import cargar_parametros, cents, f_de_midi
from indice_nsynth import filtrar, remuestrear
from metricas import clasificar, resumen_por_nota, tabla_metricas
from procesar_librosa import procesar_archivo
from provisional import compuerta, tramos

FS = 48000


def tono_armonico(f0: float, dur: float = 2.5, fs: int = FS, n_arm: int = 8, sin_fundamental: bool = False) -> np.ndarray:
    t = np.arange(int(dur * fs)) / fs
    x = sum(
        (0.0 if (k == 1 and sin_fundamental) else 0.8**k) * np.sin(2 * np.pi * k * f0 * t)
        for k in range(1, n_arm + 1)
    )
    return 0.5 * x / np.max(np.abs(x))


# --- Conversiones -------------------------------------------------------------

def test_f_de_midi_y_cents():
    assert f_de_midi(69) == pytest.approx(440.0)
    assert f_de_midi(28) == pytest.approx(41.2034, abs=1e-3)  # Mi1 del bajo
    assert cents(440 * 2 ** (1 / 1200), 440) == pytest.approx(1.0)


# --- Clasificación de errores -------------------------------------------------

@pytest.mark.parametrize(
    "c, esperado",
    [
        (0.0, "afinado"), (-5.0, "afinado"), (5.1, "nota_correcta"), (49.9, "nota_correcta"),
        (1190.0, "octava_arriba"), (-1230.0, "octava_abajo"), (1900.0, "armonico_3"),
        (2420.0, "armonico_4"), (-1902.0, "subarmonico_3"), (300.0, "otro"), (np.nan, "sin_estimacion"),
    ],
)
def test_clasificar(c, esperado):
    assert clasificar(c) == esperado


# --- Compuerta ----------------------------------------------------------------

def test_compuerta_silencio_tono_y_ruido():
    p = cargar_parametros()
    N, salto = 4096, 512
    silencio = tramos(np.zeros(FS), N, salto)
    tono = tramos(tono_armonico(110.0), N, salto)
    ruido = tramos(np.random.default_rng(0).normal(0, 0.1, FS), N, salto)

    assert not compuerta(silencio, FS, p)["activa"].any()
    g_tono = compuerta(tono, FS, p)
    assert g_tono["activa"].all()
    # Un tono de 8 armónicos ya tiene H ~ 0,5 por el ancho del lóbulo principal
    # de Hann y el número de picos; un seno puro, ~0,17. El ruido blanco no llega
    # a 1 porque la potencia de cada bin del periodograma fluctúa: queda en ~0,9.
    assert g_tono["entropia"].max() < p["compuerta"]["entropia_max"]
    g_ruido = compuerta(ruido, FS, p)
    assert not g_ruido["activa"].any()
    assert g_ruido["entropia"].min() > 0.85


def test_tramos_siguen_el_contrato():
    x = np.arange(10_000, dtype=float)
    m = tramos(x, 4096, 512, quitar_media=False)
    assert m.shape == (1 + (10_000 - 4096) // 512, 4096)
    assert m[3, 0] == 3 * 512


# --- Resumen por nota y métricas ----------------------------------------------

def _tramos_falsos(f0s, ts, activa=None, archivo="a"):
    n = len(f0s)
    return pd.DataFrame({
        "implementacion": "prueba", "conjunto": "sinteticos", "archivo": archivo, "metodo": "yin", "N": 4096,
        "tramo": range(n), "t_s": ts, "activa": activa if activa is not None else [1] * n,
        "rms_dbfs": -20.0, "entropia": 0.1, "f0_hz": f0s, "claridad": 0.9,
    })


def test_resumen_usa_solo_la_ventana_y_tramos_activos():
    # Ventana por defecto: 0,2 s a 2,2 s. El ataque (t=0,1) y el tramo inactivo no cuentan.
    t = _tramos_falsos([880.0, 440.0, 441.0, 439.0, 1.0, 999.0], [0.1, 0.5, 1.0, 1.5, 2.0, 3.0],
                       activa=[1, 1, 1, 1, 0, 1])
    notas = resumen_por_nota(t, pd.DataFrame({"archivo": ["a"], "f_ref_hz": [440.0]}))
    assert notas.loc[0, "f0_hz"] == pytest.approx(440.0)
    assert notas.loc[0, "tramos_activos"] == 3


def test_nota_sin_tramos_activos_queda_vacia_y_cuenta_como_fallo():
    t = pd.concat([
        _tramos_falsos([440.0] * 3, [0.5, 1.0, 1.5], archivo="a"),
        _tramos_falsos([np.nan] * 3, [0.5, 1.0, 1.5], activa=[0, 0, 0], archivo="b"),
    ])
    refs = pd.DataFrame({"archivo": ["a", "b"], "f_ref_hz": [440.0, 220.0]})
    notas = resumen_por_nota(t, refs)
    assert notas.set_index("archivo").loc["b", "f0_hz"] != notas.set_index("archivo").loc["b", "f0_hz"]  # NaN
    m = tabla_metricas(notas).iloc[0]
    assert m["notas"] == 2
    assert m["acierto_nota_pct"] == pytest.approx(50.0)
    assert m["con_estimacion_pct"] == pytest.approx(50.0)


def test_referencia_faltante_falla_explicitamente():
    with pytest.raises(ValueError):
        resumen_por_nota(_tramos_falsos([440.0], [0.5]), pd.DataFrame({"archivo": ["otro"], "f_ref_hz": [440.0]}))


# --- Cadena provisional de punta a punta --------------------------------------

@pytest.mark.parametrize("midi", [40, 45, 57, 69])  # Mi2, La2, La3, La4
def test_procesar_tono_limpio(tmp_path, midi):
    f0 = float(f_de_midi(midi))
    ruta = tmp_path / f"tono_{midi}.wav"
    sf.write(ruta, tono_armonico(f0), FS, subtype="PCM_16")
    t = procesar_archivo(ruta, "sinteticos", [4096])
    notas = resumen_por_nota(t, pd.DataFrame({"archivo": [ruta.stem], "f_ref_hz": [f0]}))
    assert abs(notas.loc[0, "cents_error"]) < 2.0


# --- Índice de NSynth ---------------------------------------------------------

def test_filtrar_nsynth():
    ejemplos = {
        k: {"note_str": k, "instrument_family_str": fam, "instrument_source_str": src, "pitch": pitch}
        for k, fam, src, pitch in [
            ("guitar_acoustic_000-040-100", "guitar", "acoustic", 40),
            ("guitar_electronic_000-040-100", "guitar", "electronic", 40),
            ("bass_synthetic_000-040-100", "bass", "synthetic", 40),
            ("bass_electronic_000-020-100", "bass", "electronic", 20),
            ("string_acoustic_000-076-100", "string", "acoustic", 76),
            ("keyboard_acoustic_000-060-100", "keyboard", "acoustic", 60),
        ]
    }
    elegidos = [e["note_str"] for e in filtrar(json.loads(json.dumps(ejemplos)), 23, 76)]
    assert elegidos == ["guitar_acoustic_000-040-100", "guitar_electronic_000-040-100", "string_acoustic_000-076-100"]


def test_remuestrear_conserva_la_frecuencia():
    t = np.arange(16000) / 16000
    y = remuestrear(0.5 * np.sin(2 * np.pi * 220 * t), 16000, 48000)
    assert len(y) == 48000
    espectro = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    assert np.argmax(espectro) * 48000 / len(y) == pytest.approx(220, abs=1)
