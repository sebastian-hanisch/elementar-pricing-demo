"""Orakel-Tests (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK §2 und §5): das Label-Verfahren gegen einen anderen Rechenweg, der nichts aus `epr_algorithm` benutzt.

Orakel 1: Aufzählung aller zulässigen Besuchsfolgen (Tiefensuche und, als zweiter Weg, Permutationen aller Teilmengen) mit eigener Bewertung: bester Wert und jede
          gelieferte Route des elementaren Verfahrens; Zahl der zulässigen Routen.
Orakel 2: das Verfahren mit Gedächtnis k < n gegen die Aufzählung aller Folgen, die die Gedächtnisregel erlaubt (ein Kunde darf wiederkehren, wenn zwischen den
          Besuchen ein Kunde lag, in dessen Nachbarschaft er nicht liegt).
Orakel 3: eine zweite, bewusst anders geschriebene Fassung des Label-Verfahrens (frozenset-Mengen, eigene Schleife) liefert dieselben Zählungen (erzeugte, verworfene, verdrängte
          Labels, Dominanzvergleiche, Prüfungen nur an der Menge), die Anfänge ohne Dominanz sind gleich den zulässigen Teilwegen (Aufzählung).
Orakel 4: der genaue Master (Brüche) gegen scipy/HiGHS; die Spaltenerzeugung gegen einen Master über alle Routen.
Alles zusammen läuft in wenigen Sekunden (Instanzen mit höchstens 8 Kunden)."""

import heapq
import itertools
import random
from fractions import Fraction

import pytest

import epr_algorithm as A
import epr_colgen as G
import epr_scenario as S
from conftest import build_hand

EPS = 1e-9


# --- Orakel 1: Aufzählung -------------------------------------------------------------------------------------------------------------------

def eval_route(inst, pi, route):
    """Eigene Bewertung einer Besuchsfolge (Kunden 1..n): reduzierte Kosten oder None, wenn Last, Fenster oder Horizont verletzt sind. Kreise sind hier erlaubt."""
    t, q, cost, prev = 0, 0, 0, 0
    for j in route:
        q += inst.demand[j]
        arrive = t + (inst.service if prev else 0) + inst.d[prev][j]
        if q > inst.capacity or arrive > inst.due[j] + EPS:
            return None
        t = max(arrive, inst.ready[j])
        cost += inst.d[prev][j] - pi[j]
        prev = j
    if t + inst.service + inst.d[prev][0] > inst.horizon:
        return None
    return cost + inst.d[prev][0]


def all_feasible_routes(inst, pi):
    """Zweiter Weg: Permutationen aller Teilmengen der Kunden (jeder höchstens einmal); {Route: reduzierte Kosten}."""
    found = {}
    customers = range(1, inst.n + 1)
    for size in range(1, inst.n + 1):
        for subset in itertools.combinations(customers, size):
            for perm in itertools.permutations(subset):
                rc = eval_route(inst, pi, perm)
                if rc is not None:
                    found[perm] = rc
    return found


def dfs_feasible_routes(inst, pi):
    """Erster Weg: Tiefensuche über Folgen mit Abbruch, sobald ein Teilweg unzulässig ist (anderer Aufbau als die Permutationen)."""
    found = {}

    def go(route):
        for j in range(1, inst.n + 1):
            if j in route:
                continue
            nxt = route + (j,)
            # ein Teilweg ist nur zulässig, wenn Last und Fenster bis j halten; die Rückkehr prüft eval_route am Ende
            t, q, prev = 0, 0, 0
            ok = True
            for x in nxt:
                q += inst.demand[x]
                arrive = t + (inst.service if prev else 0) + inst.d[prev][x]
                if q > inst.capacity or arrive > inst.due[x] + EPS:
                    ok = False
                    break
                t = max(arrive, inst.ready[x])
                prev = x
            if not ok:
                continue
            rc = eval_route(inst, pi, nxt)
            if rc is not None:
                found[nxt] = rc
            go(nxt)

    go(())
    return found


def random_cases(count, seed0=0):
    """Zufallsinstanzen mit 5 bis 7 Kunden, drei Fensterbreiten, zwei Arten von Dualpreisen (zufällig zwischen 20 und 70 und die der ersten Runde)."""
    cases = []
    for i in range(count):
        rng = random.Random(seed0 + i)
        n = rng.randint(5, 7)
        width = rng.choice([40, 100, 200])
        inst = S.make_instance(n, seed0 + i, width)
        pi = (0.0,) + tuple(rng.uniform(20, 70) for _ in range(n)) if i % 2 == 0 else S.first_round_duals(inst)
        cases.append((inst, pi))
    return cases


