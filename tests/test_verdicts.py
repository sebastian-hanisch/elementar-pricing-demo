"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Schwelle der Art und jede Zahl im Text steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zahlen, keine Seeds."""

import epr_constants as C
import epr_evaluation as ev


def test_verdict_hand_elementary_success_and_error_name_their_numbers():
    kind, text = ev.verdict_hand(7, 7, -10, (2, 7, 6), -10, (2, 7, 6), 79, 56, 34)
    assert kind == "success"
    assert "einen besten Weg 2-7-6 mit reduzierten Kosten −10" in text and "aller 79 zulässigen elementaren Routen" in text
    assert "Es erzeugt 56 Labels; bei 34 Dominanzprüfungen" in text and "nur die Besuchsmenge verhinderte es" in text
    kind, text = ev.verdict_hand(7, 7, -9, (2, 7), -10, (2, 7, 6), 79, 50, 3)
    assert kind == "error" and "findet 2-7 mit −9" in text and "2-7-6 mit −10" in text


def test_verdict_hand_right_value_but_wrong_route_is_an_error():
    assert ev.verdict_hand(7, 7, -10, (7, 6, 2), -10, (2, 7, 6), 79, 56, 34)[0] == "error"


def test_verdict_hand_small_memory_three_branches():
    kind, text = ev.verdict_hand(1, 7, -18, (7, 6, 7, 6), -10, (2, 7, 6), 79, 62, 0)
    assert kind == "info" and "Kreise erlaubt" in text and "7-6-7-6 mit −18" in text and "besser als die beste elementare Route 2-7-6 mit −10" in text
    assert "Es erzeugt 62 Labels; keine Dominanzprüfung scheitert nur an der Besuchsmenge." in text
    kind, text = ev.verdict_hand(3, 7, -10, (2, 7, 6), -10, (2, 7, 6), 79, 55, 7)
    assert kind == "info" and "denselben Weg 2-7-6 mit −10" in text and "bei 7 Dominanzprüfungen" in text
    kind, text = ev.verdict_hand(3, 7, -8, (2, 7), -10, (2, 7, 6), 79, 55, 7)
    assert kind == "warning" and "k = 3" in text


def test_verdict_memory_lists_every_memory_and_the_pairs():
    rows = [{"k": 1, "blocked": 0, "generated": 62, "pairs": 0}, {"k": 7, "blocked": 34, "generated": 56, "pairs": 31}]
    kind, text = ev.verdict_memory(rows, 7)
    assert kind == "info" and "k = 1: 0 Prüfungen, 62 Labels" in text and "elementar (k = 7): 34 Prüfungen, 56 Labels" in text and "31 Paare" in text


class _Run:
    def __init__(self, value, route, generated):
        self.value, self.route, self.generated = value, route, generated


class _Nomem:
    def __init__(self, misses, right=(-11, (3, 6, 7)), wrong=(-10, (2, 7, 6)), loss=None):
        self.right, self.wrong = _Run(*right, 56), _Run(*wrong, 52)
        self.ref_value, self.ref_route, self.n_routes, self.misses, self.loss = -11, (3, 6, 7), 79, misses, loss


def test_verdict_nomem_three_branches():
    kind, text = ev.verdict_nomem(_Nomem(True, loss=ev.Loss((3, 6), 24, 32)))
    assert kind == "error" and "**verfehlt**" in text and "2-7-6 mit −10" in text and "3-6-7 mit −11" in text and "aller 79 zulässigen Routen" in text
    assert "Vorstufe 3-6 (L24), gestrichen von L32" in text
    kind, text = ev.verdict_nomem(_Nomem(False, wrong=(-11, (3, 6, 7))))
    assert kind == "success" and "**trifft**" in text and "ohne Garantie" in text and "sie erzeugt 52 Labels, mit Menge sind es 56" in text
    kind, text = ev.verdict_nomem(_Nomem(False, right=(-10, (2, 7, 6))))
    assert kind == "error" and "der Kern ist fehlerhaft" in text


def test_verdict_search_both_branches():
    kind, text = ev.verdict_search([], 3000)
    assert kind == "info" and "3 000 Sätzen" in text and "nie" in text
    kind, text = ev.verdict_search([(1778, (2, 4, 13, 4, 2, 5, 13))], 3000)
    assert kind == "warning" and "in 1 von 3 000 Sätzen" in text and "Zufalls-Seed 1778" in text and "…" not in text
    kind, text = ev.verdict_search([(1, ()), (2, ()), (3, ()), (4, ())], 3000)
    assert "in 4 von 3 000" in text and "Zufalls-Seeds 1, 2, 3, …" in text


def _stats(generated, comps, aborted=False, blocked=0):
    return ev.RunStats(generated, 0, comps, blocked, aborted, 0.0, (), (), ())


