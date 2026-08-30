# -*- coding: utf-8 -*-
"""
Unificacion de las fuentes en un corpus unico.

Cada museo describe la procedencia a su manera: el Met usa un campo `Culture`
libre ("Peru; central coast (?)"), Cleveland encadena pais, region, valle y
estilo ("Peru, South Coast, Ica Valley, Chavin style"), Cooper Hewitt reparte la
informacion entre `culture` y `place`. Aqui se normalizan a una etiqueta
cultural canonica y a un horizonte cronologico, que son las dos variables
objetivo del estudio.

La incertidumbre no se borra: las fichas con interrogante ("(?)") se marcan en
la columna `attribution_uncertain` para poder excluirlas o tratarlas aparte.

Salidas (data/):
  corpus.csv          una fila por imagen, con ruta local y etiquetas
  corpus_summary.json conteos por fuente, cultura, horizonte y soporte
"""
import csv
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
RAW = os.path.join(DATA, "raw")

# Cultura canonica -> (horizonte, inicio, fin) en anos; negativos = a.C.
CULTURES = [
    ("chavin",     ["chavin", "chavín"],                          "Horizonte Temprano",  -900,  -200),
    ("paracas",    ["paracas"],                                   "Horizonte Temprano",  -800,   100),
    ("nasca",      ["nasca", "nazca"],                            "Intermedio Temprano", -100,   800),
    ("moche",      ["moche", "mochica"],                          "Intermedio Temprano",  100,   800),
    ("recuay",     ["recuay"],                                    "Intermedio Temprano",  100,   700),
    ("salinar",    ["salinar"],                                   "Intermedio Temprano", -200,   200),
    ("vicus",      ["vicus", "vicús"],                            "Intermedio Temprano", -200,   400),
    ("wari",       ["wari", "huari"],                             "Horizonte Medio",      600,  1000),
    ("tiwanaku",   ["tiwanaku", "tiahuanaco"],                    "Horizonte Medio",      500,  1000),
    ("pachacamac", ["pachacamac"],                                "Horizonte Medio",      600,  1100),
    ("sican",      ["sican", "sicán", "lambayeque"],              "Intermedio Tardio",    800,  1350),
    ("chimu",      ["chimu", "chimú"],                            "Intermedio Tardio",    900,  1470),
    ("chancay",    ["chancay"],                                   "Intermedio Tardio",   1000,  1470),
    ("ica",        ["ica", "ychsma", "chincha"],                  "Intermedio Tardio",   1000,  1470),
    ("chuquibamba", ["chuquibamba"],                              "Intermedio Tardio",   1000,  1470),
    ("inca",       ["inca", "inka"],                              "Horizonte Tardio",    1400,  1533),
    ("colonial",   ["colonial", "aymara", "quechua", "shipibo"],  "Colonial/Republicano", 1533, 1950),
]
_SUFFIX = r"(?:n|an|ian|s|es)?"
PATTERNS = [(canon, re.compile(r"\b(?:%s)%s\b" % ("|".join(map(re.escape, alts)), _SUFFIX)), hor, a, b)
            for canon, alts, hor, a, b in CULTURES]

REGIONS = [
    ("costa sur",    ["south coast", "costa sur", "ica valley", "nasca valley", "paracas"]),
    ("costa central", ["central coast", "costa central", "chancay valley", "lima", "rimac"]),
    ("costa norte",  ["north coast", "costa norte", "moche valley", "chicama", "lambayeque"]),
    ("sierra sur",   ["south highlands", "cusco", "cuzco", "titicaca", "arequipa"]),
    ("sierra central", ["central highlands", "ayacucho", "huancayo"]),
    ("sierra norte", ["north highlands", "cajamarca", "callejon"]),
    ("altiplano",    ["altiplano", "bolivia", "tiwanaku"]),
]
REGION_PATTERNS = [(canon, re.compile(r"(?:%s)" % "|".join(map(re.escape, alts)))) for canon, alts in REGIONS]

UNCERTAIN = re.compile(r"\(\?\)|\bprobably\b|\bpossibly\b|\battributed\b|\bstyle of\b|\?")


def classify_culture(text):
    t = (text or "").lower()
    for canon, pat, hor, a, b in PATTERNS:
        if pat.search(t):
            return canon, hor, a, b
    return "no determinada", "no determinado", None, None


def classify_region(text):
    t = (text or "").lower()
    for canon, pat in REGION_PATTERNS:
        if pat.search(t):
            return canon
    return "no determinada"


