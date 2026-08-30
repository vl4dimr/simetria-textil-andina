# -*- coding: utf-8 -*-
"""
Nucleo de analisis de simetria para patrones textiles.

Sigue el planteamiento clasico de Liu, Collins y Tsin (2004): detectar la red de
traslacion por autocorrelacion y despues probar cada operacion de simetria
midiendo cuanto se parece la imagen a su propia transformada. Lo que aqui se
anade es un umbral empirico por imagen en vez de una constante global.

El umbral importa mas de lo que parece. Una fotografia de museo tiene fondo
uniforme, iluminacion suave y a menudo el textil ocupa una fraccion del encuadre;
en esas condiciones cualquier par de recortes correlaciona alto y un umbral fijo
declara simetrias que no existen. Aqui se construye una distribucion nula por
imagen —correlacion contra desplazamientos aleatorios no periodicos— y se exige
superar su percentil 95. Asi el criterio se adapta al contraste y al ruido de
cada pieza.

Funciones principales:
    load_gray        carga, recorta fondo y normaliza
    autocorrelation  autocorrelacion normalizada por FFT
    lattice_vectors  vectores de traslacion dominantes
    symmetry_scores  puntuacion de cada operacion
    frieze_group     asignacion de grupo de friso (7)
    wallpaper_group  asignacion de grupo cristalografico plano (subconjunto)
"""
import numpy as np
from scipy import ndimage

# ---------------------------------------------------------------- preprocesado


def load_gray(path, max_side=768):
    """Carga en gris, recorta el fondo liso del encuadre y normaliza a media 0."""
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("L")
        w, h = im.size
        s = max_side / max(w, h)
        if s < 1:
            im = im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
        a = np.asarray(im, dtype=np.float64)
    a = crop_background(a)
    if a.size == 0 or min(a.shape) < 32:
        return None
    a -= a.mean()
    sd = a.std()
    return a / sd if sd > 1e-9 else None


def crop_background(a, quantile=0.15):
    """Recorta filas y columnas de baja variacion en los bordes.

    Las fotografias de museo dejan un marco liso alrededor de la pieza. Ese marco
    infla la autocorrelacion —dos zonas planas correlacionan perfectamente— y
    desplaza la deteccion de periodo hacia valores espurios.
    """
    if a.ndim != 2 or min(a.shape) < 16:
        return a
    gy = np.abs(np.diff(a, axis=0)).mean(axis=1)
    gx = np.abs(np.diff(a, axis=1)).mean(axis=0)

    def span(profile):
        if profile.size == 0:
            return 0, 0
        thr = np.quantile(profile, quantile) + 1e-9
        idx = np.flatnonzero(profile > thr)
        return (idx[0], idx[-1] + 2) if idx.size else (0, profile.size + 1)

    y0, y1 = span(gy)
    x0, x1 = span(gx)
    out = a[y0:y1, x0:x1]
    return out if min(out.shape) >= 32 else a


# ------------------------------------------------------------ autocorrelacion


