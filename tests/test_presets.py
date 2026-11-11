"""Schnellstart-Szenarien: Vollständigkeit, gültige Werte, Standard-Szenario = Standardeinstellungen, und die erwartete Verdikt-Zeile je Szenario (DEMO-PLAYBOOK §11a Punkt 7)."""

import pytest

import epr_constants as C
import epr_evaluation as ev
import epr_presets as P

DEFAULT = "Erste Runde, elementar (Voreinstellung)"
# Erwartung je Szenario: Art des Verdikts im Handbeispiel, Art des Verdikts der Gegenprobe (Experiment 2, Dualpreise des Szenarios), Art und Textstück des Verdikts im Größenversuch
EXPECTED = {
    "Erste Runde, elementar (Voreinstellung)": ("success", "success", "info", "634 Labels"),
    "Dualpreise B: Dominanz ohne Menge": ("success", "error", "info", "634 Labels"),
    "Kleines Gedächtnis (k = 1)": ("info", "success", "info", "634 Labels"),
    "20 Kunden, Breite 100: die Rechnung wird fertig": ("success", "success", "info", "5 844 Labels"),
    "20 Kunden, Breite 100: Abbruch am Budget": ("success", "success", "warning", "bricht die elementare Rechnung nach 10 000 000 Dominanzvergleichen ab"),
    "10 Kunden, Breite 40: kleines Beispiel": ("success", "success", "info", "188 Labels"),
}


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(EXPECTED)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_widget_bounds():
    for name, preset in C.PRESETS.items():
        assert preset["memory"] in C.MEMORY_OPTIONS and preset["width"] in C.WIDTH_OPTIONS, name
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["seed"] <= C.SEED_MAX, name
        assert all(C.DUAL_MIN <= preset[f"pi{i}"] <= C.DUAL_MAX for i in range(1, 8)), name


def test_default_preset_equals_the_default_settings():
    preset = C.PRESETS[DEFAULT]
    assert next(iter(C.PRESETS)) == DEFAULT
    for state_key, spec in P.SETTING_SPECS.items():
        key = next(k for k, v in P.PRESET_KEYS.items() if v == state_key)
        assert preset[key] == spec.default, state_key


def test_setting_specs_cover_every_preset_key_and_choices_are_the_constants():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    assert P.SETTING_SPECS["memory_radio"].choices == C.MEMORY_OPTIONS and P.SETTING_SPECS["width_radio"].choices == C.WIDTH_OPTIONS


def test_the_duals_of_the_scenarios_are_the_stated_ones():
    first = tuple(C.PRESETS[DEFAULT][f"pi{i}"] for i in range(1, 8))
    b = tuple(C.PRESETS["Dualpreise B: Dominanz ohne Menge"][f"pi{i}"] for i in range(1, 8))
    assert first == C.HAND_DUALS_FIRST == (6, 6, 10, 6, 6, 6, 10) and b == C.HAND_DUALS_B == (2, 4, 13, 4, 2, 5, 13)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_expected_verdict_lines_of_every_preset(name):
    hand_kind, nomem_kind, size_kind, size_piece = EXPECTED[name]
    p = C.PRESETS[name]
    a = ev.analyse_hand(p["memory"])
    kind, _ = ev.verdict_hand(p["memory"], 7, a.result.value, a.result.route, a.ref_value, a.ref_route, a.n_routes, a.result.generated, a.result.blocked)
    assert kind == hand_kind
    kind, _ = ev.verdict_nomem(ev.analyse_nomem(tuple(p[f"pi{i}"] for i in range(1, 8))))
    assert kind == nomem_kind
    kind, text = ev.verdict_size(ev.size_experiment(p["n"], p["width"], p["seed"]))
    assert kind == size_kind and size_piece in text, text


def test_the_help_texts_state_what_the_scenarios_show():
    """Hilfetexte sind Behauptungen: k = 1 hat keine an der Menge scheiternde Prüfung; das Abbruch-Szenario erreicht das Budget, das andere 20-Kunden-Szenario nicht."""
    assert ev.analyse_hand(1).result.blocked == 0 and "keine Dominanzprüfung scheitert dann an der Besuchsmenge" in C.PRESET_HELP["Kleines Gedächtnis (k = 1)"]
    assert ev.size_experiment(20, 100, 0).elementary.aborted and "bricht ab" in C.PRESET_HELP["20 Kunden, Breite 100: Abbruch am Budget"]
    assert not ev.size_experiment(20, 100, 1).elementary.aborted and "bleibt unter dem Vergleichsbudget" in C.PRESET_HELP["20 Kunden, Breite 100: die Rechnung wird fertig"]
    assert "10 Millionen Dominanzvergleichen" in C.PRESET_HELP["20 Kunden, Breite 100: Abbruch am Budget"] and C.MAX_COMPS == 10_000_000
    nm = ev.analyse_nomem(C.HAND_DUALS_B)
    assert nm.misses and nm.wrong.value != nm.ref_value and "verfehlt" in C.PRESET_HELP["Dualpreise B: Dominanz ohne Menge"]


def test_the_small_example_scenario_has_few_labels():
    s = ev.size_experiment(10, 40, 0)
    assert (s.elementary.generated, s.k1.generated, s.none.generated) == (188, 138, 193) and not s.elementary.aborted
