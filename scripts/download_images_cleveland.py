# -*- coding: utf-8 -*-
"""
Descarga de imagenes CC0 del Cleveland Museum of Art.

Cleveland publica dos derivadas por pieza: `web` (unos 800 px de lado mayor) y
`print` (resolucion de impresion, varias veces mayor). Para medir simetrias y
grupos de friso interesa la segunda; se cae a `web` cuando `print` no existe.

Uso:
    python download_images_cleveland.py            # solo soporte textil
    python download_images_cleveland.py --all      # todas las piezas andinas

Salida: data/raw/cleveland/images/  +  images_manifest.csv
"""
import csv
import os
import sys
import time
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "cleveland")
SRC = os.path.join(ROOT, "andean_textiles.csv")
IMGDIR = os.path.join(ROOT, "images")
MANIFEST = os.path.join(ROOT, "images_manifest.csv")
UA = {"User-Agent": "andean-iconography-research/1.0 (academic)"}

# Tipos que corresponden a soporte textil propiamente dicho. El filtro lexico
# del recolector deja pasar ceramica y metal porque terminos como "band",
# "panel" o "fragment" aparecen en sus titulos.
TEXTILE_TYPES = {"Textile", "Embroidery", "Tapestry", "Garment"}


def main():
    take_all = "--all" in sys.argv
    if not os.path.exists(SRC):
        sys.exit("Falta %s. Ejecuta antes harvest_cleveland.py" % SRC)

    with open(SRC, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f)]
    if not take_all:
        rows = [r for r in rows if r["type"] in TEXTILE_TYPES]
    rows = [r for r in rows if r.get("image_print") or r.get("image_web")]

    os.makedirs(IMGDIR, exist_ok=True)
    print("A descargar: %d piezas (%s)" % (
        len(rows), "todas" if take_all else "solo soporte textil"), flush=True)

    out = []
    for n, r in enumerate(rows, 1):
        url = r.get("image_print") or r.get("image_web")
        which = "print" if r.get("image_print") else "web"
        path = os.path.join(IMGDIR, "cma_%s.jpg" % r["id"])
        if not os.path.exists(path):
            try:
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as fh:
                    fh.write(resp.read())
            except Exception as e:
                print("  fallo %s: %s" % (r["id"], e), flush=True)
                continue
            time.sleep(0.3)
        out.append({
            "id": r["id"],
            "file": os.path.basename(path),
            "derivative": which,
            "bytes": os.path.getsize(path),
            "title": r["title"],
            "culture": r["culture"],
            "type": r["type"],
            "creation_date": r["creation_date"],
            "license": r["share_license_status"],
            "url": r["url"],
        })
        if n % 25 == 0:
            print("  [%d/%d]" % (n, len(rows)), flush=True)

    with open(MANIFEST, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["id"])
        w.writeheader()
        w.writerows(out)

    total = sum(r["bytes"] for r in out)
    print("\n  %d imagenes, %.0f MB" % (len(out), total / 1e6))
    print("  ->", MANIFEST)


if __name__ == "__main__":
    main()
