"""Konstanten: Regler-Grenzen, feste Annahmen, Farben, Schnellstart-Szenarien und Texte, die App und README gemeinsam haben."""

# --- Regler ---------------------------------------------------------------------------------------------------------------------------------
# Komplexität am Regler-Maximum (n = 20, Fensterbreite 100): die elementare Rechnung des ersten Pricing-Aufrufs braucht bei den 60 geprüften Zufalls-Seeds
# im Median 3,0 Millionen Dominanzvergleiche und bei 7 dieser 60 mehr als 12 Millionen. MAX_COMPS fängt das ab: Der Lauf bricht nach so vielen Vergleichen ab
# (einige Sekunden in Python) und die App zeigt den Abbruch als Befund. Die Rechnung mit Gedächtnis k = 1 und ohne Dominanz ist bei n = 20 um Größenordnungen kleiner.
N_MIN, N_MAX, DEFAULT_N = 5, 20, 10
WIDTH_OPTIONS, DEFAULT_WIDTH = (40, 100), 100
SEED_MAX, DEFAULT_SEED = 999999, 0
MAX_COMPS = 10_000_000                   # Abbruch eines elementaren Live-Laufs bei so vielen Dominanzvergleichen
MAX_LABELS_NO_DOMINANCE = 100_000        # Abbruch eines Laufs ohne Dominanz bei so vielen erzeugten Labels
MEMORY_OPTIONS = (1, 2, 3, 7)            # Gedächtnis k im Handbeispiel; 7 = elementar (7 Kunden)
DEFAULT_MEMORY = 7
DUAL_MIN, DUAL_MAX = 0, 20               # Regler der Dualpreise (ganze Zahlen) in Experiment 2
SEARCH_SETS, SEARCH_LOW, SEARCH_HIGH = 3000, 2, 14   # Suche in Experiment 2: 3 000 Sätze ganzzahliger Dualpreise zwischen 2 und 14 (Zufalls-Seeds 0 bis 2999)
PER_CLUSTER = 6                          # Instanzen je Zelle der festen Messreihen (Zufalls-Seeds 0 bis 5)

# --- Farben ---------------------------------------------------------------------------------------------------------------------------------
COLOR_OK = "#2F6B65"
COLOR_BAD = "#C0392B"
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_LINE = "#4c78a8"
COLOR_LINE2 = "#e08a2c"
CELL_OK = "background-color: rgba(46, 160, 67, 0.28)"
CELL_BAD = "background-color: rgba(218, 54, 51, 0.30)"

# --- Schnellstart-Szenarien -----------------------------------------------------------------------------------------------------------------
# Jedes Szenario setzt alle Regler: Gedächtnis im Handbeispiel, die sieben Dualpreise von Experiment 2, Kundenzahl, Fensterbreite und Zufalls-Seed des Größenversuchs.
HAND_DUALS_FIRST = (6, 6, 10, 6, 6, 6, 10)   # Dualpreise der ersten Runde des Handbeispiels (zweimal der Abstand zum Depot)
HAND_DUALS_B = (2, 4, 13, 4, 2, 5, 13)       # Dualpreise B: mit ihnen verfehlt die Dominanz ohne Besuchsmenge den besten Weg


def _scenario(memory, duals, n, width, seed):
    return {"memory": memory, **{f"pi{i + 1}": int(p) for i, p in enumerate(duals)}, "n": n, "width": width, "seed": seed}