def dims(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return (None, None)


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def met_rows():
    meta = {r["Object ID"]: r for r in read_csv(os.path.join(RAW, "met", "andean_textiles.csv"))}
    idx = read_csv(os.path.join(RAW, "met", "images_index.csv"))
    imgdir = os.path.join(RAW, "met", "images")
    out = []
    for r in idx:
        if r.get("isPublicDomain") != "True" or not r.get("primaryImage"):
            continue
        oid = r["objectID"]
        m = meta.get(oid, {})
        ext = os.path.splitext(r["primaryImage"])[1] or ".jpg"
        path = os.path.join(imgdir, "met_%s%s" % (oid, ext))
        if not os.path.exists(path):
            continue
        prov = " ".join([r.get("culture") or "", m.get("Country") or "",
                         m.get("Region") or "", m.get("Subregion") or "", m.get("Excavation") or ""])
        out.append({
            "source": "met", "source_id": oid, "file": path,
            "title": r.get("title"), "provenance_raw": prov.strip(),
            "object_type": r.get("classification") or m.get("Object Name"),
            "medium": m.get("Medium"), "date_raw": r.get("objectDate"),
            "date_begin": m.get("Object Begin Date"), "date_end": m.get("Object End Date"),
            "license": "CC0 (dominio publico)", "url": r.get("objectURL"),
        })
    return out


def cleveland_rows():
    imgdir = os.path.join(RAW, "cleveland", "images")
    meta = {r["id"]: r for r in read_csv(os.path.join(RAW, "cleveland", "andean_textiles.csv"))}
    out = []
    for r in read_csv(os.path.join(RAW, "cleveland", "images_manifest.csv")):
        path = os.path.join(imgdir, r["file"])
        if not os.path.exists(path):
            continue
        m = meta.get(r["id"], {})
        out.append({
            "source": "cleveland", "source_id": r["id"], "file": path,
            "title": r.get("title"), "provenance_raw": r.get("culture"),
            "object_type": r.get("type"), "medium": m.get("technique"),
            "date_raw": r.get("creation_date"),
            "date_begin": m.get("creation_date_earliest"), "date_end": m.get("creation_date_latest"),
            "license": "CC0", "url": r.get("url"),
        })
    return out


def smithsonian_rows():
    imgdir = os.path.join(RAW, "smithsonian", "images")
    out = []
    for r in read_csv(os.path.join(RAW, "smithsonian", "images_manifest.csv")):
        if r.get("unit_code") not in ("CHNDM", "NMAI", "NMNHANTHRO"):
            continue  # descarta arrastres de unidades de historia natural
        path = os.path.join(imgdir, r["file"])
        if not os.path.exists(path):
            continue
        out.append({
            "source": "smithsonian/%s" % r.get("unit_code"), "source_id": r["id"], "file": path,
            "title": r.get("title"),
            "provenance_raw": " ".join([r.get("culture") or "", r.get("place") or ""]).strip(),
            "object_type": r.get("object_type"), "medium": "",
            "date_raw": r.get("date"), "date_begin": "", "date_end": "",
            "license": r.get("license") or "CC0", "url": r.get("record_link"),
        })
    return out


def main():
    rows = met_rows() + cleveland_rows() + smithsonian_rows()
    print("Imagenes localizadas: %d" % len(rows), flush=True)

    for n, r in enumerate(rows, 1):
        blob = " ".join(str(r.get(k) or "") for k in ("provenance_raw", "title", "date_raw"))
        culture, horizon, a, b = classify_culture(blob)
        r["culture"] = culture
        r["horizon"] = horizon
        r["horizon_begin"] = a
        r["horizon_end"] = b
        r["region"] = classify_region(blob)
        r["attribution_uncertain"] = bool(UNCERTAIN.search(blob))
        w, h = dims(r["file"])
        r["width"], r["height"] = w, h
        r["megapixels"] = round(w * h / 1e6, 2) if w and h else None
        r["bytes"] = os.path.getsize(r["file"])
        r["file"] = os.path.relpath(r["file"], BASE).replace("\\", "/")
        if n % 200 == 0:
            print("  %d/%d procesadas" % (n, len(rows)), flush=True)

    fields = ["source", "source_id", "file", "title", "object_type", "medium",
              "culture", "horizon", "horizon_begin", "horizon_end", "region",
              "attribution_uncertain", "provenance_raw", "date_raw", "date_begin",
              "date_end", "width", "height", "megapixels", "bytes", "license", "url"]
    out_path = os.path.join(DATA, "corpus.csv")
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    def count(key):
        c = {}
        for r in rows:
            c[str(r.get(key))] = c.get(str(r.get(key)), 0) + 1
        return dict(sorted(c.items(), key=lambda kv: -kv[1]))

    usable = [r for r in rows if (r["megapixels"] or 0) >= 0.5]
    summary = {
        "images_total": len(rows),
        "bytes_total_mb": round(sum(r["bytes"] for r in rows) / 1e6),
        "by_source": count("source"),
        "by_culture": count("culture"),
        "by_horizon": count("horizon"),
        "by_region": count("region"),
        "uncertain_attribution": sum(1 for r in rows if r["attribution_uncertain"]),
        "median_megapixels": sorted(r["megapixels"] or 0 for r in rows)[len(rows) // 2] if rows else 0,
        "at_least_0_5_mpx": len(usable),
        "culture_determined": sum(1 for r in rows if r["culture"] != "no determinada"),
    }
    with open(os.path.join(DATA, "corpus_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\nCORPUS UNIFICADO")
    print("  imagenes            %d  (%.0f MB)" % (summary["images_total"], summary["bytes_total_mb"]))
    print("  cultura determinada %d" % summary["culture_determined"])
    print("  atribucion dudosa   %d" % summary["uncertain_attribution"])
    print("  mediana de megapix  %.2f" % summary["median_megapixels"])
    print("\n  por fuente:    %s" % summary["by_source"])
    print("\n  por horizonte:")
    for k, v in summary["by_horizon"].items():
        print("    %-24s %d" % (k, v))
    print("\n  por cultura:")
    for k, v in summary["by_culture"].items():
        print("    %-24s %d" % (k, v))
    print("\n  ->", out_path)


if __name__ == "__main__":
    main()
