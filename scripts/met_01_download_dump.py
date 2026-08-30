# -*- coding: utf-8 -*-
"""
Recolector 1a — Metropolitan Museum, volcado Open Access completo.

La API del Met bloquea por IP cuando se la consulta en paralelo (HTTP 403 en
todas las peticiones tras una rafaga de 12 hilos). El volcado oficial en CSV
resuelve los metadatos en una sola descarga y sin limite de peticiones; la API
queda reservada para resolver URLs de imagen del subconjunto ya filtrado
(met_02_resolve_images.py).

Fuente: https://github.com/metmuseum/openaccess (CC0 para los metadatos)

Salidas (data/raw/met/):
  MetObjects.csv        volcado integro (~317 MB, se reanuda si se corta)
  andean_textiles.csv   subconjunto filtrado
  harvest_log.json
"""
import csv
import json
import os
import re
import sys
import urllib.request

URL = "https://media.githubusercontent.com/media/metmuseum/openaccess/master/MetObjects.csv"
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "met")
DUMP = os.path.join(ROOT, "MetObjects.csv")
UA = {"User-Agent": "andean-iconography-research/1.0 (academic)"}

ANDEAN_CULTURES = [
    "paracas", "nasca", "nazca", "wari", "huari", "tiwanaku", "tiahuanaco",
    "chimu", "chimú", "chancay", "inca", "inka", "moche", "mochica",
    "lambayeque", "sican", "sicán", "chuquibamba", "recuay", "chavin",
    "chavín", "pachacamac", "aymara", "quechua", "vicus", "viru", "virú",
    "huarmey", "chincha", "cajamarca", "andean", "andes", "central andes",
    "south andes", "nasca-wari", "wari-tiwanaku", "ica", "ychsma", "sihuas",
]
ANDEAN_COUNTRIES = ["peru", "perú", "bolivia", "chile", "ecuador", "argentina"]
TEXTILE_TERMS = [
    "textile", "tapestry", "tunic", "mantle", "poncho", "cloth", "weaving",
    "woven", "loom", "fiber", "featherwork", "camelid", "cotton", "wool",
    "knotted", "quipu", "khipu", "shirt", "band", "bag", "hat", "headdress",
    "sling", "belt", "fringe", "embroider", "gauze", "brocade", "tie-dye",
]


def download():
    """Descarga reanudable: pide solo el rango que falta si el fichero existe."""
    have = os.path.getsize(DUMP) if os.path.exists(DUMP) else 0
    req = urllib.request.Request(URL, headers=dict(UA))
    if have:
        req.add_header("Range", "bytes=%d-" % have)
    try:
        resp = urllib.request.urlopen(req, timeout=120)
    except Exception as e:
        sys.exit("No se pudo iniciar la descarga: %s" % e)

    total = int(resp.headers.get("Content-Length") or 0) + (have if resp.status == 206 else 0)
    mode = "ab" if resp.status == 206 else "wb"
    if resp.status != 206:
        have = 0
    if have and resp.status != 206:
        print("      el servidor no admite reanudacion; se descarga de nuevo.")

    print("      %.0f MB por descargar (%.0f MB ya en disco)" % ((total - have) / 1e6, have / 1e6), flush=True)
    done = have
    with open(DUMP, mode) as f:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if done % (25 << 20) < (1 << 20):
                print("      %.0f/%.0f MB" % (done / 1e6, total / 1e6), flush=True)
    print("      descarga completa: %.0f MB" % (done / 1e6), flush=True)


# Los nombres de cultura deben casar como palabra completa. Sin esta precaucion
# "ica" (cultura Ica, costa sur del Peru) casa dentro de "Amer-ica-n" y arrastra
# miles de prendas estadounidenses del Costume Institute al corpus.
# Se admite el sufijo adjetival habitual: Nasca/Nascan, Wari/Waris, Inca/Incan.
_SUFFIX = r"(?:n|an|ian|s|es)?"
RE_CULTURE = re.compile(r"\b(?:%s)%s\b" % ("|".join(map(re.escape, ANDEAN_CULTURES)), _SUFFIX))
# Los paises si admiten coincidencia por prefijo: "peru" debe casar "Peruvian".
RE_COUNTRY = re.compile(r"\b(?:%s)" % "|".join(map(re.escape, ANDEAN_COUNTRIES)))
RE_TEXTILE = re.compile(r"(?:%s)" % "|".join(map(re.escape, TEXTILE_TERMS)))


def blob(row, keys):
    return " ".join(str(row.get(k) or "") for k in keys).lower()


def is_andean(text):
    return bool(RE_COUNTRY.search(text) or RE_CULTURE.search(text))


def main():
    os.makedirs(ROOT, exist_ok=True)

    print("[1/2] Descargando el volcado Open Access del Met...", flush=True)
    expected = 317650992
    if os.path.exists(DUMP) and os.path.getsize(DUMP) >= expected:
        print("      ya presente (%.0f MB), se omite." % (os.path.getsize(DUMP) / 1e6), flush=True)
    else:
        download()

    print("[2/2] Filtrando textiles andinos...", flush=True)
    geo_keys = ["Culture", "Country", "Region", "Subregion", "City", "Locale", "Excavation", "Locus"]
    obj_keys = ["Object Name", "Title", "Medium", "Classification"]

    keep = ["Object ID", "Object Number", "Is Public Domain", "Department", "Object Name",
            "Title", "Culture", "Period", "Dynasty", "Object Date", "Object Begin Date",
            "Object End Date", "Medium", "Dimensions", "Credit Line", "Classification",
            "Country", "Region", "Subregion", "Excavation", "Link Resource",
            "Repository", "Tags"]

    rows, total, by_dept, by_culture = [], 0, {}, {}
    csv.field_size_limit(10 ** 7)
    with open(DUMP, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            total += 1
            if not (is_andean(blob(row, geo_keys)) and RE_TEXTILE.search(blob(row, obj_keys))):
                continue
            rec = {k: row.get(k, "") for k in keep}
            rows.append(rec)
            d = rec.get("Department", "?")
            by_dept[d] = by_dept.get(d, 0) + 1
            c = (rec.get("Culture") or "sin cultura declarada").strip()[:60]
            by_culture[c] = by_culture.get(c, 0) + 1
            if total % 100000 == 0:
                print("      %d filas leidas, %d retenidas" % (total, len(rows)), flush=True)

    out = os.path.join(ROOT, "andean_textiles.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keep)
        w.writeheader()
        w.writerows(rows)

    pd = sum(1 for r in rows if str(r.get("Is Public Domain", "")).strip().lower() in ("true", "1"))
    log = {
        "source": "The Met Open Access CSV dump (github.com/metmuseum/openaccess)",
        "metadata_license": "CC0",
        "rows_scanned": total,
        "andean_textiles": len(rows),
        "public_domain": pd,
        "by_department": dict(sorted(by_dept.items(), key=lambda kv: -kv[1])),
        "top_cultures": dict(sorted(by_culture.items(), key=lambda kv: -kv[1])[:30]),
    }
    with open(os.path.join(ROOT, "harvest_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print("\nRESUMEN MET")
    print("  filas totales           %d" % total)
    print("  textiles andinos        %d" % len(rows))
    print("  dominio publico         %d" % pd)
    print("  departamentos           %s" % log["by_department"])
    print("\n  culturas mas frecuentes:")
    for c, n in list(log["top_cultures"].items())[:15]:
        print("    %-52s %d" % (c, n))
    print("\n  ->", out)


if __name__ == "__main__":
    main()
