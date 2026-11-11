"""Kern gegen Handrechnung am Handbeispiel (DEMO-PLAYBOOK §1b): je Einheit eine Prüfung (Fortsetzung, Dominanzregel, Gedächtnis, Zählungen, Spaltenerzeugung),
dazu die Zahlen des Handbeispiels. Die Rechnungen stehen als Rechnung da; was nur das Ergebnis des Codes abschriebe, steht in `test_oracle_*` gegen einen anderen Weg."""

import random

import pytest

import epr_algorithm as A
import epr_colgen as G
import epr_constants as C
import epr_evaluation as ev
import epr_scenario as S
from conftest import HAND_TABLE, manhattan

EL = 7   # Kunden des Handbeispiels = Gedächtnis k für elementar


def test_scenario_matches_the_typed_table(hand):
    inst, pi = hand
    ref = S.hand_instance()
    assert (inst.n, inst.points, inst.d, inst.demand, inst.ready, inst.due) == (ref.n, ref.points, ref.d, ref.demand, ref.ready, ref.due)
    assert (inst.service, inst.horizon, inst.capacity) == (ref.service, ref.horizon, ref.capacity)
    assert tuple(S.hand_duals()) == pi == (0, 6, 6, 10, 6, 6, 6, 10)   # zweimal der Abstand zum Depot: 2 * 3, 2 * 3, 2 * 5, ...


def test_distances_are_the_manhattan_distances(hand):
    inst, _ = hand
    assert inst.d[0][1] == 1 + 2 and inst.d[0][3] == 3 + 2 and inst.d[6][7] == 1 + 1 and inst.d[3][7] == 6 + 4
    assert all(inst.d[i][j] == inst.d[j][i] == manhattan(HAND_TABLE[i][0], HAND_TABLE[j][0]) for i in range(8) for j in range(8))


def test_extend_by_hand_calculation(hand):
    """Weg 0-5-3: Kunde 5 liegt 3 vom Depot (Fenster [3, 12]: Ankunft 3, Beginn 3), Kosten 3 - 6 = -3, Last 1;
    dann 5 nach 3: Ankunft 3 + Bedienzeit 2 + Abstand 2 = 7 (Fenster [5, 15]: Beginn 7), Kosten -3 + 2 - 10 = -11, Last 1 + 3 = 4."""
    inst, pi = hand
    ng = A.ng_masks(inst, EL)
    start = A.Label(0, 0, 0, 0, 0, -1)
    l5 = A.extend(inst, pi, ng, start, 0, 5)
    assert (l5.time, l5.cost, l5.load, l5.node, l5.mem) == (3, 3 - 6, 1, 5, 1 << 5)
    l53 = A.extend(inst, pi, ng, l5, 1, 3)
    assert (l53.time, l53.cost, l53.load, l53.mem) == (3 + 2 + 2, -3 + 2 - 10, 1 + 3, (1 << 5) | (1 << 3))


def test_extend_waits_before_the_window_and_rejects_violations(hand):
    inst, pi = hand
    ng = A.ng_masks(inst, EL)
    start = A.Label(0, 0, 0, 0, 0, -1)
    assert A.extend(inst, pi, ng, start, 0, 1).time == 18          # Kunde 1: Ankunft 3, Fenster beginnt bei 18: warten bis 18
    l2 = A.extend(inst, pi, ng, start, 0, 2)
    assert A.extend(inst, pi, ng, l2, 1, 2) is None                 # derselbe Kunde direkt noch einmal
    too_heavy = A.Label(10, 0, 5, 1 << 1, 1, 0)
    assert A.extend(inst, pi, ng, too_heavy, 1, 2) is None          # Last 5 + 3 > 6
    too_late = A.Label(30, 0, 0, 1 << 1, 1, 0)
    assert A.extend(inst, pi, ng, too_late, 1, 5) is None           # Ankunft 30 + 2 + 4 = 36 > Fensterende 12
    assert A.extend(inst, pi, ng, A.Label(3, 0, 1, 1 << 5, 5, 0), 1, 5) is None


