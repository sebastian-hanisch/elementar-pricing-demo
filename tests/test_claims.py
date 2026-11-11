"""Jede Zahl der README an festen Zufalls-Seeds (DEMO-PLAYBOOK §4, §11a): Handbeispiel und Gegenprobe exakt, Größenversuche neu gerechnet, die Messreihen aus ihren Rohzeilen
abgeleitet (die Tabellen der README müssen zeichengleich aus `data/laeufe.json` entstehen), eine Stichprobe der Messreihen mit dem Kern neu gerechnet.

Zeiten und Abbruchquoten werden nie festgeschrieben: Die Zeilen der Messreihe sind Daten, ihre Auswertung ist exakt, die Neurechnung der Stichprobe prüft Schranken (bis 1e-6)
und Zählungen in Bändern. Zahl-zu-Test-Tabelle: README, Abschnitt „Befunde“."""

import json
from pathlib import Path
from statistics import median

import pytest

import epr_constants as C
import epr_evaluation as ev
import epr_scenario as S

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _rows(lines):
    return [ln for ln in lines if ln.startswith("|")]


# --- Handbeispiel ---------------------------------------------------------------------------------------------------------------------------

def test_hand_example_numbers_of_the_readme():
    a = ev.analyse_hand(7)
    r = a.result
    assert (a.n_routes, a.ref_value, a.ref_route) == (79, -10, (2, 7, 6)) and (r.value, r.route) == (-10, (2, 7, 6))
    assert (r.generated, r.discarded, r.displaced, r.alive, r.blocked, len(a.pairs)) == (56, 20, 0, 36, 34, 31)
    for text in ("79 zulässige elementare Routen", "56 erzeugte Labels, 20 sofort verworfen, 0 verdrängt, 36 am Ende lebend", "Bei 34 Dominanzprüfungen", "31 Paare lebender Labels",
                 "bester Wert −10, zum Beispiel mit 2-7-6"):
        assert text in README, text
    pairs = ev.pair_rows(a)
    example = next(p for p in pairs if p["Label A"].startswith("L8 (Weg 2-1") and "Weg 3-1" in p["Label B"])
    assert "Kosten −7, Last 4, Menge {1,2}" in example["Label A"] or "Zeit 18, Kosten −7, Last 4, Menge {1,2}" in example["Label A"]
    assert "Zeit 18, Kosten −5, Last 4, Menge {1,3}" in example["Label B"] and example["fehlt in B"] == "{2}"
    assert "2-1 mit Kosten −7 und 3-1 mit Kosten −5, beide Zeit 18, Last 4: die Menge {2} fehlt in {1,3}" in README


def test_memory_table_of_the_readme():
    rows = {r["k"]: r for r in ev.compare_memory()}
    assert [(rows[k]["generated"], rows[k]["blocked"], rows[k]["value"], rows[k]["route"]) for k in (1, 2, 3, 7)] == \
        [(62, 0, -18, (7, 6, 7, 6)), (58, 5, -14, (5, 3, 5, 1)), (55, 7, -10, (2, 7, 6)), (56, 34, -10, (2, 7, 6))]
    assert [rows[k]["elementary"] for k in (1, 2, 3, 7)] == [False, False, True, True]
    assert "k = 1: 62 / 0 / −18 (Route 7-6-7-6 mit Kreis); k = 2: 58 / 5 / −14 (Route 5-3-5-1); k = 3: 55 / 7 / −10 (Route 2-7-6); elementar: 56 / 34 / −10" in README


def test_column_generation_numbers_of_the_readme():
    cg = ev.colgen_hand()
    assert (len(cg.rounds), cg.labels, cg.bound) == (7, 326, 30) and ev.G.bound_over_all_routes(S.hand_instance()) == (30, 79)
    assert "7 Runden, 326 erzeugte Labels, Schranke 30; ein Master über alle 79 Routen ergibt 30" in README


