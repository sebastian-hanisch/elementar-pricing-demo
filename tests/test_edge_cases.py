"""Randfälle des Label-Verfahrens (DEMO-PLAYBOOK §12): n = 1, n = 2, Gleichstand, inklusive Grenzen, leere Route, Abbruch, Gedächtnis größer als n."""

import pytest

import epr_algorithm as A
import epr_scenario as S
from epr_scenario import Instance


def _line_instance(n, dist=5.0, due=100.0, demand=5, capacity=70, horizon=300.0, ready=0.0, service=10.0):
    """Kunden auf einer Linie im Abstand `dist`; Fenster [ready, due]."""
    pts = [(float(i) * dist, 0.0) for i in range(n + 1)]
    d = tuple(tuple(abs(a[0] - b[0]) for b in pts) for a in pts)
    return Instance(n, tuple(pts), d, (0,) + (demand,) * n, (0.0,) + (ready,) * n, (horizon,) + (due,) * n, service, horizon, capacity)


def test_one_customer():
    inst = _line_instance(1)
    pi = (0.0, 20.0)
    res = A.price(inst, pi, 1, "voll")
    assert res.route == (1,) and res.value == pytest.approx(5 + 5 - 20)       # 0-1-0: Abstand 5 hin, 5 zurück, Dualpreis 20
    assert res.generated == 2 and res.dominated == 0 and res.comps == 0 and res.blocked == 0
    assert A.price(inst, pi, 7, "voll").generated == 2                        # k größer als n wird auf n begrenzt
    assert A.best_by_enumeration(inst, pi) == (pytest.approx(-10), (1,), 1)


def test_exactly_two_customers_and_the_comparisons_between_them():
    inst = _line_instance(2)
    pi = (0.0, 20.0, 20.0)
    for mode in ("keine", "ohne_menge", "voll"):
        res = A.price(inst, pi, 2, mode)
        assert res.route == (1, 2) and res.value == pytest.approx(5 + 5 + 10 - 40)    # Weg 0-1-2-0: 5 + 5 + 10, Dualpreise 20 + 20
    full = A.price(inst, pi, 2, "voll")
    assert full.generated == 5      # Start, 1, 2, 1-2, 2-1: kein Label wird gestrichen (die Wege 1-2 und 2-1 enden an verschiedenen Kunden)
    assert full.dominated == 0 and A.standing_pairs(full) == []


def test_two_customers_at_the_same_place():
    """Abstand 0 zwischen Kunde 1 und 2: beide Reihenfolgen kosten gleich; das Label des später erzeugten Weges bleibt nicht, wenn es dominiert wird."""
    pts = ((0.0, 0.0), (5.0, 0.0), (5.0, 0.0))
    d = tuple(tuple(abs(a[0] - b[0]) for b in pts) for a in pts)
    inst = Instance(2, pts, d, (0, 5, 5), (0.0,) * 3, (300.0,) * 3, 10.0, 300.0, 70)
    res = A.price(inst, (0.0, 20.0, 20.0), 2, "voll")
    assert res.value == pytest.approx(5 + 0 + 5 - 40) and res.route in ((1, 2), (2, 1))
    assert res.route == (1, 2)       # Gleichstand: das zuerst gefundene (kleinere Reihenfolge) wird gewählt


def test_all_duals_zero_means_no_route_pays():
    inst = _line_instance(3)
    res = A.price(inst, (0.0,) * 4, 3, "voll")
    assert res.route == () and res.value == 0 and A.routes_of(res) == []
    assert A.best_by_enumeration(inst, (0.0,) * 4)[:2] == (0, ())


def test_load_equal_to_capacity_allows_one_customer_per_route_and_the_limit_is_inclusive():
    inst = _line_instance(3, demand=70, capacity=70)
    res = A.price(inst, (0.0, 40.0, 40.0, 40.0), 3, "voll")
    assert res.generated == 4 and len(A.routes_of(res)) == 3 and all(len(r) == 1 for _, r in A.routes_of(res))
    assert A.route_value(inst, (0.0, 40.0, 40.0, 40.0), (1, 2)) is None       # Last 140 > 70
    inst2 = _line_instance(3, demand=35, capacity=70)
    assert A.route_value(inst2, (0.0, 30.0, 30.0, 30.0), (1, 2)) is not None   # Last 70 = Kapazität: erlaubt
    assert A.route_value(inst2, (0.0, 30.0, 30.0, 30.0), (1, 2, 3)) is None


