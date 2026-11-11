"""Kern der Demo: Label-Verfahren mit Besuchsmenge (elementarer kürzester Weg mit Grenzen) und wählbarer Dominanz (reines Python, Standardbibliothek).

Aufgabe: den Weg mit den kleinsten **reduzierten Kosten** finden (Weglänge minus Dualpreise der besuchten Kunden), mit Last-, Zeitfenster- und
Horizontgrenze, **jeder Kunde höchstens einmal** (elementar). Ein **Label** hält einen Teilweg fest: Zeit, Kosten, Last und das **Gedächtnis**
(die Menge der Kunden, die nicht noch einmal besucht werden dürfen; als Bitmaske). Das Gedächtnis ist wählbar: `k = n` heißt elementar (jeder
besuchte Kunde bleibt im Gedächtnis), kleinere `k` lassen Kreise nach `k` Halten wieder zu (Nachbarschaft der `k` nächsten Kunden).

Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b): `ng_masks` (Gedächtnis), `extend` (Zulässigkeit einer
Fortsetzung), `relation` (die Dominanzregel samt dem Fall „nur die Menge verhindert sie“), `price` (nur die Schleife in Zeitreihenfolge),
`enumerate_routes` und `route_value` (Vergleichsweg ohne Labels). Kein versteckter Zustand, kein Zufall im Kern: Instanzen und Dualpreise kommen
fertig herein. Einzige Ausnahme vom reinen Rechnen ist die optionale Zeitgrenze von `price` (`time_limit`, Sekunden): sie dient nur dazu, die
Rechnung abzubrechen.

Messgrößen der Demo: erzeugte Labels (jedes erzeugte Label, auch ein sofort verworfenes, plus das Start-Label) und **Dominanzvergleiche** (jeder
ausgewertete Test „altes gegen neues Label“ und „neues gegen altes Label“ zählt einmal). Sekunden sind nur Information."""

import heapq
import time
from typing import NamedTuple

from epr_scenario import Instance

EPS = 1e-9            # Toleranz für Vergleiche von Kosten und Zeiten (Gleitkomma)
IMPROVING = -1e-7     # eine Route zählt als verbessernd, wenn ihre reduzierten Kosten darunter liegen

DOMINANCE_MODES = ("voll", "ohne_menge", "keine")   # volle Dominanz mit Menge; falsche Dominanz ohne Menge (Lehrschalter); nichts streichen
CONDITION_NAMES = ("Kosten", "Zeit", "Last", "Besuchsmenge")

DOMINATES, BLOCKED, NO = "dominiert", "blockiert", "nein"   # Ergebnisse von `relation`


class Label(NamedTuple):
    time: float     # Beginn der Bedienung am Knoten (nach Warten)
    cost: float     # reduzierte Kosten des Teilwegs
    load: int       # verbrauchte Last
    mem: int        # Bitmaske: Kunden, die nicht noch einmal besucht werden dürfen (Besuchsmenge, bei k < n nur die Nachbarschaft)
    node: int       # letzter Kunde (0 = Start im Depot)
    parent: int     # Nummer des Vorgänger-Labels, -1 beim Start


class Event(NamedTuple):
    """Eine Entscheidung der Dominanzprüfung.

    kind "bleibt":     das neue Label `label` bleibt (partner = -1);
    kind "verworfen":  das neue Label `label` wird vom älteren Label `partner` dominiert;
    kind "verdraengt": das ältere Label `label` entfällt, weil das neue Label `partner` es dominiert.
    `blocked` zählt bei "bleibt" und "verworfen" die Prüfungen dieses neuen Labels, an denen Kosten, Zeit und Last gereicht hätten und nur die
    Besuchsmenge die Dominanz verhinderte (bei "verdraengt" immer 0)."""

    kind: str
    label: int
    partner: int
    blocked: int


