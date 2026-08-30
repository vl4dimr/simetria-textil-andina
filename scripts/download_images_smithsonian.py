# -*- coding: utf-8 -*-
"""
Descarga de las imagenes CC0 recuperables del Smithsonian.

En la practica esto significa Cooper Hewitt: el NMAI publica metadatos CC0 pero
no distribuye imagenes (ver data/README_corpus.md, seccion 2). Las URLs apuntan
al IDS delivery service, que admite el parametro `max` para fijar el lado mayor.

Salida: data/raw/smithsonian/images/  +  images_manifest.csv
"""
import csv
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "smithsonian")
SRC = os.path.join(ROOT, "andean_textiles.csv")
IMGDIR = os.path.join(ROOT, "images")
MANIFEST = os.path.join(ROOT, "images_manifest.csv")
UA = {"User-Agent": "andean-iconography-research/1.0 (academic)"}
MAX_SIDE = 4000  # el servicio devuelve la mayor derivada disponible por debajo de este valor


def with_max(url, px):
    parts = urllib.parse.urlsplit(url)
    qs = urllib.parse.parse_qs(parts.query)
    qs["max"] = [str(px)]
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(qs, doseq=True), parts.fragment))


def main():
    if not os.path.exists(SRC):
        sys.exit("Falta %s. Ejecuta antes harvest_smithsonian.py" % SRC)

    with open(SRC, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("media_url")]
    print("Piezas con imagen: %d" % len(rows), flush=True)
    if not rows:
        sys.exit("Ninguna pieza trae imagen. Es el resultado esperado si solo hay NMAI.")

    os.makedirs(IMGDIR, exist_ok=True)
    out = []
    for n, r in enumerate(rows, 1):
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in r["id"])[:80]
        path = os.path.join(IMGDIR, "si_%s.jpg" % safe)
        if not os.path.exists(path):
            try:
                req = urllib.request.Request(with_max(r["media_url"], MAX_SIDE), headers=UA)
                with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as fh:
                    fh.write(resp.read())
            except Exception as e:
                print("  fallo %s: %s" % (r["id"][:40], e), flush=True)
                continue
            time.sleep(0.3)
        out.append({
            "id": r["id"],
            "file": os.path.basename(path),
            "bytes": os.path.getsize(path),
            "title": r["title"],
            "unit_code": r["unit_code"],
            "culture": r["culture"],
            "place": r["place"],
            "object_type": r["object_type"],
            "date": r["date"],
            "license": r["media_usage"],
            "record_link": r["record_link"],
        })
        if n % 25 == 0:
            print("  [%d/%d]" % (n, len(rows)), flush=True)

    with open(MANIFEST, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    units = {}
    for r in out:
        units[r["unit_code"]] = units.get(r["unit_code"], 0) + 1
    print("\n  %d imagenes, %.0f MB" % (len(out), sum(r["bytes"] for r in out) / 1e6))
    print("  por unidad: %s" % units)
    print("  ->", MANIFEST)


if __name__ == "__main__":
    main()
