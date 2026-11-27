"""Estilo común de las figuras del artículo (plantilla IEEE, dos columnas).

Uso:
    from estilo import aplicar_estilo, ANCHO_COLUMNA, guardar
    aplicar_estilo()
    fig, ax = plt.subplots(figsize=(ANCHO_COLUMNA, 2.2))
    ...
    guardar(fig, "error_vs_midi")
"""

from __future__ import annotations

import locale

import matplotlib as mpl
import matplotlib.pyplot as plt

from comun import FIGURAS

ANCHO_COLUMNA = 3.5      # pulgadas, una columna IEEE
ANCHO_PAGINA = 7.16      # pulgadas, las dos columnas

# Colores por método (los mismos en todas las figuras).
COLOR_METODO = {"fft": "#1f77b4", "hps": "#ff7f0e", "yin": "#2ca02c"}


def aplicar_estilo() -> None:
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Nimbus Roman", "TeX Gyre Termes", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "legend.fontsize": 7,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })
    # Coma decimal si el sistema tiene un locale en español.
    for nombre in ("es_CO.UTF-8", "es_ES.UTF-8"):
        try:
            locale.setlocale(locale.LC_NUMERIC, nombre)
            mpl.rcParams["axes.formatter.use_locale"] = True
            break
        except locale.Error:
            continue


def guardar(fig: plt.Figure, nombre: str) -> None:
    """Guarda la figura en PDF (para el artículo) y PNG (para revisarla en GitHub)."""
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURAS / f"{nombre}.pdf")
    fig.savefig(FIGURAS / f"{nombre}.png", dpi=200)
