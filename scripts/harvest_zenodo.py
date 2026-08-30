# -*- coding: utf-8 -*-
"""
Recolector 3 — Zenodo (API publica, sin clave).

Zenodo indexa texto completo, asi que una consulta suelta como "andean textile"
devuelve decenas de miles de falsos positivos. Aqui se usan consultas dirigidas
a titulo y palabras clave, restringidas a datasets, imagenes y software, y
despues se aplica un filtro de pertinencia sobre los metadatos.

Salidas (data/raw/zenodo/):
  records.jsonl   registros crudos deduplicados
  candidates.csv  subconjunto pertinente con enlaces de descarga
  harvest_log.json
"""
import csv
import json
import os
import time
import urllib.parse
import urllib.request

API = "https://zenodo.org/api/records"
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "zenodo")
UA = {"User-Agent": "andean-iconography-research/1.0 (academic)"}

# Consultas dirigidas: titulo/keywords, no texto completo.
QUERIES = [
    'title:(textile AND (andean OR peru OR peruvian OR bolivia OR precolumbian OR "pre-columbian"))',
    'title:(paracas OR nasca OR nazca OR wari OR huari OR tiwanaku OR tiahuanaco)',
    'title:(chancay OR chimu OR "chimú" OR moche OR lambayeque OR sican)',
    'title:(quipu OR khipu)',
    'keywords:("andean textiles" OR "peruvian textiles" OR "pre-columbian textiles")',
    'title:(iconography AND (andean OR peru OR inca OR inka))',
    'title:((weaving OR loom OR tapestry) AND (andes OR andean OR peru OR bolivia))',
    'title:(inca OR inka) AND title:(art OR design OR pattern OR iconography OR textile)',
]
TYPES = ["dataset", "image", "software", "publication"]

# La API anonima de Zenodo rechaza size>25 con HTTP 400; se pagina en bloques de 25.
PAGE_SIZE = 25
PAGES = 8

ANDEAN = ["andean", "andes", "peru", "peruvian", "bolivia", "bolivian", "inca", "inka",
          "paracas", "nasca", "nazca", "wari", "huari", "tiwanaku", "tiahuanaco",
          "chancay", "chimu", "chimú", "moche", "lambayeque", "sican", "quechua",
          "aymara", "pre-columbian", "precolumbian", "prehispanic", "pre-hispanic",
          "cusco", "cuzco", "titicaca", "quipu", "khipu"]
TOPIC = ["textile", "weaving", "woven", "tapestry", "tunic", "iconograph", "pattern",
         "motif", "design", "ornament", "geometr", "symmetry", "art", "image", "photograph",
         "quipu", "khipu", "cloth", "fiber", "fibre", "dye", "loom"]


def fetch(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.load(r)
        except Exception as e:
            print("      error (%s), reintento %d" % (e, i + 1))
            time.sleep(2 * (i + 1))
    return None


def flatten(rec):
    m = rec.get("metadata", {})
    files = rec.get("files") or []
    creators = m.get("creators") or []
    return {
        "id": rec.get("id"),
        "doi": m.get("doi") or rec.get("doi"),
        "title": (m.get("title") or "").replace("\n", " ").strip(),
        "type": (m.get("resource_type") or {}).get("type"),
        "subtype": (m.get("resource_type") or {}).get("subtype"),
        "publication_date": m.get("publication_date"),
        "creators": "; ".join(c.get("name", "") for c in creators[:5]),
        "keywords": "; ".join(m.get("keywords") or [])[:300],
        "license": (m.get("license") or {}).get("id") if isinstance(m.get("license"), dict) else m.get("license"),
        "access_right": m.get("access_right"),
        "n_files": len(files),
        "size_mb": round(sum(f.get("size", 0) for f in files) / 1e6, 2),
        "file_types": "; ".join(sorted({(f.get("key", "").rsplit(".", 1) + [""])[1].lower() for f in files})[:8]),
        "url": rec.get("links", {}).get("self_html") or ("https://zenodo.org/records/%s" % rec.get("id")),
        "description": (m.get("description") or "")[:400].replace("<p>", " ").replace("</p>", " "),
    }


def is_relevant(row):
    blob = " ".join(str(row.get(k) or "") for k in
                    ("title", "keywords", "description", "creators")).lower()
    return any(a in blob for a in ANDEAN) and any(t in blob for t in TOPIC)


def main():
    os.makedirs(ROOT, exist_ok=True)
    seen, raw = {}, []

    for q in QUERIES:
        for rtype in TYPES:
            page = 1
            while page <= PAGES:
                url = API + "?" + urllib.parse.urlencode(
                    {"q": q, "type": rtype, "size": PAGE_SIZE, "page": page, "sort": "bestmatch"})
                d = fetch(url)
                if not d:
                    break
                hits = d.get("hits", {}).get("hits", [])
                total = d.get("hits", {}).get("total", 0)
                if page == 1:
                    print("[q] %-58s %-11s -> %s" % (q[:58], rtype, total), flush=True)
                if not hits:
                    break
                for h in hits:
                    if h.get("id") not in seen:
                        seen[h["id"]] = 1
                        raw.append(h)
                if len(hits) < PAGE_SIZE:
                    break
                page += 1
                time.sleep(0.4)
            time.sleep(0.3)

    with open(os.path.join(ROOT, "records.jsonl"), "w", encoding="utf-8") as f:
        for r in raw:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    flat = [flatten(r) for r in raw]
    rel = [r for r in flat if is_relevant(r)]
    rel.sort(key=lambda r: (r["type"] != "dataset", r["type"] != "image", -r["size_mb"]))

    csv_path = os.path.join(ROOT, "candidates.csv")
    if rel:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rel[0].keys()))
            w.writeheader()
            w.writerows(rel)

    by_type = {}
    for r in rel:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1

    log = {
        "source": "Zenodo REST API",
        "queries": QUERIES,
        "records_retrieved": len(raw),
        "relevant": len(rel),
        "by_type": by_type,
        "open_access": sum(1 for r in rel if r["access_right"] == "open"),
        "with_files": sum(1 for r in rel if r["n_files"] > 0),
    }
    with open(os.path.join(ROOT, "harvest_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print("\nRESUMEN ZENODO")
    for k, v in log.items():
        if k != "queries":
            print("  %-20s %s" % (k, v))
    print("\n  ->", csv_path)
    print("\nTop candidatos (dataset/image):")
    for r in rel[:15]:
        print("  [%-11s] %-62s %6.1f MB  %s" % (r["type"], r["title"][:62], r["size_mb"], r["url"]))


if __name__ == "__main__":
    main()
