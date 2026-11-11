"""Spaltenerzeugung mit genauem Master für das Handbeispiel (nur Standardbibliothek, Brüche statt Gleitkomma).

Master (Überdeckung): minimiere die Kosten der gewählten Routen, jeder Kunde mindestens einmal überdeckt. Gelöst wird sein Duales
    max sum(pi)   unter   A^T pi <= c,  pi >= 0
mit dem Simplex-Verfahren in Brüchen (Regel von Bland); das Ergebnis sind genaue Dualpreise, der Wert und die Mengen der Routen. So ist jede
Runde der Spaltenerzeugung am Handbeispiel von Hand nachrechenbar und reproduzierbar (kein Löser mit eigener Wahl unter gleich guten Dualpreisen).

Für große Instanzen (Messreihen) rechnet `tools/colgen_ref.py` den Master mit scipy (HiGHS); beide Wege werden in den Tests verglichen."""

from fractions import Fraction as Fr
from typing import NamedTuple

import epr_algorithm as A
from epr_scenario import Instance


def route_cost(inst: Instance, route) -> float:
    """Kosten (Weglänge) einer Route: vom Depot über die Kunden zurück ins Depot."""
    seq = (0,) + tuple(route) + (0,)
    return sum(inst.d[a][b] for a, b in zip(seq, seq[1:]))


def solve_master(inst: Instance, cols) -> tuple[list, Fr, list]:
    """Überdeckungs-Master über den Routen `cols`: (Dualpreise mit Index 0 für das Depot, Zielwert, Mengen der Routen), alles als Brüche."""
    n, m = inst.n, len(cols)
    tableau = []
    for r, route in enumerate(cols):
        row = [Fr(0)] * (n + m)
        for j in route:
            row[j - 1] += 1
        row[n + r] = Fr(1)
        tableau.append(row + [Fr(route_cost(inst, route))])
    obj = [Fr(1)] * n + [Fr(0)] * m + [Fr(0)]
    basis = [n + r for r in range(m)]
    while True:
        e = next((j for j in range(n + m) if obj[j] > 0), None)
        if e is None:
            break
        best = None
        for r in range(m):
            if tableau[r][e] > 0:
                key = (tableau[r][-1] / tableau[r][e], basis[r])
                if best is None or key < best[0]:
                    best = (key, r)
        if best is None:
            raise ValueError(f"Master unzulässig: Kunde {e + 1} wird von keiner Spalte überdeckt")
        r = best[1]
        piv = tableau[r][e]
        tableau[r] = [x / piv for x in tableau[r]]
        for i in range(m):
            if i != r and tableau[i][e] != 0:
                f = tableau[i][e]
                tableau[i] = [a - f * b for a, b in zip(tableau[i], tableau[r])]
        f = obj[e]
        obj = [a - f * b for a, b in zip(obj, tableau[r])]
        basis[r] = e
    pi = [Fr(0)] * (n + 1)
    for r, b in enumerate(basis):
        if b < n:
            pi[b + 1] = tableau[r][-1]
    x = [-obj[n + r] for r in range(m)]
    return pi, -obj[-1], x


class Round(NamedTuple):
    number: int
    master_value: Fr
    duals: tuple          # Dualpreise der Kunden 1..n
    best_route: tuple     # beste verbessernde Spalte, () wenn keine
    best_value: Fr        # ihre reduzierten Kosten (0, wenn keine)
    generated: int        # erzeugte Labels dieser Runde


class ColgenResult(NamedTuple):
    bound: Fr
    rounds: tuple
    columns: tuple
    labels: int           # erzeugte Labels über alle Runden


def colgen(inst: Instance, k: int, max_rounds: int = 200) -> ColgenResult:
    """Spaltenerzeugung mit genauem Master und elementarem (k = n) oder k-Gedächtnis-Pricing; je Runde kommt die beste Spalte hinzu (Gleichstand: die kleinere Folge)."""
    cols = [(j,) for j in range(1, inst.n + 1)]
    rounds = []
    for number in range(1, max_rounds + 1):
        pi, value, _ = solve_master(inst, cols)
        result = A.price(inst, pi, k, "voll")
        candidates = A.routes_of(result, 1)
        best_value, best_route = candidates[0] if candidates else (0, ())
        rounds.append(Round(number, value, tuple(pi[1:]), best_route, best_value, result.generated))
        if not candidates:
            break
        cols.append(best_route)
    return ColgenResult(rounds[-1].master_value, tuple(rounds), tuple(cols), sum(r.generated for r in rounds))


def bound_over_all_routes(inst: Instance) -> tuple[Fr, int]:
    """Bezug: ein Master über ALLE zulässigen elementaren Routen (Aufzählung): (Zielwert, Zahl der Routen). Muss gleich der Schranke der Spaltenerzeugung sein."""
    walks = [route for _, route, _ in A.enumerate_routes(inst, [0] * (inst.n + 1))]
    return solve_master(inst, walks)[1], len(walks)
