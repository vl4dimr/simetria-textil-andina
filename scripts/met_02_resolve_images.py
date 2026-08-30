# -*- coding: utf-8 -*-
"""
Recolector 1b — Resolucion de URLs de imagen del Met, en modo cortes.

El volcado CSV no incluye enlaces de imagen; solo la API los devuelve. La API
bloquea por IP ante rafagas concurrentes, asi que aqui se consulta de forma
estrictamente secuencial, con pausa configurable y retroceso exponencial ante
403/429. Solo se consultan los objetos del subconjunto andino, no los 500.000
del volcado.

Uso:
    python met_02_resolve_images.py            # resuelve URLs
    python met_02_resolve_images.py --download # ademas descarga las imagenes

Salidas (data/raw/met/):
  images_index.csv   objectID, URLs de imagen, dominio publico, fichero local
  images/            ficheros descargados (solo con --download)
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://collectionapi.metmuseum.org/public/collection/v1/objects"
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "met")
SRC = os.path.join(ROOT, "andean_textiles.csv")
INDEX = os.path.join(ROOT, "images_index.csv")
IMGDIR = os.path.join(ROOT, "images")
UA = {"User-Agent": "andean-iconography-research/1.0 (academic; low-rate sequential)"}

DELAY = 1.2       # segundos entre peticiones: por debajo de esto el Met bloquea
MAX_BACKOFF = 300  # 5 minutos de espera maxima ante bloqueo sostenido


def fetch(url, tries=6):
    wait = 5
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503):
                print("      HTTP %d, esperando %ds (intento %d/%d)" % (e.code, wait, i + 1, tries), flush=True)
                time.sleep(wait)
                wait = min(wait * 2, MAX_BACKOFF)
                continue
            return None
        except Exception:
            time.sleep(wait)
            wait = min(wait * 2, MAX_BACKOFF)
    return None


def safe_url(url):
    """Codifica el path: algunas rutas del Met traen espacios sin escapar
    ('.../29.146.14 -15.jpg') y urllib los rechaza como caracter de control."""
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(
        (p.scheme, p.netloc, urllib.parse.quote(p.path), p.query, p.fragment))


def download_one(url, path, tries=3):
    """Descarga con reintentos. Los fallos de DNS son transitorios y frecuentes
    en tandas largas; un 404 es definitivo y no se reintenta."""
    for i in range(tries):
        try:
            req = urllib.request.Request(safe_url(url), headers=UA)
            with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as out:
                out.write(resp.read())
            return True
        except urllib.error.HTTPError as e:
            print("  fallo %s: HTTP %d (definitivo)" % (os.path.basename(path), e.code), flush=True)
            return False
        except Exception as e:
            if i == tries - 1:
                print("  fallo %s: %s" % (os.path.basename(path), e), flush=True)
                return False
            time.sleep(3 * (i + 1))
    return False


def load_done():
    done = {}
    if os.path.exists(INDEX):
        with open(INDEX, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                done[r["objectID"]] = r
    return done


def main():
    do_download = "--download" in sys.argv
    if not os.path.exists(SRC):
        sys.exit("Falta %s. Ejecuta antes met_01_download_dump.py" % SRC)

    with open(SRC, encoding="utf-8-sig", newline="") as f:
        targets = [r for r in csv.DictReader(f)]
    print("Subconjunto andino: %d objetos" % len(targets), flush=True)

    done = load_done()
    pending = [r for r in targets if r["Object ID"] not in done]
    print("Ya resueltos: %d. Pendientes: %d" % (len(done), len(pending)), flush=True)
    print("Ritmo: 1 peticion cada %.1f s -> ~%.0f min\n" % (DELAY, len(pending) * DELAY / 60), flush=True)

    fields = ["objectID", "title", "culture", "objectDate", "classification",
              "isPublicDomain", "primaryImage", "primaryImageSmall", "n_additional", "objectURL"]
    new = not os.path.exists(INDEX)
    with open(INDEX, "a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        for n, r in enumerate(pending, 1):
            oid = r["Object ID"]
            o = fetch("%s/%s" % (BASE, oid))
            time.sleep(DELAY)
            if not o:
                print("  [%d/%d] %s sin respuesta" % (n, len(pending), oid), flush=True)
                continue
            w.writerow({
                "objectID": o.get("objectID"),
                "title": o.get("title"),
                "culture": o.get("culture"),
                "objectDate": o.get("objectDate"),
                "classification": o.get("classification"),
                "isPublicDomain": o.get("isPublicDomain"),
                "primaryImage": o.get("primaryImage"),
                "primaryImageSmall": o.get("primaryImageSmall"),
                "n_additional": len(o.get("additionalImages") or []),
                "objectURL": o.get("objectURL"),
            })
            if n % 25 == 0:
                f.flush()
                print("  [%d/%d] resueltos" % (n, len(pending)), flush=True)

    if do_download:
        os.makedirs(IMGDIR, exist_ok=True)
        rows = load_done()
        pool = [r for r in rows.values()
                if r.get("primaryImage") and str(r.get("isPublicDomain")).lower() == "true"]
        print("\nDescargando %d imagenes en dominio publico..." % len(pool), flush=True)
        missing = []
        for n, r in enumerate(pool, 1):
            ext = os.path.splitext(r["primaryImage"])[1] or ".jpg"
            path = os.path.join(IMGDIR, "met_%s%s" % (r["objectID"], ext))
            if os.path.exists(path) and os.path.getsize(path) > 0:
                continue
            if not download_one(r["primaryImage"], path):
                missing.append(r["objectID"])
            time.sleep(0.5)
            if n % 25 == 0:
                print("  [%d/%d] descargadas" % (n, len(pool)), flush=True)
        if missing:
            print("\n  %d imagenes no recuperadas: %s" % (len(missing), ", ".join(missing[:20])), flush=True)
            print("  Vuelve a ejecutar con --download para reintentarlas.", flush=True)

    print("\n  ->", INDEX)


if __name__ == "__main__":
    main()