def test_relation_distinguishes_dominates_blocked_and_no():
    new = A.Label(10, -5, 3, 0b0110, 4, 0)
    assert A.relation(A.Label(10, -5, 3, 0b0010, 4, 0), new) == A.DOMINATES      # alles gleich oder besser, Menge {1} liegt in {1,2}: der Gleichstand dominiert
    assert A.relation(A.Label(9, -6, 2, 0b0100, 4, 0), new) == A.DOMINATES
    assert A.relation(A.Label(9, -6, 2, 0b1000, 4, 0), new) == A.BLOCKED         # Kosten, Zeit, Last reichen, Menge {3} liegt nicht in {1,2}
    assert A.relation(A.Label(9, -6, 2, 0b1000, 4, 0), new, use_set=False) == A.DOMINATES
    assert A.relation(A.Label(11, -6, 2, 0b0010, 4, 0), new) == A.NO              # später
    assert A.relation(A.Label(9, -4, 2, 0b0010, 4, 0), new) == A.NO               # teurer
    assert A.relation(A.Label(9, -6, 4, 0b0010, 4, 0), new) == A.NO               # mehr Last
    assert A.conditions(A.Label(9, -6, 4, 0b1000, 4, 0), new) == {"Kosten": True, "Zeit": True, "Last": False, "Besuchsmenge": False}


def test_ng_masks_of_the_hand_example(hand):
    inst, _ = hand
    assert A.ng_masks(inst, 1) == [0] + [1 << j for j in range(1, 8)]                       # k = 1: nur der Kunde selbst
    assert A.ng_masks(inst, EL) == [0] + [sum(1 << i for i in range(1, 8))] * 7             # elementar: alle
    assert A.ng_masks(inst, 99) == A.ng_masks(inst, EL)                                      # k wird auf n begrenzt
    # k = 2 für Kunde 1: Abstände von Kunde 1: zu 2 ist 2, zu 4, 5, 6, 7 je 4; die zwei nächsten sind 1 selbst und 2
    assert A.ng_masks(inst, 2)[1] == (1 << 1) | (1 << 2)
    # k = 3 für Kunde 1: dazu der Kunde mit dem kleinsten Abstand unter den Gleichständen (kleinere Nummer: 4)
    assert A.ng_masks(inst, 3)[1] == (1 << 1) | (1 << 2) | (1 << 4)


def test_first_round_elementary_counts_of_the_hand_example(hand):
    inst, pi = hand
    r = A.price(inst, pi, EL, "voll", trace=True)
    assert (r.generated, r.discarded, r.displaced, r.alive) == (56, 20, 0, 36)
    assert r.dominated == 20 and r.blocked == 34
    assert (r.value, r.route) == (-10, (2, 7, 6))
    assert sum(ev_.blocked for ev_ in r.events) == r.blocked
    assert sum(1 for ev_ in r.events if ev_.kind == "verworfen") == 20 and sum(1 for ev_ in r.events if ev_.kind == "bleibt") == 35
    assert len(A.standing_pairs(r)) == 31


def test_best_route_by_hand_calculation(hand):
    """Weg 2-7-6: 0 nach 2: Abstand 3, Ankunft 3 (Fenster [3, 16]), Last 3, Kosten 3 - 6 = -3; 2 nach 7: Abstand 4, Ankunft 3 + 2 + 4 = 9 (Fenster [8, 20]), Last 5,
    Kosten -3 + 4 - 10 = -9; 7 nach 6: Abstand 2, Ankunft 9 + 2 + 2 = 13 (Fenster [11, 21]), Last 6, Kosten -9 + 2 - 6 = -13; zurück ins Depot: 13 + 2 + 3 = 18 <= 38,
    reduzierte Kosten -13 + 3 = -10."""
    inst, pi = hand
    assert A.route_value(inst, pi, (2, 7, 6)) == (3 - 6) + (4 - 10) + (2 - 6) + 3 == -10