def test_the_two_enumerations_agree_and_count_79_routes_in_the_hand_example(hand):
    inst, pi = hand
    a, b = all_feasible_routes(inst, pi), dfs_feasible_routes(inst, pi)
    assert len(a) == 79 and a.keys() == b.keys()
    assert all(abs(a[r] - b[r]) < EPS for r in a)
    assert min(a.values()) == -10 and min(a, key=lambda r: (a[r], r)) == (2, 7, 6)
    assert len(A.enumerate_routes(inst, pi)) == 79


def test_elementary_pricing_equals_the_enumeration_on_random_instances():
    for inst, pi in random_cases(90):
        routes = all_feasible_routes(inst, pi)
        best = min(routes.values(), default=0)
        want = best if best < A.IMPROVING else 0
        res = A.price(inst, pi, inst.n, "voll")
        assert res.value == pytest.approx(want, abs=1e-7), (inst.n, inst.due[1])
        assert len(A.enumerate_routes(inst, pi)) == len(routes)
        assert A.best_by_enumeration(inst, pi)[0] == pytest.approx(want, abs=1e-7)
        # jede gelieferte Route ist elementar, zulässig und richtig bewertet (eigene Bewertung)
        for rc, route in A.routes_of(res, 50):
            assert len(set(route)) == len(route) and routes[route] == pytest.approx(rc, abs=1e-7)
        if res.route:
            assert routes[res.route] == pytest.approx(res.value, abs=1e-7)


def test_pricing_without_the_set_never_beats_the_enumeration_and_the_set_version_is_exact():
    """Ohne Menge können nur Routen verloren gehen (nie ein besserer Wert als die Aufzählung); mit Menge nie."""
    for inst, pi in random_cases(60, 500):
        routes = all_feasible_routes(inst, pi)
        best = min(routes.values(), default=0)
        want = best if best < A.IMPROVING else 0
        assert A.price(inst, pi, inst.n, "ohne_menge").value >= want - 1e-7
        assert A.price(inst, pi, inst.n, "voll").value == pytest.approx(want, abs=1e-7)


# --- Orakel 2: Gedächtnis k < n gegen Aufzählung der erlaubten Folgen ------------------------------------------------------------------------

def ng_sets(inst, k):
    """Nachbarschaft NG(j): die k nächsten Kunden von j einschließlich j (Gleichstand: kleinere Nummer), als Mengen."""
    out = {}
    for j in range(1, inst.n + 1):
        order = sorted(range(1, inst.n + 1), key=lambda i: (inst.d[j][i], i))
        out[j] = set(order[:k]) | {j}
    return out


def memory_allows(walk, ng):
    """Darf der letzte Kunde der Folge wiederkehren? Ja, wenn er noch nie vorkam oder zwischen den Besuchen ein Kunde lag, dessen Nachbarschaft ihn nicht enthält
    (und nicht der unmittelbar vorige Kunde ist)."""
    q = len(walk) - 1
    j = walk[q]
    for p in range(q - 1, -1, -1):
        if walk[p] == j:
            return q - p > 1 and any(j not in ng[walk[r]] for r in range(p + 1, q))
    return True


def best_walk_value(inst, pi, k, depth=60):
    """Beste reduzierte Kosten aller zulässigen Folgen, die die Gedächtnisregel k erlaubt. `depth` ist nur ein Sicherheitsnetz: Last (Kapazität) und Fenster
    beenden jede Folge viel früher; ein zu kleines `depth` schnitte lange Folgen ab (das fiel im Scratch-Lauf über 300 Instanzen bei depth = n + 2 auf)."""
    ng = ng_sets(inst, k)
    best = [0.0]

    def go(walk):
        rc = eval_route(inst, pi, walk) if walk else None
        if rc is not None and rc < best[0]:
            best[0] = rc
        if len(walk) >= depth:
            return
        for j in range(1, inst.n + 1):
            if walk and walk[-1] == j:
                continue
            nxt = walk + (j,)
            if not memory_allows(nxt, ng):
                continue
            t, q, prev, ok = 0, 0, 0, True
            for x in nxt:
                q += inst.demand[x]
                arrive = t + (inst.service if prev else 0) + inst.d[prev][x]
                if q > inst.capacity or arrive > inst.due[x] + EPS:
                    ok = False
                    break
                t = max(arrive, inst.ready[x])
                prev = x
            if ok:
                go(nxt)

    go(())
    return best[0]


def test_memory_k_pricing_equals_the_enumeration_of_allowed_walks():
    checked = 0
    for i in range(36):
        rng = random.Random(900 + i)
        n = rng.randint(4, 6)
        inst = S.make_instance(n, 900 + i, rng.choice([100, 200]))
        pi = S.first_round_duals(inst) if i % 2 else (0.0,) + tuple(rng.uniform(20, 70) for _ in range(n))
        for k in (1, 2, 3):
            want = best_walk_value(inst, pi, k)
            got = A.price(inst, pi, k, "voll").value
            assert got == pytest.approx(want, abs=1e-7), (i, k)
            checked += 1
    assert checked == 108


