"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Die Mini-Instanz ist das Handbeispiel: Depot bei (0, 0) und sieben Kunden auf einem Gitter, Entfernung = Fahrzeit = Kosten = Manhattan-Abstand, Bedienzeit 2,
Horizont 38, Kapazität 6, Zeitfenster [früh, spät], Dualpreise der ersten Runde (zweimal der Abstand zum Depot). Die Zahlen stehen hier **noch einmal von Hand**
(nicht aus epr_scenario); `test_algorithm.py` vergleicht beide Fassungen. Die Handrechnung steht als Rechnung in den Tests, nicht als abgeschriebenes Ergebnis."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from epr_scenario import Instance  # noqa: E402

# Kunde: (Punkt, Last, früh, spät); Index 0 ist das Depot
HAND_TABLE = {
    0: ((0, 0), 0, 0, 38),
    1: ((-1, 2), 1, 18, 28),
    2: ((0, 3), 3, 3, 16),
    3: ((-3, -2), 3, 5, 15),
    4: ((-1, -2), 3, 20, 28),
    5: ((-2, -1), 1, 3, 12),
    6: ((2, 1), 1, 11, 21),
    7: ((3, 2), 2, 8, 20),
}
SERVICE, HORIZON, CAPACITY = 2, 38, 6


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def build_hand():
    pts = tuple(HAND_TABLE[i][0] for i in range(8))
    d = tuple(tuple(manhattan(a, b) for b in pts) for a in pts)
    inst = Instance(7, pts, d, tuple(HAND_TABLE[i][1] for i in range(8)), tuple(HAND_TABLE[i][2] for i in range(8)), tuple(HAND_TABLE[i][3] for i in range(8)),
                    SERVICE, HORIZON, CAPACITY)
    pi = (0,) + tuple(2 * d[0][j] for j in range(1, 8))
    return inst, pi


@pytest.fixture
def hand():
    """(Instanz, Dualpreise der ersten Runde) des Handbeispiels aus der Tabelle oben."""
    return build_hand()
