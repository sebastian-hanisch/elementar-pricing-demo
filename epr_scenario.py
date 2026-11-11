"""Szenario: Instanzen für das Label-Verfahren (ein Depot, Kunden mit Last, Zeitfenster und Dualpreis).

Zwei Arten von Instanzen:
- das **Handbeispiel** (7 Kunden, Manhattan-Abstand, ganze Zahlen; von Hand nachrechenbar; dasselbe Netz wie in den anderen Demos der Linie
  „Ressourcenwege und Spaltenerzeugung“),
- **Zufallsinstanzen** im Stil der Solomon-Instanzen (Quadrat 100 x 100, Fahrzeit = Entfernung, Bedienzeit 10, Kapazität 70, Horizont 300;
  nicht die Originalinstanzen). `make_instance` zieht die Zahlen in derselben Reihenfolge wie die Messreihen der Planung, damit die festen
  Zufalls-Seeds dieselben Instanzen ergeben.

Dazu die Dualpreise der **ersten Runde** der Spaltenerzeugung: Solange der Master nur die Einzelfahrten kennt, ist der Dualpreis eines
Kunden gleich den Kosten seiner Einzelfahrt (zweimal die Entfernung zum Depot)."""

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Instance:
    """Knoten 0 ist das Depot, die Kunden sind 1..n. Alle Tupel haben die Länge n + 1."""

    n: int
    points: tuple[tuple[float, float], ...]
    d: tuple[tuple[float, ...], ...]   # Entfernung = Fahrzeit = Kosten
    demand: tuple[int, ...]
    ready: tuple[float, ...]           # frühester Beginn der Bedienung (früher ankommen heißt warten, kostenlos)
    due: tuple[float, ...]             # spätester Beginn der Bedienung
    service: float                     # Bedienzeit je Kunde
    horizon: float                     # spätestmögliche Rückkehr ins Depot
    capacity: int


def make_instance(n: int, seed: int, width: float, horizon: float = 300.0, capacity: int = 70, service: float = 10.0) -> Instance:
    """Zufallsinstanz aus (n, seed, Fensterbreite): gleiche Eingabe, gleiche Instanz (Zufallsgenerator `random.Random(seed)`)."""
    rng = random.Random(seed)
    customers = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]
    points = [(50.0, 50.0)] + customers
    d = tuple(tuple(math.dist(a, b) for b in points) for a in points)
    demand = [0] + [rng.randint(5, 25) for _ in range(n)]
    ready = [0.0] * (n + 1)
    due = [horizon] * (n + 1)
    for i in range(1, n + 1):
        lo = d[0][i]
        hi = horizon - service - d[0][i]
        center = rng.uniform(lo, hi)
        ready[i] = max(lo, center - width / 2)
        due[i] = min(hi, center + width / 2)
    return Instance(n, tuple(points), d, tuple(demand), tuple(ready), tuple(due), service, horizon, capacity)


def restrict(inst: Instance, m: int) -> Instance:
    """Teilnetz mit den ersten m Kunden (Depot und Kunden 1..m, alle übrigen Zahlen unverändert)."""
    if not 1 <= m <= inst.n:
        raise ValueError(f"m = {m} liegt außerhalb von 1 bis {inst.n}")
    keep = range(m + 1)
    d = tuple(tuple(inst.d[i][j] for j in keep) for i in keep)
    return Instance(m, tuple(inst.points[i] for i in keep), d, tuple(inst.demand[i] for i in keep), tuple(inst.ready[i] for i in keep),
                    tuple(inst.due[i] for i in keep), inst.service, inst.horizon, inst.capacity)


def first_round_duals(inst: Instance) -> tuple:
    """Dualpreise der ersten Runde: Master mit nur den Einzelfahrten, Dualpreis des Kunden = Kosten seiner Einzelfahrt (zweimal der Abstand zum Depot)."""
    return (0,) + tuple(2 * inst.d[0][j] for j in range(1, inst.n + 1))


# --- Handbeispiel ---------------------------------------------------------------------------------------------------------------------------

HAND_POINTS = ((0, 0), (-1, 2), (0, 3), (-3, -2), (-1, -2), (-2, -1), (2, 1), (3, 2))   # Depot, dann Kunde 1 bis 7
HAND_DEMAND = (0, 1, 3, 3, 3, 1, 1, 2)
HAND_READY = (0, 18, 3, 5, 20, 3, 11, 8)
HAND_DUE = (38, 28, 16, 15, 28, 12, 21, 20)
HAND_SERVICE, HAND_HORIZON, HAND_CAPACITY = 2, 38, 6
HAND_DUALS_B = (0, 2, 4, 13, 4, 2, 5, 13)   # Dualpreise B: mit ihnen verfehlt die Dominanz ohne Besuchsmenge den besten Weg (siehe Experiment 2)


def _manhattan(points) -> tuple:
    return tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in points) for a in points)


def hand_instance() -> Instance:
    """Das Handbeispiel: Manhattan-Abstand, alle Zahlen ganz (die Zufallsinstanzen rechnen euklidisch)."""
    return Instance(7, HAND_POINTS, _manhattan(HAND_POINTS), HAND_DEMAND, HAND_READY, HAND_DUE, HAND_SERVICE, HAND_HORIZON, HAND_CAPACITY)


def hand_duals() -> tuple:
    """Dualpreise der ersten Runde des Handbeispiels: (6, 6, 10, 6, 6, 6, 10) für die Kunden 1 bis 7."""
    return first_round_duals(hand_instance())


def hand_subnet(m: int, variant: str) -> Instance:
    """Teilnetz des Handbeispiels mit den ersten m Kunden.

    Variante A: das Handbeispiel unverändert (Last 6, Fenster wie in der Tabelle).
    Variante B: ohne Lastgrenze (Kapazität 99) und mit weiten Fenstern [0, H - 2 - Abstand] bei H = 60; hier wachsen die Wege am schnellsten."""
    base = hand_instance()
    if variant == "A":
        return restrict(base, m)
    if variant != "B":
        raise ValueError(f"unbekannte Variante {variant!r}")
    sub = restrict(base, m)
    horizon = 60
    due = (horizon,) + tuple(horizon - sub.service - sub.d[0][j] for j in range(1, m + 1))
    return Instance(m, sub.points, sub.d, sub.demand, (0,) * (m + 1), due, sub.service, horizon, 99)
