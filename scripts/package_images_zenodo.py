# -*- coding: utf-8 -*-
"""
Empaqueta las imagenes del corpus para su deposito en Zenodo.

Las imagenes no caben en GitHub —2,1 GB frente a un limite de 100 MB por fichero
y una recomendacion de no pasar de 1 GB por repositorio— asi que se depositan
como registro de datos independiente. Subir 1 193 ficheros sueltos por navegador
no es viable, de modo que se agrupan en un archivo por coleccion.

Cada archivo lleva dentro el manifiesto de las piezas que contiene, para que el
fichero sea interpretable por si solo aunque se descargue separado del resto.

Salida: zenodo_images/
  met_images.zip, cleveland_images.zip, cooperhewitt_images.zip
  manifest.csv        una fila por imagen, con procedencia y licencia
  README.md           texto listo para la descripcion del registro
"""
import csv
import hashlib
import os
import sys
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "zenodo_images")

SOURCES = [
    ("met", "met_images.zip", "The Metropolitan Museum of Art",
     os.path.join(BASE, "data", "raw", "met", "images")),
    ("cleveland", "cleveland_images.zip", "Cleveland Museum of Art",
     os.path.join(BASE, "data", "raw", "cleveland", "images")),
    ("smithsonian/CHNDM", "cooperhewitt_images.zip", "Cooper Hewitt, Smithsonian Design Museum",
     os.path.join(BASE, "data", "raw", "smithsonian", "images")),
]


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def load_corpus():
    """Metadatos por fichero, tomados del corpus ya unificado."""
    idx = {}
    path = os.path.join(BASE, "data", "corpus.csv")
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            idx[os.path.basename(r["file"])] = r
    return idx


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = load_corpus()
    rows, totals = [], {}

    for source, zipname, museum, folder in SOURCES:
        if not os.path.isdir(folder):
            print("  aviso: falta %s" % folder, flush=True)
            continue
        # Solo entran ficheros que estan en el corpus. La descarga del
        # Smithsonian arrastro un especimen de botanica (Plumbago coerulea) que
        # el filtro de unidades excluyo del corpus pero quedo en la carpeta;
        # empaquetarlo lo colaria en un deposito de textiles andinos, y ademas
        # atribuido al museo equivocado, porque la carpeta no distingue unidades.
        files = sorted(f for f in os.listdir(folder)
                       if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff"))
                       and f in meta)
        omitidos = sum(1 for f in os.listdir(folder)
                       if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff"))
                       and f not in meta)
        if omitidos:
            print("  %d fichero(s) omitido(s): no figuran en el corpus" % omitidos, flush=True)
        zpath = os.path.join(OUT, zipname)
        print("[%s] %d imágenes -> %s" % (museum, len(files), zipname), flush=True)

        # ZIP_STORED: son JPEG, ya comprimidos. Volver a comprimirlos gastaria
        # minutos de CPU para ahorrar decimas de porcentaje.
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as z:
            for n, fn in enumerate(files, 1):
                full = os.path.join(folder, fn)
                z.write(full, arcname="%s/%s" % (zipname[:-4], fn))
                m = meta.get(fn, {})
                rows.append({
                    "file": fn,
                    "archive": zipname,
                    "museum": museum,
                    "source_id": m.get("source_id", ""),
                    "title": m.get("title", ""),
                    "culture": m.get("culture", ""),
                    "horizon": m.get("horizon", ""),
                    "region": m.get("region", ""),
                    "object_type": m.get("object_type", ""),
                    "attribution_uncertain": m.get("attribution_uncertain", ""),
                    "width": m.get("width", ""),
                    "height": m.get("height", ""),
                    "bytes": os.path.getsize(full),
                    "license": "CC0 1.0",
                    "record_url": m.get("url", ""),
                })
                if n % 200 == 0:
                    print("    %d/%d" % (n, len(files)), flush=True)
        totals[zipname] = os.path.getsize(zpath)
        print("    %.0f MB" % (totals[zipname] / 1e6), flush=True)

    man = os.path.join(OUT, "manifest.csv")
    with open(man, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # El manifiesto entra tambien en cada archivo, filtrado a sus propias piezas.
    for _, zipname, _, _ in SOURCES:
        sub = [r for r in rows if r["archive"] == zipname]
        if not sub:
            continue
        tmp = os.path.join(OUT, "_m.csv")
        with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(sub[0].keys()))
            w.writeheader()
            w.writerows(sub)
        with zipfile.ZipFile(os.path.join(OUT, zipname), "a", zipfile.ZIP_STORED, allowZip64=True) as z:
            z.write(tmp, arcname="%s/manifest.csv" % zipname[:-4])
        os.remove(tmp)

    by_museum = {}
    for r in rows:
        by_museum[r["museum"]] = by_museum.get(r["museum"], 0) + 1

    readme = os.path.join(OUT, "README.md")
    with open(readme, "w", encoding="utf-8") as f:
        f.write("""# Corpus de imágenes de textiles andinos de colecciones de acceso abierto

%d imágenes de piezas textiles de procedencia andina, reunidas desde tres colecciones museísticas
que publican sus fondos bajo licencia **CC0 1.0**.

## Procedencia

| Museo | Imágenes |
|---|---|
%s

Todas las imágenes proceden de los programas de acceso abierto de sus respectivas instituciones y se
redistribuyen bajo CC0, la licencia con la que las publican. La atribución a la institución de origen
figura en `manifest.csv` y no es una exigencia legal de CC0, sino una práctica que hace verificable el
corpus.

## Contenido

- `met_images.zip`, `cleveland_images.zip`, `cooperhewitt_images.zip` — las imágenes agrupadas por
  colección. Cada archivo incluye su propio `manifest.csv`, de modo que resulta interpretable aunque se
  descargue por separado.
- `manifest.csv` — una fila por imagen: fichero, museo, identificador en la colección de origen,
  título, cultura y horizonte cronológico asignados, región, tipo de objeto, dimensiones en píxeles y
  enlace al registro del museo.

La columna `attribution_uncertain` marca las piezas cuya atribución cultural el propio museo señala con
interrogante o con las fórmulas «probably» o «possibly». Conviene tratarlas aparte en cualquier análisis
que dependa de la etiqueta cultural.

## Por qué existe este depósito

El corpus se construye consultando las API de los museos, y esas interfaces cambian. Durante la
elaboración de este trabajo la API del Metropolitan bloqueó la dirección IP tras una ráfaga de
peticiones concurrentes, y el Smithsonian modificó lo que devuelve según la consulta. Un corpus que
depende de que varias API sigan respondiendo igual dentro de unos años no es reproducible; por eso las
imágenes se archivan aquí y no solo el código que las recolecta.

## Relación con el resto del material

El código que recolecta, unifica y analiza este corpus se deposita aparte, junto con los datos
derivados: corpus unificado, asignaciones de grupo de simetría y contrastes estadísticos.

## Cómo citar

Cítese junto al artículo asociado y al depósito de código.
""" % (len(rows), "\n".join("| %s | %d |" % (k, v) for k, v in sorted(by_museum.items()))))

    total = sum(totals.values())
    print("\nRESUMEN")
    print("  imágenes    %d" % len(rows))
    for k, v in totals.items():
        print("  %-24s %6.0f MB" % (k, v / 1e6))
    print("  total       %.2f GB" % (total / 1e9))
    print("\n  ->", OUT)


if __name__ == "__main__":
    main()
