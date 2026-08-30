# -*- coding: utf-8 -*-
"""
Contraste: la distribucion de grupos de simetria depende de la cultura?

Es la pregunta del articulo. Describir que en Wari abunda p2mm no dice nada por
si solo: hay que mostrar que el reparto de grupos difiere entre culturas mas de
lo que difieren dos muestras del mismo reparto.

Se usa una prueba de permutacion sobre el estadistico chi-cuadrado en vez de la
prueba chi-cuadrado clasica. El motivo es concreto: con siete grupos de friso y
culturas de setenta piezas, muchas casillas quedan por debajo de cinco casos y
la aproximacion asintotica de la chi-cuadrado deja de ser valida. La permutacion
no necesita ese supuesto porque construye la distribucion nula barajando las
etiquetas de cultura sobre los mismos datos.

Se informa ademas la V de Cramer, que mide cuanta asociacion hay, no solo si la
hay: con muestras grandes un p pequeno puede acompanar a un efecto irrelevante.

Salidas (results/):
  stats_symmetry.json
"""
import csv
import json
import os
import sys

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "results")
N_PERM = 10000
MIN_PER_CLASS = 20  # por debajo de esto la clase no aporta y desestabiliza el estadistico


def chi2_stat(table):
    """Chi-cuadrado de independencia, sin correcciones."""
    t = np.asarray(table, dtype=float)
    total = t.sum()
    if total <= 0:
        return 0.0
    expected = np.outer(t.sum(axis=1), t.sum(axis=0)) / total
    mask = expected > 0
    return float((((t - expected) ** 2)[mask] / expected[mask]).sum())


def cramers_v(table):
    t = np.asarray(table, dtype=float)
    n = t.sum()
    if n <= 0:
        return 0.0
    k = min(t.shape) - 1
    if k <= 0:
        return 0.0
    return float(np.sqrt(chi2_stat(t) / (n * k)))


def permutation_test(labels, groups, n_perm=N_PERM, seed=20260810):
    """p exacto por remuestreo: se barajan las etiquetas, no los datos."""
    labels = np.asarray(labels)
    groups = np.asarray(groups)
    lab_u = sorted(set(labels))
    grp_u = sorted(set(groups))
    idx_l = {v: i for i, v in enumerate(lab_u)}
    idx_g = {v: i for i, v in enumerate(grp_u)}

    def build(lab):
        t = np.zeros((len(lab_u), len(grp_u)))
        for a, b in zip(lab, groups):
            t[idx_l[a], idx_g[b]] += 1
        return t

    observed = build(labels)
    stat = chi2_stat(observed)
    rng = np.random.default_rng(seed)
    shuffled = labels.copy()
    count = 0
    for _ in range(n_perm):
        rng.shuffle(shuffled)
        if chi2_stat(build(shuffled)) >= stat:
            count += 1
    # Estimador con correccion de continuidad: nunca informa p = 0.
    p = (count + 1) / (n_perm + 1)
    return {
        "chi2": round(stat, 3),
        "p_permutation": round(p, 5),
        "n_permutations": n_perm,
        "cramers_v": round(cramers_v(observed), 4),
        "levels": lab_u,
        "groups": grp_u,
        "table": observed.astype(int).tolist(),
        "n": int(observed.sum()),
    }


def load(exclude_uncertain):
    path = os.path.join(OUT, "symmetry.csv")
    if not os.path.exists(path):
        sys.exit("Falta %s. Ejecuta antes analyze_corpus_symmetry.py" % path)
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("status") == "ok"]
    if exclude_uncertain:
        rows = [r for r in rows if r.get("attribution_uncertain") != "True"]
    return rows


def run(rows, label_key, group_key="frieze_group"):
    counts = {}
    for r in rows:
        counts[r[label_key]] = counts.get(r[label_key], 0) + 1
    keep = {k for k, v in counts.items() if v >= MIN_PER_CLASS
            and k not in ("no determinada", "no determinado")}
    sub = [r for r in rows if r[label_key] in keep]
    if len({r[label_key] for r in sub}) < 2:
        return {"skipped": "menos de dos clases con n>=%d" % MIN_PER_CLASS}
    res = permutation_test([r[label_key] for r in sub], [r[group_key] for r in sub])
    res["classes_used"] = sorted(keep)
    res["classes_dropped"] = sorted(set(counts) - keep)
    return res


def main():
    report = {}
    for tag, excl in [("todas", False), ("sin atribucion dudosa", True)]:
        rows = load(excl)
        report[tag] = {
            "n_ok": len(rows),
            "cultura_vs_friso": run(rows, "culture"),
            "horizonte_vs_friso": run(rows, "horizon"),
            "cultura_vs_orden_rotacion": run(rows, "culture", "rotation_order"),
        }

    with open(os.path.join(OUT, "stats_symmetry.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    for tag, blk in report.items():
        print("\n=== %s (n=%d) ===" % (tag.upper(), blk["n_ok"]))
        for test, res in blk.items():
            if test == "n_ok":
                continue
            if "skipped" in res:
                print("  %-28s omitido: %s" % (test, res["skipped"]))
                continue
            print("  %-28s chi2=%8.2f  p=%.5f  V=%.3f  n=%d  clases=%s" % (
                test, res["chi2"], res["p_permutation"], res["cramers_v"],
                res["n"], ",".join(res["classes_used"])))
    print("\n  ->", os.path.join(OUT, "stats_symmetry.json"))


if __name__ == "__main__":
    main()
