# -*- coding: utf-8 -*-
"""
Recolector 2 — Smithsonian Open Access (api.si.edu).

Requiere una clave gratuita de api.data.gov. Se lee de la variable de entorno
SI_API_KEY; si no existe usa DEMO_KEY, que funciona pero esta limitada a
30 peticiones por hora y 50 por dia (suficiente para una prueba, no para el
corpus completo).

Unidades relevantes:
  NMAI  National Museum of the American Indian  (coleccion andina principal)
  NMNH  National Museum of Natural History      (etnologia sudamericana)
  CHNDM Cooper Hewitt, Smithsonian Design Museum (textiles)

Salidas (data/raw/smithsonian/):
  records.jsonl        registros crudos
  andean_textiles.csv  subconjunto con imagen y licencia CC0
  harvest_log.json
"""
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.si.edu/openaccess/api/v1.0"
KEY = os.environ.get("SI_API_KEY") or os.environ.get("DATA_GOV_API_KEY") or "DEMO_KEY"
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "smithsonian")
UA = {"User-Agent": "andean-iconography-research/1.0 (academic)"}
ROWS = 1000  # maximo permitido por peticion

# Consultas acotadas. La condicion online_media_type:Images es decisiva: sin ella
# el buscador devuelve sobre todo fichas catalograficas sin imagen asociada
# (en una prueba, 1 de cada 8.708 registros de NMAI traia media).
QUERIES = [
    'unit_code:NMAI AND online_media_type:Images AND (textile OR tunic OR mantle OR poncho OR weaving)',
    'unit_code:NMAI AND online_media_type:Images AND (Peru OR Bolivia OR Andean)',
    'unit_code:NMNH AND online_media_type:Images AND (Peru OR Bolivia) AND (textile OR cloth OR weaving)',
    'online_media_type:Images AND (Paracas OR Nasca OR Nazca OR Wari OR Huari OR Tiwanaku OR Chancay OR Chimu)',
    'unit_code:CHNDM AND online_media_type:Images AND (Peru OR Peruvian OR Andean) AND textile',
]

ANDEAN = ["peru", "perú", "bolivia", "chile", "ecuador", "andean", "andes", "aymara",
          "quechua", "paracas", "nasca", "nazca", "wari", "huari", "tiwanaku",
          "tiahuanaco", "chancay", "chimu", "chimú", "inca", "inka", "moche",
          "lambayeque", "ica", "chuquibamba", "cusco", "cuzco", "titicaca"]
TEXTILE = ["textile", "tunic", "mantle", "poncho", "cloth", "weaving", "woven", "tapestry",
           "shirt", "bag", "band", "belt", "fiber", "cotton", "wool", "camelid", "alpaca",
           "llama", "featherwork", "quipu", "khipu", "loom", "shawl", "manta", "aguayo"]


def fetch(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "ignore")[:300]
            except Exception:
                pass
            if e.code == 429:
                print("      limite de peticiones alcanzado (%s). %s" % (e.code, body))
                return "RATE_LIMIT"
            print("      HTTP %s: %s" % (e.code, body))
            time.sleep(2 * (i + 1))
        except Exception as e:
            print("      error: %s" % e)
            time.sleep(2 * (i + 1))
    return None


def search(q, start=0):
    url = API + "/search?" + urllib.parse.urlencode(
        {"api_key": KEY, "q": q, "rows": ROWS, "start": start})
    return fetch(url)


def media_of(rec):
    """URL de imagen y licencia declarada, si el registro las trae."""
    try:
        om = rec["content"]["descriptiveNonRepeating"]["online_media"]
    except Exception:
        return None, None, 0
    media = om.get("media") or []
    if not media:
        return None, None, om.get("mediaCount", 0)
    m = media[0]
    url = m.get("content") or m.get("thumbnail")
    usage = (m.get("usage") or {}).get("access")
    return url, usage, om.get("mediaCount", len(media))


def flatten(rec):
    c = rec.get("content", {})
    dnr = c.get("descriptiveNonRepeating", {})
    idx = c.get("indexedStructured", {})
    free = c.get("freetext", {})

    def ft(key):
        vals = free.get(key) or []
        return " | ".join(str(v.get("content")) for v in vals if v.get("content"))

    img, usage, count = media_of(rec)
    return {
        "id": rec.get("id"),
        "title": rec.get("title"),
        "unit_code": rec.get("unitCode"),
        "record_link": dnr.get("record_link"),
        "object_type": " | ".join(idx.get("object_type") or []),
        "culture": " | ".join(idx.get("culture") or []),
        "place": " | ".join(idx.get("place") or []),
        "date": " | ".join(idx.get("date") or []),
        "topic": " | ".join(idx.get("topic") or []),
        "physical_description": ft("physicalDescription"),
        "notes": ft("notes")[:500],
        "media_url": img,
        "media_usage": usage,
        "media_count": count,
    }


def is_relevant(row):
    geo = " ".join(str(row.get(k) or "") for k in ("culture", "place", "topic", "title", "notes")).lower()
    obj = " ".join(str(row.get(k) or "") for k in
                   ("object_type", "title", "physical_description", "topic")).lower()
    return any(a in geo for a in ANDEAN) and any(t in obj for t in TEXTILE)


def main():
    os.makedirs(ROOT, exist_ok=True)
    if KEY == "DEMO_KEY":
        print("AVISO: usando DEMO_KEY (30 peticiones/hora). Para el corpus completo,")
        print("       obten una clave gratuita en https://api.data.gov/signup/ y define SI_API_KEY.\n")

    seen, raw, rate_limited = {}, [], False
    for q in QUERIES:
        print("[q] %s" % q[:70], flush=True)
        start, got = 0, 0
        while True:
            d = search(q, start)
            if d == "RATE_LIMIT":
                rate_limited = True
                break
            if not d or "response" not in d:
                break
            resp = d["response"]
            total = resp.get("rowCount", 0)
            rows = resp.get("rows", [])
            if start == 0:
                print("      %d resultados declarados" % total, flush=True)
            if not rows:
                break
            for r in rows:
                if r.get("id") not in seen:
                    seen[r["id"]] = 1
                    raw.append(r)
            got += len(rows)
            start += ROWS
            if start >= min(total, 5000):
                break
            time.sleep(0.5)
        print("      %d recuperados" % got, flush=True)
        if rate_limited:
            print("      se detiene la recoleccion por limite de peticiones.")
            break

    with open(os.path.join(ROOT, "records.jsonl"), "w", encoding="utf-8") as f:
        for r in raw:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    flat = [flatten(r) for r in raw]
    rel = [r for r in flat if is_relevant(r)]
    with_img = [r for r in rel if r["media_url"]]
    cc0 = [r for r in with_img if (r["media_usage"] or "").upper() == "CC0"]

    csv_path = os.path.join(ROOT, "andean_textiles.csv")
    if rel:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rel[0].keys()))
            w.writeheader()
            w.writerows(rel)

    log = {
        "source": "Smithsonian Open Access API",
        "api_key_mode": "DEMO_KEY (limitada)" if KEY == "DEMO_KEY" else "clave propia",
        "rate_limited": rate_limited,
        "queries": QUERIES,
        "records_retrieved": len(raw),
        "andean_textiles": len(rel),
        "with_image": len(with_img),
        "cc0_with_image": len(cc0),
    }
    with open(os.path.join(ROOT, "harvest_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print("\nRESUMEN SMITHSONIAN")
    for k, v in log.items():
        if k != "queries":
            print("  %-22s %s" % (k, v))


if __name__ == "__main__":
    main()
