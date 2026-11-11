"""Kennzahlen, Verdikte (reine Funktionen) und Messreihen der Demo.

Jedes Verdikt ist eine reine Funktion `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`, `tests/test_verdicts.py` prüft
Schwellen und jede Zahl im Text an handgesetzten Werten. Die festen Messreihen (data/*.json) laden `load_*`; jede Zeile nennt ihre Quelle."""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import NamedTuple

import epr_algorithm as A
import epr_colgen as G
import epr_constants as C
from epr_scenario import Instance, first_round_duals, hand_duals, hand_instance, hand_subnet, make_instance

DATA_DIR = Path(__file__).resolve().parent / "data"


# --- Zahlen und Mengen als Text -------------------------------------------------------------------------------------------------------------

def fmt_num(x, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und echtem Minuszeichen; ganze Zahlen ohne Nachkommastellen (Brüche als Dezimalzahl)."""
    x = float(x)
    text = f"{int(x)}" if x.is_integer() else f"{x:.{digits}f}".replace(".", ",")
    return text.replace("-", "−")


def fmt_dec(x: float, digits: int = 1) -> str:
    """Dezimalzahl mit immer gleich vielen Nachkommastellen und deutschem Komma (1,0 statt 1)."""
    return f"{x:.{digits}f}".replace(".", ",")


def fmt_int(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner (4 424 statt 4424)."""
    return f"{n:,}".replace(",", " ")


def fmt_pct(x: float, digits: int = 1) -> str:
    """Prozentwert mit deutschem Dezimalkomma (x ist schon in Prozent)."""
    return f"{x:.{digits}f}".replace(".", ",") + " %"


def fmt_set(mem: int, n: int) -> str:
    """Menge der Kunden (Bitmaske) als {1,3,5}."""
    return "{" + ",".join(str(i) for i in range(1, n + 1) if (mem >> i) & 1) + "}"


def fmt_route(route) -> str:
    return "-".join(str(i) for i in route) if route else "keine"


def memory_label(k: int, n: int) -> str:
    """Name des Gedächtnisses: „k = 1“ oder „elementar (k = 7)“."""
    return f"elementar (k = {n})" if k >= n else f"k = {k}"


# --- Handbeispiel ---------------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class HandAnalysis:
    inst: Instance
    pi: tuple
    k: int                          # Gedächtnis (k = n: elementar)
    result: A.PriceResult           # mit Protokoll der Entscheidungen
    ref_value: float                # bester Wert aller zulässigen elementaren Routen (Aufzählung)
    ref_route: tuple
    n_routes: int                   # Zahl der zulässigen elementaren Routen
    pairs: tuple                    # (A, B): Paare lebender Labels, die nur an der Besuchsmenge scheitern und nebeneinander stehen
    elementary_route: bool          # ist die gefundene Route elementar?
    checked_value: float | None     # unabhängig nachgerechneter Wert der gefundenen Route (None: unzulässig)


def analyse_hand(k: int) -> HandAnalysis:
    """Handbeispiel mit den Dualpreisen der ersten Runde und Gedächtnis k (k = 7: elementar), dazu die Aufzählung aller elementaren Routen als Bezug."""
    inst = hand_instance()
    pi = hand_duals()
    result = A.price(inst, pi, k, "voll", trace=True)
    ref_value, ref_route, n_routes = A.best_by_enumeration(inst, pi)
    route = result.route
    elementary = len(set(route)) == len(route)
    checked = A.route_value(inst, pi, route) if elementary else A.walk_value(inst, pi, route)
    pairs = tuple(A.standing_pairs(result))
    return HandAnalysis(inst, tuple(pi), k, result, ref_value, ref_route, n_routes, pairs, elementary, checked)


def compare_memory(options=C.MEMORY_OPTIONS) -> list[dict]:
    """Zeile je Gedächtnis für das Handbeispiel: erzeugte und lebende Labels, Dominanzvergleiche, Prüfungen, die nur an der Menge scheitern, bester Wert und Route."""
    rows = []
    for k in options:
        a = analyse_hand(k)
        rows.append({"k": k, "generated": a.result.generated, "dominated": a.result.dominated, "alive": a.result.alive, "comps": a.result.comps,
                     "blocked": a.result.blocked, "pairs": len(a.pairs), "value": a.result.value, "route": a.result.route, "elementary": a.elementary_route})
    return rows


def label_text(inst: Instance, result: A.PriceResult, index: int) -> str:
    """L8 (Weg 2-1, Zeit 18, Kosten −7, Last 4, besucht {1,2})."""
    label = result.labels[index]
    return (f"L{index} (Weg {fmt_route(A.route_of(result.labels, index))}, Zeit {fmt_num(label.time)}, Kosten {fmt_num(label.cost)}, Last {label.load}, "
            f"Menge {fmt_set(label.mem, inst.n)})")


def short_label(result: A.PriceResult, index: int) -> str:
    """L8 (Weg 2-1): Nummer und Weg."""
    return f"L{index} (Weg {fmt_route(A.route_of(result.labels, index))})"


def condition_text(name: str, o: A.Label, new: A.Label, n: int) -> tuple[bool, str]:
    """(erfüllt, Text) für eine der vier Bedingungen: `o` soll `new` dominieren, Text als Vergleich `o ≤ new` bzw. `o > new`."""
    ok = A.conditions(o, new)[name]
    if name == "Kosten":
        a, b = fmt_num(o.cost), fmt_num(new.cost)
    elif name == "Zeit":
        a, b = fmt_num(o.time), fmt_num(new.time)
    elif name == "Last":
        a, b = str(o.load), str(new.load)
    else:
        return ok, f"{fmt_set(o.mem, n)} {'⊆' if ok else '⊄'} {fmt_set(new.mem, n)}"
    return ok, f"{a} {'≤' if ok else '>'} {b}"


def _own_values(label: A.Label, n: int) -> dict:
    return {"Kosten": fmt_num(label.cost), "Zeit": fmt_num(label.time), "Last": str(label.load), "Besuchsmenge": fmt_set(label.mem, n)}


def condition_summary(o: A.Label, new: A.Label, n: int) -> str:
    """Die vier Bedingungen der vollen Regel für `o` gegenüber `new` als ein Satzteil: „Kosten: −11 ≤ −5 ✓; Zeit: …; Besuchsmenge: {6,7} ⊄ {3,6} ✗“."""
    parts = []
    for name in A.CONDITION_NAMES:
        ok, text = condition_text(name, o, new, n)
        parts.append(f"{name}: {text} {'✓' if ok else '✗'}")
    return "; ".join(parts)


def event_rows(a: HandAnalysis, show_all: bool = False) -> list[dict]:
    """Zeile je Entscheidung der Dominanzprüfung in der Reihenfolge der Erzeugung. Beim Streichen stehen in den vier Spalten Kosten, Zeit, Last und Besuchsmenge
    die Vergleiche des dominierenden Labels (links) mit dem gestrichenen (rechts): ✓ erfüllt, ✗ verletzt. Bei einem Label, das bleibt, stehen seine eigenen Werte.
    Dazu die Zahl der Prüfungen, die bei diesem neuen Label nur an der Besuchsmenge scheiterten (Kosten, Zeit und Last hätten zum Streichen gereicht).
    Ohne `show_all` nur die Zeilen, in denen ein Label wegfällt."""
    inst, res = a.inst, a.result
    rows = []
    for ev in res.events:
        if ev.kind == "bleibt":
            if not show_all:
                continue
            row = {"Ereignis": "bleibt", "Label": short_label(res, ev.label), "Dominiert von": "–", **_own_values(res.labels[ev.label], inst.n)}
        else:
            o, new = res.labels[ev.partner], res.labels[ev.label]
            row = {"Ereignis": "neues Label verworfen" if ev.kind == "verworfen" else "älteres entfällt", "Label": short_label(res, ev.label),
                   "Dominiert von": short_label(res, ev.partner)}
            for name in A.CONDITION_NAMES:
                ok, text = condition_text(name, o, new, inst.n)
                row[name] = f"{text} {'✓' if ok else '✗'}"
        row["Nur an der Menge gescheitert"] = ev.blocked
        rows.append(row)
    return rows


def pair_rows(a: HandAnalysis) -> list[dict]:
    """Die Paare lebender Labels, die nach Kosten, Zeit und Last besser wären und nur wegen der Besuchsmenge nebeneinander stehen."""
    inst, res = a.inst, a.result
    rows = []
    for x, y in a.pairs:
        lx, ly = res.labels[x], res.labels[y]
        rows.append({"Kunde": lx.node, "Label A": label_text(inst, res, x), "Label B": label_text(inst, res, y), "fehlt in B": fmt_set(lx.mem & ~ly.mem, inst.n)})
    return rows


def first_blocked_pairs(a: HandAnalysis, limit: int = 8) -> list[dict]:
    return pair_rows(a)[:limit]


def colgen_hand() -> G.ColgenResult:
    """Die ganze Spaltenerzeugung am Handbeispiel, elementar, mit genauem Master (Brüche)."""
    return G.colgen(hand_instance(), hand_instance().n)


def colgen_rows(cg: G.ColgenResult) -> list[dict]:
    return [{"Runde": r.number, "Master": fmt_num(r.master_value), "Dualpreise der Kunden 1 bis 7": ", ".join(fmt_num(p) for p in r.duals),
             "beste neue Spalte": fmt_route(r.best_route), "reduzierte Kosten": fmt_num(r.best_value) if r.best_route else "keine unter 0",
             "erzeugte Labels": r.generated} for r in cg.rounds]


# --- Experiment 2: Dominanz ohne Besuchsmenge ------------------------------------------------------------------------------------------------

class Loss(NamedTuple):
    prefix: tuple      # Vorstufe des besten Weges, die verloren geht
    lost: int          # Nummer des verlorenen Labels
    dominator: int     # Nummer des Labels, das es streicht


@dataclass(frozen=True)
class NomemAnalysis:
    pi: tuple
    ref_value: float
    ref_route: tuple
    n_routes: int
    right: A.PriceResult     # mit Menge in der Dominanz
    wrong: A.PriceResult     # ohne Menge in der Dominanz (mit Protokoll)
    loss: Loss | None        # erste Vorstufe des besten Weges, die ohne Menge verloren geht (nur wenn der Weg verfehlt wird)
    misses: bool             # verfehlt die Dominanz ohne Menge den besten Weg (schlechterer Wert als die Aufzählung)?


def first_loss(inst: Instance, result: A.PriceResult, ref_route: tuple) -> Loss | None:
    """Die erste Entscheidung (in der Reihenfolge der Erzeugung), bei der ein Label wegfällt, dessen Weg eine Vorstufe `ref_route[:m]` (m >= 1) des besten Weges ist."""
    prefixes = {tuple(ref_route[:m]) for m in range(1, len(ref_route) + 1)}
    for ev in result.events:
        if ev.kind != "bleibt" and A.route_of(result.labels, ev.label) in prefixes:
            return Loss(A.route_of(result.labels, ev.label), ev.label, ev.partner)
    return None


def analyse_nomem(duals) -> NomemAnalysis:
    """Handbeispiel mit den gegebenen ganzzahligen Dualpreisen der Kunden 1 bis 7: mit und ohne Menge in der Dominanz, dazu die Aufzählung."""
    inst = hand_instance()
    pi = (0,) + tuple(int(p) for p in duals)
    ref_value, ref_route, n_routes = A.best_by_enumeration(inst, pi)
    right = A.price(inst, pi, inst.n, "voll")
    wrong = A.price(inst, pi, inst.n, "ohne_menge", trace=True)
    misses = wrong.value > ref_value + A.EPS
    loss = first_loss(inst, wrong, ref_route) if misses else None
    return NomemAnalysis(pi, ref_value, ref_route, n_routes, right, wrong, loss, misses)


def search_counterexamples(total: int = C.SEARCH_SETS, low: int = C.SEARCH_LOW, high: int = C.SEARCH_HIGH) -> list[tuple[int, tuple]]:
    """Suche am Handbeispiel: für `total` Sätze ganzzahliger Dualpreise (low bis high, Zufallsgenerator `random.Random(seed)` mit Zufalls-Seed 0 bis total - 1) verfehlt die
    Dominanz ohne Besuchsmenge den besten elementaren Weg? Rückgabe: Liste (Zufalls-Seed, Dualpreise der Kunden 1 bis 7) der Fälle, in denen sie ihn verfehlt.
    Die zulässigen Routen hängen nicht von den Dualpreisen ab: sie werden einmal aufgezählt, der Bezugswert je Satz ist das Minimum über sie."""
    inst = hand_instance()
    routes = [(A.route_value(inst, [0] * (inst.n + 1), route), route) for _, route, _ in A.enumerate_routes(inst, [0] * (inst.n + 1))]
    missed = []
    for seed in range(total):
        rng = random.Random(seed)
        duals = tuple(rng.randint(low, high) for _ in range(inst.n))
        pi = (0,) + duals
        best = min(cost - sum(pi[j] for j in route) for cost, route in routes)
        ref = best if best < A.IMPROVING else 0
        if A.price(inst, pi, inst.n, "ohne_menge").value > ref + A.EPS:
            missed.append((seed, duals))
    return missed


# --- Experiment 3: Wie wächst es? -------------------------------------------------------------------------------------------------------------

def subnet_rows(variant: str) -> list[dict]:
    """Teilnetze des Handbeispiels mit den ersten m = 2 bis 7 Kunden (Dualpreise: zweimal der Abstand zum Depot): erzeugte und lebende Labels elementar, erzeugte
    Labels ohne Dominanz und mit Gedächtnis k = 1, Zahl der zulässigen elementaren Routen, Faktor gegen das Teilnetz mit einem Kunden weniger."""
    rows, prev = [], None
    for m in range(2, 8):
        sub = hand_subnet(m, variant)
        pi = first_round_duals(sub)
        e = A.price(sub, pi, m, "voll")
        none = A.price(sub, pi, m, "keine")
        k1 = A.price(sub, pi, 1, "voll")
        routes = A.best_by_enumeration(sub, pi)[2]
        rows.append({"m": m, "elementar": e.generated, "uebrig": e.alive, "ohne_dominanz": none.generated, "k1": k1.generated, "wege": routes,
                     "faktor": None if prev is None else e.generated / prev, "wert": e.value})
        prev = e.generated
    return rows


class RunStats(NamedTuple):
    generated: int
    dominated: int
    comps: int
    blocked: int
    aborted: bool
    value: float
    route: tuple
    alive_per_customer: tuple
    dominated_per_customer: tuple

    @property
    def alive(self) -> int:
        return self.generated - self.dominated


def run_stats(inst: Instance, result: A.PriceResult) -> RunStats:
    alive = [0] * inst.n
    gone = [0] * inst.n
    for index, label in enumerate(result.labels):
        if label.node == 0:
            continue
        (gone if result.dead[index] else alive)[label.node - 1] += 1
    return RunStats(result.generated, result.dominated, result.comps, result.blocked, result.aborted, result.value, result.route, tuple(alive), tuple(gone))


@dataclass(frozen=True)
class SizeAnalysis:
    n: int
    width: int
    seed: int
    elementary: RunStats
    k1: RunStats
    none: RunStats

    @property
    def per_label(self) -> float:
        """Dominanzvergleiche je erzeugtem Label der elementaren Rechnung."""
        return self.elementary.comps / self.elementary.generated

    @property
    def share_blocked(self) -> float:
        """Anteil der Dominanzvergleiche, die nur an der Besuchsmenge scheiterten (in Prozent)."""
        return 100 * self.elementary.blocked / self.elementary.comps if self.elementary.comps else 0.0


def size_experiment(n: int, width: int, seed: int) -> SizeAnalysis:
    """Eine Zufallsinstanz, ein Pricing-Aufruf mit den Dualpreisen der ersten Runde: elementar (Abbruch bei MAX_COMPS Vergleichen), Gedächtnis k = 1, ohne Dominanz
    (Abbruch bei MAX_LABELS_NO_DOMINANCE Labels)."""
    inst = make_instance(n, seed, width)
    pi = first_round_duals(inst)
    e = A.price(inst, pi, n, "voll", max_comps=C.MAX_COMPS)
    k1 = A.price(inst, pi, 1, "voll")
    none = A.price(inst, pi, n, "keine", max_labels=C.MAX_LABELS_NO_DOMINANCE)
    return SizeAnalysis(n, width, seed, run_stats(inst, e), run_stats(inst, k1), run_stats(inst, none))


# --- Messreihen (data/*.json) ----------------------------------------------------------------------------------------------------------------

def load_runs() -> list[dict]:
    return json.loads((DATA_DIR / "laeufe.json").read_text(encoding="utf-8"))["zeilen"]


def load_premeasured() -> dict:
    return json.loads((DATA_DIR / "vormessung.json").read_text(encoding="utf-8"))


MODE_OF_K = {1: "k1", 5: "k5"}


def mode_of(row: dict) -> str:
    """Art des Gedächtnisses einer Messzeile: k1, k5 oder elementar (k = n)."""
    return "elementar" if row["k"] >= row["n"] else MODE_OF_K[row["k"]]


def wall_table(rows: list[dict], width: int) -> list[dict]:
    """Zeile je Kundenzahl für eine Fensterbreite: je Gedächtnis (k1, k5, elementar) die Zahl der fertigen Läufe, Median der Labels der ganzen Spaltenerzeugung,
    mittlerer Anteil gestrichener Labels, Median der Dominanzvergleiche und Vergleiche je Label (gepoolt über die fertigen Läufe)."""
    out = []
    for n in sorted({r["n"] for r in rows if r["breite"] == width}):
        entry = {"n": n}
        for mode in ("k1", "k5", "elementar"):
            runs = [r for r in rows if r["breite"] == width and r["n"] == n and mode_of(r) == mode]
            done = [r for r in runs if not r["abgebrochen"]]
            entry[mode] = {
                "laeufe": len(runs), "fertig": len(done),
                "labels_median": median(r["labels"] for r in done) if done else None,
                "gestrichen_prozent": 100 * sum(r["gestrichen"] / r["labels"] for r in done) / len(done) if done else None,
                "vergleiche_median": median(r["vergleiche"] for r in done) if done else None,
                "vergleiche_je_label": sum(r["vergleiche"] for r in done) / sum(r["labels"] for r in done) if done else None,
            }
        out.append(entry)
    return out


def growth_factors(table: list[dict]) -> list[float]:
    """Faktor der Labels (Median, elementar) von einer gemessenen Kundenzahl zur nächsten, nur wo bei beiden alle elementaren Läufe fertig sind
    (sonst stammt der Median aus einer Auswahl der leichteren Instanzen)."""
    out = []
    for a, b in zip(table, table[1:]):
        if all(r["elementar"]["fertig"] == r["elementar"]["laeufe"] for r in (a, b)):
            out.append(b["elementar"]["labels_median"] / a["elementar"]["labels_median"])
    return out


def last_complete_row(table: list[dict]) -> dict:
    """Die Zeile mit der größten Kundenzahl, bei der alle elementaren Läufe fertig sind (sonst die erste Zeile)."""
    complete = [r for r in table if r["elementar"]["fertig"] == r["elementar"]["laeufe"]]
    return complete[-1] if complete else table[0]


def abort_table(rows: list[dict], n: int = 30) -> list[dict]:
    """Elementare Läufe bei `n` Kunden je Fensterbreite: Zahl der Läufe, abgebrochen, davon im ersten Pricing-Aufruf, fertig."""
    out = []
    for width in sorted({r["breite"] for r in rows if r["n"] == n}):
        runs = [r for r in rows if r["n"] == n and r["breite"] == width and mode_of(r) == "elementar"]
        aborted = [r for r in runs if r["abgebrochen"]]
        out.append({"breite": width, "laeufe": len(runs), "abgebrochen": len(aborted), "im_ersten_aufruf": sum(1 for r in aborted if r["abbruch_runde"] == 1), "fertig": len(runs) - len(aborted)})
    return out


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def _blocked_sentence(generated: int, blocked: int) -> str:
    if blocked == 0:
        return f" Es erzeugt {generated} Labels; keine Dominanzprüfung scheitert nur an der Besuchsmenge."
    return (f" Es erzeugt {generated} Labels; bei {blocked} Dominanzprüfungen hätten Kosten, Zeit und Last zum Streichen gereicht, und nur die Besuchsmenge verhinderte es.")


def verdict_hand(k: int, n: int, value, route, ref_value, ref_route, n_routes: int, generated: int, blocked: int) -> tuple[str, str]:
    """Kernfrage am Handbeispiel: findet das Verfahren mit Gedächtnis k den besten Weg, und was kostet die Besuchsmenge?"""
    name = memory_label(k, n)
    elementary = len(set(route)) == len(route)
    tail = _blocked_sentence(generated, blocked)
    if k >= n:
        if value == ref_value and tuple(route) == tuple(ref_route):
            return "success", (f"Mit der Besuchsmenge im Label (elementar, k = {n}) findet das Verfahren einen besten Weg {fmt_route(route)} mit reduzierten Kosten {fmt_num(value)}, "
                               f"wie die Aufzählung aller {n_routes} zulässigen elementaren Routen." + tail)
        return "error", (f"Das Verfahren findet {fmt_route(route)} mit {fmt_num(value)}, die Aufzählung aller {n_routes} zulässigen elementaren Routen {fmt_route(ref_route)} "
                         f"mit {fmt_num(ref_value)}.")
    if value < ref_value and not elementary:
        return "info", (f"Mit Gedächtnis {name} sind Kreise erlaubt: Das Verfahren findet {fmt_route(route)} mit {fmt_num(value)}; "
                        f"die Route fährt einen Kunden mehrfach an und ist damit besser als die beste elementare Route {fmt_route(ref_route)} mit {fmt_num(ref_value)}." + tail)
    if value == ref_value and elementary and tuple(route) == tuple(ref_route):
        return "info", (f"Mit Gedächtnis {name} findet das Verfahren hier denselben Weg {fmt_route(route)} mit {fmt_num(value)} wie die Aufzählung der elementaren Routen: "
                        "Kreise sind erlaubt, aber an diesen Dualpreisen lohnt sich keiner." + tail)
    return "warning", f"Mit Gedächtnis {name} findet das Verfahren {fmt_route(route)} mit {fmt_num(value)}; die beste elementare Route ist {fmt_route(ref_route)} mit {fmt_num(ref_value)}."


def verdict_memory(rows: list[dict], n: int) -> tuple[str, str]:
    """Experiment 1: wie viele Prüfungen scheitern je Gedächtnis nur an der Menge, und wie viele Labels entstehen?"""
    parts = [f"{memory_label(r['k'], n)}: {r['blocked']} Prüfungen, {r['generated']} Labels" for r in rows]
    elem = next(r for r in rows if r["k"] >= n)
    return "info", ("Prüfungen, die nur an der Besuchsmenge scheitern, und erzeugte Labels je Gedächtnis: " + "; ".join(parts) + ". "
                    f"Bei {memory_label(elem['k'], n)} stehen am Ende {elem['pairs']} Paare lebender Labels nebeneinander, die nach Kosten, Zeit und Last streichbar wären.")


def verdict_nomem(a: NomemAnalysis) -> tuple[str, str]:
    """Experiment 2: trifft oder verfehlt die Dominanz ohne Besuchsmenge den besten elementaren Weg? („trifft“ ohne Garantie: ein Treffer an diesen Dualpreisen beweist nichts.)"""
    if a.right.value != a.ref_value or tuple(a.right.route) != tuple(a.ref_route):
        return "error", (f"Mit Menge in der Dominanz findet das Verfahren {fmt_route(a.right.route)} mit {fmt_num(a.right.value)}, die Aufzählung {fmt_route(a.ref_route)} "
                         f"mit {fmt_num(a.ref_value)}: Das darf nicht sein, der Kern ist fehlerhaft.")
    if a.misses:
        text = (f"Die Dominanz ohne Besuchsmenge **verfehlt** den besten Weg: Sie findet {fmt_route(a.wrong.route)} mit {fmt_num(a.wrong.value)}, die Aufzählung aller "
                f"{a.n_routes} zulässigen Routen {fmt_route(a.ref_route)} mit {fmt_num(a.ref_value)}; mit Menge findet das Verfahren den besten Weg.")
        if a.loss is not None:
            text += f" Verloren geht die Vorstufe {fmt_route(a.loss.prefix)} (L{a.loss.lost}), gestrichen von L{a.loss.dominator}."
        return "error", text
    return "success", (f"Die Dominanz ohne Besuchsmenge **trifft** hier den besten Weg {fmt_route(a.wrong.route)} mit {fmt_num(a.wrong.value)} (ohne Garantie: "
                       f"an diesen Dualpreisen, nicht allgemein); sie erzeugt {a.wrong.generated} Labels, mit Menge sind es {a.right.generated}.")


def verdict_search(missed: list, total: int) -> tuple[str, str]:
    """Suche über `total` Sätze von Dualpreisen: in wie vielen verfehlt die Dominanz ohne Menge den besten Weg?"""
    if not missed:
        return "info", f"In {fmt_int(total)} Sätzen ganzzahliger Dualpreise verfehlt die Dominanz ohne Besuchsmenge den besten Weg nie."
    seeds = ", ".join(str(s) for s, _ in missed[:3])
    return "warning", (f"Die Dominanz ohne Besuchsmenge verfehlt den besten Weg in {len(missed)} von {fmt_int(total)} Sätzen ganzzahliger Dualpreise "
                       f"({'Zufalls-Seed' if len(missed) == 1 else 'Zufalls-Seeds'} {seeds}{', …' if len(missed) > 3 else ''}). Der Fehler ist selten, aber vorhanden.")


def verdict_size(a: SizeAnalysis) -> tuple[str, str]:
    """Experiment 3: Labels und Vergleiche der elementaren Rechnung gegen Gedächtnis k = 1 und gegen die Rechnung ohne Dominanz an einer Zufallsinstanz."""
    e, k1, none = a.elementary, a.k1, a.none
    if e.aborted:
        return "warning", (f"Bei n = {a.n} Kunden und Fensterbreite {a.width} bricht die elementare Rechnung nach {fmt_int(C.MAX_COMPS)} Dominanzvergleichen ab; bis dahin hat sie "
                           f"{fmt_int(e.generated)} Labels erzeugt, also {fmt_dec(e.comps / e.generated)} Vergleiche je Label. Mit Gedächtnis k = 1 sind es für den ganzen Aufruf nur {fmt_int(k1.generated)} Labels.")
    none_txt = f"mehr als {fmt_int(C.MAX_LABELS_NO_DOMINANCE)}" if none.aborted else fmt_int(none.generated)
    return "info", (f"Bei n = {a.n} Kunden und Fensterbreite {a.width} erzeugt die elementare Rechnung {fmt_int(e.generated)} Labels und braucht {fmt_int(e.comps)} Dominanzvergleiche, "
                    f"das sind {fmt_dec(e.comps / e.generated)} je Label; mit Gedächtnis k = 1 sind es {fmt_int(k1.generated)} Labels, ohne Dominanz {none_txt}.")


def verdict_wall(rows: list[dict], width: int) -> tuple[str, str]:
    """Experiment 4: Vergleiche je Label, elementar gegen k = 5, über die gemessenen Kundenzahlen (nur fertige Läufe)."""
    both = [(r["elementar"]["vergleiche_je_label"], r["k5"]["vergleiche_je_label"]) for r in rows
            if r["elementar"]["vergleiche_je_label"] is not None and r["k5"]["vergleiche_je_label"] is not None]
    elem = [e for e, _ in both]
    k5 = [k for _, k in both]
    ratios = [e / k for e, k in both]
    first, last = rows[0], rows[-1]
    return "info", (f"Bei Fensterbreite {width} liegen die Dominanzvergleiche je Label bei k = 5 zwischen {fmt_dec(min(k5))} und {fmt_dec(max(k5))}, bei der elementaren Rechnung zwischen "
                    f"{fmt_dec(min(elem))} und {fmt_dec(max(elem))}: je nach Kundenzahl das {fmt_dec(min(ratios))}- bis {fmt_dec(max(ratios))}-Fache (n = {first['n']} bis {last['n']}, nur fertige Läufe; bei n = {last['n']} "
                    f"sind {last['elementar']['fertig']} von {last['elementar']['laeufe']} elementaren Läufen fertig). Die Zahl der Labels allein zeigt die Wand nicht.")


def verdict_abort(rows: list[dict], n: int = 30) -> tuple[str, str]:
    """Experiment 5: wie viele elementare Läufe brechen je Fensterbreite an der Zeitgrenze ab, und in welchem Pricing-Aufruf?"""
    parts = [f"Breite {r['breite']}: {r['abgebrochen']} von {r['laeufe']}" for r in rows]
    total_ab = sum(r["abgebrochen"] for r in rows)
    first = sum(r["im_ersten_aufruf"] for r in rows)
    return "warning" if total_ab else "info", (f"Bei n = {n} Kunden brechen elementare Läufe an der Zeitgrenze von 30 Sekunden je Pricing-Aufruf ab ({'; '.join(parts)}). "
                                              f"Von {total_ab} abgebrochenen Läufen brachen {first} schon im ersten Pricing-Aufruf ab, also mit den Dualpreisen der Einzelfahrten.")
