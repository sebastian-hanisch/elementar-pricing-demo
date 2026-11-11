"""End-to-end-Tests über Streamlits AppTest: lädt app.py mit den Standardeinstellungen, klickt jeden Knopf, fährt jeden Regler an seine Grenzen, wählt jede Option,
prüft den Permalink und je Schnellstart-Szenario die erwartete Verdikt-Zeile. Expander werden nie per Index angesprochen (DEMO-PLAYBOOK §2 Punkt 7)."""

import os
import re

import pytest
from streamlit.testing.v1 import AppTest

import epr_constants as C
import epr_presets as P

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "▶"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen
SLIDER_KEYS = [k for k, spec in P.SETTING_SPECS.items() if spec.choices is None and spec.hi is not None and k != "seed_input"]


def _fresh_app(query=None) -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    if query:
        at.query_params.update(query)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at, kind):
    return [e.value for e in getattr(at, kind)]


def test_app_loads_without_exception():
    at = _fresh_app()
    assert at.title[0].value.endswith("Elementarität im Pricing: die Wand")


def test_the_buttons_are_the_presets_and_the_new_instance_button():
    labels = [b.label for b in _fresh_app().button]
    assert labels[: len(C.PRESETS)] == list(C.PRESETS) and labels[len(C.PRESETS):] == ["🎲 Neue Instanz generieren"]


@pytest.mark.parametrize("index", range(len(C.PRESETS) + 1))
def test_every_button_click_does_not_raise(index):
    at = _fresh_app()
    label = at.button[index].label
    if AUTOPLAY_MARKER in label:
        pytest.skip("Auto-Play")
    at.button[index].click().run(timeout=TIMEOUT)
    assert not at.exception, (label, [str(e) for e in at.exception])


@pytest.mark.parametrize("state_key", SLIDER_KEYS)
@pytest.mark.parametrize("edge", ["min", "max"])
def test_every_slider_at_its_min_and_max_does_not_raise(state_key, edge):
    at = _fresh_app()
    spec = P.SETTING_SPECS[state_key]
    at.sidebar.slider(key=state_key).set_value(int(spec.lo if edge == "min" else spec.hi)).run(timeout=TIMEOUT)
    assert not at.exception, (state_key, edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("key,options", [("memory_radio", C.MEMORY_OPTIONS), ("width_radio", C.WIDTH_OPTIONS)])
def test_every_option_of_every_choice_widget_does_not_raise(key, options):
    for option in options:
        at = _fresh_app()
        at.sidebar.radio(key=key).set_value(option).run(timeout=TIMEOUT)
        assert not at.exception, (key, option, [str(e) for e in at.exception])


@pytest.mark.parametrize("n,width,seed", [(C.N_MIN, 40, 0), (C.N_MIN, 100, C.SEED_MAX), (C.N_MAX, 40, 0), (C.N_MAX, 100, C.SEED_MAX), (C.N_MAX, 100, 0)])
def test_corner_matrix_and_worst_case_at_the_widget_maximum(n, width, seed):
    """Eckfall-Matrix (DEMO-PLAYBOOK §1d) und Worst-Case am Regler-Maximum (§1c): Kundenzahl und Fensterbreite an den Rändern, Zufalls-Seed am Minimum und Maximum;
    n = 20 mit Breite 100 und Zufalls-Seed 0 erreicht das Vergleichsbudget und muss trotzdem fertig werden."""
    at = _fresh_app()
    at.sidebar.slider(key="n_slider").set_value(n)
    at.sidebar.radio(key="width_radio").set_value(width)
    at.sidebar.number_input(key="seed_input").set_value(seed)
    at.run(timeout=TIMEOUT)
    assert not at.exception, ((n, width, seed), [str(e) for e in at.exception])
    assert at.sidebar.slider(key="n_slider").value == n


def test_all_dual_prices_at_zero_and_at_the_maximum():
    at = _fresh_app()
    for i in range(1, 8):
        at.sidebar.slider(key=f"pi{i}_slider").set_value(C.DUAL_MIN)
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert any("trifft" in t for t in _texts(at, "success"))                          # nichts lohnt sich: ohne Menge wie mit Menge ohne Route
    for i in range(1, 8):
        at.sidebar.slider(key=f"pi{i}_slider").set_value(C.DUAL_MAX)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]