def test_counterexample_numbers_of_the_readme():
    first = ev.analyse_nomem(C.HAND_DUALS_FIRST)
    assert (first.wrong.value, first.wrong.route, first.wrong.generated, first.right.generated, first.misses) == (-10, (2, 7, 6), 54, 56, False)
    b = ev.analyse_nomem(C.HAND_DUALS_B)
    assert (b.misses, b.wrong.value, b.wrong.route, b.ref_value, b.ref_route, b.right.value, b.right.route) == (True, -10, (2, 7, 6), -11, (3, 6, 7), -11, (3, 6, 7))
    for text in ("trifft sie den besten Weg (2-7-6, −10) mit 54 statt 56 Labels", "B = (2, 4, 13, 4, 2, 5, 13)", "findet 2-7-6 mit −10, die Aufzählung 3-6-7 mit −11; mit Menge wird 3-6-7 gefunden",
                 "In 1 von 3 000 Sätzen ganzzahliger Dualpreise (2 bis 14, Zufalls-Seeds 0 bis 2999)", "Zufalls-Seed 1778 = Dualpreise B"):
        assert text in README, text
    assert (C.SEARCH_SETS, C.SEARCH_LOW, C.SEARCH_HIGH) == (3000, 2, 14) and ev.search_counterexamples() == [(1778, C.HAND_DUALS_B)]


def _subnet_md(rows):
    lines = []
    for r in rows:
        factor = "–" if r["faktor"] is None else ev.fmt_dec(r["faktor"], 2)
        lines.append(f"| {r['m']} | {ev.fmt_int(r['elementar'])} | {ev.fmt_int(r['uebrig'])} | {ev.fmt_int(r['ohne_dominanz'])} | {ev.fmt_int(r['k1'])} | {ev.fmt_int(r['wege'])} | {factor} |")
    return lines


@pytest.mark.parametrize("variant", ["A", "B"])
def test_subnet_tables_of_the_readme_are_the_computed_ones(variant):
    for line in _subnet_md(ev.subnet_rows(variant)):
        assert line in README, line


def test_variant_b_growth_sentences_of_the_readme():
    rows = ev.subnet_rows("B")
    factors = [r["faktor"] for r in rows[1:]]
    ratios = [b["wege"] / a["wege"] for a, b in zip(rows[1:], rows[2:])]
    assert (round(min(factors), 2), round(max(factors), 2)) == (2.62, 3.10) and (round(min(ratios), 1), round(max(ratios), 1)) == (4.3, 7.0)
    assert (rows[0]["elementar"], rows[-1]["elementar"], rows[0]["wege"], rows[-1]["wege"], rows[-1]["ohne_dominanz"]) == (5, 962, 4, 13603, 13604)
    assert (rows[-1]["k1"], rows[-1]["elementar"]) == (1061, 962)
    for text in ("um das 2,62- bis 3,10-Fache, die Zahl der zulässigen elementaren Routen (m = 4 bis 7) um das 4,3- bis 7,0-Fache", "von 5 bei 2 Kunden auf 962 bei 7, die zulässigen elementaren Routen von 4 auf 13 603",
                 "ohne Dominanz entstehen 13 604 Labels", "(1 061 gegen 962 Labels)"):
        assert text in README, text


# --- Größenversuche -------------------------------------------------------------------------------------------------------------------------