class PriceResult(NamedTuple):
    value: float                  # kleinster reduzierter Kostenwert aller gefundenen Routen; 0, wenn keine Route unter IMPROVING liegt
    route: tuple[int, ...]        # zugehörige Route (ohne Depot); () bei value == 0
    generated: int                # erzeugte Labels inklusive Start-Label
    discarded: int                # davon sofort verworfen (vom älteren Label dominiert)
    displaced: int                # später von einem neuen Label verdrängt
    comps: int                    # Dominanzvergleiche (siehe Moduldoc)
    blocked: int                  # Prüfungen, die nur an der Besuchsmenge scheiterten (Kosten, Zeit und Last hätten gereicht)
    labels: tuple[Label, ...]     # alle erzeugten Labels in der Reihenfolge der Erzeugung (Nummer = Index)
    dead: tuple[bool, ...]        # Label am Ende gestrichen?
    ended: tuple[tuple[float, int], ...]   # (reduzierte Kosten einschließlich Rückfahrt, Nummer des letzten Labels) je Label, das ins Depot zurückkehren kann
    events: tuple[Event, ...]     # Entscheidungen in der Reihenfolge der Erzeugung (nur mit trace=True)
    aborted: bool                 # abgebrochen (max_labels oder time_limit erreicht)

    @property
    def dominated(self) -> int:
        return self.discarded + self.displaced

    @property
    def alive(self) -> int:
        return self.generated - self.discarded - self.displaced


def ng_masks(inst: Instance, k: int) -> list[int]:
    """Gedächtnis NG(j): die k nächsten Kunden von j (j selbst eingeschlossen; Gleichstand: kleinere Nummer). k >= n heißt: jeder besuchte Kunde bleibt im Gedächtnis (elementar)."""
    k = max(1, min(k, inst.n))
    masks = [0] * (inst.n + 1)
    for j in range(1, inst.n + 1):
        order = sorted(range(1, inst.n + 1), key=lambda i: (inst.d[j][i], i))
        m = 0
        for i in order[:k]:
            m |= 1 << i
        masks[j] = m | (1 << j)
    return masks


def relation(o: Label, new: Label, use_set: bool = True) -> str:
    """Wie steht Label `o` zu Label `new` (am selben Knoten)?

    DOMINATES: `o` ist in Kosten, Zeit und Last höchstens so groß wie `new`, und (mit `use_set`) die Besuchsmenge von `o` ist eine Teilmenge der von `new`.
    BLOCKED:   Kosten, Zeit und Last reichen, nur die Besuchsmenge verhindert die Dominanz (nur mit `use_set`).
    NO:        schon Kosten, Zeit oder Last reichen nicht."""
    if o.cost > new.cost + EPS or o.time > new.time + EPS or o.load > new.load:
        return NO
    if use_set and (o.mem & ~new.mem) != 0:
        return BLOCKED
    return DOMINATES


def conditions(o: Label, new: Label) -> dict[str, bool]:
    """Die vier Einzelbedingungen der vollen Regel für `o` gegenüber `new` (True = erfüllt), in der Reihenfolge CONDITION_NAMES."""
    return {
        "Kosten": o.cost <= new.cost + EPS,
        "Zeit": o.time <= new.time + EPS,
        "Last": o.load <= new.load,
        "Besuchsmenge": (o.mem & ~new.mem) == 0,
    }


def extend(inst: Instance, pi, ng: list[int], label: Label, parent: int, j: int) -> Label | None:
    """Fortsetzung von `label` (Nummer `parent`) zum Kunden j, oder None, wenn sie unzulässig ist (Kunde im Gedächtnis, Last, Zeitfenster).
    Ankunft vor dem Fenster heißt warten (kostenlos). Die Rückkehr ins Depot prüft `price` beim Abschluss."""
    i = label.node
    if j == i or (label.mem >> j) & 1:
        return None
    load = label.load + inst.demand[j]
    if load > inst.capacity:
        return None
    arrival = label.time + (inst.service if i != 0 else 0) + inst.d[i][j]
    if arrival > inst.due[j] + EPS:
        return None
    return Label(max(arrival, inst.ready[j]), label.cost + inst.d[i][j] - pi[j], load, (label.mem & ng[j]) | (1 << j), j, parent)


def route_of(labels, index: int) -> tuple[int, ...]:
    """Route (ohne Depot) des Labels mit der Nummer `index`."""
    route = []
    while index != -1:
        route.append(labels[index].node)
        index = labels[index].parent
    return tuple(reversed(route))[1:]


