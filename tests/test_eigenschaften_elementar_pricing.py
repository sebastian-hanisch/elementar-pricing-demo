"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen über das Verfahren, die ohne bekanntes Ergebnis gelten müssen.

- Umnummerieren der Kunden ändert den besten Wert der elementaren Rechnung nicht.
- Alle Längen, Zeiten, Fenster, Bedienzeiten und Dualpreise mit demselben Faktor 2 multipliziert: dieselbe Route, doppelter Wert, gleiche Zählungen.
- Mit Dominanz entstehen nie mehr Labels als ohne; „keine“ und „volle Dominanz“ liefern denselben besten Wert (Streichen eines dominierten Labels ändert nie den besten Wert).
- Je kleiner das Gedächtnis, desto besser (oder gleich) der beste Wert: k = 1 <= k = 2 <= k = 3 <= elementar (die Nachbarschaften sind ineinander enthalten).
- Eine zusätzliche Option (ein weiterer Kunde) verschlechtert den besten Wert nie.
- Gleicher Eingang, gleiches Ergebnis."""

import random

import pytest

import epr_algorithm as A
import epr_scenario as S
from epr_scenario import Instance


def _cases(count=30, n=7):
    for seed in range(count):
        width = (40, 100, 200)[seed % 3]
        rng = random.Random(seed)
        pi = (0.0,) + tuple(rng.uniform(20, 70) for _ in range(n))
        yield seed, S.make_instance(n, seed + 700, width), pi


def _permute(inst, pi, perm):
    """Kunde i heißt danach perm[i] (perm ist eine Permutation von 1..n, perm[0] = 0 für das Depot)."""
    n = inst.n
    inv = [0] * (n + 1)
    for old, new in enumerate(perm):
        inv[new] = old

    def pick(values):
        return tuple(values[inv[new]] for new in range(n + 1))

    d = tuple(tuple(inst.d[inv[a]][inv[b]] for b in range(n + 1)) for a in range(n + 1))
    return Instance(n, pick(inst.points), d, pick(inst.demand), pick(inst.ready), pick(inst.due), inst.service, inst.horizon, inst.capacity), pick(pi)


def _undo(route, perm):
    inv = {new: old for old, new in enumerate(perm)}
    return tuple(inv[j] for j in route)


def test_renumbering_customers_does_not_change_the_elementary_result():
    rng = random.Random(3)
    for seed, inst, pi in _cases():
        perm = [0] + rng.sample(range(1, inst.n + 1), inst.n)
        inst2, pi2 = _permute(inst, pi, perm)
        a = A.price(inst, pi, inst.n, "voll")
        b = A.price(inst2, pi2, inst2.n, "voll")
        assert b.value == pytest.approx(a.value, abs=1e-9), seed
        if b.route:
            assert A.route_value(inst, pi, _undo(b.route, perm)) == pytest.approx(a.value, abs=1e-9), seed
        else:
            assert a.value == 0, seed


def test_scaling_all_lengths_times_and_duals_by_two_doubles_the_value_and_keeps_the_route():
    for seed, inst, pi in _cases(20, 6):
        big = Instance(inst.n, inst.points, tuple(tuple(2 * x for x in row) for row in inst.d), inst.demand, tuple(2 * x for x in inst.ready),
                       tuple(2 * x for x in inst.due), 2 * inst.service, 2 * inst.horizon, inst.capacity)
        a = A.price(inst, pi, inst.n, "voll")
        b = A.price(big, tuple(2 * x for x in pi), big.n, "voll")
        assert b.value == pytest.approx(2 * a.value, abs=1e-8) and b.route == a.route, seed
        assert (b.generated, b.discarded, b.displaced, b.comps, b.blocked) == (a.generated, a.discarded, a.displaced, a.comps, a.blocked), seed


def test_dominance_never_creates_more_labels_and_never_changes_the_best_value():
    for seed, inst, pi in _cases(30, 7):
        with_dom = A.price(inst, pi, inst.n, "voll")
        without = A.price(inst, pi, inst.n, "keine")
        assert with_dom.generated <= without.generated, seed
        assert with_dom.value == pytest.approx(without.value, abs=1e-9), seed


def test_a_smaller_memory_never_makes_the_best_value_worse_and_elementary_is_the_largest():
    for seed, inst, pi in _cases(30, 6):
        values = [A.price(inst, pi, k, "voll").value for k in (1, 2, 3, inst.n)]
        assert all(a <= b + 1e-9 for a, b in zip(values, values[1:])), (seed, values)


def test_an_additional_customer_never_worsens_the_best_value():
    for seed in range(20):
        big = S.make_instance(7, seed + 900, (40, 100)[seed % 2])
        rng = random.Random(seed)
        pi = (0.0,) + tuple(rng.uniform(20, 70) for _ in range(7))
        small = S.restrict(big, 6)
        assert A.price(big, pi, 7, "voll").value <= A.price(small, pi[:7], 6, "voll").value + 1e-9, seed


def test_the_same_input_gives_the_same_result():
    for seed, inst, pi in _cases(5, 7):
        a, b = A.price(inst, pi, inst.n, "voll", trace=True), A.price(inst, pi, inst.n, "voll", trace=True)
        assert a == b


def test_every_route_of_a_run_is_elementary_feasible_and_correctly_valued():
    for seed, inst, pi in _cases(20, 7):
        res = A.price(inst, pi, inst.n, "voll")
        for rc, route in A.routes_of(res, 100):
            assert len(set(route)) == len(route)
            assert A.route_value(inst, pi, route) == pytest.approx(rc, abs=1e-9)