def test_live_size_runs():
    a = ev.size_experiment(10, 100, 0)
    assert (a.elementary.generated, a.elementary.comps, round(a.per_label, 1), a.k1.generated, a.none.generated) == (634, 47529, 75.0, 421, 772)
    b = ev.size_experiment(20, 100, 1)
    assert (b.elementary.generated, b.elementary.comps, round(b.per_label, 1), b.k1.generated, b.none.generated) == (5844, 2000502, 342.3, 1761, 7542)
    c = ev.size_experiment(20, 100, 0)
    assert (c.elementary.aborted, c.elementary.comps, c.elementary.generated, c.k1.generated) == (True, 10000152, 11754, 3310)
    d = ev.size_experiment(10, 40, 0)
    assert (d.elementary.generated, d.elementary.comps, d.k1.generated, d.none.generated) == (188, 6661, 138, 193)
    for text in ("10 Kunden (Zufalls-Seed 0): 634 Labels, 47 529 Dominanzvergleiche (75,0 je Label); mit k = 1 421 Labels, ohne Dominanz 772",
                 "20 Kunden (Zufalls-Seed 1): 5 844 Labels, 2 000 502 Vergleiche (342,3 je Label)",
                 "20 Kunden (Zufalls-Seed 0): Abbruch nach 10 Millionen Vergleichen bei 11 754 Labels",
                 "| 634 Labels, 47 529 Vergleiche; mit k = 1 421 Labels, ohne Dominanz 772 |", "| 5 844 Labels, 2 000 502 Vergleiche; mit k = 1 1 761 Labels, ohne Dominanz 7 542 |",
                 "| Abbruch nach 10 000 152 Vergleichen (Budget 10 Millionen) bei 11 754 Labels; mit k = 1 3 310 Labels |",
                 "| 188 Labels, 6 661 Vergleiche; mit k = 1 138 Labels, ohne Dominanz 193 |"):
        assert text in README, text
    assert C.MAX_COMPS == 10_000_000 and a.share_blocked > 0


# --- Messreihen: Rohzeilen, Auswertung, Stichprobe ------------------------------------------------------------------------------------------

def test_the_rows_of_the_measurement_series_are_complete_and_cite_their_source():
    rows = ev.load_runs()
    assert len(rows) == 198 and all(r["quelle"].startswith("tools/bands_bauen.py messen") for r in rows)
    keys = {(r["breite"], r["n"], r["seed"], r["k"]) for r in rows}
    assert len(keys) == len(rows)
    cells = {(r["breite"], r["n"], ev.mode_of(r)) for r in rows}
    assert len(cells) == 2 * 5 * 3 + 3                                      # Breite 40 und 100 mal 5 Kundenzahlen mal 3 Gedächtnisse, dazu n = 30 bei Breite 200
    assert {r["seed"] for r in rows} == set(range(C.PER_CLUSTER)) and all(r["zeitgrenze_je_aufruf"] == 30.0 for r in rows)
    for r in rows:
        assert r["abgebrochen"] == (r["schranke"] is None) and (r["abbruch_runde"] is not None) == r["abgebrochen"]
        assert r["labels"] > 0 and r["vergleiche"] >= 0 and 0 <= r["scheitert_an_menge"] <= r["vergleiche"]
        assert r["gestrichen"] <= r["labels"]
        if not (r["k"] >= r["n"]):
            assert not r["abgebrochen"]
    elementary_aborted = [r for r in rows if r["abgebrochen"]]
    assert all(r["k"] == r["n"] and r["n"] == 30 for r in elementary_aborted)
    assert "Zeitgrenze 30 Sekunden je Pricing-Aufruf, 120 Sekunden je Spaltenerzeugung" in README


def _wall_md(row):
    e, k5, k1 = row["elementar"], row["k5"], row["k1"]

    def pct(x):
        return ev.fmt_pct(x)

    return (f"| {row['n']} | {e['fertig']} von {e['laeufe']} | {ev.fmt_int(round(e['labels_median']))} | {ev.fmt_int(round(k5['labels_median']))} | {ev.fmt_int(round(k1['labels_median']))} | "
            f"{pct(e['gestrichen_prozent'])} | {pct(k5['gestrichen_prozent'])} | {ev.fmt_int(round(e['vergleiche_median']))} | {ev.fmt_int(round(k5['vergleiche_median']))} | "
            f"{ev.fmt_dec(e['vergleiche_je_label'])} | {ev.fmt_dec(k5['vergleiche_je_label'])} |")


@pytest.mark.parametrize("width", [100, 40])
def test_wall_tables_of_the_readme_are_derived_from_the_rows(width):
    table = ev.wall_table(ev.load_runs(), width)
    assert [r["n"] for r in table] == [10, 15, 20, 25, 30]
    for row in table:
        assert _wall_md(row) in README, _wall_md(row)


