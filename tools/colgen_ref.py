"""Spaltenerzeugung (Überdeckungs-Master, scipy/HiGHS) für Messreihen, Tests und Werkzeuge: nicht für die App (braucht scipy).

Master: Kosten der Routen minimieren, jeder Kunde mindestens einmal überdeckt (LP, HiGHS). Die Dualpreise des Masters gehen als Kundenpreise in das
Label-Verfahren der Demo (`epr_algorithm.price`); neue Routen mit negativen reduzierten Kosten (bis zu 15 je Runde) werden als Spalten ergänzt, bis keine
neue mehr kommt. Das Ergebnis ist die Schranke des Masters. Bricht das Preisproblem an seiner Zeitgrenze ab (`time_limit_price`, Sekunden je Aufruf)
oder die ganze Spaltenerzeugung an `time_limit_total`, ist `aborted` wahr und `bound` None; `abort_round` nennt die Runde (1 = der erste Aufruf mit den
Dualpreisen der Einzelfahrten)."""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import epr_algorithm as A  # noqa: E402


def route_cost(inst, route) -> float:
    seq = (0,) + tuple(route) + (0,)
    return sum(inst.d[a][b] for a, b in zip(seq, seq[1:]))


def colgen(inst, k: int, dominance: str = "voll", max_iter: int = 400, time_limit_price: float | None = None,
           time_limit_total: float | None = None) -> dict:
    """Schranke, Runden, Spalten, erzeugte und gestrichene Labels, Dominanzvergleiche und Abbruch der Spaltenerzeugung."""
    from scipy.optimize import linprog

    n = inst.n
    cols = [(i,) for i in range(1, n + 1)]
    costs = [route_cost(inst, r) for r in cols]
    totals = {"generated": 0, "dominated": 0, "comps": 0, "blocked": 0}
    bound = None
    rounds = 0
    started = time.perf_counter()
    first = None
    while rounds < max_iter:
        rounds += 1
        matrix = np.zeros((n, len(cols)))
        for c, route in enumerate(cols):
            for i in route:
                matrix[i - 1, c] += 1
        res = linprog(costs, A_ub=-matrix, b_ub=-np.ones(n), bounds=(0, None), method="highs")
        pi = (0.0,) + tuple(-res.ineqlin.marginals)
        bound = res.fun
        result = A.price(inst, pi, k, dominance, time_limit=time_limit_price)
        for key, value in (("generated", result.generated), ("dominated", result.dominated), ("comps", result.comps), ("blocked", result.blocked)):
            totals[key] += value
        if first is None:
            first = {"generated": result.generated, "comps": result.comps, "aborted": result.aborted}
        timed_out = time_limit_total is not None and time.perf_counter() - started > time_limit_total
        if result.aborted or timed_out:
            return {"bound": None, "iterations": rounds, "columns": len(cols), "aborted": True, "abort_round": rounds, "first_call": first, **totals}
        known = set(cols)
        fresh = [route for _, route in A.routes_of(result, 15) if route not in known]
        if not fresh:
            break
        for route in fresh:
            cols.append(route)
            costs.append(route_cost(inst, route))
    return {"bound": bound, "iterations": rounds, "columns": len(cols), "aborted": False, "abort_round": None, "first_call": first, **totals}