def autocorrelation(a):
    """Autocorrelacion normalizada, con el origen centrado."""
    f = a - a.mean()
    n0, n1 = 2 * a.shape[0], 2 * a.shape[1]
    F = np.fft.rfft2(f, s=(n0, n1))
    ac = np.fft.irfft2(F * np.conj(F), s=(n0, n1))
    ac = np.fft.fftshift(ac)[
        n0 // 2 - a.shape[0] // 2: n0 // 2 + (a.shape[0] + 1) // 2,
        n1 // 2 - a.shape[1] // 2: n1 // 2 + (a.shape[1] + 1) // 2]
    peak = ac.max()
    return ac / peak if peak > 1e-12 else ac


def lattice_vectors(ac, min_radius=6, n_peaks=12):
    """Los dos vectores de traslacion mas cortos e independientes.

    Devuelve (v1, v2, picos). v2 es None cuando el patron solo es periodico en
    una direccion, que es el caso de las cenefas y bandas —muy frecuentes en
    tunicas y mantos andinos— y obliga a clasificar por grupo de friso en vez de
    por grupo cristalografico.
    """
    c = np.array(ac.shape) // 2
    local_max = ndimage.maximum_filter(ac, size=5)
    yy, xx = np.mgrid[0:ac.shape[0], 0:ac.shape[1]]
    far = np.hypot(yy - c[0], xx - c[1]) >= min_radius
    if not far.any():
        return None, None, []

    # El umbral es relativo al pico mas alto fuera del origen, no absoluto. Con
    # un umbral fijo se cuelan maximos locales debiles muy cercanos al centro
    # —el hombro de la autocorrelacion— y, como despues se elige el vector mas
    # corto, uno de esos impostores se lleva la eleccion y el periodo detectado
    # no tiene nada que ver con la celda real.
    peak_max = ac[far].max()
    if peak_max <= 0:
        return None, None, []

    # El corte se pone alto a proposito. Un patron con rotacion de 180 grados
    # produce un pico intermedio a media celda —la celda girada se parece a la
    # original— con valor tipico de 0,5. Admitirlo hace que se elija como periodo
    # la mitad de la celda real, y a partir de ahi la fase del deslizamiento y la
    # normalizacion por traslacion quedan mal calculadas. Solo se aceptan picos
    # comparables al mejor; si ninguno lo es, se relaja el criterio.
    for rel in (0.8, 0.6, 0.4):
        cand = (ac == local_max) & far & (ac >= rel * peak_max)
        ys, xs = np.nonzero(cand)
        if ys.size:
            break
    if ys.size == 0:
        return None, None, []
    d = np.hypot(ys - c[0], xs - c[1])
    order = np.argsort(d)[:n_peaks]
    peaks = [(int(ys[i] - c[0]), int(xs[i] - c[1]), float(ac[ys[i], xs[i]])) for i in order]

    v1 = np.array(peaks[0][:2], dtype=float)
    v2 = None
    for p in peaks[1:]:
        w = np.array(p[:2], dtype=float)
        cross = abs(v1[0] * w[1] - v1[1] * w[0])
        if cross > 0.25 * np.linalg.norm(v1) * np.linalg.norm(w):
            v2 = w
            break
    return v1, v2, peaks


# ------------------------------------------------------------------ simetrias


def rectify(a, v1):
    """Endereza la imagen alineando el vector de traslacion con el eje horizontal.

    El propio vector de red delata la inclinacion: en una banda periodica deberia
    salir horizontal, y si sale como (-3, -96) es que la pieza esta girada 1,8
    grados en la fotografia. Enderezar antes de buscar simetrias corrige la causa
    en lugar de compensar el sintoma operacion por operacion, y deja los ejes de
    simetria alineados con los ejes de la imagen, que es lo que suponen las
    pruebas de reflexion.

    Devuelve (imagen rectificada, angulo aplicado en grados).
    """
    if v1 is None:
        return a, 0.0
    ang = float(np.degrees(np.arctan2(v1[0], v1[1])))
    if ang > 90:
        ang -= 180
    elif ang < -90:
        ang += 180
    if abs(ang) < 0.2 or abs(ang) > 45:
        return a, 0.0
    out = ndimage.rotate(a, ang, reshape=False, order=1, mode="reflect")
    return out, ang


def max_shift_ncc(a, b):
    """Maxima correlacion normalizada entre a y b sobre todos los desplazamientos.

    Un eje de simetria puede estar en cualquier punto del patron, no en el centro
    de la fotografia. Comparar la imagen con su reflejo sin permitir traslacion
    solo detecta la simetria cuando el encuadre acierta a centrarla, lo que en
    fotografia de museo no ocurre casi nunca. Se maximiza sobre traslaciones
    mediante correlacion circular por FFT, que ademas es el modelo correcto para
    un patron periodico: dos reflejos separados por media celda son la misma
    simetria vista desde otro origen.
    """
    if a.shape != b.shape or a.size == 0:
        return 0.0, 0, 0
    x = a - a.mean()
    y = b - b.mean()
    sx, sy = x.std(), y.std()
    if sx < 1e-9 or sy < 1e-9:
        return 0.0, 0, 0
    corr = np.fft.irfft2(np.fft.rfft2(x) * np.conj(np.fft.rfft2(y)), s=a.shape)
    idx = int(np.argmax(corr))
    dy, dx = np.unravel_index(idx, corr.shape)
    return float(corr.flat[idx] / (a.size * sx * sy)), int(dy), int(dx)


def _rotate(a, deg):
    return ndimage.rotate(a, deg, reshape=False, order=1, mode="nearest")


def _shear(a, sx, sy):
    if sx == 0 and sy == 0:
        return a
    m = np.array([[1.0, sx], [sy, 1.0]])
    return ndimage.affine_transform(a, m, order=1, mode="reflect")


# Correcciones afines que se prueban al buscar cada simetria. Una cizalla de
# apenas 0,03 —menos de dos grados, indistinguible a ojo en una foto de catalogo—
# hunde la correlacion de una reflexion exacta de 1,00 a 0,50, porque el eje deja
# de estar alineado con los ejes de la imagen. Como la pieza rara vez se
# fotografia frontal y el tejido cuelga deformado, la simetria hay que buscarla
# permitiendo esta correccion. El mismo margen se concede al calcular el suelo de
# ruido, para no regalar puntuacion a las operaciones que no son simetria.
SHEAR_GRID = [(0.0, 0.0), (0.05, 0.0), (-0.05, 0.0), (0.0, 0.05), (0.0, -0.05),
              (0.05, 0.05), (-0.05, -0.05), (0.05, -0.05), (-0.05, 0.05)]


def best_op_score(a, b):
    """Mejor correlacion entre a y b permitiendo pequena correccion afin.

    Devuelve (puntuacion, dy, dx) del mejor ajuste.
    """
    best = (0.0, 0, 0)
    for sx, sy in SHEAR_GRID:
        s, dy, dx = max_shift_ncc(a, _shear(b, sx, sy))
        if s > best[0]:
            best = (s, dy, dx)
    return best


# Angulos que no son simetria de ningun grupo cristalografico plano. Sirven para
# medir cuanta correlacion produce la textura de esta imagen por si sola.
NULL_ANGLES = (17, 41, 73, 109)


def translation_score(a, v):
    """Correlacion de la imagen consigo misma desplazada un vector de la red.

    Es el techo del metodo. Si el patron esta desgastado, mal encuadrado o
    fotografiado en escorzo, ni siquiera su propia traslacion alcanza correlacion
    alta; exigirle a una reflexion mas que eso seria absurdo. Todas las simetrias
    se miden como fraccion de este valor.
    """
    if v is None:
        return None
    dy, dx = int(round(v[0])), int(round(v[1]))
    if dy == 0 and dx == 0:
        return None
    b = np.roll(a, (dy, dx), axis=(0, 1))
    x = a - a.mean()
    y = b - b.mean()
    sx, sy = x.std(), y.std()
    if sx < 1e-9 or sy < 1e-9:
        return None
    return float((x * y).mean() / (sx * sy))


def null_threshold(a, margin=1.15):
    """Suelo de correlacion espuria: rotaciones a angulos no cristalograficos.

    Una trama regular de hilos correlaciona consigo misma en cualquier
    orientacion. Este suelo evita que esa regularidad del tejido, ajena a la
    iconografia, se confunda con simetria del diseno.
    """
    vals = [best_op_score(a, _rotate(a, ang))[0] for ang in NULL_ANGLES]
    return float(np.percentile(vals, 90) * margin)


DEFAULT_RATIO = 0.70  # elegido por barrido sobre los sinteticos: ver results/threshold_sweep.json


def decision_threshold(a, v1, ratio=DEFAULT_RATIO):
    """Umbral con el que se declara presente una simetria.

    Combina los dos criterios: hay que superar el suelo de correlacion espuria y
    ademas acercarse al techo que marca la propia traslacion del patron. El
    segundo es el que discrimina de verdad; el primero solo protege de imagenes
    sin periodicidad, donde el techo no esta definido.

    El valor 0,70 no es arbitrario. Por debajo, las reflexiones debiles del ruido
    de fondo se declaran validas y p1m1 se desmorona; por encima, se pierden las
    simetrias reales de las piezas desgastadas y caen p2 y p11g. El optimo es
    plano entre 0,65 y 0,70, lo que indica que la eleccion no esta sobreajustada
    a un punto concreto.
    """
    floor = null_threshold(a)
    ceiling = translation_score(a, v1)
    if ceiling is None or ceiling <= floor:
        return floor, ceiling
    return max(floor, ratio * ceiling), ceiling


def _half_period_offset(shift, period):
    """Fraccion de periodo en la que cae un desplazamiento, en [0, 0.5].

    Cero significa que el desplazamiento es multiplo del periodo; 0,5 que cae
    justo a mitad de celda. Es lo que separa una reflexion de un deslizamiento.
    """
    if not period or period < 2:
        return None
    frac = (shift % period) / period
    return float(min(frac, 1.0 - frac))


def symmetry_scores(a, period_y=None, period_x=None, glide_tol=0.15):
    """Puntua cada operacion de simetria, invariante a la posicion del eje.

    Reflexion y deslizamiento producen la misma puntuacion cuando se maximiza
    sobre traslaciones: la media celda del deslizamiento queda absorbida por el
    maximo. Lo que los separa es *donde* cae ese desplazamiento optimo. Para una
    reflexion de eje horizontal, un patron con reflexion pura casa sin
    desplazamiento en x; uno con deslizamiento exige media celda. Por eso se
    conserva el argumento del maximo y se mide su fase respecto al periodo.
    """
    sh, _, dx_h = best_op_score(a, np.flipud(a))
    sv, dy_v, _ = best_op_score(a, np.fliplr(a))

    phase_h = _half_period_offset(dx_h, period_x)
    phase_v = _half_period_offset(dy_v, period_y)
    is_glide_h = phase_h is not None and phase_h > 0.5 - glide_tol
    is_glide_v = phase_v is not None and phase_v > 0.5 - glide_tol

    return {
        # Puntuacion de la reflexion, valida tanto para eje puro como deslizado.
        "reflect_h": sh,
        "reflect_v": sv,
        # Reflexion pura: solo si el desplazamiento optimo no cae a media celda.
        "mirror_h": 0.0 if is_glide_h else sh,
        "mirror_v": 0.0 if is_glide_v else sv,
        "glide_h": sh if is_glide_h else 0.0,
        "glide_v": sv if is_glide_v else 0.0,
        "phase_h": phase_h,
        "phase_v": phase_v,
        "rot180": best_op_score(a, np.rot90(a, 2))[0],
        "rot90": best_op_score(a, _rotate(a, 90))[0],
        "rot120": best_op_score(a, _rotate(a, 120))[0],
        "rot60": best_op_score(a, _rotate(a, 60))[0],
    }


# --------------------------------------------------------------------- grupos

FRIEZE = ["p1", "p11g", "p1m1", "p11m", "p2", "p2mg", "p2mm"]


def frieze_group(s, thr):
    """Grupo de friso a partir de las operaciones que superan el umbral.

    Notacion: el primer eje es el de traslacion (horizontal por convencion).
      p1    solo traslacion
      p11g  deslizamiento
      p1m1  reflexion en eje vertical (perpendicular a la traslacion)
      p11m  reflexion en eje horizontal (paralelo a la traslacion)
      p2    rotacion de 180 grados
      p2mg  rotacion y deslizamiento
      p2mm  rotacion y ambas reflexiones
    """
    v = s["mirror_v"] > thr   # perpendicular al eje de traslacion
    h = s["mirror_h"] > thr   # paralelo al eje de traslacion
    r = s["rot180"] > thr
    g = s["glide_h"] > thr

    if r and h and v:
        return "p2mm"
    if r and g and not h:
        return "p2mg"
    if r:
        return "p2"
    if h:
        return "p11m"
    if v:
        return "p1m1"
    if g:
        return "p11g"
    return "p1"


def wallpaper_group(s, thr):
    """Asignacion aproximada de grupo cristalografico plano.

    Se limita a los grupos distinguibles con las operaciones medidas. Los
    diecisiete grupos completos exigen resolver ademas el tipo de red y la
    posicion exacta de los ejes, que en fotografia de museo —con perspectiva y
    pieza deformada— no es fiable. Se devuelve el grupo mas probable junto con el
    orden de rotacion, que si es robusto.
    """
    rot = 1
    if s["rot60"] > thr:
        rot = 6
    elif s["rot90"] > thr:
        rot = 4
    elif s["rot120"] > thr:
        rot = 3
    elif s["rot180"] > thr:
        rot = 2

    mirror = (s["mirror_h"] > thr) or (s["mirror_v"] > thr)
    glide = (s["glide_h"] > thr) or (s["glide_v"] > thr)

    table = {
        (1, False, False): "p1",
        (1, False, True): "pg",
        (1, True, False): "pm",
        (1, True, True): "cm",
        (2, False, False): "p2",
        (2, False, True): "pgg",
        (2, True, False): "pmm",
        (2, True, True): "pmg",
        (3, False, False): "p3",
        (3, True, False): "p3m1",
        (3, True, True): "p31m",
        (3, False, True): "p3",
        (4, False, False): "p4",
        (4, True, False): "p4m",
        (4, True, True): "p4g",
        (4, False, True): "p4g",
        (6, False, False): "p6",
        (6, True, False): "p6m",
        (6, True, True): "p6m",
        (6, False, True): "p6",
    }
    return table.get((rot, mirror, glide), "p1"), rot