def test_other_memories_of_the_hand_example(hand):
    inst, pi = hand
    expected = {1: (62, 30, 0, -18, (7, 6, 7, 6)), 2: (58, 28, 5, -14, (5, 3, 5, 1)), 3: (55, 27, 7, -10, (2, 7, 6)), EL: (56, 36, 34, -10, (2, 7, 6))}
    for k, (generated, alive, blocked, value, route) in expected.items():
        r = A.price(inst, pi, k, "voll")
        assert (r.generated, r.alive, r.blocked, r.value, r.route) == (generated, alive, blocked, value, route), k
        assert A.walk_value(inst, pi, r.route) == r.value   # der unabhängige Prüfer bewertet die Route wie das Verfahren (Kreise erlaubt)
    assert A.route_value(inst, pi, (7, 6, 7, 6)) is None     # nicht elementar
    assert A.walk_value(inst, pi, (7, 6, 7, 6)) == (5 - 10) + (2 - 6) + (2 - 10) + (2 - 6) + 3 == -18


def test_best_by_enumeration_counts_79_routes(hand):
    inst, pi = hand
    assert A.best_by_enumeration(inst, pi) == (-10, (2, 7, 6), 79)
    assert A.best_by_enumeration(inst, S.HAND_DUALS_B) == (-11, (3, 6, 7), 79)
    assert A.best_by_enumeration(inst, (0,) * 8)[:2] == (0, ())                # Dualpreise 0: nichts lohnt sich


def test_dominance_without_the_set_loses_the_best_route_with_duals_b(hand):
    """Mit Dualpreisen B = (2, 4, 13, 4, 2, 5, 13): bester Weg 3-6-7: 0 nach 3: 5 - 13 = -8; 3 nach 6: 8 - 5 = 3 gibt -5; 6 nach 7: 2 - 13 = -11 gibt -16; zurück 5 gibt -11."""
    inst, _ = hand
    pb = S.HAND_DUALS_B
    assert A.route_value(inst, pb, (3, 6, 7)) == (5 - 13) + (8 - 5) + (2 - 13) + 5 == -11
    right = A.price(inst, pb, EL, "voll")
    wrong = A.price(inst, pb, EL, "ohne_menge", trace=True)
    assert (right.value, right.route) == (-11, (3, 6, 7))
    assert (wrong.value, wrong.route) == (-10, (2, 7, 6))
    assert wrong.blocked == 0                                                     # ohne Mengenbedingung scheitert nichts an der Menge (sie wird nicht geprüft)
    assert (wrong.generated, wrong.discarded, wrong.displaced) == (52, 22, 9)      # Zählung des Kerns; die unabhängige Nachzählung steht in test_oracle_*
    nm = ev.analyse_nomem(S.HAND_DUALS_B[1:])
    assert nm.misses and nm.loss is not None and nm.loss.prefix == (3, 6)
    # das verlorene Label hat die Menge {3,6}, das streichende {6,7}: 3 liegt nicht in {6,7}, und der nächste Halt 7 ist beim streichenden schon besucht
    lost, winner = nm.wrong.labels[nm.loss.lost], nm.wrong.labels[nm.loss.dominator]
    assert lost.mem == (1 << 3) | (1 << 6) and winner.mem == (1 << 6) | (1 << 7)


def test_dominance_without_the_set_hits_with_the_duals_of_round_one(hand):
    inst, pi = hand
    wrong = A.price(inst, pi, EL, "ohne_menge")
    assert (wrong.value, wrong.route, wrong.generated, wrong.alive) == (-10, (2, 7, 6), 54, 23)


def test_search_over_3000_dual_sets_finds_exactly_one_miss():
    assert ev.search_counterexamples() == [(1778, (2, 4, 13, 4, 2, 5, 13))]
    rng = random.Random(1778)
    assert tuple(rng.randint(2, 14) for _ in range(7)) == S.HAND_DUALS_B[1:]