def test_wall_sentences_of_the_readme():
    t100, t40 = ev.wall_table(ev.load_runs(), 100), ev.wall_table(ev.load_runs(), 40)
    elem = [r["elementar"]["vergleiche_je_label"] for r in t100]
    k5 = [r["k5"]["vergleiche_je_label"] for r in t100]
    assert [round(x, 1) for x in elem] == [17.3, 51.3, 346.4, 214.6, 474.0] and [round(x, 1) for x in k5] == [8.6, 9.9, 11.5, 11.9, 12.1]
    row25 = next(r for r in t100 if r["n"] == 25)
    assert round(row25["elementar"]["labels_median"] / row25["k5"]["labels_median"], 1) == 1.5
    assert round(row25["elementar"]["vergleiche_median"] / row25["k5"]["vergleiche_median"], 1) == 23.5
    assert [round(g, 1) for g in ev.growth_factors(t100)] == [5.7, 2.7, 2.6]
    assert [r["elementar"]["fertig"] for r in t100] == [6, 6, 6, 6, 2] and [r["elementar"]["fertig"] for r in t40] == [6, 6, 6, 6, 6]
    for text in ("elementar 17,3 / 51,3 / 346,4 / 214,6 / 474,0 bei n = 10 / 15 / 20 / 25 / 30, k = 5: 8,6 / 9,9 / 11,5 / 11,9 / 12,1", "das 1,5-Fache der Labels und das 23,5-Fache der Vergleiche von k = 5",
                 "5,7 (10 auf 15), 2,7 (15 auf 20) und 2,6 (20 auf 25)", "Die Vergleiche je Label der elementaren Rechnung steigen von 17,3 (n = 10)\nauf 474,0 (n = 30), aber nicht gleichmäßig: bei n = 25 ist der Wert (214,6) niedriger als bei n = 20 (346,4). Bei k = 5 liegen sie zwischen 8,6 und 12,1.",
                 "stammen die Mediane der elementaren Rechnung aus den 2 fertigen von 6 Läufen"):
        assert text in README, text
    assert (t100[-1]["elementar"]["labels_median"], t100[-1]["elementar"]["fertig"]) == (135326.5, 2)


def test_the_premeasured_numbers_agree_with_the_rows_up_to_the_documented_exception():
    """Die Neurechnung stimmt mit run_p07.log (Vormessung) in 29 von 30 Zellen überein (Zahl der fertigen Läufe, Median der Labels ganzzahlig gerundet); die Ausnahme ist 30 Kunden, Breite 100, elementar."""
    runs, pm = ev.load_runs(), ev.load_premeasured()
    equal, different = 0, []
    for v in pm["wand_median"]:
        mine = next(r for r in ev.wall_table(runs, v["breite"]) if r["n"] == v["n"])[ev.mode_of({"k": v["k"], "n": v["n"]})]
        same = mine["fertig"] == v["laeufe"] - v["abgebrochen"] and ((mine["labels_median"] is None and v["labels_median"] is None) or round(mine["labels_median"]) == v["labels_median"])
        equal += same
        if not same:
            different.append((v["breite"], v["n"], v["k"]))
    assert len(pm["wand_median"]) == 30 and equal == 29 and different == [(100, 30, 30)]
    assert all(v["quelle"].startswith("run_p07.log") for v in pm["wand_median"])
    assert "in 29 von 30 Zellen (2 Fensterbreiten × 5 Kundenzahlen × 3 Gedächtnisse)" in README and "dort sind in der Neurechnung 2 von 6 Läufen fertig, in der früheren Messung 3 von 6" in README