def test_verdict_size_finished_and_aborted():
    size = ev.SizeAnalysis(10, 100, 0, _stats(634, 47529), _stats(421, 0), _stats(772, 0))
    kind, text = ev.verdict_size(size)
    assert kind == "info" and "n = 10 Kunden und Fensterbreite 100" in text and "634 Labels" in text and "47 529 Dominanzvergleiche" in text and "75,0 je Label" in text
    assert "k = 1 sind es 421 Labels, ohne Dominanz 772" in text
    size = ev.SizeAnalysis(20, 100, 0, _stats(11754, C.MAX_COMPS, aborted=True), _stats(3310, 0), _stats(33280, 0))
    kind, text = ev.verdict_size(size)
    assert kind == "warning" and "bricht die elementare Rechnung nach 10 000 000 Dominanzvergleichen ab" in text and "11 754 Labels" in text
    assert "850,8 Vergleiche je Label" in text and "3 310" in text
    size = ev.SizeAnalysis(20, 100, 0, _stats(5000, 100000), _stats(100, 0), _stats(C.MAX_LABELS_NO_DOMINANCE, 0, aborted=True))
    assert "ohne Dominanz mehr als 100 000" in ev.verdict_size(size)[1]
    assert size.per_label == 20.0 and _stats(100, 50, blocked=25).alive == 100


def _wall_row(n, e_fertig, e_per, k5_per):
    def cell(per, fertig):
        return {"laeufe": 6, "fertig": fertig, "labels_median": 1.0, "gestrichen_prozent": 50.0, "vergleiche_median": 1.0, "vergleiche_je_label": per}

    return {"n": n, "k1": cell(5.0, 6), "k5": cell(k5_per, 6), "elementar": cell(e_per, e_fertig)}


def test_verdict_wall_uses_the_extremes_and_the_ratio():
    rows = [_wall_row(10, 6, 20.0, 10.0), _wall_row(20, 6, 400.0, 10.0), _wall_row(30, 2, 500.0, 12.5)]
    kind, text = ev.verdict_wall(rows, 100)
    assert kind == "info" and "Fensterbreite 100" in text and "bei k = 5 zwischen 10,0 und 12,5" in text and "elementaren Rechnung zwischen 20,0 und 500,0" in text
    assert "das 2,0- bis 40,0-Fache" in text and "n = 10 bis 30" in text and "bei n = 30 sind 2 von 6 elementaren Läufen fertig" in text


def test_growth_factors_and_last_complete_row_skip_incomplete_cells():
    rows = [_wall_row(10, 6, 1, 1), _wall_row(15, 6, 1, 1), _wall_row(20, 2, 1, 1)]
    for row, labels in zip(rows, (100.0, 400.0, 900.0)):
        row["elementar"]["labels_median"] = labels
    assert ev.growth_factors(rows) == [4.0]                  # n = 20 ist nicht vollständig fertig: kein Faktor 15 -> 20
    assert ev.last_complete_row(rows)["n"] == 15
    assert ev.last_complete_row([_wall_row(10, 3, 1, 1)])["n"] == 10


def test_verdict_abort_counts_and_kind():
    rows = [{"breite": 40, "laeufe": 6, "abgebrochen": 0, "im_ersten_aufruf": 0, "fertig": 6},
            {"breite": 100, "laeufe": 6, "abgebrochen": 4, "im_ersten_aufruf": 4, "fertig": 2},
            {"breite": 200, "laeufe": 6, "abgebrochen": 6, "im_ersten_aufruf": 5, "fertig": 0}]
    kind, text = ev.verdict_abort(rows, 30)
    assert kind == "warning" and "Breite 40: 0 von 6; Breite 100: 4 von 6; Breite 200: 6 von 6" in text
    assert "Von 10 abgebrochenen Läufen brachen 9 schon im ersten Pricing-Aufruf ab" in text
    assert ev.verdict_abort([rows[0]], 30)[0] == "info"


def test_condition_summary_names_every_condition_with_its_comparison():
    import epr_algorithm as A

    o = A.Label(12, -11, 3, (1 << 6) | (1 << 7), 6, 0)
    new = A.Label(15, -5, 4, (1 << 3) | (1 << 6), 6, 0)
    assert ev.condition_summary(o, new, 7) == "Kosten: −11 ≤ −5 ✓; Zeit: 12 ≤ 15 ✓; Last: 3 ≤ 4 ✓; Besuchsmenge: {6,7} ⊄ {3,6} ✗"
    assert ev.condition_summary(new, o, 7) == "Kosten: −5 > −11 ✗; Zeit: 15 > 12 ✗; Last: 4 > 3 ✗; Besuchsmenge: {3,6} ⊄ {6,7} ✗"


def test_number_formats():
    assert ev.fmt_num(-10) == "−10" and ev.fmt_num(2.5) == "2,50" and ev.fmt_num(-0.5) == "−0,50"
    assert ev.fmt_int(1234567) == "1 234 567" and ev.fmt_pct(54.57) == "54,6 %" and ev.fmt_dec(8.64) == "8,6"
    assert ev.fmt_set(0b101010, 7) == "{1,3,5}" and ev.fmt_route(()) == "keine" and ev.fmt_route((2, 7, 6)) == "2-7-6"
    assert ev.memory_label(1, 7) == "k = 1" and ev.memory_label(7, 7) == "elementar (k = 7)"