SUBNETS = {
    "A": {"elementar": [4, 8, 13, 24, 35, 56], "uebrig": [4, 6, 10, 17, 22, 36], "ohne": [4, 8, 13, 26, 48, 80], "k1": [4, 8, 13, 26, 37, 62], "wege": [3, 7, 12, 25, 47, 79],
          "wert": [-4, -4, -6, -8, -8, -10]},
    "B": {"elementar": [5, 14, 41, 127, 333, 962], "uebrig": [5, 10, 25, 63, 137, 342], "ohne": [5, 16, 65, 326, 1957, 13604], "k1": [29, 73, 345, 545, 798, 1061],
          "wege": [4, 15, 64, 325, 1956, 13603], "wert": [-4, -6, -12, -18, -20, -28]},
}


@pytest.mark.parametrize("variant", ["A", "B"])
def test_subnet_tables_of_the_hand_example(variant):
    rows = ev.subnet_rows(variant)
    want = SUBNETS[variant]
    assert [r["m"] for r in rows] == [2, 3, 4, 5, 6, 7]
    assert [r["elementar"] for r in rows] == want["elementar"] and [r["uebrig"] for r in rows] == want["uebrig"]
    assert [r["ohne_dominanz"] for r in rows] == want["ohne"] and [r["k1"] for r in rows] == want["k1"]
    assert [r["wege"] for r in rows] == want["wege"] and [r["wert"] for r in rows] == want["wert"]
    assert rows[0]["faktor"] is None and rows[1]["faktor"] == pytest.approx(want["elementar"][1] / want["elementar"][0])


def test_variant_b_has_no_load_limit_and_wide_windows():
    sub = S.hand_subnet(7, "B")
    assert sub.capacity == 99 and sub.horizon == 60 and sub.ready == (0,) * 8
    assert all(sub.due[j] == 60 - 2 - sub.d[0][j] for j in range(1, 8))
    with pytest.raises(ValueError):
        S.hand_subnet(3, "C")


def test_column_generation_of_the_hand_example_with_the_exact_master():
    inst = S.hand_instance()
    cg = G.colgen(inst, EL)
    assert cg.bound == 30 and len(cg.rounds) == 7 and cg.labels == 326
    assert [r.generated for r in cg.rounds] == [56, 51, 45, 41, 42, 44, 47] and sum(r.generated for r in cg.rounds) == 326
    assert [r.master_value for r in cg.rounds] == [50, 40, 32, 32, 32, 30, 30]
    assert [r.best_route for r in cg.rounds] == [(2, 7, 6), (5, 3, 1), (2, 1), (3, 4), (5, 4, 1), (6, 7, 1), ()]
    assert [r.best_value for r in cg.rounds] == [-10, -8, -4, -4, -4, -4, 0]
    assert cg.rounds[0].duals == (6, 6, 10, 6, 6, 6, 10) and cg.rounds[1].duals == (6, 6, 10, 6, 6, 6, 0) and cg.rounds[-1].duals == (4, 4, 6, 4, 4, 6, 2)
    # Gegenprobe: ein Master über alle 79 elementaren Routen
    assert G.bound_over_all_routes(inst) == (30, 79)


def test_exact_master_on_a_tiny_example_by_hand():
    """Zwei Kunden, Spalten (1), (2), (1,2): Kosten der Einzelfahrten 2 * Abstand. Master: jeder Kunde mindestens einmal."""
    inst = S.Instance(2, ((0, 0), (1, 0), (0, 2)), ((0, 1, 2), (1, 0, 3), (2, 3, 0)), (0, 1, 1), (0, 0, 0), (50, 50, 50), 1, 50, 5)
    pi, value, x = G.solve_master(inst, [(1,), (2,), (1, 2)])
    # Kosten: (1) = 2, (2) = 4, (1,2) = 1 + 3 + 2 = 6; die Einzelfahrten zusammen kosten 6, die Doppeltour auch 6: der Wert ist 6.
    assert value == 6 and pi[1] + pi[2] == 6 and pi[1] <= 2 and pi[2] <= 4 and pi[1] + pi[2] <= 6
    assert sum(c * xi for c, xi in zip((2, 4, 6), x)) == 6