def test_abort_table_of_the_readme():
    runs, pm = ev.load_runs(), ev.load_premeasured()
    table = ev.abort_table(runs, 30)
    assert [(r["breite"], r["laeufe"], r["fertig"], r["abgebrochen"], r["im_ersten_aufruf"]) for r in table] == [(40, 6, 6, 0, 0), (100, 6, 2, 4, 4), (200, 6, 0, 6, 6)]
    v1 = {r["breite"]: r["abgebrochen"] for r in pm["abbrueche"] if r["gruppe"] == "V1"}
    assert v1 == {40: 0, 100: 3, 200: 6}
    for r in table:
        assert f"| {r['breite']} | {r['laeufe']} | {r['fertig']} | {r['abgebrochen']} | {r['im_ersten_aufruf']} | {v1[r['breite']]} |" in README
    assert "Breite 40: 0 von 6, Breite 100: 4 von 6, Breite 200: 6 von 6 abgebrochen; alle 10 abgebrochenen Läufe brachen im ersten Pricing-Aufruf ab" in README
    assert sum(r["abgebrochen"] for r in table) == sum(r["im_ersten_aufruf"] for r in table) == 10
    assert "In der Neurechnung brechen auf dem Messrechner bei 30 Kunden und Breite 100 4 von 6 elementaren Läufen" in README


def test_premeasured_rows_of_the_readme_are_marked_as_not_recomputed():
    pm = ev.load_premeasured()["abbrueche"]
    by = {r["bezeichnung"]: r for r in pm}
    v7 = [r for r in pm if r["gruppe"] == "V7"]
    assert [(r["breite"], r["laeufe"], r["abgebrochen"], r["im_ersten_aufruf"]) for r in v7] == [(100, 5, 4, 4), (100, 5, 4, 4), (60, 5, 5, 5)]
    v8 = next(r for r in pm if r["gruppe"] == "V8")
    assert (v8["laeufe"], v8["abgebrochen"], v8["im_ersten_aufruf"]) == (96, 94, 94)
    load = next(r for r in pm if r["gruppe"] == "P07b")
    assert (load["laeufe"], load["abgebrochen"], load["im_ersten_aufruf"]) == (6, 4, 4)
    assert all(r["nicht_neu_gerechnet"] for r in v7 + [v8, load]) and all(not r["nicht_neu_gerechnet"] for r in pm if r["gruppe"] == "V1")
    assert all(r["quelle"] for r in pm) and by
    assert ("30 Kunden, Breite 100: 3 von 6 (frühere Messung V1), 4 von 6 (fünf Rechnungen gleichzeitig); 30 Kunden, Überdeckungs-Master, Breite 100 zufällig verteilt und gruppiert je 4 von 5, "
            "Breite 60 5 von 5; 50 und 100 Kunden (8 Zellen mit je 12 Instanzen): 94 von 96; alle abgebrochenen im ersten Pricing-Aufruf") in README


def test_a_sample_of_the_measurement_series_is_recomputed_with_the_kernel():
    """n = 10 und 15, Breite 40 und 100, je 6 Instanzen und 3 Gedächtnisse (72 Läufe): Schranke gleich bis 1e-6, Labels und Vergleiche in Bändern (HiGHS kann bei
    entarteten Master-Problemen andere gleich gute Dualpreise wählen; auf dem Rechner der Messung stimmen die Zählungen exakt)."""
    colgen_ref = pytest.importorskip("colgen_ref")
    rows = {(r["breite"], r["n"], r["seed"], r["k"]): r for r in ev.load_runs()}
    exact = 0
    for width in (40, 100):
        for n in (10, 15):
            for seed in range(C.PER_CLUSTER):
                inst = S.make_instance(n, seed, width)
                for k in (1, 5, n):
                    got, row = colgen_ref.colgen(inst, k), rows[(width, n, seed, k)]
                    assert not got["aborted"] and got["bound"] == pytest.approx(row["schranke"], abs=1e-6), (width, n, seed, k)
                    assert got["generated"] == pytest.approx(row["labels"], rel=0.25), (width, n, seed, k)
                    assert got["comps"] == pytest.approx(row["vergleiche"], rel=0.35), (width, n, seed, k)
                    exact += (got["generated"], got["comps"], got["dominated"]) == (row["labels"], row["vergleiche"], row["gestrichen"])
    assert exact >= 36     # mindestens die Hälfte stimmt auch exakt (auf dem Rechner der Messung alle 72)


