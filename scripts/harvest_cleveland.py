# -*- coding: utf-8 -*-
"""
Recolector 4 — Cleveland Museum of Art (Open Access API, sin clave).

Incorporado al plan despues de comprobar que el NMAI del Smithsonian publica sus
metadatos como CC0 pero no distribuye imagenes: de toda la unidad, solo 180
registros tienen media CC0, y ninguno de los textiles andinos consultados. Sin
una segunda fuente con imagen abierta el corpus visual quedaba en manos de un
unico museo.

Cleveland declara procedencia con un detalle poco habitual —"Peru, South Coast,
Ica Valley, Chavin style"— util para etiquetar cultura, region y periodo sin
recurrir a texto libre.

Salidas (data/raw/cleveland/):
  records.jsonl        registros crudos
  andean_textiles.csv  subconjunto con imagen CC0
  harvest_log.json
"""
import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request

API = "https://openaccess-api.clevelandart.org/api/artworks/"
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "cleveland")
UA = {"User-Agent": "andean-iconography-research/1.0 (academic)"}
LIMIT = 100

QUERIES = ["Peru", "Andean", "Andes", "Bolivia", "Paracas", "Nasca", "Nazca",
           "Wari", "Huari", "Tiwanaku", "Chancay", "Chimu", "Inca", "Moche",
           "Ica", "Recuay", "Chavin", "Lambayeque", "Aymara", "Quechua"]

ANDEAN_CULTURES = ["paracas", "nasca", "nazca", "wari", "huari", "tiwanaku", "tiahuanaco",
                   "chimu", "chimú", "chancay", "inca", "inka", "moche", "mochica",
                   "lambayeque", "sican", "sicán", "ica", "chuquibamba", "recuay",
                   "chavin", "chavín", "pachacamac", "aymara", "quechua", "andean", "andes"]
ANDEAN_COUNTRIES = ["peru", "perú", "bolivia", "chile", "ecuador"]
TEXTILE_TERMS = ["textile", "tapestry", "tunic", "mantle", "poncho", "cloth", "weaving",
                 "woven", "loom", "fiber", "featherwork", "camelid", "cotton", "wool",
                 "garment", "loincloth", "shirt", "band", "bag", "hat", "headdress",
                 "sling", "belt", "embroider", "gauze", "brocade", "panel", "fragment"]

_SUFFIX = r"(?:n|an|ian|s|es)?"
RE_CULTURE = re.compile(r"\b(?:%s)%s\b" % ("|".join(map(re.escape, ANDEAN_CULTURES)), _SUFFIX))
RE_COUNTRY = re.compile(r"\b(?:%s)" % "|".join(map(re.escape, ANDEAN_COUNTRIES)))
RE_TEXTILE = re.compile(r"(?:%s)" % "|".join(map(re.escape, TEXTILE_TERMS)))


def fetch(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.load(r)
        except Exception as e:
            print("      error (%s), reintento %d" % (e, i + 1), flush=True)
            time.sleep(2 * (i + 1))
    return None


def flatten(a):
    imgs = a.get("images") or {}
    web = imgs.get("web") or {}
    print_ = imgs.get("print") or {}
    culture = a.get("culture")
    if isinstance(culture, list):
        culture = " | ".join(str(c) for c in culture)
    creators = a.get("creators") or []
    return {
        "id": a.get("id"),
        "accession_number": a.get("accession_number"),
        "title": a.get("title"),
        "culture": culture,
        "type": a.get("type"),
        "technique": a.get("technique"),
        "department": a.get("department"),
        "creation_date": a.get("creation_date"),
        "creation_date_earliest": a.get("creation_date_earliest"),
        "creation_date_latest": a.get("creation_date_latest"),
        "measurements": a.get("measurements"),
        "share_license_status": a.get("share_license_status"),
        "image_web": web.get("url"),
        "image_print": print_.get("url"),
        "image_width": web.get("width"),
        "image_height": web.get("height"),
        "url": a.get("url"),
        "creators": "; ".join(c.get("description", "") for c in creators[:3]),
        "description": (a.get("description") or "")[:400],
    }


def is_relevant(row):
    geo = " ".join(str(row.get(k) or "") for k in ("culture", "title", "description")).lower()
    obj = " ".join(str(row.get(k) or "") for k in
                   ("type", "title", "technique", "department", "description")).lower()
    return bool((RE_COUNTRY.search(geo) or RE_CULTURE.search(geo)) and RE_TEXTILE.search(obj))


def main():
    os.makedirs(ROOT, exist_ok=True)
    seen, raw = {}, []

    for q in QUERIES:
        skip = 0
        while True:
            url = API + "?" + urllib.parse.urlencode(
                {"q": q, "limit": LIMIT, "skip": skip, "has_image": 1, "cc0": 1})
            d = fetch(url)
            if not d:
                break
            data = d.get("data", [])
            total = d.get("info", {}).get("total", 0)
            if skip == 0:
                print("[q] %-12s -> %s con imagen CC0" % (q, total), flush=True)
            if not data:
                break
            for a in data:
                if a.get("id") not in seen:
                    seen[a["id"]] = 1
                    raw.append(a)
            skip += LIMIT
            if skip >= min(total, 1000):
                break
            time.sleep(0.3)
        time.sleep(0.2)

    with open(os.path.join(ROOT, "records.jsonl"), "w", encoding="utf-8") as f:
        for a in raw:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    flat = [flatten(a) for a in raw]
    rel = [r for r in flat if is_relevant(r)]
    with_img = [r for r in rel if r["image_web"]]

    csv_path = os.path.join(ROOT, "andean_textiles.csv")
    if rel:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rel[0].keys()))
            w.writeheader()
            w.writerows(rel)

    types = {}
    for r in rel:
        types[r["type"]] = types.get(r["type"], 0) + 1

    log = {
        "source": "Cleveland Museum of Art Open Access API",
        "image_license": "CC0 (filtro cc0=1 aplicado en la peticion)",
        "queries": QUERIES,
        "records_retrieved": len(raw),
        "andean_textiles": len(rel),
        "with_image": len(with_img),
        "by_type": dict(sorted(types.items(), key=lambda kv: -kv[1])),
    }
    with open(os.path.join(ROOT, "harvest_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print("\nRESUMEN CLEVELAND")
    for k, v in log.items():
        if k != "queries":
            print("  %-20s %s" % (k, v))
    print("\n  ->", csv_path)


if __name__ == "__main__":
    main()
