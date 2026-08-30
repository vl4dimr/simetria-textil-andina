# Corpus — Iconografía textil andina en colecciones digitalizadas abiertas

Documentación de procedencia, licencias y criterios de filtrado. Estado: 9 de agosto de 2026.

## Fuentes

| Fuente | Acceso | Licencia de metadatos | Licencia de imágenes | Estado |
|---|---|---|---|---|
| The Met — volcado Open Access | Sin clave | CC0 | CC0 solo si `Is Public Domain = True` | Completo |
| The Met — Collection API | Sin clave | CC0 | idem | Resolviendo URLs |
| Smithsonian Open Access | Requiere clave de api.data.gov | CC0 | **Casi inexistente en NMAI** | Completo; ver §2 |
| Cleveland Museum of Art | Sin clave | CC0 | CC0 | Completo |
| Zenodo | Sin clave | Por registro | Por registro (mayoría CC-BY 4.0) | Completo |

## 1. The Metropolitan Museum of Art

**Ruta seguida.** La API del Met bloquea por IP ante peticiones concurrentes: una ráfaga con 12 hilos
produjo HTTP 403 en todas las peticiones posteriores, incluidas las secuenciales, durante varios
minutos. Por eso los metadatos se obtienen del volcado oficial en CSV (318 MB, 484.956 filas) y la API
se reserva para resolver enlaces de imagen del subconjunto ya filtrado, a un ritmo de una petición cada
1,2 segundos con retroceso exponencial.

**Filtro.** Un objeto entra al corpus si cumple las dos condiciones:

1. *Procedencia andina* — algún término andino en `Culture`, `Country`, `Region`, `Subregion`, `City`,
   `Locale`, `Excavation` o `Locus`. Los países casan por prefijo (`peru` captura «Peruvian»); los
   nombres de cultura exigen palabra completa con sufijo adjetival opcional (`\b(nasca|wari|ica|…)(n|an|ian|s|es)?\b`).
2. *Objeto textil* — algún término textil en `Object Name`, `Title`, `Medium` o `Classification`.

**Advertencia metodológica registrada.** La primera versión del filtro usaba coincidencia por
subcadena y devolvía 10.309 piezas. El fallo: `ica`, por la cultura Ica de la costa sur peruana, casa
dentro de «Amer**ica**n», e incorporó 7.691 prendas estadounidenses del Costume Institute. Con límites
de palabra el corpus baja a **1.158 piezas**, de las cuales 1.120 pertenecen al departamento correcto
(Arts of Africa, Oceania, and the Americas). Este contraste conviene reportarlo en el artículo: es un
ejemplo concreto de cómo un filtro léxico ingenuo infla un corpus en un factor de 9.

**Resultado.** 1.158 objetos; 910 en dominio público; culturas dominantes Peruvian (177), Aymara (138),
Wari (103), Nasca (96), Paracas (80), Chimú (79), Ica (74), Chancay (41), Inca (28), Moche (22).

**Ficheros.** `raw/met/MetObjects.csv`, `raw/met/andean_textiles.csv`, `raw/met/images_index.csv`,
`raw/met/harvest_log.json`.

## 2. Smithsonian Open Access

Ejecutado con clave propia, sin limitación de cuota: 7.743 registros recuperados, 3.740 pertinentes.

**Resultado central, y negativo.** El NMAI —la colección andina más grande de las consultadas— publica
sus metadatos como CC0 pero **no distribuye las imágenes**. La comprobación fue en tres pasos:

1. De 6.390 registros NMAI recuperados, solo **7** traían bloque `online_media`.
2. El campo indexado `online_media_type` marca «Images» en los 7.743 registros, pero 5.921 marcan
   además «Catalog cards»: lo digitalizado es la ficha de catálogo, no la pieza.
3. `unit_code:NMAI AND media_usage:CC0` devuelve **180 registros en toda la unidad**. Consultado el
   endpoint `/content/{id}` para una túnica peruana concreta, la respuesta no incluye `online_media`;
   `metadata_usage` sí declara CC0.

