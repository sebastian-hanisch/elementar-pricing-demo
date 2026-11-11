"""Elementarität im Pricing: die Wand - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Label-Verfahren für den Weg mit den kleinsten reduzierten Kosten (Preisproblem der Spaltenerzeugung), wenn jeder Kunde höchstens einmal besucht werden darf:
Was kostet es, die Besuchsmenge im Label mitzuführen? Handbeispiel Schritt für Schritt, die Gegenprobe „Dominanz ohne Menge“, Größenversuch live,
feste Messreihen bis 30 Kunden und die Abbrüche der elementaren Rechnung.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import epr_algorithm as A
import epr_colgen as G
import epr_constants as C
import epr_evaluation as ev
from epr_layout import dunkles_design, kopf_css
from epr_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from epr_scenario import hand_instance, hand_duals
from epr_visualization import build_abort_chart, build_hand_map, build_labels_chart, build_size_chart, build_subnet_chart, build_wall_chart

st.set_page_config(page_title="Elementarität im Pricing – Sebastian Hanisch", layout="wide")

N_HAND = hand_instance().n


@st.cache_data(show_spinner=False)
def _hand(k):
    return ev.analyse_hand(k)


@st.cache_data(show_spinner=False)
def _memory_table():
    return ev.compare_memory()


@st.cache_data(show_spinner=False)
def _colgen_hand():
    cg = ev.colgen_hand()
    return cg, ev.colgen_rows(cg), G.bound_over_all_routes(hand_instance())


@st.cache_data(show_spinner=False)
def _nomem(duals):
    return ev.analyse_nomem(duals)


@st.cache_data(show_spinner=False)
def _search():
    return ev.search_counterexamples()


@st.cache_data(show_spinner=False)
def _subnets(variant):
    return ev.subnet_rows(variant)


@st.cache_data(show_spinner=False)
def _size(n, width, seed):
    return ev.size_experiment(n, width, seed)


@st.cache_data(show_spinner=False)
def _bands():
    return ev.load_runs(), ev.load_premeasured()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in epr_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧱 Elementarität im Pricing: die Wand")
st.markdown(
    """
Beim **Preisproblem der Spaltenerzeugung** wird ein Weg mit negativen **reduzierten Kosten** gesucht (Weglänge minus die **Dualpreise** der besuchten Kunden; der Dualpreis ist der Betrag, den die
übergeordnete Planung einem Kunden zurechnet). Darf ein Weg einen Kunden mehrfach anfahren, bildet er **Kreise**. Wer Kreise **ganz verbietet** (**elementar**: jeder Kunde höchstens einmal), muss in jedem
**Label** (Teilweg) die **Menge der besuchten Kunden** mitführen, und ein Label darf nur noch gestrichen werden, wenn dessen Menge in der des anderen enthalten ist. Diese Demo fragt: **Was kostet das?** Gezählt werden
**Labels** und **Dominanzvergleiche** (keine Sekunden): am Handbeispiel Schritt für Schritt, an der Gegenprobe „Dominanz ohne Menge“, an Zufallsinstanzen mit bis zu 20 Kunden, in festen Messreihen bis 30 Kunden und an den
Läufen, die an ihrer Zeitgrenze abbrechen.

