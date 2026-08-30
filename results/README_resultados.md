# Resultados — Simetría en iconografía textil andina

Estado: 10 de agosto de 2026. Corpus: 866 imágenes CC0 (Met 592, Cooper Hewitt 141, Cleveland 133).

## 1. Validación del detector

Antes de aplicarlo al corpus, el detector se probó sobre 84 patrones sintéticos construidos por los
generadores de cada uno de los siete grupos de friso y degradados con ruido, desenfoque y cizalla.
Sobre fotografía real no existe etiqueta de simetría contra la que contrastar, así que esta es la única
evidencia de que el método mide lo que dice medir.

**Exactitud global: 92,9 % (78/84).** Por grupo: p1 100 %, p11m 100 %, p2mg 100 %, p2mm 100 %,
p2 92 %, p11g 83 %, p1m1 75 %.

Cuatro correcciones fueron necesarias para llegar ahí, y las cuatro son reportables porque cada una
falla en silencio:

| Problema | Efecto | Corrección |
|---|---|---|
| El eje de simetría no pasa por el centro del encuadre | La simetría solo se detecta si la foto la centra por casualidad | Maximizar la correlación sobre traslaciones |
| Reflexión y deslizamiento puntúan igual | p11g y p2mg indistinguibles de p11m y p2mm | Medir la fase del desplazamiento óptimo respecto al periodo |
| La red se detecta a media celda en patrones con rotación | El periodo sale a la mitad y la fase queda mal | Exigir picos ≥ 0,8 del máximo de la autocorrelación |
| Cizalla de 0,03 (menos de 2°) | Hunde una reflexión exacta de 1,00 a 0,50 | Rectificar por el vector de red antes de medir |

La última fue la más costosa: por sí sola subió el acierto del 28,6 % al 85,7 %. Ruido y desenfoque, en
cambio, no afectan (0,99 y 1,00 respectivamente).

El umbral de decisión —fracción de la correlación bajo traslación que una simetría debe alcanzar— se
fijó en 0,70 por barrido, con óptimo plano entre 0,65 y 0,70.

## 2. El artefacto de trama, y por qué importa

En la primera pasada, el 29 % de las piezas con grupo asignado tenían periodos de 4 a 15 píxeles. Eso
no es iconografía: es la retícula de hilos.

Un tejido tiene dos periodicidades superpuestas. La trama es mucho más regular que el diseño, así que
domina la autocorrelación y el detector se queda con ella. El sesgo no es neutro: un ligamento tafetán
es una retícula con reflexión en ambos ejes, es decir p2mm, justo el grupo que sostiene la conclusión.

Excluyendo la escala de la trama (radio mínimo del 3 % del lado mayor), las piezas con periodo por
debajo de 15 px caen de 71 a 15 y la mediana de periodo sube de 39 a 45 px.

**El artefacto estaba enmascarando la señal, no creándola.** Al eliminarlo, la asociación se refuerza:

| Contraste | Con trama | Sin trama |
|---|---|---|
| Cultura × friso | p = 0,046 · V = 0,29 | **p = 0,0004 · V = 0,36** |
| Horizonte × friso | p = 0,019 · V = 0,29 | **p = 0,0015 · V = 0,33** |

Y, decisivo para la credibilidad: con la corrección, el resultado **sobrevive** al excluir las piezas de
atribución dudosa (cultura × friso p = 0,0007), mientras que antes se derrumbaba a p = 0,099.

Ambas versiones se conservan (`symmetry_summary_weave_included.json`) porque la comparación es en sí
un resultado metodológico.

## 3. Resultado principal

Prueba de permutación sobre chi-cuadrado, 10.000 remuestreos. Se usa permutación y no la chi-cuadrado
clásica porque con seis grupos observados y culturas de veinte piezas muchas casillas quedan por debajo
de cinco casos, y la aproximación asintótica deja de ser válida.

### Cultura × grupo de friso (n = 96, sin atribución dudosa, p = 0,0007, V = 0,363)

| Cultura | p1 | p11m | p1m1 | p2 | p2mg | p2mm | n |
|---|---|---|---|---|---|---|---|
| Nasca | 5 % | — | 5 % | — | 14 % | **76 %** | 21 |
| Wari | — | 7 % | 7 % | 7 % | **54 %** | 25 % | 28 |
| Chimú | 21 % | 12 % | 12 % | 4 % | 4 % | **46 %** | 24 |
| Ica | 9 % | 4 % | 22 % | — | **35 %** | 30 % | 23 |

### Lectura

**Nasca y Wari se oponen con nitidez.** Nasca concentra el 76 % en p2mm, el grupo de simetría máxima:
reflexión en ambos ejes más rotación. Wari invierte el reparto y concentra el 54 % en p2mg, donde la
reflexión de eje paralelo se sustituye por un deslizamiento —reflejo más media celda de traslación—.

Esa preferencia Wari por el deslizamiento concuerda con lo que se sabe del diseño de sus túnicas de
tapiz, construidas por repetición desplazada de módulos en vez de por repetición especular. El método
lo recupera sin haber recibido esa información.

**Chimú es el más diverso**: reparte entre cinco grupos y es la única cultura con presencia apreciable
de p1 (21 %), el grupo sin más simetría que la traslación.

**Por horizonte** (n = 127, p = 0,0003, V = 0,351) el patrón se ordena cronológicamente: Intermedio
Temprano 80 % p2mm, Horizonte Medio 48 % p2mg, Intermedio Tardío el más repartido con p2mm al 46 %.

## 4. Limitaciones

**Cobertura del 28 %.** Solo 242 de 866 piezas reciben grupo; 330 no presentan periodicidad detectable
y 294 la presentan demasiado débil. Parte es real —buena parte de la iconografía andina es figurativa o
de composición única, y forzar una etiqueta de friso sobre un diseño no periódico produciría
exactamente el tipo de resultado que no se sostiene—. Parte es limitación del método sobre piezas
fragmentarias o mal encuadradas.

**Periodicidad imperfecta.** La mediana de correlación bajo traslación en los casos válidos es 0,59:
periodicidad genuina pero degradada por desgaste, deformación del tejido y escorzo fotográfico.

**Sesgo residual hacia p2mm.** La validación muestra que p1m1 se confunde con p2mm en 3 de 12 casos.
El predominio de p2mm es por tanto una cota superior, aunque la oposición Nasca–Wari no depende de él:
descansa en p2mg, cuya recuperación fue del 100 % en validación.

**Muestra pequeña por clase.** Entre 21 y 28 piezas por cultura. Cuatro culturas superan el umbral de
20; Paracas, Inca, Moche y Chancay quedan fuera del contraste por debajo de él.

**Sesgo de colección.** Tres museos estadounidenses. Lo que llegó a esas colecciones no es una muestra
aleatoria de la producción textil andina, sino el resultado de un siglo de comercio de antigüedades con
preferencias propias, probablemente sesgadas hacia piezas vistosas y bien conservadas.

## 5. Ficheros

- `symmetry.csv` — una fila por imagen: grupo, periodos, puntuaciones por operación, ángulo de
  rectificación, estado.
- `symmetry_summary.json` — reparto por cultura y horizonte.
- `symmetry_summary_weave_included.json` — versión previa, con el artefacto de trama.
- `stats_symmetry.json` — tablas de contingencia y pruebas de permutación.
- `validation_frieze.csv`, `validation_summary.json` — validación sintética.
