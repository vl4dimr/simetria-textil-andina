# Simetría computacional en iconografía textil andina

Código y datos derivados del análisis de grupos de simetría sobre un corpus de **866 textiles andinos**
reunido a partir de tres colecciones museísticas de acceso abierto, todas bajo licencia CC0.

Material asociado al artículo *Simetría computacional en iconografía textil andina: análisis de grupos
de friso en colecciones digitalizadas de acceso abierto*.

## Qué contiene este repositorio

| Ruta | Contenido |
|---|---|
| `scripts/` | Recolectores por fuente, detector de simetría, validación, análisis y figuras |
| `data/corpus.csv` | Corpus unificado, una fila por imagen, con procedencia normalizada |
| `data/corpus_textile.csv` | Subconjunto de análisis: 866 piezas de soporte textil |
| `data/README_corpus.md` | Procedencia, licencias y criterios de filtrado por fuente |
| `results/symmetry.csv` | Asignación de grupo y descriptores por pieza |
| `results/stats_symmetry.json` | Tablas de contingencia y pruebas de permutación |
| `results/validation_*` | Validación sintética del detector |
| `results/figuras/` | Figuras del artículo |
| `results/README_resultados.md` | Resultados, con las limitaciones declaradas |

**No incluye las imágenes.** Son 2,1 GB, muy por encima de lo razonable para GitHub, y se depositan
como registro de datos independiente en Zenodo. Tampoco incluye `MetObjects.csv`, el volcado Open
Access del Met, que pesa 303 MB y supera el límite de 100 MB por fichero de GitHub; se descarga con
`scripts/met_01_download_dump.py`.

## Reproducir el análisis

Requiere Python 3.11 o superior con `numpy`, `scipy`, `matplotlib`, `pandas`, `Pillow` y `python-docx`.

```bash
python scripts/met_01_download_dump.py       # volcado del Met y filtrado andino
python scripts/met_02_resolve_images.py --download
python scripts/harvest_cleveland.py
python scripts/harvest_smithsonian.py        # requiere SI_API_KEY de api.data.gov
python scripts/harvest_zenodo.py

python scripts/build_corpus.py               # unificación y normalización de procedencia
python scripts/filter_corpus.py              # filtrado por soporte y resolución

python scripts/validate_symmetry.py          # validación sintética del detector
python scripts/analyze_corpus_symmetry.py    # asignación de grupo sobre el corpus
python scripts/stats_symmetry.py             # contrastes por permutación
python scripts/make_figures.py               # figuras
```

Los recolectores son reanudables: `met_01` reanuda la descarga por rangos de bytes y `met_02` relee su
índice para no repetir peticiones ya resueltas.

## Advertencia sobre las interfaces de los museos

El corpus se reconstruye consultando las API de los museos, y esas interfaces cambian. Durante este
trabajo, la API del Met bloqueó la dirección IP tras una ráfaga de peticiones concurrentes, y el
Smithsonian modificó lo que devuelve según la consulta. Por eso las imágenes se depositan también en
Zenodo: un corpus que depende de que varias API sigan respondiendo igual dentro de unos años no es
reproducible.

## Licencias

- **Código** (`scripts/`): MIT, véase `LICENSE`.
- **Datos derivados** (`data/`, `results/`): CC BY 4.0.
- **Imágenes del corpus**: CC0, procedentes de The Metropolitan Museum of Art, Cooper Hewitt
  (Smithsonian) y Cleveland Museum of Art. No se redistribuyen aquí; véase el registro de datos.

## Cómo citar

Véase `CITATION.cff`. Una vez publicado el artículo, cítese este junto al depósito.