Weiter unten: der Expander **So funktioniert die elementare Suche** (zuerst), fünf Experimente (**🔬**), **🚧 Wo die Annahmen enden**, **📐 Mathematische Formulierung** und **⚠️ Annahmen, Grenzen und bekannte Probleme**.
Die Anwendung dieses Verfahrens in einem Fall (Besatzungsplanung im Zugverkehr) zeigt [crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo). Aus derselben Linie:
[dominanz-labels-demo](https://github.com/sebastian-hanisch/dominanz-labels-demo) (wann ein Label gestrichen werden darf) und [kreise-im-pricing-demo](https://github.com/sebastian-hanisch/kreise-im-pricing-demo) (was Kreise anrichten).
Nicht zu verwechseln mit [hub-labeling-demo](https://github.com/sebastian-hanisch/hub-labeling-demo): Dort sind Labels vorberechnete Listen für schnelle Abfragen kürzester Wege, hier sind es Teilwege im Preisproblem.
"""
)

with st.expander("So funktioniert die elementare Suche", expanded=True):
    st.markdown(
        """
1. **Ein Label ist ein Teilweg in vier Zahlen und einer Menge:** die **reduzierten Kosten** bisher, die **Zeit** (Beginn der Bedienung; wer zu früh kommt, wartet kostenlos), die verbrauchte **Last** und das
   **Gedächtnis**: die Kunden, die der Weg nicht noch einmal besuchen darf. Beim **elementaren** Weg ist das die **Menge aller bisher besuchten Kunden**.
2. **Das Verfahren verlängert Labels in Zeitreihenfolge** um je einen Kunden. Am selben Kunden enden sehr viele Labels (verschiedene Wege dorthin).
3. **Ein Label O dominiert ein Label N am selben Kunden,** wenn O Kosten, Zeit und Last **nicht höher** hat **und** die besuchten Kunden von O eine **Teilmenge** derer von N sind. Dann kann jede Fortsetzung von N auch von O
   gefahren werden, und N darf gehen. Fehlt die Mengenbedingung, kann ein Label gehen, das einen Kunden noch anfahren dürfte, den das andere schon verbraucht hat.
4. **Die Menge macht das Streichen schwerer:** Zwei Labels mit gleichen oder besseren Kosten, Zeit und Last, aber verschiedenen Mengen, bleiben nebeneinander stehen. In den Messreihen von Experiment 4 wird dadurch bei der elementaren Rechnung in allen 10 Zellen (2 Fensterbreiten, 5 Kundenzahlen) ein kleinerer Anteil der Labels gestrichen als bei k = 5, und je Label sind
   mehr Vergleiche nötig. Die Demo zählt beides.
5. **Ein kleineres Gedächtnis** (die **k nächsten Kunden** jedes weiteren Halts, den Kunden selbst eingeschlossen, statt aller besuchten) erlaubt Kreise und macht die Mengen kleiner; mit **k = 1** ist nur „Kunde i direkt nach i“ verboten, die Wiederkehr nach einem anderen Kunden (a-b-a) ist erlaubt.

Merksatz: **Jeder Kunde höchstens einmal kostet Vergleiche, nicht nur Labels.** Ob das eine Wand ist, steht in den Messungen (Experimente 4 und 5), nicht im Handbeispiel.
"""
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Szenario ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Handbeispiel** (Ergebnis und Experiment 1)")
    memory = st.radio("Gedächtnis k", C.MEMORY_OPTIONS, key="memory_radio", format_func=lambda k: ev.memory_label(k, N_HAND),
                      help="Wie viel das Verfahren sich merkt: k = 1 nur „Kunde i direkt nach i“ verboten, bei k = 7 (sieben Kunden) alle besuchten Kunden (elementar).")
    st.markdown("**Dualpreise des Handbeispiels** (Experiment 2)")
    duals = tuple(
        int(st.slider(f"Dualpreis Kunde {i}", *bounds(f"pi{i}_slider"), key=f"pi{i}_slider", help="Ganzzahlig. Voreinstellung: die Dualpreise der ersten Runde (zweimal der Abstand zum Depot).")) for i in range(1, N_HAND + 1)
    )
    st.markdown("**Größenversuch** (Experiment 3)")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help="Zahl der Kunden der Zufallsinstanz (5 bis 20).")
    width = st.radio("Fensterbreite", C.WIDTH_OPTIONS, key="width_radio", horizontal=True,
                     help="Breite der Zeitfenster der Kunden in Zeiteinheiten (Horizont 300). Breite Fenster lassen viel mehr Wege zu. Gilt auch für die Tabelle von Experiment 4.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"memory_radio": int(memory), **{f"pi{i}_slider": duals[i - 1] for i in range(1, N_HAND + 1)}, "n_slider": int(n), "width_radio": int(width), "seed_input": int(seed)})

hand = _hand(int(memory))
inst, res = hand.inst, hand.result
runs, premeasured = _bands()
mem_name = ev.memory_label(int(memory), N_HAND)

# --- Ergebnis: das Handbeispiel ------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Das Handbeispiel: sieben Kunden, jeder höchstens einmal")
st.markdown(
    "Ein Fahrzeug startet im Depot (Gitterpunkt (0, 0)) und besucht Kunden. **Entfernung = Fahrzeit = Kosten = Manhattan-Abstand** (so bleiben alle Zahlen ganz). "
    f"Bedienzeit {inst.service}, Rückkehr spätestens zur Zeit {inst.horizon}, Last höchstens {inst.capacity}. Wer vor Beginn seines Fensters ankommt, wartet kostenlos. **Reduzierte Kosten einer Route** = "
    "Summe der Entfernungen minus Summe der Dualpreise der besuchten Kunden; gesucht ist die kleinste (negativste). Die Dualpreise der Tabelle sind die der **ersten Runde** der Spaltenerzeugung: "
    "Solange der übergeordnete Plan nur Einzelfahrten kennt, ist der Dualpreis eines Kunden gleich den Kosten seiner Einzelfahrt."
)
first_duals = hand_duals()
table = pd.DataFrame(
    {
        "Kunde": list(range(1, inst.n + 1)),
        "Punkt": [f"({inst.points[i][0]}, {inst.points[i][1]})" for i in range(1, inst.n + 1)],
        "Entfernung zum Depot": [inst.d[0][i] for i in range(1, inst.n + 1)],
        "Last": [inst.demand[i] for i in range(1, inst.n + 1)],
        "Zeitfenster [früh, spät]": [f"[{inst.ready[i]}, {inst.due[i]}]" for i in range(1, inst.n + 1)],
        "Dualpreis (erste Runde)": [first_duals[i] for i in range(1, inst.n + 1)],
    }
)
st.dataframe(table, hide_index=True, width="stretch")

m1, m2, m3, m4 = st.columns(4)
mem_short = "elementar" if int(memory) >= N_HAND else f"k = {int(memory)}"
delta_value = res.value - hand.ref_value   # mein Wert minus Referenz (Aufzählung der elementaren Routen); größer ist schlechter
m1.metric(f"Bester Wert, {mem_short}", ev.fmt_num(res.value),
          delta=f"{delta_value:+g} gegen die Aufzählung".replace("-", "−") if delta_value else "wie die Aufzählung", delta_color="inverse" if delta_value else "off",
          help="Kleinster reduzierter Kostenwert, den das Verfahren findet. Bei kleinem Gedächtnis darf die Route Kreise haben und kann besser sein als jede elementare Route.")
m2.metric(f"Aufzählung ({hand.n_routes} Routen)", ev.fmt_num(hand.ref_value), help=f"Bester Wert über alle {hand.n_routes} zulässigen elementaren Routen (Aufzählung ohne Labels).")
elem_generated = _hand(N_HAND).result.generated
delta_labels = res.generated - elem_generated
m3.metric("Erzeugte Labels", res.generated, delta=f"{delta_labels:+d} gegen elementar".replace("-", "−") if delta_labels else "wie elementar", delta_color="inverse" if delta_labels else "off")
m4.metric("An der Menge gescheitert", res.blocked, help="Dominanzprüfungen, bei denen Kosten, Zeit und Last zum Streichen gereicht hätten und nur die Besuchsmenge es verhinderte.")
st.caption(f"Die Aufzählung findet {hand.n_routes} zulässige elementare Routen. Von den {res.generated} erzeugten Labels bleiben {res.alive} am Ende (das Start-Label im Depot eingeschlossen).")
st.plotly_chart(build_hand_map(inst, hand.ref_route, res.route, mem_name), width="stretch", key="hand_map")
st.caption("Hell grün: die beste elementare Route laut Aufzählung. Rot gestrichelt: der Weg des Verfahrens, falls er abweicht (bei kleinem Gedächtnis mit Kreisen; Linien folgen dem Gitter, erst waagerecht, dann senkrecht).")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was kostet es, jeden Kunden höchstens einmal zu besuchen?")
kind, text = ev.verdict_hand(int(memory), N_HAND, res.value, res.route, hand.ref_value, hand.ref_route, hand.n_routes, res.generated, res.blocked)
getattr(st, kind)(text)
if hand.checked_value is None or abs(hand.checked_value - res.value) > 1e-9:
    st.error("Der unabhängige Routenprüfer bewertet die gefundene Route anders als das Verfahren: Der Kern ist fehlerhaft.")

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Besuchsmengen im Label, Schritt für Schritt")
st.caption(
    f"Handbeispiel mit dem Gedächtnis {mem_name} (Seitenleiste). Jede Zeile ist eine Entscheidung: Ein neues Label wird verworfen, oder ein älteres entfällt. Beim Streichen vergleichen die vier Spalten das **dominierende** Label "
    "(links) mit dem gestrichenen (rechts): ✓ erfüllt (grün), ✗ verletzt (rot). Bei einem Label, das bleibt, stehen seine eigenen Werte. Die letzte Spalte zählt, wie oft bei diesem neuen Label Kosten, Zeit und Last "
    "zum Streichen gereicht hätten und **nur die Besuchsmenge** es verhinderte."
)
show_all = st.checkbox("Auch die Labels zeigen, die bleiben", key="show_all")
rows = ev.event_rows(hand, show_all=show_all)
if rows:
    df = pd.DataFrame(rows)
    cond_cols = list(A.CONDITION_NAMES)
    styled = df.style.map(lambda v: C.CELL_OK if str(v).endswith("✓") else (C.CELL_BAD if str(v).endswith("✗") else ""), subset=cond_cols)
    widths = {"Ereignis": 150, "Label": 100, "Dominiert von": 105, "Nur an der Menge gescheitert": 95, **{c: 100 for c in cond_cols}}
    st.dataframe(styled, hide_index=True, width="stretch", height=min(38 * (len(df) + 1) + 3, 420),
                 column_config={name: st.column_config.TextColumn(name, width=w) for name, w in widths.items()})
else:
    st.info("Mit diesem Gedächtnis wird nichts gestrichen, es gibt keine Entscheidung zu zeigen. Mit „Auch die Labels zeigen, die bleiben“ erscheinen alle erzeugten Labels.")

mem_rows = _memory_table()
st.markdown("**Dasselbe Handbeispiel mit jedem Gedächtnis** (Dualpreise der ersten Runde): Wie viele Prüfungen scheitern nur an der Menge, wie viele Labels entstehen, wie viele Paare stehen am Ende nebeneinander?")
df_mem = pd.DataFrame(
    {
        "Gedächtnis": [ev.memory_label(r["k"], N_HAND) for r in mem_rows],
        "Erzeugte Labels": [r["generated"] for r in mem_rows],
        "Am Ende lebend": [r["alive"] for r in mem_rows],
        "Dominanzvergleiche": [r["comps"] for r in mem_rows],
        "Prüfungen nur an der Menge gescheitert": [r["blocked"] for r in mem_rows],
        "Paare nebeneinander": [r["pairs"] for r in mem_rows],
        "Bester Wert": [ev.fmt_num(r["value"]) for r in mem_rows],
        "Route": [ev.fmt_route(r["route"]) + ("" if r["elementary"] else " (Kunde mehrfach)") for r in mem_rows],
    }
)
st.dataframe(df_mem, hide_index=True, width="stretch")
kind, text = ev.verdict_memory(mem_rows, N_HAND)
getattr(st, kind)(text)

elem_hand = _hand(N_HAND)
st.markdown(f"**Die Paare, die bei elementarem Gedächtnis nebeneinander stehen bleiben** (nach Kosten, Zeit und Last wäre Label A besser oder gleich, aber die Menge von A ist keine Teilmenge der von B; {len(elem_hand.pairs)} Paare am Ende):")
show_pairs = st.checkbox(f"Alle {len(elem_hand.pairs)} Paare zeigen (sonst die ersten 8)", key="show_pairs")
pairs = ev.pair_rows(elem_hand) if show_pairs else ev.first_blocked_pairs(elem_hand, 8)
st.dataframe(pd.DataFrame(pairs), hide_index=True, width="stretch")

cg, cg_rows, (all_routes_bound, all_routes_count) = _colgen_hand()
st.markdown("**Und die ganze Spaltenerzeugung?** Elementar bis zum Ende, mit genauem Master (Brüche): je Runde die beste neue Spalte, bis keine Route mehr unter 0 liegt.")
st.dataframe(pd.DataFrame(cg_rows), hide_index=True, width="stretch")
st.caption(
    f"Die Schranke des Masters ist {ev.fmt_num(cg.bound)} nach {len(cg.rounds)} Runden mit insgesamt {cg.labels} erzeugten Labels. Gegenprobe: Ein Master über alle {all_routes_count} zulässigen elementaren Routen "
    f"(Aufzählung) ergibt {ev.fmt_num(all_routes_bound)}."
)

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Dominanz ohne die Menge (Gegenprobe)")
st.caption(
    "Was geschieht, wenn man die Mengenbedingung einfach weglässt und nur Kosten, Zeit und Last vergleicht? Das Verfahren rechnet dann mit weniger Labels. Hier rechnet die App am Handbeispiel (elementar) mit den Dualpreisen aus der "
    "Seitenleiste dreimal: richtig (mit Menge), falsch (ohne Menge) und als Bezug die Aufzählung aller zulässigen elementaren Routen. Die Voreinstellung der Dualpreise ist die der ersten Runde; "
    "der Schnellstart „Dualpreise B“ setzt Dualpreise, bei denen das Weglassen den besten Weg kostet."
)
nm = _nomem(duals)
c1, c2, c3 = st.columns(3)
c1.metric("Mit Menge (richtig)", ev.fmt_num(nm.right.value), help=f"Weg {ev.fmt_route(nm.right.route)}; {nm.right.generated} erzeugte Labels, {nm.right.comps} Dominanzvergleiche.")
c2.metric("Ohne Menge", ev.fmt_num(nm.wrong.value), delta=f"{nm.wrong.value - nm.ref_value:+g} gegen die Aufzählung".replace("-", "−") if nm.wrong.value != nm.ref_value else "wie die Aufzählung",
          delta_color="inverse" if nm.wrong.value != nm.ref_value else "off", help=f"Weg {ev.fmt_route(nm.wrong.route)}; {nm.wrong.generated} erzeugte Labels, {nm.wrong.comps} Dominanzvergleiche.")
c3.metric("Aufzählung aller Routen", ev.fmt_num(nm.ref_value), help=f"Weg {ev.fmt_route(nm.ref_route)}; {nm.n_routes} zulässige elementare Routen.")
st.dataframe(pd.DataFrame({
    "Rechnung": ["mit Menge (richtig)", "ohne Menge (falsch)", "Aufzählung (Bezug)"],
    "Bester Weg": [ev.fmt_route(nm.right.route), ev.fmt_route(nm.wrong.route), ev.fmt_route(nm.ref_route)],
    "Reduzierte Kosten": [ev.fmt_num(nm.right.value), ev.fmt_num(nm.wrong.value), ev.fmt_num(nm.ref_value)],
    "Erzeugte Labels": [str(nm.right.generated), str(nm.wrong.generated), "–"],
    "Am Ende lebend": [str(nm.right.alive), str(nm.wrong.alive), "–"],
}), hide_index=True, width="stretch")
kind, text = ev.verdict_nomem(nm)
getattr(st, kind)(text)
if nm.loss is not None:
    lost, winner = nm.loss.lost, nm.loss.dominator
    lines = [f"- **Gestrichen:** {ev.label_text(inst, nm.wrong, lost)}.",
             f"- **Von wem:** {ev.label_text(inst, nm.wrong, winner)}; nach Kosten, Zeit und Last besser oder gleich.",
             f"- **Was die volle Regel dazu sagt:** {ev.condition_summary(nm.wrong.labels[winner], nm.wrong.labels[lost], inst.n)}."]
    nxt = nm.ref_route[len(nm.loss.prefix)] if len(nm.loss.prefix) < len(nm.ref_route) else None
    if nxt is not None and (nm.wrong.labels[winner].mem >> nxt) & 1:
        lines.append(f"- **Folge:** Der nächste Halt des besten Weges ist Kunde {nxt}. Beim Label, das streicht, steht er schon in der Menge, es kann ihn nicht mehr anfahren; der beste Weg ist ab hier nicht mehr zu finden.")
    st.markdown("\n".join(lines))

st.markdown("**Wie oft passiert das?** Suche am Handbeispiel über 3 000 zufällige Sätze ganzzahliger Dualpreise (2 bis 14, Zufalls-Seeds 0 bis 2999); Bezug: Aufzählung aller zulässigen elementaren Routen.")
with st.spinner("Rechnet die Suche …"):
    missed = _search()
kind, text = ev.verdict_search(missed, C.SEARCH_SETS)
getattr(st, kind)(text)
if missed:
    st.dataframe(pd.DataFrame([{"Zufalls-Seed": seed_, "Dualpreise der Kunden 1 bis 7": ", ".join(str(p) for p in d)} for seed_, d in missed]), hide_index=True, width="stretch")
st.caption("Ob ein solcher Dualpreis-Satz in einer echten Spaltenerzeugung vorkommt, ist hier nicht gemessen; die Suche zeigt nur, dass der Fehler vorkommt.")

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Wie wächst es mit der Kundenzahl?")
st.markdown("**a) Teilnetze des Handbeispiels** (die ersten m Kunden, Dualpreise der ersten Runde). Variante A ist das Handbeispiel unverändert (Last 6, enge Fenster); Variante B hat keine Lastgrenze und weite Fenster.")
for variant, title in (("A", "Variante A: Handbeispiel unverändert"), ("B", "Variante B: ohne Lastgrenze, weite Fenster")):
    sub = _subnets(variant)
    st.markdown(f"*{title}*")
    st.dataframe(pd.DataFrame({
        "Kunden m": [r["m"] for r in sub],
        "Labels elementar": [r["elementar"] for r in sub],
        "Davon am Ende lebend": [r["uebrig"] for r in sub],
        "Labels ohne Dominanz": [r["ohne_dominanz"] for r in sub],
        "Labels, Gedächtnis k = 1": [r["k1"] for r in sub],
        "Zulässige elementare Routen": [r["wege"] for r in sub],
        "Faktor gegen m − 1": [None if r["faktor"] is None else r["faktor"] for r in sub],
    }), hide_index=True, width="stretch", column_config={"Faktor gegen m − 1": st.column_config.NumberColumn(format="%.2f")})
    if variant == "B":
        st.plotly_chart(build_subnet_chart(sub, variant), width="stretch", key="subnet_chart")
sub_a, sub_b = _subnets("A"), _subnets("B")
st.caption(
    f"Im Handbeispiel (Variante A, 7 Kunden) ist die Wand noch nicht zu sehen: {sub_a[-1]['elementar']} Labels elementar und {sub_a[-1]['wege']} zulässige Routen, in Variante B {ev.fmt_int(sub_b[-1]['elementar'])} Labels und {ev.fmt_int(sub_b[-1]['wege'])} Routen. In Variante B wächst die Zahl der Labels je zusätzlichem Kunden um das "
    f"{ev.fmt_dec(min(r['faktor'] for r in sub_b[1:]), 2)}- bis {ev.fmt_dec(max(r['faktor'] for r in sub_b[1:]), 2)}-Fache, die Zahl der zulässigen elementaren Routen um das "
    f"{ev.fmt_dec(min(b['wege'] / a['wege'] for a, b in zip(sub_b[1:], sub_b[2:])), 1)}- bis {ev.fmt_dec(max(b['wege'] / a['wege'] for a, b in zip(sub_b[1:], sub_b[2:])), 1)}-Fache: "
    "Die Zahl der Labels wächst langsamer als die der Routen."
)

st.markdown("**b) Zufallsinstanz.**")
st.caption(
    f"Live: eine Zufallsinstanz mit n Kunden, Fensterbreite und Zufalls-Seed aus der Seitenleiste, **ein** Pricing-Aufruf mit den Dualpreisen der ersten Runde (zweimal der Abstand zum Depot). Gerechnet wird elementar, mit Gedächtnis k = 1 "
    f"und ohne Dominanz; die elementare Rechnung bricht bei {ev.fmt_int(C.MAX_COMPS)} Dominanzvergleichen ab, die ohne Dominanz bei {ev.fmt_int(C.MAX_LABELS_NO_DOMINANCE)} Labels. Gezählt werden Labels und Vergleiche, **nicht Sekunden**."
)
with st.spinner("Rechnet die drei Läufe (bei 20 Kunden und Breite 100 dauert das einige Sekunden) …"):
    size = _size(int(n), int(width), int(seed))
e, k1, none = size.elementary, size.k1, size.none
d1, d2, d3, d4 = st.columns(4)
d1.metric("Labels elementar", ev.fmt_int(e.generated) + (" (Abbruch)" if e.aborted else ""), help="Erzeugte Labels des elementaren Laufs, auch sofort gestrichene, plus das Start-Label.")
d2.metric("Dominanzvergleiche", ev.fmt_int(e.comps) + (" (Budget)" if e.aborted else ""), help="Jeder ausgewertete Test „altes gegen neues Label“ und „neues gegen altes Label“ zählt einmal.")
d3.metric("Vergleiche je Label", ev.fmt_dec(size.per_label), help="Dominanzvergleiche geteilt durch erzeugte Labels des elementaren Laufs.")
d4.metric("An der Menge gescheitert", ev.fmt_pct(size.share_blocked), help="Anteil der Vergleiche, bei denen Kosten, Zeit und Last zum Streichen gereicht hätten und nur die Besuchsmenge es verhinderte.")
f1, f2, f3, f4 = st.columns(4)
f1.metric("Labels mit k = 1", ev.fmt_int(k1.generated), delta=None if e.aborted else f"{k1.generated - e.generated:+,d} gegen elementar".replace(",", " ").replace("-", "−"), delta_color="off",
          help="Gedächtnis k = 1: nur „Kunde i direkt nach i“ ist verboten, Kreise (auch a-b-a) sind erlaubt.")
f2.metric("Labels ohne Dominanz", ev.fmt_int(none.generated) + (" (Abbruch)" if none.aborted else ""), help="Nichts wird gestrichen (Gedächtnis elementar); jeder Weg, der Kunden höchstens einmal besucht, bleibt als Label stehen.")
f3.metric("Bester Wert elementar", ev.fmt_num(e.value) if not e.aborted else "–", help="Kleinster reduzierter Kostenwert; bei Abbruch nicht gezeigt.")
f4.metric("Bester Wert, k = 1", ev.fmt_num(k1.value), help="Mit Kreisen kann der Wert besser sein als der elementare.")
st.plotly_chart(build_size_chart(e, int(n)), width="stretch", key="size_chart")
st.caption(f"Gezeigt: der elementare Lauf{' bis zum Abbruch' if e.aborted else ''}; Gestrichen: {ev.fmt_pct(100 * e.dominated / e.generated)} der erzeugten Labels.")
kind, text = ev.verdict_size(size)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

wall = ev.wall_table(runs, int(width))
st.subheader("🔬 Experiment 4: Die Wand in den Messungen")
st.caption(
    f"Feste Messreihe, mit dem Kern dieser Demo neu gerechnet: je Kundenzahl {C.PER_CLUSTER} Zufallsinstanzen (Zufalls-Seeds 0 bis 5), Fensterbreite {int(width)} (Seitenleiste), Überdeckungs-Master, die **ganze Spaltenerzeugung** "
    "(viele Pricing-Aufrufe mit wechselnden Dualpreisen). Verglichen: elementar, Gedächtnis k = 5 und k = 1. Zeitgrenze 30 Sekunden je Pricing-Aufruf; Mediane über die fertigen Läufe. Gerechnete Sekunden stehen in `data/laeufe.json`, "
    "hängen von Rechner und Last ab und sind hier nicht gezeigt."
)
df4 = pd.DataFrame(
    {
        "Kunden n": [r["n"] for r in wall],
        "Fertig (elementar)": [f"{r['elementar']['fertig']} von {r['elementar']['laeufe']}" for r in wall],
        "Labels elementar (Median)": [round(r["elementar"]["labels_median"]) if r["elementar"]["labels_median"] is not None else None for r in wall],
        "Labels k = 5 (Median)": [round(r["k5"]["labels_median"]) if r["k5"]["labels_median"] is not None else None for r in wall],
        "Gestrichen elementar (%)": [r["elementar"]["gestrichen_prozent"] for r in wall],
        "Gestrichen k = 5 (%)": [r["k5"]["gestrichen_prozent"] for r in wall],
        "Vergleiche elementar (Median)": [round(r["elementar"]["vergleiche_median"]) if r["elementar"]["vergleiche_median"] is not None else None for r in wall],
        "Vergleiche k = 5 (Median)": [round(r["k5"]["vergleiche_median"]) if r["k5"]["vergleiche_median"] is not None else None for r in wall],
        "Vergleiche je Label, elementar": [r["elementar"]["vergleiche_je_label"] for r in wall],
        "Vergleiche je Label, k = 5": [r["k5"]["vergleiche_je_label"] for r in wall],
    }
)
st.dataframe(df4, hide_index=True, width="stretch",
             column_config={"Gestrichen elementar (%)": st.column_config.NumberColumn(format="%.1f %%"), "Gestrichen k = 5 (%)": st.column_config.NumberColumn(format="%.1f %%"),
                            "Vergleiche je Label, elementar": st.column_config.NumberColumn(format="%.1f"), "Vergleiche je Label, k = 5": st.column_config.NumberColumn(format="%.1f"),
                            "Labels elementar (Median)": st.column_config.NumberColumn(format="%d"), "Labels k = 5 (Median)": st.column_config.NumberColumn(format="%d"),
                            "Vergleiche elementar (Median)": st.column_config.NumberColumn(format="%d"), "Vergleiche k = 5 (Median)": st.column_config.NumberColumn(format="%d")})
st.markdown("**Vergleiche je Label über die Kundenzahl** (logarithmische Achse; nur fertige Läufe; der Stern ist Ihre Instanz aus Experiment 3, ein einzelner Pricing-Aufruf):")
st.plotly_chart(build_wall_chart(wall, int(width), int(n), size.per_label if not e.aborted else None), width="stretch", key="wall_chart")
st.markdown("**Labels der ganzen Spaltenerzeugung über die Kundenzahl** (Median, logarithmische Achse):")
st.plotly_chart(build_labels_chart(wall), width="stretch", key="labels_chart")
kind, text = ev.verdict_wall(wall, int(width))
getattr(st, kind)(text)
growth = ev.growth_factors(wall)
full = ev.last_complete_row(wall)
done_last = wall[-1]["elementar"]["fertig"]
st.caption(
    f"Hinweise: Die Zahl der Labels (Median, elementar) wächst je fünf Kunden um das {', '.join(ev.fmt_dec(g, 1) for g in growth)}-Fache (von n = {wall[0]['n']} an, nur zwischen Kundenzahlen, bei denen alle Läufe fertig sind). "
    f"Bei n = {full['n']} (alle {full['elementar']['laeufe']} elementaren Läufe fertig) braucht die elementare Rechnung das {ev.fmt_dec(full['elementar']['labels_median'] / full['k5']['labels_median'], 1)}-Fache der Labels "
    f"und das {ev.fmt_dec(full['elementar']['vergleiche_median'] / full['k5']['vergleiche_median'], 1)}-Fache der Dominanzvergleiche von k = 5 (Mediane). "
    f"Gemessen sind nur {C.PER_CLUSTER} Instanzen je Kundenzahl, zufällig verteilte Kunden und Python; bei n = {wall[-1]['n']} sind {done_last} von {wall[-1]['elementar']['laeufe']} elementaren Läufen fertig, "
    "der Median stammt aus diesen."
)

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Wann bricht die elementare Rechnung ab?")
abort = ev.abort_table(runs, 30)
st.caption(
    "Eine Rechnung **bricht ab**, wenn ein einzelner Pricing-Aufruf mehr als 30 Sekunden braucht. Das ist ein Abbruch an einer Zeitgrenze, kein Beweis, dass die Rechnung nicht zu lösen wäre, und die Zahl hängt von Rechner und Last ab. "
    "Oben: die in dieser Demo neu gerechneten Läufe (30 Kunden, je Breite 6 Instanzen, Überdeckungs-Master, elementar)."
)
st.dataframe(pd.DataFrame({
    "Fensterbreite": [r["breite"] for r in abort],
    "Läufe": [r["laeufe"] for r in abort],
    "Fertig": [r["fertig"] for r in abort],
    "Abgebrochen": [r["abgebrochen"] for r in abort],
    "Davon im ersten Pricing-Aufruf": [r["im_ersten_aufruf"] for r in abort],
}), hide_index=True, width="stretch")
st.plotly_chart(build_abort_chart(abort), width="stretch", key="abort_chart")
kind, text = ev.verdict_abort(abort, 30)
getattr(st, kind)(text)
st.markdown("**Vergleich mit den Zahlen früherer Messungen** (Messdateien, nicht in der Demo neu gerechnet, wo die Spalte „Neu gerechnet“ „nein“ zeigt):")
pm = premeasured["abbrueche"]
st.dataframe(pd.DataFrame({
    "Messung": [r["bezeichnung"] for r in pm],
    "Läufe": [r["laeufe"] for r in pm],
    "Abgebrochen": [r["abgebrochen"] for r in pm],
    "Davon im ersten Pricing-Aufruf": [r["im_ersten_aufruf"] for r in pm],
    "Neu gerechnet": ["ja, siehe oben" if not r["nicht_neu_gerechnet"] else "nein" for r in pm],
    "Quelle": [r["quelle"] for r in pm],
}), hide_index=True, width="stretch")
v1_100_vm = next(r for r in pm if r["gruppe"] == "V1" and r["breite"] == 100)
v1_100_new = next(r for r in abort if r["breite"] == 100)
load_row = next(r for r in pm if r["gruppe"] == "P07b")
st.caption(
    f"Hinweise: Die Quote hängt von der Zeitgrenze und der Last ab. Bei 30 Kunden und Breite 100 brachen in der früheren Messung {v1_100_vm['abgebrochen']} von {v1_100_vm['laeufe']} Läufen ab, in einem Lauf mit fünf gleichzeitigen Rechnungen "
    f"{load_row['abgebrochen']} von {load_row['laeufe']}, in der Neumessung dieser Demo {v1_100_new['abgebrochen']} von {v1_100_new['laeufe']}; die Richtung bleibt gleich. "
    "Bei 50 und 100 Kunden und bei gruppiert verteilten Kunden stehen nur die Zahlen früherer Messungen."
)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie nicht gilt | Belegt durch |
|---|---|---|
| **Jeder Kunde höchstens einmal** (elementar) | Mit kleinerem Gedächtnis sind Kreise erlaubt; im Handbeispiel findet k = 1 eine Route mit Kreis und den Wert {ev.fmt_num(mem_rows[0]['value'])} statt {ev.fmt_num(hand.ref_value)}. | Experiment 1 |
| **Dominanz mit Menge** | Ohne die Mengenbedingung rechnet das Verfahren mit weniger Labels und verfehlt am Handbeispiel in {len(_search())} von {ev.fmt_int(C.SEARCH_SETS)} Dualpreis-Sätzen den besten Weg. | Experiment 2 |
| **Eigene Instanzen, zufällig verteilt, bis 30 Kunden** | Bei gruppierten Kunden und bei 50 und 100 Kunden stehen nur Zahlen früherer Messungen (nicht neu gerechnet). | Experiment 5 |
| **Zeitgrenze von 30 Sekunden je Pricing-Aufruf** | Abbrüche hängen von Rechner und Last ab; die Zahlen zeigen die Richtung, nicht eine feste Grenze. | Experiment 5 |
| **Eine Python-Fassung ohne Beschleunigung** | Gezählt werden Labels und Vergleiche; beide gelten für diese Fassung (Prüfreihenfolge gegen die lebenden Labels, keine Eimer), die Sekunden ebenso. | Experimente 3 und 4 |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** *Gegeben:* ein Depot $0$ und Kunden $1,\dots,n$ mit Entfernungen $d_{ij}$, Lasten $q_j$, Zeitfenstern $[e_j, l_j]$ und Dualpreisen $\pi_j$. *Gesucht:* die Route ab und bis zum Depot mit den kleinsten
reduzierten Kosten, **jeder Kunde höchstens einmal** (elementar). *Das Label-Verfahren* verlängert Teilwege Kunde für Kunde und streicht dominierte Labels; beim elementaren Weg führt jedes Label die Menge der besuchten Kunden mit.

| Symbol | Bedeutung |
|---|---|
| $i, j$ | Knoten; $0$ ist das Depot, $1,\dots,n$ sind Kunden |
| $d_{ij}$ | Entfernung von $i$ nach $j$; gleich der Fahrzeit und den Kosten |
| $\pi_j$ | Dualpreis des Kunden $j$ ($\pi_0 = 0$) |
| $q_j$, $Q$ | Last des Kunden $j$; Kapazität des Fahrzeugs |
| $e_j$, $l_j$ | frühester und spätester Beginn der Bedienung bei $j$ |
| $s$, $H$ | Bedienzeit je Kunde; Horizont (späteste Rückkehr ins Depot) |
| $\bar c(r)$ | reduzierte Kosten der Route $r$ |
| $(T, C, R, V)$ | Label: Zeit, reduzierte Kosten, verbrauchte Last, Menge der besuchten Kunden (Gedächtnis) |
| $L_1 \preceq L_2$ | Label $L_1$ dominiert Label $L_2$ (am selben Kunden) |
| $k$ | Größe des Gedächtnisses (die $k$ nächsten Kunden); $k = n$ heißt elementar |

**Reduzierte Kosten** einer Route $r = (j_0 = 0, j_1, \dots, j_m, j_{m+1} = 0)$ mit verschiedenen Kunden $j_1, \dots, j_m$:

$$\bar c(r) = \sum_{t=0}^{m} d_{j_t j_{t+1}} - \sum_{t=1}^{m} \pi_{j_t}$$

**Fortsetzung** eines Labels $(T, C, R, V)$ am Knoten $i$ zum Kunden $j \notin V$ (mit $s\,[i \ne 0]$: im Depot entfällt die Bedienzeit):

$$T' = \max\bigl(e_j,\; T + s\,[i \ne 0] + d_{ij}\bigr), \quad C' = C + d_{ij} - \pi_j, \quad R' = R + q_j, \quad V' = V \cup \{j\}$$

Zulässig ist sie, wenn $T + s\,[i \ne 0] + d_{ij} \le l_j$ und $R' \le Q$ gelten. Zurück ins Depot geht es, wenn

$$T + s + d_{i0} \le H$$

**Dominanz** (elementar, mit Menge):

$$L_1 \preceq L_2 \iff C_1 \le C_2, \quad T_1 \le T_2, \quad R_1 \le R_2, \quad V_1 \subseteq V_2$$

**Warum die Menge nötig ist:** Jede zulässige Fortsetzung von $L_2$ ist auch für $L_1$ zulässig (früher oder gleich spät ankommen hält Fenster und Horizont ein, weil Warten erlaubt ist; weniger oder gleich viel Last; wegen $V_1 \subseteq V_2$ hat $L_1$
mindestens so viele freie Kunden) und kostet am Ende nicht mehr. Ohne $V_1 \subseteq V_2$ gilt das nicht: Experiment 2 zeigt am Handbeispiel ein Label, das einen Kunden noch anfahren dürfte, den das dominierende schon besucht hat.
**Kleineres Gedächtnis:** Mit $k < n$ ersetzt man $V$ durch $V' = (V \cap NG(j)) \cup \{j\}$ mit $NG(j)$ gleich den $k$ nächsten Kunden von $j$ (einschließlich $j$); die Route darf dann Kunden mehrfach besuchen, und die Dominanz vergleicht die kleineren Mengen.

**Zählgrößen.** *Labels:* jedes erzeugte Label, auch ein sofort verworfenes, plus das Start-Label. *Dominanzvergleiche:* jeder ausgewertete Test „altes gegen neues Label“ und „neues gegen altes Label“ zählt einmal. Dass die Zahl der Labels langsamer wächst als die der zulässigen
elementaren Routen, ist am Handbeispiel (Variante B) und in den Messreihen gezählt, kein Satz.

**Literatur** (Prüfstand: Autoren, Titel, Zeitschrift und Jahr per Suchtreffer bzw. Zusammenfassung geprüft; die Volltexte sind nicht gelesen, die Demo übernimmt keine Zahl daraus):
- Feillet, Dejax, Gendreau, Gueguen (2004): An exact algorithm for the elementary shortest path problem with resource constraints: application to some vehicle routing problems, Networks 44(3), 216–229 (Elementarität als zusätzliche Ressource in der Spaltenerzeugung für Touren mit Zeitfenstern).
- Boland, Dethridge, Dumitrescu (2006): Accelerated label setting algorithms for the elementary resource constrained shortest path problem, Operations Research Letters 34(1), 58–68 (Besuchsressourcen verhindern Wiederholungen).
- Irnich, Desaulniers (2005): Shortest path problems with resource constraints, Kapitel 2 in *Column Generation*, Springer (nur als Titel geprüft; Inhalt nicht gelesen).
- Dass der elementare Fall im schlimmsten Fall schwer ist, ist in der Literatur bekannt; hier nur aus dem Gedächtnis genannt und nicht geprüft. Die Demo behauptet es nicht, sie misst.
        """
    )

st.markdown("---")

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html)."
)
