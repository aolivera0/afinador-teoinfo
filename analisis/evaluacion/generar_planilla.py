"""Genera la planilla de la sesión de grabación a partir de compartido/afinaciones.json.

Escribe:
  - datos/grabaciones/lecturas.csv con una fila por archivo previsto: los campos
    de identificación ya llenos y las lecturas vacías, para completarlas durante
    la sesión (docs/contratos.md, sección 5.2);
  - datos/grabaciones/planilla.md, una lista de tomas para seguir en la sesión.

No sobrescribe un lecturas.csv que ya tenga lecturas, salvo con --forzar.

Uso:
    python analisis/evaluacion/generar_planilla.py --uso-real portatil
"""

from __future__ import annotations

import argparse

import pandas as pd

from comun import DATOS, cargar_afinaciones

REPETICIONES = 3
# (instrumento, afinación, cadena de referencia)
SESION = [("guitarra", "estandar", "sm57"), ("bajo", "estandar-4", "di"), ("ukelele", "estandar", "sm57")]
# Notas pisadas: (instrumento, cuerda, nota, midi, descripción)
PISADAS = [("guitarra", 1, "A4", 69, "cuerda 1, traste 5 (comparación de timbre con ukelele_A4_c1)")]
COLUMNAS = [
    "archivo", "toma", "instrumento", "cuerda", "nota_esperada", "midi_esperado", "repeticion", "dispositivo",
    "detalle_captura", "guitartuna_nota", "guitartuna_cents", "datuner_nota", "datuner_cents", "datuner_hz",
    "audacity_hz", "fecha", "observaciones",
]
LECTURAS = ["guitartuna_nota", "guitartuna_cents", "datuner_nota", "datuner_cents", "datuner_hz", "audacity_hz"]


def notas_previstas() -> list[dict]:
    afin = {(i["id"], a["id"]): a for i in cargar_afinaciones()["instrumentos"] for a in i["afinaciones"]}
    notas = []
    for inst, id_afin, ref in SESION:
        for c in afin[(inst, id_afin)]["cuerdas"]:
            notas.append({"instrumento": inst, "cuerda": c["cuerda"], "nota": c["nota"], "midi": c["midi"],
                          "referencia": ref, "descripcion": "al aire"})
    for inst, cuerda, nota, midi, desc in PISADAS:
        ref = next(r for i, _, r in SESION if i == inst)
        notas.append({"instrumento": inst, "cuerda": cuerda, "nota": nota, "midi": midi,
                      "referencia": ref, "descripcion": desc})
    return notas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--uso-real", default="portatil", choices=["portatil", "celular"],
                    help="Cadena de uso real que se graba junto a la de referencia")
    ap.add_argument("--forzar", action="store_true")
    args = ap.parse_args()

    destino = DATOS / "grabaciones"
    destino.mkdir(parents=True, exist_ok=True)
    ruta_csv = destino / "lecturas.csv"
    if ruta_csv.exists() and not args.forzar:
        previo = pd.read_csv(ruta_csv)
        if previo[LECTURAS].notna().any().any():
            raise SystemExit(f"{ruta_csv} ya tiene lecturas; usa --forzar para sobrescribirlo.")

    filas, lineas = [], [
        "# Planilla de la sesión de grabación",
        "",
        "Generada por `analisis/evaluacion/generar_planilla.py`. Protocolo completo en el README.",
        "",
        "- [ ] Interfaz y proyecto (Reaper o Audacity) a 48 kHz; mejoras de audio del sistema desactivadas",
        "- [ ] Pistas o archivos sin efectos ni normalización; monitoreo apagado en la pista del micrófono del portátil",
        f"- [ ] Segunda cadena (`{args.uso_real}`) grabando a 48 kHz, 16 bits, mono, sin control automático de ganancia",
        "- [ ] Aplauso al inicio de cada bloque para alinear las dos grabaciones",
        "- [ ] Nivel con picos entre −12 y −6 dBFS en las dos cadenas",
        "- [ ] Anotar en `detalle_captura`: interfaz, distancia y posición de los micrófonos, ganancia",
        "",
    ]
    actual = None
    for n in notas_previstas():
        if n["instrumento"] != actual:
            actual = n["instrumento"]
            lineas += ["", f"## {actual.capitalize()} · referencia `{n['referencia']}` + `{args.uso_real}`", "",
                       "| Toma | Nota | Cuerda | GuitarTuna | DaTuner | Hecha |", "|---|---|---|---|---|---|"]
        for r in range(1, REPETICIONES + 1):
            toma = f"{n['instrumento']}_{n['nota']}_c{n['cuerda']}_r{r}"
            lineas.append(f"| `{toma}` | {n['nota']} ({n['descripcion']}) | {n['cuerda']} |  |  | [ ] |")
            for disp in (n["referencia"], args.uso_real):
                filas.append({"archivo": f"{toma}_{disp}.wav", "toma": toma, "instrumento": n["instrumento"],
                              "cuerda": n["cuerda"], "nota_esperada": n["nota"], "midi_esperado": n["midi"],
                              "repeticion": r, "dispositivo": disp})

    pd.DataFrame(filas, columns=COLUMNAS).to_csv(ruta_csv, index=False)
    (destino / "planilla.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    tomas = len(filas) // 2
    print(f"{tomas} tomas, {len(filas)} archivos previstos -> {ruta_csv} y planilla.md")


if __name__ == "__main__":
    main()