def price(inst: Instance, pi, k: int, dominance: str = "voll", trace: bool = False, max_labels: int | None = None,
          max_comps: int | None = None, time_limit: float | None = None) -> PriceResult:
    """Label-Setting in Zeitreihenfolge. `dominance`: "voll" (Kosten, Zeit, Last und Besuchsmenge), "ohne_menge" (falsch für elementare Wege) oder "keine".

    Ein neues Label wird verworfen, wenn ein lebendes Label am selben Kunden es dominiert (bei Gleichstand bleibt das ältere); sonst verdrängt es alle
    lebenden Labels, die es dominiert. `k` ist die Größe des Gedächtnisses (k = n: elementar). Abbruch (aborted) bei `max_labels` erzeugten Labels oder
    `max_comps` Dominanzvergleichen (beides nach dem Erzeugen eines Labels geprüft, also auf Zählungen gestützt und deterministisch) oder, wenn
    `time_limit` (Sekunden) überschritten ist (vor jeder Verlängerung eines Labels geprüft; hängt von Rechner und Last ab)."""
    if dominance not in DOMINANCE_MODES:
        raise ValueError(f"unbekannte Dominanz {dominance!r}")
    use_set = dominance == "voll"
    ng = ng_masks(inst, k)
    labels = [Label(0, 0, 0, 0, 0, -1)]
    dead = [False]
    at_node: list[list[int]] = [[] for _ in range(inst.n + 1)]
    heap = [(0, 0)]
    discarded = displaced = comps = blocked = 0
    ended: list[tuple[float, int]] = []
    events: list[Event] = []
    aborted = False
    start = time.perf_counter()
    while heap:
        _, li = heapq.heappop(heap)
        if dead[li]:
            continue
        if time_limit is not None and time.perf_counter() - start > time_limit:
            aborted = True
            break
        label = labels[li]
        i = label.node
        if i != 0 and label.time + inst.service + inst.d[i][0] <= inst.horizon:
            ended.append((label.cost + inst.d[i][0], li))
        for j in range(1, inst.n + 1):
            new = extend(inst, pi, ng, label, li, j)
            if new is None:
                continue
            nid = len(labels)
            labels.append(new)
            dead.append(False)
            own_blocked = 0
            if dominance != "keine":
                lost_to = None
                for o in at_node[j]:
                    comps += 1
                    rel = relation(labels[o], new, use_set)
                    if rel == DOMINATES:
                        lost_to = o
                        break
                    if rel == BLOCKED:
                        own_blocked += 1
                if lost_to is not None:
                    dead[nid] = True
                    discarded += 1
                    blocked += own_blocked
                    if trace:
                        events.append(Event("verworfen", nid, lost_to, own_blocked))
                    continue
                survivors = []
                for o in at_node[j]:
                    comps += 1
                    rel = relation(new, labels[o], use_set)
                    if rel == DOMINATES:
                        dead[o] = True
                        displaced += 1
                        if trace:
                            events.append(Event("verdraengt", o, nid, 0))
                    else:
                        if rel == BLOCKED:
                            own_blocked += 1
                        survivors.append(o)
                at_node[j] = survivors
                blocked += own_blocked
            at_node[j].append(nid)
            heapq.heappush(heap, (new.time, nid))
            if trace:
                events.append(Event("bleibt", nid, -1, own_blocked))
            if (max_labels is not None and len(labels) >= max_labels) or (max_comps is not None and comps >= max_comps):
                aborted = True
                break
        if aborted:
            break
    best_value, best_route = 0, ()
    candidates = sorted((rc, route_of(labels, li)) for rc, li in ended if rc < IMPROVING)
    if candidates:
        best_value, best_route = candidates[0]
    return PriceResult(best_value, best_route, len(labels), discarded, displaced, comps, blocked, tuple(labels), tuple(dead), tuple(ended),
                       tuple(events), aborted)


def routes_of(result: PriceResult, limit: int = 15) -> list[tuple[float, tuple[int, ...]]]:
    """Die besten verschiedenen verbessernden Routen eines Laufs (reduzierte Kosten, Route), aufsteigend; Grundlage für neue Spalten."""
    found: dict[tuple[int, ...], float] = {}
    for rc, li in result.ended:
        if rc < IMPROVING:
            found.setdefault(route_of(result.labels, li), rc)
    return sorted((rc, route) for route, rc in found.items())[:limit]