def test_memory_k_on_the_hand_example_matches_the_enumeration(hand):
    inst, pi = hand
    assert [round(best_walk_value(inst, pi, k), 9) for k in (1, 2, 3, 7)] == [-18, -14, -10, -10]


# --- Orakel 3: zweite Fassung des Label-Verfahrens -------------------------------------------------------------------------------------------

def reference_counts(inst, pi, k, mode):
    """Bewusst anders geschrieben: Mengen als frozenset, Labels als Dictionaries, eigene Schleife. Rückgabe (erzeugt, verworfen, verdrängt, Vergleiche, nur an der Menge gescheitert, bester Wert)."""
    ng = ng_sets(inst, k)
    labels = [{"t": 0, "c": 0, "q": 0, "m": frozenset(), "node": 0, "alive": True, "parent": -1}]
    at = {j: [] for j in range(1, inst.n + 1)}
    heap = [(0, 0)]
    discarded = displaced = comps = blocked = 0
    ended = []

    def rel(o, n_):
        if o["c"] > n_["c"] + EPS or o["t"] > n_["t"] + EPS or o["q"] > n_["q"]:
            return "no"
        if mode == "voll" and not o["m"] <= n_["m"]:
            return "blocked"
        return "dom"

    while heap:
        _, li = heapq.heappop(heap)
        cur = labels[li]
        if not cur["alive"]:
            continue
        i = cur["node"]
        if i and cur["t"] + inst.service + inst.d[i][0] <= inst.horizon:
            ended.append(cur["c"] + inst.d[i][0])
        for j in range(1, inst.n + 1):
            if j == i or j in cur["m"]:
                continue
            q = cur["q"] + inst.demand[j]
            arrive = cur["t"] + (inst.service if i else 0) + inst.d[i][j]
            if q > inst.capacity or arrive > inst.due[j] + EPS:
                continue
            new = {"t": max(arrive, inst.ready[j]), "c": cur["c"] + inst.d[i][j] - pi[j], "q": q, "m": (cur["m"] & ng[j]) | {j}, "node": j, "alive": True, "parent": li}
            labels.append(new)
            idx = len(labels) - 1
            if mode != "keine":
                gone = False
                own_blocked = 0
                for o in at[j]:
                    comps += 1
                    r = rel(labels[o], new)
                    if r == "dom":
                        gone = True
                        break
                    own_blocked += r == "blocked"
                if gone:
                    new["alive"] = False
                    discarded += 1
                    blocked += own_blocked
                    continue
                keep = []
                for o in at[j]:
                    comps += 1
                    r = rel(new, labels[o])
                    if r == "dom":
                        labels[o]["alive"] = False
                        displaced += 1
                    else:
                        own_blocked += r == "blocked"
                        keep.append(o)
                at[j] = keep
                blocked += own_blocked
            at[j].append(idx)
            heapq.heappush(heap, (new["t"], idx))
    best = min([x for x in ended if x < A.IMPROVING], default=0)
    return len(labels), discarded, displaced, comps, blocked, best


def test_second_implementation_gives_the_same_counts_on_the_hand_example(hand):
    inst, pi = hand
    for pis in (pi, S.HAND_DUALS_B):
        for k, mode in ((1, "voll"), (2, "voll"), (3, "voll"), (7, "voll"), (7, "ohne_menge"), (7, "keine")):
            r = A.price(inst, pis, k, mode)
            ref = reference_counts(inst, pis, k, mode)
            assert (r.generated, r.discarded, r.displaced, r.comps, r.blocked) == ref[:5], (k, mode)
            assert r.value == pytest.approx(ref[5], abs=1e-9)


def test_second_implementation_gives_the_same_counts_on_random_instances():
    for i in range(24):
        rng = random.Random(3000 + i)
        n = rng.randint(6, 8)
        inst = S.make_instance(n, 3000 + i, rng.choice([40, 100]))
        pi = S.first_round_duals(inst)
        for k, mode in ((n, "voll"), (1, "voll"), (3, "voll"), (n, "ohne_menge")):
            r = A.price(inst, pi, k, mode)
            ref = reference_counts(inst, pi, k, mode)
            assert (r.generated, r.discarded, r.displaced, r.comps, r.blocked) == ref[:5], (i, k, mode)


