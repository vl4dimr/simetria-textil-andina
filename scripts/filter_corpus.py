# -*- coding: utf-8 -*-
"""
Depuracion del corpus: deja solo soporte textil con superficie iconografica.

Dos exclusiones, por motivos distintos:

1. Soporte no textil. El filtro lexico de los recolectores admitio husos, agujas
   y ovillos ("Textiles-Implements"), ornamentos de metal y utiles de madera,
   porque terminos como "band", "bag" o "hat" aparecen en sus titulos. Son
   textiles en sentido catalografico, no superficies con iconografia.

2. Resolucion insuficiente. Por debajo de 0,3 Mpx no se puede medir un grupo de
   friso con fiabilidad: el motivo repetido ocupa demasiados pocos pixeles.

Salidas (data/):
  corpus_textile.csv       corpus de analisis
  corpus_textile_stats.json
"""
import csv
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

# El tipo no viene normalizado entre museos: el Met usa "Textiles-Woven",
# Cleveland "Textile" y Cooper Hewitt encadena varios ("Coca bag | Textiles").
# Una lista blanca literal descartaba piezas textiles evidentes, asi que la
# regla es: excluir por marcador de soporte o de utillaje, y de lo que quede,
# conservar lo que nombre un textil.
EXCLUDE_MARKERS = [
    "implement", "tools and equipment", "appliance", "spindle", "bobbin",
    "metal-", "metalwork", "wood-", "ceramic", "bone/ivory", "shell-",
    "bead", "basketry", "necklace", "musical instrument", "sculpture",
    "feathers-ornaments", "feathers-containers",
]
INCLUDE_MARKERS = [
    "textile", "embroider", "tapestry", "garment", "mantle", "tunic", "poncho",
    "cloth", "costume", "needlework", "band", "bag", "border", "panel", "sampler",
    "cap", "turban", "shawl", "sling", "trimming", "velvet", "square", "ensemble",
    "upholstery", "belt", "fragment", "netted", "featherwork", "woven",
]
MIN_MPX = 0.3
VIABLE_MIN = 50  # ejemplares minimos para sostener validacion cruzada estratificada


def main():
    src = os.path.join(DATA, "corpus.csv")
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())

    def is_textile_support(t):
        t = (t or "").lower()
        if any(m in t for m in EXCLUDE_MARKERS):
            return False
        return any(m in t for m in INCLUDE_MARKERS)

    dropped_type, dropped_res = [], []
    keep = []
    for r in rows:
        if not is_textile_support(r["object_type"]):
            dropped_type.append(r)
            continue
        if float(r["megapixels"] or 0) < MIN_MPX:
            dropped_res.append(r)
            continue
        keep.append(r)

    out = os.path.join(DATA, "corpus_textile.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(keep)

    def count(key, subset=None):
        c = {}
        for r in (subset if subset is not None else keep):
            c[str(r[key])] = c.get(str(r[key]), 0) + 1
        return dict(sorted(c.items(), key=lambda kv: -kv[1]))

    cultures = count("culture")
    labelled = {k: v for k, v in cultures.items() if k != "no determinada"}
    viable = {k: v for k, v in labelled.items() if v >= VIABLE_MIN}

    stats = {
        "input": len(rows),
        "kept": len(keep),
        "dropped_non_textile": len(dropped_type),
        "dropped_low_resolution": len(dropped_res),
        "dropped_types": count("object_type", dropped_type),
        "by_source": count("source"),
        "by_culture": cultures,
        "by_horizon": count("horizon"),
        "by_region": count("region"),
        "uncertain": sum(1 for r in keep if r["attribution_uncertain"] == "True"),
        "viable_classes": viable,
        "viable_total": sum(viable.values()),
        "unlabelled_for_unsupervised": cultures.get("no determinada", 0),
    }
    with open(os.path.join(DATA, "corpus_textile_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("DEPURACION")
    print("  entrada                    %d" % stats["input"])
    print("  descartadas por soporte    %d" % stats["dropped_non_textile"])
    print("  descartadas por resolucion %d" % stats["dropped_low_resolution"])
    print("  corpus de analisis         %d" % stats["kept"])
    print("\n  tipos descartados: %s" % stats["dropped_types"])
    print("\n  por fuente:   %s" % stats["by_source"])
    print("\n  clases viables (>=%d): %s" % (VIABLE_MIN, stats["viable_classes"]))
    print("  total etiquetado viable:  %d" % stats["viable_total"])
    print("  sin etiqueta (no supervisado): %d" % stats["unlabelled_for_unsupervised"])
    print("\n  por horizonte:")
    for k, v in stats["by_horizon"].items():
        print("    %-24s %d" % (k, v))
    print("\n  ->", out)


if __name__ == "__main__":
    main()