Es decir: metadatos abiertos, imágenes cerradas. La distinción no aparece en la documentación de la API
y es fácil de pasar por alto al planificar un corpus. Conviene reportarla en el artículo.

**Lo aprovechable.** Cooper Hewitt (`CHNDM`) sí entrega imagen: 152 textiles peruanos con media CC0.

**Ficheros.** `raw/smithsonian/records.jsonl`, `raw/smithsonian/andean_textiles.csv`,
`raw/smithsonian/harvest_log.json`.

## 2b. Cleveland Museum of Art

Añadido al plan como respuesta al vacío de imágenes del NMAI. API abierta, sin clave, con filtros
`has_image=1` y `cc0=1` aplicados en la propia petición.

**Resultado.** 374 registros recuperados, **215 pertinentes, todos con imagen CC0**. Por tipo: Textile
118, Ceramic 29, Metalwork 13, Jewelry 12, Sculpture 7, Embroidery 7, Garment 4, Tapestry 4.
Restringido a soporte textil estricto (Textile + Embroidery + Tapestry + Garment): **133 piezas**.

**Ventaja de esta fuente.** La procedencia viene estructurada y detallada —«Peru, South Coast, Ica
Valley, Chavín style»— lo que permite derivar cultura, región y periodo sin analizar texto libre. Es la
fuente con mejor señal por pieza de las cuatro.

**Ficheros.** `raw/cleveland/records.jsonl`, `raw/cleveland/andean_textiles.csv`,
`raw/cleveland/harvest_log.json`.

## 3. Zenodo

**Limitación de la API.** El parámetro `size` está topado en 25 para peticiones anónimas; valores
mayores devuelven HTTP 400. Se pagina en bloques de 25, hasta 8 páginas por consulta y tipo.

**Filtro.** Búsqueda dirigida a `title:` y `keywords:` (no a texto completo: `q=andean textile` sin
restricción devuelve 18.921 resultados casi todos ajenos), seguida de un filtro de pertinencia sobre
título, palabras clave, descripción y autoría.

**Resultado.** 350 registros recuperados, 138 pertinentes: 34 datasets, 22 imágenes, 78 publicaciones,
4 software. 136 en acceso abierto, 93 bajo CC-BY 4.0 y 10 bajo CC0.

**Ruido conocido, sin depurar todavía.** Los epítetos taxonómicos arrastran falsos positivos: especies
como *Brachymeria mochica* o esponjas descritas en Perú entran por «mochica» y «peru». Afecta sobre
todo al tipo `image`. Requiere una pasada de exclusión por vocabulario biológico antes de usar el
subconjunto.

**Piezas de mayor valor.**

- *The Open Khipu Repository* (79,8 MB) — base de khipus digitalizados. Complementa la iconografía
  textil con un sistema de registro andino sobre fibra.
- *XRF maps of Paracas textiles and threads* (874,8 MB) — mapas de fluorescencia de rayos X sobre
  textiles Paracas; da acceso a la dimensión material, no solo a la visual.
- Modelos 3D de cerámica Moche, Nasca, Chancay y Wari — iconografía comparable, soporte distinto.
  Útiles para contrastar si los motivos geométricos cruzan de soporte.

**Ficheros.** `raw/zenodo/records.jsonl`, `raw/zenodo/candidates.csv`, `raw/zenodo/harvest_log.json`.

## Corpus unificado

`corpus.csv` — 1.193 imágenes, 2.127 MB. Met 908, Cooper Hewitt 152, Cleveland 133.
Resolución: 161 por debajo de 1 Mpx, 541 entre 1 y 5, 491 por encima de 5. Mediana 3,61 Mpx.

### Distribución por cultura

| Clase | n | | Clase | n |
|---|---|---|---|---|
| no determinada | 443 | | inca | 32 |
| wari | 120 | | salinar | 25 |
| paracas | 112 | | tiwanaku | 19 |
| chimú | 111 | | colonial | 17 |
| nasca | 110 | | sicán | 14 |
| ica | 80 | | chuquibamba | 6 |
| chancay | 51 | | recuay | 5 |
| moche | 38 | | chavín, pachacamac, vicús | 4, 4, 2 |

