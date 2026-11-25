"""Verifica la coherencia de compartido/afinaciones.json y compartido/parametros.json.

Uso:  python3 compartido/verificar_compartido.py [--tabla]

Solo usa la biblioteca estándar. Termina con código 1 si encuentra errores,
así que se puede correr en CI o antes de cada PR que toque compartido/.
"""

import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
NOTAS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SOLFEO = ["Do", "Do♯", "Re", "Re♯", "Mi", "Fa", "Fa♯", "Sol", "Sol♯", "La", "La♯", "Si"]


def midi_de_nombre(nombre: str) -> int:
    """'E2' -> 40, 'Eb2' -> 39, 'F#3' -> 54 (C4 = 60)."""
    letra, resto = nombre[0], nombre[1:]
    alter = 0
    while resto and resto[0] in "b#":
        alter += -1 if resto[0] == "b" else 1
        resto = resto[1:]
    return 12 * (int(resto) + 1) + NOTAS[letra] + alter


def frecuencia(midi: int, la4: float) -> float:
    return la4 * 2 ** ((midi - 69) / 12)


def obtener(d: dict, ruta: str):
    for parte in ruta.split("."):
        d = d[parte]
    return d


def main() -> int:
    afin = json.loads((AQUI / "afinaciones.json").read_text(encoding="utf-8"))
    par = json.loads((AQUI / "parametros.json").read_text(encoding="utf-8"))
    errores = []
    la4 = afin["referencia_la4_hz"]
    if par["referencia_la4_hz"] != la4:
        errores.append("referencia_la4_hz distinta en afinaciones.json y parametros.json")

    f_min, f_max = par["rango"]["f_min_hz"], par["rango"]["f_max_hz"]
    filas = []
    ids_inst = set()
    for inst in afin["instrumentos"]:
        if inst["id"] in ids_inst:
            errores.append(f"instrumento repetido: {inst['id']}")
        ids_inst.add(inst["id"])
        ids_afin = set()
        for a in inst["afinaciones"]:
            clave = f"{inst['id']}/{a['id']}"
            if a["id"] in ids_afin:
                errores.append(f"afinación repetida: {clave}")
            ids_afin.add(a["id"])
            numeros = [c["cuerda"] for c in a["cuerdas"]]
            if numeros != list(range(len(numeros), 0, -1)):
                errores.append(f"{clave}: cuerdas deben ir de {len(numeros)} a 1, hay {numeros}")
            for c in a["cuerdas"]:
                if midi_de_nombre(c["nota"]) != c["midi"]:
                    errores.append(f"{clave} cuerda {c['cuerda']}: {c['nota']} no es MIDI {c['midi']}")
                f = frecuencia(c["midi"], la4)
                if not f_min <= f <= f_max:
                    errores.append(f"{clave} cuerda {c['cuerda']}: {f:.2f} Hz fuera del rango")
                filas.append((clave, c["cuerda"], c["nota"], c["midi"], f))

    for ruta in par["provisionales"]:
        try:
            obtener(par, ruta)
        except KeyError:
            errores.append(f"provisional inexistente en parametros.json: {ruta}")

    # YIN necesita una ventana de integración W = N - tau_max >= tau_max.
    N = par["tramo"]["N"]
    for fs in (16000, 44100, 48000):
        tau_max = int(fs / f_min)
        if N - tau_max < tau_max:
            errores.append(f"N={N} es corto para YIN con f_min={f_min} Hz a fs={fs} Hz")

    if "--tabla" in sys.argv:
        for clave, cuerda, nota, midi, f in filas:
            nombre_es = f"{SOLFEO[midi % 12]}{midi // 12 - 1}"
            print(f"{clave:28s} c{cuerda}  {nota:4s} {nombre_es:6s} MIDI {midi:3d}  {f:8.2f} Hz")

    if errores:
        print("ERRORES:")
        for e in errores:
            print("  -", e)
        return 1
    print(f"OK: {len(ids_inst)} instrumentos, {len(filas)} cuerdas, parámetros coherentes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