def test_windows_so_narrow_that_every_route_has_one_customer():
    """Fenster [kürzester Abstand, kürzester Abstand]: nach Kunde 1 ist Kunde 2 nie mehr rechtzeitig."""
    pts = ((0.0, 0.0), (10.0, 0.0), (20.0, 0.0), (30.0, 0.0))
    d = tuple(tuple(abs(a[0] - b[0]) for b in pts) for a in pts)
    inst = Instance(3, pts, d, (0, 5, 5, 5), (0.0, 10.0, 20.0, 30.0), (300.0, 10.0, 20.0, 30.0), 10.0, 300.0, 70)
    res = A.price(inst, (0.0, 50.0, 50.0, 50.0), 3, "voll")
    assert A.best_by_enumeration(inst, (0.0, 50.0, 50.0, 50.0))[2] == 3    # nur die drei Einzelfahrten
    assert res.generated == 4


def test_arrival_exactly_at_window_end_and_return_exactly_at_horizon_are_allowed():
    inst = _line_instance(1, dist=5.0, due=5.0, horizon=20.0)          # Ankunft 5 = Fensterende; Rückkehr 5 + 10 + 5 = 20 = Horizont
    assert A.route_value(inst, (0.0, 30.0), (1,)) == pytest.approx(10 - 30)
    late = _line_instance(1, dist=5.0, due=5.0, horizon=19.9)
    assert A.route_value(late, (0.0, 30.0), (1,)) is None
    early = _line_instance(1, dist=5.0, due=4.9)
    assert A.route_value(early, (0.0, 30.0), (1,)) is None


def test_ties_the_older_label_stays():
    """Zwei gleiche Labels am Kunden 3 (Wege 1-3 und 2-3 mit gleicher Zeit, Kosten, Last, aber verschiedener Menge): bei gleicher Menge bleibt das ältere."""
    d = ((0.0, 5.0, 5.0, 10.0), (5.0, 0.0, 100.0, 5.0), (5.0, 100.0, 0.0, 5.0), (10.0, 5.0, 5.0, 0.0))
    inst = Instance(3, ((0.0, 0.0),) * 4, d, (0, 5, 5, 5), (0.0,) * 4, (300.0,) * 4, 10.0, 300.0, 70)
    pi = (0.0, 20.0, 20.0, 20.0)
    # mit Menge: {1,3} und {2,3} sind unvergleichbar, beide Labels bleiben, am Ende stehen sie als Paar nebeneinander
    full = A.price(inst, pi, 3, "voll", trace=True)
    at3 = [i for i, lab in enumerate(full.labels) if lab.node == 3 and not full.dead[i] and len(A.route_of(full.labels, i)) == 2]
    assert sorted(A.route_of(full.labels, i) for i in at3) == [(1, 3), (2, 3)]
    assert len(A.standing_pairs(full)) >= 2
    # ohne Menge: gleiche Kosten, Zeit und Last, das ältere (über Kunde 1) bleibt, das jüngere wird verworfen
    wrong = A.price(inst, pi, 3, "ohne_menge", trace=True)
    at3 = [i for i, lab in enumerate(wrong.labels) if lab.node == 3 and not wrong.dead[i] and len(A.route_of(wrong.labels, i)) == 2]
    assert [A.route_of(wrong.labels, i) for i in at3] == [(1, 3)]


def test_abort_returns_a_partial_result_without_an_error(hand):
    inst, pi = hand
    r = A.price(inst, pi, 7, "voll", max_labels=1)
    assert r.aborted and r.generated >= 1 and r.value <= 0
    r0 = A.price(inst, pi, 7, "voll", max_comps=0)       # das Vergleichsbudget 0 ist erreicht, sobald das erste Label bleibt
    assert r0.aborted and r0.generated <= 1 + inst.n


def test_a_k1_run_never_blocks_on_the_set(hand):
    inst, pi = hand
    r = A.price(inst, pi, 1, "voll")
    assert r.blocked == 0 and A.standing_pairs(r) == []


def test_restrict_to_one_customer_and_the_subnet_with_two():
    sub = S.restrict(S.make_instance(6, 2, 100), 1)
    assert sub.n == 1 and A.price(sub, S.first_round_duals(sub), 1, "voll").generated >= 1
    assert S.hand_subnet(2, "A").n == 2 and S.hand_subnet(2, "A").capacity == 6
