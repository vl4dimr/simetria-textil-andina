# -*- coding: utf-8 -*-
"""
Figuras del articulo.

Figura 1 — lamina de ejemplos: dos piezas por grupo de friso, elegidas por ser
las de periodicidad mas limpia dentro de su grupo. Da al lector la posibilidad de
juzgar por si mismo si la asignacion es sensata, que en un metodo automatico
sobre material patrimonial es tan necesario como el estadistico.

Figura 2 — reparto de grupos por cultura, en pequenos multiples. Se usa un solo
tono y se deja la comparacion codificada por posicion: entre culturas se lee
recorriendo la misma fila en los cuatro paneles. Un apilado de seis colores
obligaria al lector a resolver seis identidades cromaticas antes de ver el
contraste, y ademas no sobrevive a la impresion en escala de grises, que sigue
siendo el destino de muchas copias de un articulo.

Figura 3 — sensibilidad a las degradaciones: por que la cizalla importa y el
ruido no.

Las imagenes NO llevan titulo ni numero incrustados. Dos razones: la norma de VAR
prohibe superponer texto a las ilustraciones y exige que el pie sea texto del
documento; y el numero de figura depende del orden de aparicion en el manuscrito,
que no coincide con el orden en que se generan aqui. Manteniendo el numero solo
en el pie, renumerar es cambiar una linea de texto y no volver a dibujar nada.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import symmetry_core as sc

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = os.path.join(BASE, "results", "figuras")

HUE = "#2a78d6"        # tono unico para magnitud
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#dedddb"
SURFACE = "#fcfcfb"

FRIEZE_ORDER = ["p1", "p11m", "p1m1", "p2", "p2mg", "p2mm"]
CULTURE_ORDER = ["nasca", "wari", "chimu", "ica"]
CULTURE_LABEL = {"nasca": "Nasca", "wari": "Wari", "chimu": "Chimú", "ica": "Ica"}


def load_rows():
    path = os.path.join(BASE, "results", "symmetry.csv")
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if r.get("status") == "ok"]


# ------------------------------------------------------------------ figura 1
def figura_ejemplos(rows):
    from PIL import Image
    fig = plt.figure(figsize=(9.6, 3.9), dpi=300, facecolor=SURFACE)
    gs = GridSpec(2, 6, figure=fig, hspace=0.34, wspace=0.08,
                  left=0.02, right=0.98, top=0.93, bottom=0.05)

    for col, grp in enumerate(FRIEZE_ORDER):
        sub = [r for r in rows if r["frieze_group"] == grp and r["translation"] not in ("", "None")]
        sub.sort(key=lambda r: -float(r["translation"]))
        for row_i in range(2):
            ax = fig.add_subplot(gs[row_i, col])
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_color(GRID); sp.set_linewidth(0.8)
            if row_i < len(sub):
                r = sub[row_i]
                try:
                    with Image.open(os.path.join(BASE, r["file"])) as im:
                        # Lienzo cuadrado con relleno neutro. Las piezas van de
                        # cintas muy alargadas a mantos casi cuadrados; sin
                        # normalizar la proporcion cada celda toma un alto
                        # distinto y la retícula se descuadra. Recortar al cuadrado
                        # perderia justamente la repeticion de las cintas, que es
                        # lo que la figura debe mostrar, asi que se rellena.
                        im = im.convert("RGB")
                        im.thumbnail((400, 400), Image.LANCZOS)
                        canvas = Image.new("RGB", (400, 400), (250, 250, 248))
                        canvas.paste(im, ((400 - im.width) // 2, (400 - im.height) // 2))
                        ax.imshow(np.asarray(canvas))
                except Exception:
                    ax.text(0.5, 0.5, "sin imagen", ha="center", va="center",
                            fontsize=6, color=INK_SOFT, transform=ax.transAxes)
                cul = r["culture"]
                cap = CULTURE_LABEL.get(cul, cul if cul != "no determinada" else "s. atribuir")
                ax.set_xlabel("%s · r=%.2f" % (cap, float(r["translation"])),
                              fontsize=6, color=INK_SOFT, labelpad=1.5)
            if row_i == 0:
                ax.set_title(grp, fontsize=10.5, color=INK, pad=5, fontweight="bold")

    out = os.path.join(FIGDIR, "figura1_ejemplos.png")
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


# ------------------------------------------------------------------ figura 2
def figura_reparto(rows):
    sub = [r for r in rows if r["culture"] in CULTURE_ORDER
           and r["attribution_uncertain"] != "True"]
    # El alto y el margen superior se fijan con holgura: con la caja anterior el
    # subtitulo invadia los titulos de panel y el texto quedaba ilegible.
    fig, axes = plt.subplots(1, 4, figsize=(9.6, 3.2), dpi=300,
                             facecolor=SURFACE, sharey=True,
                             gridspec_kw={"wspace": 0.28})
    y = np.arange(len(FRIEZE_ORDER))

    for ax, cul in zip(axes, CULTURE_ORDER):
        s = [r for r in sub if r["culture"] == cul]
        n = len(s)
        pct = [100.0 * sum(1 for r in s if r["frieze_group"] == g) / n if n else 0
               for g in FRIEZE_ORDER]
        ax.barh(y, pct, height=0.62, color=HUE, zorder=3)
        for yi, v in zip(y, pct):
            if v > 0:
                ax.text(v + 2.5, yi, "%.0f" % v, va="center", ha="left",
                        fontsize=7.5, color=INK_SOFT, zorder=4)
        ax.set_title("%s  (n=%d)" % (CULTURE_LABEL[cul], n), fontsize=10,
                     color=INK, pad=8)
        ax.set_xlim(0, 104)
        ax.set_xticks([0, 50, 100])
        ax.tick_params(axis="x", labelsize=7.5, colors=INK_SOFT, length=0)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color=GRID, linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right", "bottom", "left"):
            ax.spines[side].set_visible(False)
        ax.set_facecolor(SURFACE)

    axes[0].set_yticks(y)
    axes[0].set_yticklabels(FRIEZE_ORDER, fontsize=9, color=INK)
    axes[0].tick_params(axis="y", length=0)
    axes[0].invert_yaxis()

    # Margenes explicitos en lugar de tight_layout: con cuatro paneles y titulos
    # propios, tight_layout no respeta el rectangulo reservado y el subtitulo
    # acaba escrito encima de los nombres de cultura.
    fig.subplots_adjust(top=0.88, left=0.07, right=0.99, bottom=0.13, wspace=0.30)
    out = os.path.join(FIGDIR, "figura2_reparto.png")
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


# ------------------------------------------------------------------ figura 3
def figura_degradaciones():
    """Mide de nuevo el efecto de cada degradacion para que la figura tenga dato."""
    import validate_symmetry as V
    from scipy import ndimage
    rng = np.random.default_rng(5)

    # Punto decimal: la norma de VAR lo exige tambien dentro de las figuras.
    labels = ["sin degradar", "ruido 0.12", "desenfoque σ=1", "cizalla 0.01",
              "cizalla 0.02", "cizalla 0.03", "cizalla 0.05"]

    def variants(a):
        return [
            a,
            a + rng.normal(0, 0.12 * a.std(), a.shape),
            ndimage.gaussian_filter(a, 1.0),
            ndimage.affine_transform(a, np.array([[1.0, 0.01], [0.01, 1.0]]), order=1, mode="reflect"),
            ndimage.affine_transform(a, np.array([[1.0, 0.02], [0.02, 1.0]]), order=1, mode="reflect"),
            ndimage.affine_transform(a, np.array([[1.0, 0.03], [0.03, 1.0]]), order=1, mode="reflect"),
            ndimage.affine_transform(a, np.array([[1.0, 0.05], [0.05, 1.0]]), order=1, mode="reflect"),
        ]

    # Tres niveles de correccion. Separarlos importa: medir "sin rectificar" con
    # la rejilla afin ya activa oculta la mitad del problema, porque la rejilla
    # compensa por su cuenta parte de la cizalla.
    crudo, afin, completo = [[] for _ in labels], [[] for _ in labels], [[] for _ in labels]
    for rep in range(6):
        band = V.build("p11m", rng)
        for i, v in enumerate(variants(band.copy())):
            a = (v - v.mean()) / v.std()
            crudo[i].append(sc.max_shift_ncc(a, np.flipud(a))[0])
            afin[i].append(sc.best_op_score(a, np.flipud(a))[0])
            v1, _, _ = sc.lattice_vectors(sc.autocorrelation(a))
            ar, _ = sc.rectify(a, v1)
            completo[i].append(sc.best_op_score(ar, np.flipud(ar))[0])

    m_crudo = [float(np.mean(x)) for x in crudo]
    m_sin = [float(np.mean(x)) for x in afin]
    m_con = [float(np.mean(x)) for x in completo]

    fig, ax = plt.subplots(figsize=(8.2, 3.0), dpi=300, facecolor=SURFACE)
    x = np.arange(len(labels))
    ax.plot(x, m_crudo, "-o", color="#c9c8c4", linewidth=2, markersize=7,
            label="sin corrección", zorder=3)
    ax.plot(x, m_sin, "-o", color="#8e8d89", linewidth=2, markersize=7,
            label="+ rejilla afín", zorder=4)
    ax.plot(x, m_con, "-o", color=HUE, linewidth=2, markersize=7,
            label="+ rectificación por la red", zorder=5)
    ax.axhline(0.70, color=INK_SOFT, linewidth=1, linestyle=(0, (4, 3)), zorder=2)
    ax.text(len(labels) - 0.4, 0.715, "umbral de decisión", fontsize=7.5,
            color=INK_SOFT, ha="right", va="bottom")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, color=INK_SOFT, rotation=18, ha="right")
    ax.set_ylabel("correlación de la reflexión", fontsize=9, color=INK_SOFT)
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.set_facecolor(SURFACE)
    leg = ax.legend(fontsize=8, frameon=False, loc="lower left")
    for t in leg.get_texts():
        t.set_color(INK_SOFT)

    fig.tight_layout()
    out = os.path.join(FIGDIR, "figura3_degradaciones.png")
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out, labels, m_crudo, m_sin, m_con


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    rows = load_rows()
    print("figura 1 ->", figura_ejemplos(rows), flush=True)
    print("figura 2 ->", figura_reparto(rows), flush=True)
    out, labels, m0, ms, mc = figura_degradaciones()
    print("figura 3 ->", out)
    for l, z, a, b in zip(labels, m0, ms, mc):
        print("   %-16s crudo %.3f | +afin %.3f | +rectif %.3f" % (l, z, a, b))


if __name__ == "__main__":
    main()
