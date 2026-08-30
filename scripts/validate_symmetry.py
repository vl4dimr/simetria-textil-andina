# -*- coding: utf-8 -*-
"""
Validacion del detector de simetria sobre patrones sinteticos de grupo conocido.

Se generan bandas periodicas construidas por los generadores de cada uno de los
siete grupos de friso, se degradan con ruido, desenfoque y ligera perspectiva
—las tres degradaciones que aparecen en una fotografia de museo— y se comprueba
cuantas recupera el detector.

Sin esta comprobacion el metodo no es falsable: sobre fotografias reales no hay
etiqueta de simetria contra la que contrastar, asi que la unica evidencia de que
el detector funciona es su comportamiento sobre casos de respuesta conocida.

Salidas (results/):
  validation_frieze.csv    una fila por patron sintetico
  validation_summary.json  exactitud global y matriz de confusion
"""
import csv
import json
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import symmetry_core as sc

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "results")

CELL = 48          # lado del dominio fundamental en pixeles
REPEATS = 8        # celdas a lo largo de la banda
N_PER_GROUP = 12   # patrones por grupo, con motivo distinto cada vez


MAX_SELF_SYMMETRY = 0.45


def _draw_glyph(rng, h, w):
    """Glifo tipo 'F': tres trazos que no admiten ningun eje de simetria."""
    m = np.zeros((h, w))
    t = max(2, h // 10)
    y0, y1 = h // 6, h - h // 6
    x0 = w // 4
    m[y0:y1, x0:x0 + t] = 1.0                          # asta vertical
    m[y0:y0 + t, x0:x0 + int(w * rng.uniform(0.35, 0.5))] = 1.0   # brazo superior
    mid = y0 + (y1 - y0) // 2
    m[mid:mid + t, x0:x0 + int(w * rng.uniform(0.2, 0.32))] = 1.0  # brazo medio
    for _ in range(2):
        cy, cx = rng.integers(h // 5, h - h // 5), rng.integers(w // 2, w - w // 6)
        r = rng.integers(2, max(3, h // 8))
        y, x = np.ogrid[:h, :w]
        m[(y - cy) ** 2 + (x - cx) ** 2 <= r * r] += rng.uniform(0.6, 1.0)
    return m


def motif(rng, h, w, tries=40):
    """Dominio fundamental sin simetria propia.

    La etiqueta de referencia solo es valida si el motivo carece de simetria: un
    motivo que ya fuese simetrico haria que el patron perteneciera a un grupo
    mayor que el construido, y estariamos midiendo el acierto contra una etiqueta
    falsa. Por eso no basta con dibujar formas al azar —cuatro elipses sueltas
    salen aproximadamente simetricas mas veces de lo que parece—: se comprueba y
    se descarta el motivo que no pase.
    """
    best, best_score = None, 1e9
    for _ in range(tries):
        m = _draw_glyph(rng, h, w)
        score = max(sc.max_shift_ncc(m, np.flipud(m))[0],
                    sc.max_shift_ncc(m, np.fliplr(m))[0],
                    sc.max_shift_ncc(m, np.rot90(m, 2))[0])
        if score < best_score:
            best, best_score = m, score
        if score < MAX_SELF_SYMMETRY:
            return m
    return best


def build(group, rng):
    """Celda del grupo indicado, construida aplicando sus generadores."""
    f = motif(rng, CELL, CELL)
    fl_lr, fl_ud = np.fliplr(f), np.flipud(f)
    rot = np.rot90(f, 2)

    if group == "p1":
        cell = f
    elif group == "p11g":
        # Deslizamiento: reflejo en eje horizontal + media celda de traslacion.
        cell = np.hstack([f, fl_ud])
    elif group == "p1m1":
        # Reflexion en eje vertical, perpendicular a la direccion de traslacion.
        cell = np.hstack([f, fl_lr])
    elif group == "p11m":
        # Reflexion en eje horizontal, paralelo a la traslacion.
        cell = np.vstack([f, fl_ud])
    elif group == "p2":
        cell = np.hstack([f, rot])
    elif group == "p2mg":
        top = np.hstack([f, fl_lr])
        cell = np.vstack([top, np.flipud(np.roll(top, CELL, axis=1))])
    elif group == "p2mm":
        top = np.hstack([f, fl_lr])
        cell = np.vstack([top, np.flipud(top)])
    else:
        raise ValueError(group)

    band = np.tile(cell, (1, REPEATS))
    return band


def degrade(a, rng, noise=0.12, blur=1.0, shear=0.03):
    """Ruido, desenfoque y cizalla: la fotografia de museo nunca es frontal."""
    a = ndimage.gaussian_filter(a, blur)
    m = np.array([[1.0, shear * rng.choice([-1, 1])], [shear * rng.choice([-1, 1]), 1.0]])
    a = ndimage.affine_transform(a, m, order=1, mode="reflect")
    a = a + rng.normal(0, noise * a.std(), a.shape)
    return a


def detect(a):
    """Aplica la cadena completa y devuelve grupo estimado y diagnostico."""
    a = a - a.mean()
    sd = a.std()
    if sd < 1e-9:
        return "p1", {}
    a = a / sd
    # Primera pasada: localizar la red para saber cuanto hay que enderezar.
    v1, _, _ = sc.lattice_vectors(sc.autocorrelation(a))
    a, angle = sc.rectify(a, v1)
    # Segunda pasada: sobre la imagen ya recta, la red es la definitiva.
    v1, v2, _ = sc.lattice_vectors(sc.autocorrelation(a))

    period_x = abs(v1[1]) if v1 is not None and abs(v1[1]) > 2 else None
    period_y = abs(v1[0]) if v1 is not None and abs(v1[0]) > 2 else None
    if v2 is not None:
        period_x = period_x or (abs(v2[1]) if abs(v2[1]) > 2 else None)
        period_y = period_y or (abs(v2[0]) if abs(v2[0]) > 2 else None)
    thr, ceiling = sc.decision_threshold(a, v1)
    s = sc.symmetry_scores(a, period_y=period_y, period_x=period_x)
    return sc.frieze_group(s, thr), {"thr": thr, "translation": ceiling, "rectify_angle": angle,
                                     "period_x": period_x, "period_y": period_y, **s}


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(20260809)

    rows, confusion = [], {}
    for group in sc.FRIEZE:
        for k in range(N_PER_GROUP):
            band = degrade(build(group, rng), rng)
            pred, diag = detect(band)
            confusion.setdefault(group, {})
            confusion[group][pred] = confusion[group].get(pred, 0) + 1
            rows.append({
                "true_group": group, "pred_group": pred, "correct": pred == group,
                "replicate": k,
                **{key: (round(v, 4) if isinstance(v, float) else v)
                   for key, v in diag.items()},
            })
        acc = confusion[group].get(group, 0) / N_PER_GROUP
        print("  %-6s acierto %.0f%%   %s" % (group, 100 * acc, confusion[group]), flush=True)

    with open(os.path.join(OUT, "validation_frieze.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    correct = sum(1 for r in rows if r["correct"])
    summary = {
        "n": len(rows),
        "accuracy": round(correct / len(rows), 4),
        "per_group_accuracy": {g: round(confusion[g].get(g, 0) / N_PER_GROUP, 4) for g in sc.FRIEZE},
        "confusion": confusion,
        "settings": {"cell": CELL, "repeats": REPEATS, "n_per_group": N_PER_GROUP,
                     "noise": 0.12, "blur": 1.0, "shear": 0.03},
    }
    with open(os.path.join(OUT, "validation_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n  EXACTITUD GLOBAL %.1f%% (%d/%d)" % (100 * summary["accuracy"], correct, len(rows)))
    print("  ->", os.path.join(OUT, "validation_summary.json"))


if __name__ == "__main__":
    main()