PRESETS = {
    "Erste Runde, elementar (Voreinstellung)": _scenario(DEFAULT_MEMORY, HAND_DUALS_FIRST, DEFAULT_N, DEFAULT_WIDTH, DEFAULT_SEED),
    "Dualpreise B: Dominanz ohne Menge": _scenario(DEFAULT_MEMORY, HAND_DUALS_B, DEFAULT_N, DEFAULT_WIDTH, DEFAULT_SEED),
    "Kleines Gedächtnis (k = 1)": _scenario(1, HAND_DUALS_FIRST, DEFAULT_N, DEFAULT_WIDTH, DEFAULT_SEED),
    "20 Kunden, Breite 100: die Rechnung wird fertig": _scenario(DEFAULT_MEMORY, HAND_DUALS_FIRST, 20, 100, 1),
    "20 Kunden, Breite 100: Abbruch am Budget": _scenario(DEFAULT_MEMORY, HAND_DUALS_FIRST, 20, 100, 0),
    "10 Kunden, Breite 40: kleines Beispiel": _scenario(DEFAULT_MEMORY, HAND_DUALS_FIRST, 10, 40, 0),
}
PRESET_HELP = {
    "Erste Runde, elementar (Voreinstellung)": "Handbeispiel mit den Dualpreisen der ersten Runde und jeder Kunde höchstens einmal; Größenversuch mit 10 Kunden, Fensterbreite 100, Zufalls-Seed 0.",
    "Dualpreise B: Dominanz ohne Menge": "Dieselben Kunden, andere Dualpreise: Hier verfehlt das Streichen ohne Besuchsmenge den besten Weg (Experiment 2).",
    "Kleines Gedächtnis (k = 1)": "Handbeispiel mit Gedächtnis k = 1: Nur „Kunde i direkt nach i“ ist verboten, Kreise (auch a-b-a) sind erlaubt; keine Dominanzprüfung scheitert dann an der Besuchsmenge (Experiment 1).",
    "20 Kunden, Breite 100: die Rechnung wird fertig": "Größenversuch mit 20 Kunden, Fensterbreite 100, Zufalls-Seed 1: die elementare Rechnung bleibt unter dem Vergleichsbudget.",
    "20 Kunden, Breite 100: Abbruch am Budget": "Größenversuch mit 20 Kunden, Fensterbreite 100, Zufalls-Seed 0: die elementare Rechnung erreicht das Budget von 10 Millionen Dominanzvergleichen und bricht ab.",
    "10 Kunden, Breite 40: kleines Beispiel": "Größenversuch mit 10 Kunden, Fensterbreite 40, Zufalls-Seed 0: schmale Fenster, wenige Labels.",
}

# --- Text, den App und README gleich führen -------------------------------------------------------------------------------------------------
ASSUMPTIONS_MARKDOWN = """\
**Annahmen**
- Eigene Instanzen im Stil der Solomon-Instanzen (Quadrat 100 × 100, Fahrzeit gleich Entfernung, Bedienzeit 10, Kapazität 70, Horizont 300, Kunden zufällig verteilt), **nicht die Originalinstanzen**; das Handbeispiel rechnet mit dem Manhattan-Abstand auf einem Gitter.
- Die Dualpreise der Größenversuche und der Messreihen sind die der ersten Runde der Spaltenerzeugung (Master mit nur den Einzelfahrten) bzw. die der ganzen Spaltenerzeugung mit Überdeckungs-Master; die Dualpreise von Experiment 2 stellt man selbst ein.
- Warten vor einem Zeitfenster ist erlaubt und kostenlos.
- Gezählt werden erzeugte Labels und Dominanzvergleiche, nicht Sekunden.

**Grenzen**
- Die festen Messreihen haben je 6 Instanzen je Kundenzahl und Fensterbreite (Zufalls-Seeds 0 bis 5), nur zufällig verteilte Kunden; 10 bis 30 Kunden.
- Abbrüche der elementaren Rechnung sind Abbrüche an einer Zeitgrenze von 30 Sekunden je Pricing-Aufruf und hängen von Rechner und Last ab; die Zahlen von Experiment 5 sind kein Beleg dafür, dass die elementare Rechnung bei dieser Größe grundsätzlich nicht zu lösen wäre.
- Die Abbruchzahlen für 50 und 100 Kunden und für gruppiert verteilte Kunden stammen aus Messdateien früherer Messungen und sind in der Demo nicht neu gerechnet.
- Gemessen ist eine Python-Fassung des Label-Verfahrens ohne Beschleunigungen (keine Eimer, kein beidseitiges Suchen); sie macht keine Aussage über andere Fassungen.

**Bekannte Probleme und Unsicherheiten**
- Ursachen („weil …“) sind Deutungen, wo es dasteht; gemessen sind die Zählungen.
- Die Zahlen der ganzen Spaltenerzeugung (Experimente 4 und 5) hängen von den Dualpreisen ab, die der Löser des Master-Problems wählt, und können mit einer anderen Version der Bibliothek abweichen.
- Die Darstellung der Tabellen und Diagramme ist im Browser am Computer und in einem 375 Pixel breiten Fenster durchgesehen, nicht auf anderen Geräten oder in anderen Browsern. Die Diagramme haben keine Auswahl per Mausklick.
"""