def test_without_dominance_every_feasible_partial_route_becomes_a_label():
    """Ohne Dominanz entsteht ein Label je zulässigem Teilweg (Last, Fenster) plus das Start-Label; die Zahl der Teilwege kommt aus der Aufzählung."""
    for inst, pi in random_cases(30, 700):
        prefixes = 0
        for size in range(1, inst.n + 1):
            for subset in itertools.combinations(range(1, inst.n + 1), size):
                for perm in itertools.permutations(subset):
                    t, q, prev, ok = 0, 0, 0, True
                    for x in perm:
                        q += inst.demand[x]
                        arrive = t + (inst.service if prev else 0) + inst.d[prev][x]
                        if q > inst.capacity or arrive > inst.due[x] + EPS:
                            ok = False
                            break
                        t = max(arrive, inst.ready[x])
                        prev = x
                    prefixes += ok
        assert A.price(inst, pi, inst.n, "keine").generated == prefixes + 1


# --- Orakel 4: Master und Spaltenerzeugung ----------------------------------------------------------------------------------------------------

def test_exact_master_equals_scipy_on_random_column_sets():
    linprog = pytest.importorskip("scipy.optimize").linprog
    np = pytest.importorskip("numpy")
    for i in range(25):
        rng = random.Random(7000 + i)
        n = rng.randint(3, 6)
        inst = S.make_instance(n, 7000 + i, 100)
        cols = [(j,) for j in range(1, n + 1)]
        for _ in range(rng.randint(2, 8)):
            size = rng.randint(2, min(4, n))
            cols.append(tuple(rng.sample(range(1, n + 1), size)))
        costs = [G.route_cost(inst, c) for c in cols]
        matrix = np.zeros((n, len(cols)))
        for c, route in enumerate(cols):
            for j in route:
                matrix[j - 1, c] += 1
        res = linprog(costs, A_ub=-matrix, b_ub=-np.ones(n), bounds=(0, None), method="highs")
        # genaue Rechnung braucht ganze oder Bruch-Kosten: Kosten sind Gleitkommazahlen; also mit Brüchen aus den Gleitkommazahlen rechnen
        exact_inst = S.Instance(n, inst.points, tuple(tuple(Fraction(x).limit_denominator(10 ** 9) for x in row) for row in inst.d), inst.demand, inst.ready, inst.due,
                                inst.service, inst.horizon, inst.capacity)
        pi, value, x = G.solve_master(exact_inst, cols)
        assert float(value) == pytest.approx(res.fun, rel=1e-6, abs=1e-6)
        # Dualpreise sind zulässig: jede Spalte kostet mindestens die Summe der Dualpreise ihrer Kunden, und der Zielwert ist die Summe der Dualpreise
        for route, cost in zip(cols, costs):
            assert sum(pi[j] for j in route) <= Fraction(cost).limit_denominator(10 ** 9) + Fraction(1, 10 ** 6)
        assert sum(pi) == value


def grid_instance(seed, n):
    """Kleine ganzzahlige Instanz (Manhattan-Abstand), damit der genaue Master in Brüchen exakt rechnet."""
    rng = random.Random(seed)
    pts = [(0, 0)] + [(rng.randint(-4, 4), rng.randint(-4, 4)) for _ in range(n)]
    d = tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in pts) for a in pts)
    demand = (0,) + tuple(rng.randint(1, 3) for _ in range(n))
    ready = [0] + [d[0][j] + rng.randint(0, 8) for j in range(1, n + 1)]       # jede Einzelfahrt ist zulässig (Ankunft = Abstand <= Beginn des Fensters)
    due = [40] + [ready[j] + rng.randint(4, 14) for j in range(1, n + 1)]
    return S.Instance(n, tuple(pts), d, demand, tuple(ready), tuple(due), 1, 40, 6)


def test_column_generation_bound_equals_the_master_over_all_routes():
    scipy_colgen = pytest.importorskip("scipy.optimize")  # noqa: F841 (nur Verfügbarkeit)
    import colgen_ref
    checked = 0
    for seed in range(14):
        inst = grid_instance(seed, 4 + seed % 3)
        cg = G.colgen(inst, inst.n)
        all_bound, count = G.bound_over_all_routes(inst)
        assert cg.bound == all_bound, seed
        ref = colgen_ref.colgen(inst, inst.n)
        assert ref["bound"] == pytest.approx(float(cg.bound), abs=1e-6), seed
        assert count == len(all_feasible_routes(inst, (0,) * (inst.n + 1)))
        checked += 1
    assert checked == 14


def test_the_hand_example_column_generation_agrees_with_scipy():
    pytest.importorskip("scipy.optimize")
    import colgen_ref
    inst, _ = build_hand()
    ref = colgen_ref.colgen(inst, inst.n)
    assert ref["bound"] == pytest.approx(30, abs=1e-6) and not ref["aborted"]
