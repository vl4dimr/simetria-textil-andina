# -*- coding: utf-8 -*-
"""
Analisis de simetria sobre el corpus real.

Aplica al corpus la misma cadena validada sobre patrones sinteticos
(92,9 % de acierto en los siete grupos de friso): rectificar por la red,
detectar periodicidad, puntuar cada operacion contra el techo de la propia
traslacion y asignar grupo.

Una pieza sin periodicidad detectable no recibe grupo. No es un fallo del
metodo: buena parte de la iconografia andina es figurativa o de composicion
unica, y forzar una etiqueta de friso sobre un diseno no periodico produciria
justamente el tipo de resultado que no se sostiene en revision.

Salidas (results/):
  symmetry.csv           una fila por imagen
  symmetry_summary.json  reparto por cultura y horizonte
"""
import csv
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import symmetry_core as sc

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results")
MAX_SIDE = 512          # compromiso entre resolucion y coste: 90 correlaciones por imagen
MIN_PERIODICITY = 0.45  # correlacion minima bajo traslacion para considerar periodico

# Radio minimo, en fraccion del lado mayor, para aceptar un pico de la
# autocorrelacion como vector de red. Es la correccion mas importante del
# analisis: un tejido tiene dos periodicidades superpuestas, la de la trama de
# hilos y la del diseno. La trama es mucho mas regular, asi que domina la
# autocorrelacion y el detector se queda con ella. En una primera pasada sin este
# limite, el 29 % de las piezas con grupo asignado tenian periodos de 4 a 15
# pixeles: eso son hilos, no iconografia. Y un ligamento tafetan es una retícula
# con reflexiones en ambos ejes, es decir p2mm, de modo que el sesgo no era
# neutro sino que inflaba justo el grupo mas simetrico.
MIN_PERIOD_FRACTION = 0.03


def analyze(path):
    a = sc.load_gray(path, max_side=MAX_SIDE)
    if a is None:
        return {"status": "ilegible"}

    min_r = max(8, int(MIN_PERIOD_FRACTION * max(a.shape)))
    v1, _, _ = sc.lattice_vectors(sc.autocorrelation(a), min_radius=min_r)
    a, angle = sc.rectify(a, v1)
    v1, v2, peaks = sc.lattice_vectors(sc.autocorrelation(a), min_radius=min_r)
    if v1 is None:
        return {"status": "sin periodicidad", "rectify_angle": round(angle, 2)}

    trans = sc.translation_score(a, v1)
    if trans is None or trans < MIN_PERIODICITY:
        return {"status": "periodicidad debil", "rectify_angle": round(angle, 2),
                "translation": None if trans is None else round(trans, 4)}

    period_x = abs(v1[1]) if abs(v1[1]) > 2 else None
    period_y = abs(v1[0]) if abs(v1[0]) > 2 else None
    if v2 is not None:
        period_x = period_x or (abs(v2[1]) if abs(v2[1]) > 2 else None)
        period_y = period_y or (abs(v2[0]) if abs(v2[0]) > 2 else None)

    thr, ceiling = sc.decision_threshold(a, v1)
    s = sc.symmetry_scores(a, period_y=period_y, period_x=period_x)
    frieze = sc.frieze_group(s, thr)
    wall, rot_order = sc.wallpaper_group(s, thr)

    return {
        "status": "ok",
        "frieze_group": frieze,
        "wallpaper_group": wall,
        "rotation_order": rot_order,
        # Una sola direccion de red significa cenefa; dos, campo bidimensional.
        "lattice_dim": 2 if v2 is not None else 1,
        "period_x": None if period_x is None else round(float(period_x), 1),
        "period_y": None if period_y is None else round(float(period_y), 1),
        "translation": round(ceiling, 4) if ceiling else None,
        "threshold": round(thr, 4),
        "rectify_angle": round(angle, 2),
        **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()},
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(DATA, "corpus_textile.csv")
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    print("Piezas a analizar: %d" % len(rows), flush=True)

    results, t0 = [], time.time()
    for n, r in enumerate(rows, 1):
        path = os.path.join(BASE, r["file"])
        try:
            res = analyze(path) if os.path.exists(path) else {"status": "fichero ausente"}
        except Exception as e:
            res = {"status": "error: %s" % type(e).__name__}
        results.append({
            "source": r["source"], "source_id": r["source_id"], "file": r["file"],
            "culture": r["culture"], "horizon": r["horizon"], "region": r["region"],
            "object_type": r["object_type"],
            "attribution_uncertain": r["attribution_uncertain"],
            "megapixels": r["megapixels"], **res,
        })
        if n % 50 == 0:
            el = time.time() - t0
            print("  [%d/%d] %.1f s/img, quedan ~%.0f min" % (
                n, len(rows), el / n, (len(rows) - n) * el / n / 60), flush=True)

    fields = sorted({k for r in results for k in r},
                    key=lambda k: (k not in ("source", "source_id", "file", "culture",
                                             "horizon", "status", "frieze_group"), k))
    with open(os.path.join(OUT, "symmetry.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)

    ok = [r for r in results if r.get("status") == "ok"]

    def tally(rows_, key):
        c = {}
        for r in rows_:
            c[str(r.get(key))] = c.get(str(r.get(key)), 0) + 1
        return dict(sorted(c.items(), key=lambda kv: -kv[1]))

    by_culture = {}
    for cul in sorted({r["culture"] for r in ok}):
        sub = [r for r in ok if r["culture"] == cul]
        by_culture[cul] = {"n": len(sub), "frieze": tally(sub, "frieze_group"),
                           "rotation_order": tally(sub, "rotation_order")}
    by_horizon = {}
    for hor in sorted({r["horizon"] for r in ok}):
        sub = [r for r in ok if r["horizon"] == hor]
        by_horizon[hor] = {"n": len(sub), "frieze": tally(sub, "frieze_group")}

    summary = {
        "analyzed": len(results),
        "status": tally(results, "status"),
        "with_group": len(ok),
        "frieze_overall": tally(ok, "frieze_group"),
        "wallpaper_overall": tally(ok, "wallpaper_group"),
        "lattice_dim": tally(ok, "lattice_dim"),
        "by_culture": by_culture,
        "by_horizon": by_horizon,
        "settings": {"max_side": MAX_SIDE, "ratio": sc.DEFAULT_RATIO,
                     "min_periodicity": MIN_PERIODICITY},
    }
    with open(os.path.join(OUT, "symmetry_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\nRESULTADO")
    print("  estado:            %s" % summary["status"])
    print("  con grupo:         %d" % summary["with_group"])
    print("  grupos de friso:   %s" % summary["frieze_overall"])
    print("  dimension de red:  %s" % summary["lattice_dim"])
    print("\n  ->", os.path.join(OUT, "symmetry.csv"))


if __name__ == "__main__":
    main()