**Seis clases superan los 50 ejemplares** (wari, paracas, chimú, nasca, ica, chancay) y suman 584
imágenes. Por debajo de 20 ejemplares hay siete clases que no sostienen una evaluación por validación
cruzada estratificada.

### Distribución por horizonte

Intermedio Tardío 262 · Intermedio Temprano 180 · Horizonte Medio 143 · Horizonte Temprano 116 ·
Horizonte Tardío 32 · Colonial 17 · no determinado 443.

### Las 443 sin cultura no son basura

Casi todas declaran procedencia peruana sin precisar cultura: «Peruvian» 158, «Peru» 138, «Peru;
central coast (?)» 50, «Peru; north coast (?)» 23. Sirven para el análisis geométrico no supervisado
—que no necesita etiqueta cultural— y como conjunto de prueba para atribución asistida.

### Corpus de análisis: `corpus_textile.csv`

`filter_corpus.py` aplica dos exclusiones sobre las 1.193: **269 por soporte** (husos, agujas y ovillos
—`Textiles-Implements` 109—, ornamentos de metal 96, útiles de madera 8, figuras 3D 8, cuentas 7) y
**58 por resolución** (menos de 0,3 Mpx, insuficientes para medir un grupo de friso). Quedan
**866 imágenes**: Met 592, Cooper Hewitt 141, Cleveland 133.

El tipo de objeto no viene normalizado entre museos —el Met usa `Textiles-Woven`, Cleveland `Textile` y
Cooper Hewitt encadena varios valores (`Coca bag | Textiles`)—, así que la regla no es una lista blanca
literal, que descartaba piezas textiles evidentes, sino: excluir por marcador de soporte o de utillaje
y, de lo restante, conservar lo que nombre un textil.

**Clases viables (≥50 ejemplares):** wari 109, paracas 88, chimú 76, nasca 75, ica 72 — **420 imágenes**.
Chancay cae por debajo del umbral tras la depuración.

**Por horizonte:** Intermedio Tardío 216, Horizonte Medio 129, Intermedio Temprano 98, Horizonte Temprano
91, Horizonte Tardío 29, Colonial 17, no determinado 286. Cuatro clases superan las 90 imágenes.

**Sin etiqueta cultural:** 286, disponibles para el análisis geométrico no supervisado.

### Atribución dudosa

287 piezas llevan interrogante, «probably» o «possibly» en la ficha del museo, marcadas en
`attribution_uncertain`. De ellas 200 caen ya en «no determinada»; las 87 restantes afectan sobre todo a
salinar (25), colonial (12), tiwanaku (9), paracas (9) y chimú (8). Conviene un análisis de sensibilidad
con y sin ellas: en salinar son el 100 % de la clase.

## Reproducción

```bash
python scripts/met_01_download_dump.py       # volcado CSV + filtro
python scripts/met_02_resolve_images.py      # URLs de imagen (añade --download para bajarlas)
python scripts/harvest_zenodo.py             # Zenodo
set SI_API_KEY=...                           # clave de api.data.gov
python scripts/harvest_smithsonian.py        # Smithsonian
```

Los recolectores son reanudables: `met_01` reanuda la descarga por rangos de bytes y `met_02` relee
`images_index.csv` para no repetir peticiones ya resueltas.

## Pendiente

1. Reejecutar Smithsonian con clave propia.
2. Depurar el ruido taxonómico de Zenodo.
3. Descargar las imágenes en dominio público del Met y verificar resolución mínima utilizable.
4. Unificar las tres fuentes en un esquema común y decidir la partición por cultura y periodo.
5. Fijar el criterio de exclusión para piezas sin cultura declarada (177 «Peruvian» y 54 «Peru; central
   coast (?)» llevan interrogante en la propia ficha del museo).