def test_permalink_sets_the_widgets_and_clamps_invalid_values():
    at = _fresh_app({"gedaechtnis": "3", "n": "14", "breite": "40", "seed": "7", "pi1": "9", "pi7": "99"})
    assert at.sidebar.radio(key="memory_radio").value == 3
    assert at.sidebar.slider(key="n_slider").value == 14 and at.sidebar.radio(key="width_radio").value == 40
    assert at.sidebar.number_input(key="seed_input").value == 7
    assert at.sidebar.slider(key="pi1_slider").value == 9 and at.sidebar.slider(key="pi7_slider").value == C.DUAL_MAX     # 99 wird auf das Maximum begrenzt
    bad = _fresh_app({"gedaechtnis": "5", "n": "999", "breite": "123", "seed": "-5", "pi2": "-3"})
    assert bad.sidebar.radio(key="memory_radio").value == C.DEFAULT_MEMORY and bad.sidebar.slider(key="n_slider").value == C.N_MAX
    assert bad.sidebar.radio(key="width_radio").value == C.DEFAULT_WIDTH and bad.sidebar.number_input(key="seed_input").value == 0
    assert bad.sidebar.slider(key="pi2_slider").value == C.DUAL_MIN
    garbage = _fresh_app({"n": "abc", "seed": "1.5", "gedaechtnis": "x"})
    assert garbage.sidebar.slider(key="n_slider").value == C.DEFAULT_N and garbage.sidebar.number_input(key="seed_input").value == C.DEFAULT_SEED


def test_query_params_follow_the_settings():
    at = _fresh_app()
    at.sidebar.radio(key="memory_radio").set_value(2).run(timeout=TIMEOUT)
    assert at.query_params["gedaechtnis"] in (["2"], "2")


def test_settings_in_the_url_match_the_setting_specs():
    assert {spec.url_param for spec in P.SETTING_SPECS.values()} == {"gedaechtnis", "n", "breite", "seed", *(f"pi{i}" for i in range(1, 8))}
    assert re.fullmatch(r"[a-z0-9]+", "".join(spec.url_param for spec in P.SETTING_SPECS.values()))


def test_sections_are_present_by_title_not_by_index():
    at = _fresh_app()
    expanders = {e.label: e for e in at.expander}
    assert "So funktioniert die elementare Suche" in expanders and expanders["So funktioniert die elementare Suche"].proto.expanded
    assert "📐 Mathematische Formulierung" in expanders and "⚠️ Annahmen, Grenzen und bekannte Probleme" in expanders
    subheaders = [s.value for s in at.subheader]
    for number in range(1, 6):
        assert any(s.startswith(f"🔬 Experiment {number}:") for s in subheaders), number
    assert any(s.startswith("🚧 Wo die Annahmen enden") for s in subheaders)
    math = expanders["📐 Mathematische Formulierung"].markdown[0].value
    assert math.startswith("**Lesehilfe.**") and "| Symbol | Bedeutung |" in math
    assert "Prüfstand" in math and "Volltexte sind nicht gelesen" in math