def test_time_limit_and_budgets_abort(hand):
    inst, pi = hand
    assert A.price(inst, pi, EL, "voll", time_limit=-1.0).aborted                       # die Zeitgrenze ist schon überschritten
    r = A.price(inst, pi, EL, "voll", max_labels=10)
    assert r.aborted and 10 <= r.generated <= 10 + inst.n
    r = A.price(inst, pi, EL, "voll", max_comps=100)
    assert r.aborted and r.comps >= 100
    full = A.price(inst, pi, EL, "voll", max_comps=10 ** 9, max_labels=10 ** 9, time_limit=60.0)
    assert not full.aborted and full.generated == 56


def test_no_dominance_generates_every_partial_route(hand):
    """Ohne Dominanz entsteht jedes zulässige Teilstück als Label; im Handbeispiel sind das 79 Anfänge (jeder kann ins Depot zurück) plus das Start-Label.
    Die unabhängige Zählung der Anfänge steht in test_oracle_*."""
    inst, pi = hand
    none = A.price(inst, pi, EL, "keine")
    assert none.generated == 79 + 1 == 80 and none.comps == 0 and none.dominated == 0


def test_unknown_dominance_is_rejected(hand):
    inst, pi = hand
    with pytest.raises(ValueError):
        A.price(inst, pi, EL, "nur_kosten")


def test_route_checkers_reject_wrong_routes(hand):
    inst, pi = hand
    assert A.route_value(inst, pi, ()) == 0
    assert A.route_value(inst, pi, (2, 2)) is None                 # doppelt
    assert A.route_value(inst, pi, (0,)) is None and A.route_value(inst, pi, (8,)) is None   # kein Kunde
    assert A.route_value(inst, pi, (3, 4)) == (5 - 10) + (2 - 6) + 3 == -6     # Last 3 + 3 = 6 geht; Kunde 4 öffnet erst bei 20, Ankunft 5 + 2 + 2 = 9: warten; zurück 20 + 2 + 3 = 25 <= 38
    assert A.route_value(inst, pi, (2, 3, 4)) is None              # Last 3 + 3 + 3 = 9 > 6
    assert A.route_value(inst, pi, (1, 3)) is None                 # Kunde 3 schließt bei 15, nach Kunde 1 (Beginn 18) zu spät
    assert A.walk_value(inst, pi, (2, 2)) is None                  # derselbe Kunde direkt hintereinander ist auch mit Kreisen verboten


def test_make_instance_is_deterministic_and_restrict_keeps_the_first_customers():
    a, b = S.make_instance(12, 3, 100), S.make_instance(12, 3, 100)
    assert a == b and a != S.make_instance(12, 4, 100)
    sub = S.restrict(a, 5)
    assert sub.n == 5 and sub.d[2][3] == a.d[2][3] and sub.demand == a.demand[:6] and sub.due == a.due[:6]
    with pytest.raises(ValueError):
        S.restrict(a, 13)
    with pytest.raises(ValueError):
        S.restrict(a, 0)
    assert all(a.ready[i] <= a.due[i] for i in range(1, 13))
    assert S.first_round_duals(a)[3] == 2 * a.d[0][3]


def test_size_experiment_counts_for_two_random_instances():
    """Zählungen des Kerns an festen Zufalls-Seeds: ein Pricing-Aufruf mit den Dualpreisen der ersten Runde, Fensterbreite 100."""
    s = ev.size_experiment(10, 100, 0)
    assert (s.elementary.generated, s.elementary.comps, s.k1.generated, s.none.generated) == (634, 47529, 421, 772)
    assert not s.elementary.aborted and not s.none.aborted
    s = ev.size_experiment(20, 100, 1)
    assert (s.elementary.generated, s.elementary.comps, s.k1.generated, s.none.generated) == (5844, 2000502, 1761, 7542) and not s.elementary.aborted
    s = ev.size_experiment(20, 100, 0)
    assert s.elementary.aborted and s.elementary.comps >= C.MAX_COMPS and s.elementary.generated == 11754