def test_the_first_pricing_call_of_the_rows_is_the_first_round():
    """`erste_runde_labels` ist die Zahl der Labels des ersten Pricing-Aufrufs (Dualpreise der ersten Runde) und stimmt mit dem Größenversuch überein (feste Zufalls-Seeds, Kern)."""
    rows = {(r["breite"], r["n"], r["seed"], r["k"]): r for r in ev.load_runs()}
    for n, width, seed in ((10, 100, 0), (15, 40, 3), (20, 100, 1)):
        size = ev.size_experiment(n, width, seed)
        assert rows[(width, n, seed, n)]["erste_runde_labels"] == size.elementary.generated
        assert rows[(width, n, seed, 1)]["erste_runde_labels"] == size.k1.generated


# --- Texte, die Zahlen aus Konstanten nennen -------------------------------------------------------------------------------------------------

def test_numbers_in_help_and_intro_texts_come_from_the_constants():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert f"({C.N_MIN} bis {C.N_MAX})" in app and "Zahl der Kunden der Zufallsinstanz" in app
    assert "bis zu 20 Kunden" in app and C.N_MAX == 20 and "bis 30 Kunden" in app
    assert "(5 bis 20 Kunden)" in README and "10 bis 30 Kunden" in README and C.N_MIN == 5
    assert (C.PER_CLUSTER, C.WIDTH_OPTIONS, C.DUAL_MIN, C.DUAL_MAX) == (6, (40, 100), 0, 20)
    assert json.loads((ROOT / "data" / "laeufe.json").read_text(encoding="utf-8"))["zeilen"][0]["zeitgrenze_je_aufruf"] == 30.0
    assert "Python 3.12 oder neuer" in README


def test_the_median_of_an_even_number_of_runs_is_the_mean_of_the_two_middle_ones():
    """Die Mediane der Tabellen sind echte Mediane (bei 6 Läufen das Mittel der beiden mittleren), ganzzahlig gerundet mit Python-round (gerade Zahl bei .5), wie in den Rohausgaben der Vormessung."""
    rows = [r for r in ev.load_runs() if r["breite"] == 100 and r["n"] == 10 and ev.mode_of(r) == "elementar"]
    values = sorted(r["labels"] for r in rows)
    assert len(values) == 6 and median(values) == (values[2] + values[3]) / 2 == ev.wall_table(ev.load_runs(), 100)[0]["elementar"]["labels_median"]
    assert round(982.5) == 982 and round(983.5) == 984     # Rundung zur geraden Zahl


def test_numbers_of_the_verification_section_come_from_the_oracle_tests():
    """Die Zahlen im Abschnitt „Verifikation“ der README (90 Zufallsinstanzen, 108 Fälle des Gedächtnisses) stehen so im Orakel-Test."""
    source = (ROOT / "tests" / "test_oracle_elementar_pricing.py").read_text(encoding="utf-8")
    assert "random_cases(90)" in source and "assert checked == 108" in source and "range(36)" in source and "(1, 2, 3)" in source
    assert "an 90 Zufallsinstanzen" in README and "(108 Fälle)" in README
    assert "Ein einmaliger Orakel-Lauf mit 300 Zufallsinstanzen (5 bis 7 Kunden" in README


def test_elementary_strikes_a_smaller_share_and_needs_more_comparisons_than_k5_in_every_cell():
    """Satz aus Einleitung der App und README: in allen 10 Zellen (2 Fensterbreiten, 5 Kundenzahlen) ist bei der elementaren Rechnung der Anteil gestrichener Labels kleiner und sind die Vergleiche je Label höher als bei k = 5."""
    cells = 0
    for width in (40, 100):
        for row in ev.wall_table(ev.load_runs(), width):
            e, k5 = row["elementar"], row["k5"]
            assert e["gestrichen_prozent"] < k5["gestrichen_prozent"] and e["vergleiche_je_label"] > k5["vergleiche_je_label"], (width, row["n"])
            cells += 1
    assert cells == 10
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "in allen 10 Zellen (2 Fensterbreiten, 5 Kundenzahlen)" in app and "in allen 10 Zellen aus 2 Fensterbreiten und 5 Kundenzahlen" in README