def standing_pairs(result: PriceResult) -> list[tuple[int, int]]:
    """Paare lebender Labels am selben Kunden (A, B), bei denen Kosten, Zeit und Last von A höchstens so groß sind wie die von B und nur die
    Besuchsmenge von A keine Teilmenge der von B ist: A wäre nach den drei Größen besser, beide bleiben stehen. Geordnet nach Kunde und Nummern."""
    alive_at: dict[int, list[int]] = {}
    for index, label in enumerate(result.labels):
        if not result.dead[index] and label.node != 0:
            alive_at.setdefault(label.node, []).append(index)
    pairs = []
    for node in sorted(alive_at):
        for a in alive_at[node]:
            for b in alive_at[node]:
                if a != b and relation(result.labels[a], result.labels[b], True) == BLOCKED:
                    pairs.append((a, b))
    return pairs


def enumerate_routes(inst: Instance, pi) -> list[tuple[float, tuple[int, ...], float]]:
    """Vergleichsweg ohne Labels: alle zulässigen elementaren Routen (Tiefensuche), sortiert nach reduzierten Kosten, als (Kosten, Route, Rückkehrzeit)."""
    routes: list[tuple[float, tuple[int, ...], float]] = []

    def visit(i: int, time_: float, load: int, visited: int, cost: float, path: tuple[int, ...]) -> None:
        if i != 0 and time_ + inst.service + inst.d[i][0] <= inst.horizon:
            routes.append((cost + inst.d[i][0], path, time_ + inst.service + inst.d[i][0]))
        for j in range(1, inst.n + 1):
            if (visited >> j) & 1 or load + inst.demand[j] > inst.capacity:
                continue
            arrival = time_ + (inst.service if i != 0 else 0) + inst.d[i][j]
            if arrival > inst.due[j] + EPS:
                continue
            visit(j, max(arrival, inst.ready[j]), load + inst.demand[j], visited | (1 << j), cost + inst.d[i][j] - pi[j], path + (j,))

    visit(0, 0, 0, 0, 0, ())
    return sorted(routes)


def best_by_enumeration(inst: Instance, pi) -> tuple[float, tuple[int, ...], int]:
    """Bester Wert, Route und Zahl der zulässigen elementaren Routen; (0, (), Zahl), wenn keine verbessernd ist."""
    routes = enumerate_routes(inst, pi)
    if routes and routes[0][0] < IMPROVING:
        return routes[0][0], routes[0][1], len(routes)
    return 0, (), len(routes)


def route_value(inst: Instance, pi, route) -> float | None:
    """Unabhängiger Prüfer: reduzierte Kosten einer Route, oder None, wenn sie unzulässig ist (Kunde doppelt, Last, Zeitfenster, Horizont)."""
    route = tuple(route)
    if len(set(route)) != len(route) or any(not 1 <= j <= inst.n for j in route):
        return None
    time_, load, cost, prev = 0, 0, 0, 0
    for j in route:
        arrival = time_ + (inst.service if prev != 0 else 0) + inst.d[prev][j]
        load += inst.demand[j]
        if arrival > inst.due[j] + EPS or load > inst.capacity:
            return None
        time_ = max(arrival, inst.ready[j])
        cost += inst.d[prev][j] - pi[j]
        prev = j
    if route:
        if time_ + inst.service + inst.d[prev][0] > inst.horizon:
            return None
        cost += inst.d[prev][0]
    return cost


def walk_value(inst: Instance, pi, route) -> float | None:
    """Wie `route_value`, aber ein Kunde darf mehrfach vorkommen (nicht elementar, Kreise erlaubt); für Routen mit kleinem Gedächtnis."""
    route = tuple(route)
    if any(not 1 <= j <= inst.n for j in route):
        return None
    time_, load, cost, prev = 0, 0, 0, 0
    for j in route:
        if j == prev:
            return None
        arrival = time_ + (inst.service if prev != 0 else 0) + inst.d[prev][j]
        load += inst.demand[j]
        if arrival > inst.due[j] + EPS or load > inst.capacity:
            return None
        time_ = max(arrival, inst.ready[j])
        cost += inst.d[prev][j] - pi[j]
        prev = j
    if route:
        if time_ + inst.service + inst.d[prev][0] > inst.horizon:
            return None
        cost += inst.d[prev][0]
    return cost