def test_assumptions_expander_text_equals_the_constant_and_the_readme():
    at = _fresh_app()
    box = next(e for e in at.expander if e.label == "⚠️ Annahmen, Grenzen und bekannte Probleme")
    assert box.markdown[0].value.strip() == C.ASSUMPTIONS_MARKDOWN.strip()
    readme = open(os.path.join(os.path.dirname(APP_PATH), "README.md"), encoding="utf-8").read()
    assert C.ASSUMPTIONS_MARKDOWN.strip() in readme


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_shows_its_expected_verdict_lines(name):
    at = _fresh_app()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    p = C.PRESETS[name]
    successes, infos, warnings, errors = _texts(at, "success"), _texts(at, "info"), _texts(at, "warning"), _texts(at, "error")
    if p["memory"] == 7:
        assert any(t.startswith("Mit der Besuchsmenge im Label (elementar, k = 7) findet das Verfahren einen besten Weg 2-7-6 mit reduzierten Kosten −10") for t in successes), name
    else:
        assert any(t.startswith(f"Mit Gedächtnis k = {p['memory']}") for t in infos), name
    duals = tuple(p[f"pi{i}"] for i in range(1, 8))
    if duals == C.HAND_DUALS_B:
        assert any(t.startswith("Die Dominanz ohne Besuchsmenge **verfehlt** den besten Weg: Sie findet 2-7-6 mit −10") for t in errors) and "3-6-7 mit −11" in " ".join(errors)
    else:
        assert any(t.startswith("Die Dominanz ohne Besuchsmenge **trifft** hier den besten Weg 2-7-6 mit −10") for t in successes), name
    size_text = f"n = {p['n']} Kunden und Fensterbreite {p['width']}"
    assert any(size_text in t for t in infos + warnings), name
    if (p["n"], p["width"], p["seed"]) == (20, 100, 0):
        assert any("bricht die elementare Rechnung nach 10 000 000 Dominanzvergleichen ab" in t for t in warnings)
    else:
        assert not any("bricht die elementare Rechnung" in t for t in warnings), name


def test_checkboxes_show_the_labels_that_stay_and_all_pairs():
    at = _fresh_app()
    frames = [d.value for d in at.dataframe if hasattr(d.value, "columns") and "Ereignis" in d.value.columns]
    assert frames and set(frames[0]["Ereignis"]) == {"neues Label verworfen"} and len(frames[0]) == 20
    pairs_before = [d.value for d in at.dataframe if hasattr(d.value, "columns") and "Label A" in d.value.columns]
    assert len(pairs_before[0]) == 8
    at.checkbox(key="show_all").set_value(True).run(timeout=TIMEOUT)
    at.checkbox(key="show_pairs").set_value(True).run(timeout=TIMEOUT)
    assert not at.exception
    frames = [d.value for d in at.dataframe if hasattr(d.value, "columns") and "Ereignis" in d.value.columns]
    assert "bleibt" in set(frames[0]["Ereignis"]) and len(frames[0]) == 55
    pairs_after = [d.value for d in at.dataframe if hasattr(d.value, "columns") and "Label A" in d.value.columns]
    assert len(pairs_after[0]) == 31


def test_memory_k1_shows_the_decisions_of_the_run():
    """Mit k = 1 werden im Handbeispiel 27 Labels sofort verworfen und 5 verdrängt: 32 Zeilen in der Entscheidungstabelle."""
    at = _fresh_app({"gedaechtnis": "1"})
    frames = [d.value for d in at.dataframe if hasattr(d.value, "columns") and "Ereignis" in d.value.columns]
    assert frames and len(frames[0]) == 32


def test_the_hand_example_table_and_the_overview_tables_have_the_stated_numbers():
    at = _fresh_app()
    frames = {tuple(d.value.columns): d.value for d in at.dataframe if hasattr(d.value, "columns")}
    memory = next(v for cols, v in frames.items() if "Gedächtnis" in cols and "Paare nebeneinander" in cols)
    assert list(memory["Erzeugte Labels"]) == [62, 58, 55, 56] and list(memory["Prüfungen nur an der Menge gescheitert"]) == [0, 5, 7, 34] and list(memory["Paare nebeneinander"])[-1] == 31
    colgen = next(v for cols, v in frames.items() if "Runde" in cols and "Master" in cols)
    assert list(colgen["erzeugte Labels"]) == [56, 51, 45, 41, 42, 44, 47] and list(colgen["Master"]) == ["50", "40", "32", "32", "32", "30", "30"]
    bands = next(v for cols, v in frames.items() if "Vergleiche je Label, elementar" in cols)
    assert list(bands["Kunden n"]) == [10, 15, 20, 25, 30]
