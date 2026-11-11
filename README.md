# Elementarität im Pricing: die Wand – Streamlit-Demo

<!-- Nach dem Deploy hier direkt den Live-Link einsetzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-elementar-pricing-demo.streamlit.app/)** -->

Demo der Linie „Ressourcenwege und Spaltenerzeugung“ in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Das **Label-Verfahren** sucht den Weg mit den kleinsten **reduzierten Kosten**
(Weglänge minus die Dualpreise der besuchten Kunden), mit Zeitfenstern, Last und **höchstens einem Besuch je Kunde** (elementar); es ist das Preisproblem der Spaltenerzeugung. Jeder Teilweg ist ein **Label** (Kosten, Zeit, Last und die **Menge der
besuchten Kunden**). Diese Demo fragt nur eines: **Was kostet es, Kreise ganz zu verbieten?** Gezählt werden erzeugte Labels und Dominanzvergleiche, keine Sekunden.

Die Anwendung in einem Fall zeigt [crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo) (Besatzungsplanung im Zugverkehr: Preisproblem als Label-Verfahren, nicht gemessen). Aus derselben Linie:
[dominanz-labels-demo](https://github.com/sebastian-hanisch/dominanz-labels-demo) (wann ein Label gestrichen werden darf), [kreise-im-pricing-demo](https://github.com/sebastian-hanisch/kreise-im-pricing-demo) (was Kreise anrichten) und
[ng-routen-demo](https://github.com/sebastian-hanisch/ng-routen-demo) (kleineres Gedächtnis statt der ganzen Menge). **Abgrenzung:** [hub-labeling-demo](https://github.com/sebastian-hanisch/hub-labeling-demo) meint etwas anderes (vorberechnete
Listen für schnelle Abfragen kürzester Wege); hier sind Labels Teilwege.

## Warum dieses Problem

Erlaubt man einem Weg, einen Kunden mehrfach anzufahren, bildet er Kreise. Verbietet man sie ganz, muss jedes Label die Menge der besuchten Kunden mitführen, und ein Label darf nur gestrichen werden, wenn dessen Menge in der des anderen enthalten ist.
Damit sinkt der Anteil der gestrichenen Labels, und je Label sind mehr Vergleiche nötig (in den Messreihen dieser Demo in allen 10 Zellen aus 2 Fensterbreiten und 5 Kundenzahlen, verglichen mit k = 5). Die Demo zeigt das am Handbeispiel mit sieben Kunden, belegt an einer Gegenprobe, dass die Mengenbedingung nötig ist, und zählt
an Zufallsinstanzen mit 10 bis 30 Kunden, wie Labels, Vergleiche und Abbrüche wachsen.

## Befunde und Korrekturen gegenüber dem Plan

- **Neu gerechnet statt übernommen:** Die Messreihen der Experimente 4 und 5 sind mit dem Kern dieser Demo neu gerechnet (`tools/bands_bauen.py`); die Rohzeilen stehen in `data/laeufe.json`. Die Zahl der fertigen Läufe und der Median der Labels
  (ganzzahlig gerundet) stimmen mit der früheren Messung (`run_p07.log`; die Rohdateien früherer Messungen liegen nicht im Repo) in 29 von 30 Zellen (2 Fensterbreiten × 5 Kundenzahlen × 3 Gedächtnisse) überein. Die Ausnahme: 30 Kunden, Breite 100, elementar, dort sind in der Neurechnung 2 von 6 Läufen fertig, in der früheren Messung 3 von 6.
- **Abbrüche hängen von der Last ab:** In der Neurechnung brechen auf dem Messrechner bei 30 Kunden und Breite 100 4 von 6 elementaren Läufen an der Zeitgrenze ab, in der früheren Messung waren es 3 von 6, in einem früheren Lauf mit fünf gleichzeitigen Rechnungen 4 von 6. Die Demo nennt alle drei Zahlen.
  Eine Abbruchquote ist keine Eigenschaft der Instanzen allein.
- **Wachstum der Labels:** Der Faktor der Median-Labels (elementar, Breite 100) von einer Kundenzahl zur nächsten ist 5,7 (10 auf 15), 2,7 (15 auf 20) und 2,6 (20 auf 25). Für 25 auf 30 wird kein Faktor genannt: Bei 30 Kunden stammt der Median nur
  aus den fertigen Läufen, also aus einer Auswahl der leichteren Instanzen.
- **Sekunden:** Keine Zeitaussage. Die frühere Messung hatte auch Sekunden verglichen; sie hängen von Rechner und Last ab und stehen nicht in der Demo.

## Modell

Ein Depot und Kunden mit Last, Zeitfenster und Dualpreis; Entfernung = Fahrzeit = Kosten; Warten vor einem Fenster ist kostenlos; Kapazität, Horizont (späteste Rückkehr) und Bedienzeit je Kunde. Ein Label am Kunden $i$ ist $(T, C, R, V)$: Zeit, reduzierte
Kosten, verbrauchte Last, Menge der besuchten Kunden (Gedächtnis). **Dominanz mit Menge:** $L_1$ dominiert $L_2$, wenn $C_1 \le C_2$, $T_1 \le T_2$, $R_1 \le R_2$ und $V_1 \subseteq V_2$; bei Gleichstand bleibt das ältere Label. Ein **kleineres Gedächtnis**
$k < n$ merkt sich nur die $k$ nächsten Kunden jedes weiteren Halts, den Kunden selbst eingeschlossen (ng-Nachbarschaft); mit $k = 1$ ist nur „Kunde $i$ direkt nach $i$“ verboten, die Wiederkehr nach einem anderen Kunden (a-b-a) ist erlaubt. Die Formeln stehen im Expander **📐 Mathematische Formulierung** der App (`app.py`), mit Lesehilfe.

Zwei Arten von Instanzen: das **Handbeispiel** (7 Kunden, Manhattan-Abstand, alle Zahlen ganz, Bedienzeit 2, Horizont 38, Kapazität 6; dasselbe Netz wie in den anderen Demos der Linie) und **Zufallsinstanzen im Stil der Solomon-Instanzen** (Quadrat 100 × 100, Fahrzeit gleich Entfernung,
Bedienzeit 10, Kapazität 70, Horizont 300, Kunden zufällig verteilt, Fensterbreite 40, 100 oder 200; **nicht die Originalinstanzen**). Die Dualpreise des Größenversuchs sind die der **ersten Runde** der Spaltenerzeugung (Master mit nur den Einzelfahrten:
Dualpreis = zweimal der Abstand zum Depot); die Messreihen rechnen die ganze Spaltenerzeugung mit Überdeckungs-Master.

## Methodik

Das Label-Verfahren verlängert Labels in Zeitreihenfolge um je einen Kunden (`epr_algorithm.py`, `price`). Die **Dominanz** ist wählbar: voll (mit Menge), ohne Menge (falsch für elementare Wege, als Lehrschalter) oder keine. Ein **Orakel** (Aufzählung aller Besuchsfolgen ohne Labels)
liefert den Bezug. Die **Experimente** der App: (1) Handbeispiel Schritt für Schritt, jede Streichung mit den vier Vergleichen, dazu die Prüfungen, die nur an der Menge scheitern, die Paare, die nebeneinander stehen, die Spaltenerzeugung mit genauem Master (Brüche); (2) die Gegenprobe
„Dominanz ohne Menge“ mit sieben einstellbaren Dualpreisen und einer Suche über 3 000 Sätze; (3) Wachstum: Teilnetze des Handbeispiels und ein Größenversuch live (5 bis 20 Kunden); (4) die Wand in den Messreihen (10 bis 30 Kunden, Fensterbreite 40 und 100);
(5) Abbrüche der elementaren Rechnung bei 30 Kunden und die Zahlen früherer Messungen für andere Größen.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Zählungen erzeugter Labels (jedes erzeugte Label, auch ein sofort verworfenes, plus das Start-Label) oder Dominanzvergleiche (jeder ausgewertete Test „altes gegen neues Label“ und „neues gegen altes Label“ zählt einmal) an **festen Zufalls-Seeds**,
in Python, an den genannten Instanzen und Dualpreisen; Fälle werden gezählt, Zeiten nicht. Die Spalte „Test“ nennt die Prüfung in `tests/test_claims.py` (Zahl-zu-Test-Tabelle).

| Frage | Befund (Voraussetzung im Satz) | Test |
|---|---|---|
| Handbeispiel (7 Kunden, Dualpreise der ersten Runde): bester elementarer Weg? | 79 zulässige elementare Routen (Aufzählung); bester Wert −10, zum Beispiel mit 2-7-6 (weitere Routen haben ebenfalls −10); das Verfahren mit Menge findet den Wert. | `test_algorithm.py::test_best_by_enumeration_counts_79_routes`, `test_oracle_*` |
| Handbeispiel, elementar: Labels? | 56 erzeugte Labels, 20 sofort verworfen, 0 verdrängt, 36 am Ende lebend (das Start-Label eingeschlossen). | `test_algorithm.py::test_first_round_elementary_counts…` |
| Handbeispiel, elementar: Was kostet die Menge? | Bei 34 Dominanzprüfungen hätten Kosten, Zeit und Last zum Streichen gereicht und nur die Besuchsmenge verhinderte es; am Ende stehen 31 Paare lebender Labels nebeneinander (zum Beispiel 2-1 mit Kosten −7 und 3-1 mit Kosten −5, beide Zeit 18, Last 4: die Menge {2} fehlt in {1,3}). | `test_algorithm.py`, `test_claims.py` |
| Handbeispiel mit kleinerem Gedächtnis | Erzeugte Labels / Prüfungen nur an der Menge / bester Wert: k = 1: 62 / 0 / −18 (Route 7-6-7-6 mit Kreis); k = 2: 58 / 5 / −14 (Route 5-3-5-1); k = 3: 55 / 7 / −10 (Route 2-7-6); elementar: 56 / 34 / −10. | `test_algorithm.py::test_other_memories…` |
| Handbeispiel: ganze Spaltenerzeugung, elementar | 7 Runden, 326 erzeugte Labels, Schranke 30; ein Master über alle 79 Routen ergibt 30. | `test_algorithm.py::test_column_generation_of_the_hand_example…` |
| Gegenprobe: Dominanz ohne Menge (Handbeispiel, elementar) | Mit den Dualpreisen der ersten Runde trifft sie den besten Weg (2-7-6, −10) mit 54 statt 56 Labels. Mit den Dualpreisen B = (2, 4, 13, 4, 2, 5, 13) verfehlt sie ihn: Sie findet 2-7-6 mit −10, die Aufzählung 3-6-7 mit −11; mit Menge wird 3-6-7 gefunden. | `test_algorithm.py`, `test_claims.py` |
| Gegenprobe: wie oft? | In 1 von 3 000 Sätzen ganzzahliger Dualpreise (2 bis 14, Zufalls-Seeds 0 bis 2999) verfehlt die Dominanz ohne Menge den besten Weg (Zufalls-Seed 1778 = Dualpreise B). | `test_algorithm.py::test_search_over_3000…` |
| Teilnetze des Handbeispiels | Siehe Tabellen unten: In Variante B (ohne Lastgrenze, weite Fenster) steigen die erzeugten Labels (elementar) von 5 bei 2 Kunden auf 962 bei 7, die zulässigen elementaren Routen von 4 auf 13 603; ohne Dominanz entstehen 13 604 Labels. | `test_algorithm.py::test_subnet_tables…` |
| Zufallsinstanz, ein Pricing-Aufruf mit den Dualpreisen der ersten Runde, Breite 100 | 10 Kunden (Zufalls-Seed 0): 634 Labels, 47 529 Dominanzvergleiche (75,0 je Label); mit k = 1 421 Labels, ohne Dominanz 772. 20 Kunden (Zufalls-Seed 1): 5 844 Labels, 2 000 502 Vergleiche (342,3 je Label). 20 Kunden (Zufalls-Seed 0): Abbruch nach 10 Millionen Vergleichen bei 11 754 Labels. | `test_claims.py::test_live_size_runs` |
| Wand in den Messreihen (Breite 100, je Kundenzahl 6 Instanzen, ganze Spaltenerzeugung, Überdeckungs-Master) | Dominanzvergleiche je Label (fertige Läufe): elementar 17,3 / 51,3 / 346,4 / 214,6 / 474,0 bei n = 10 / 15 / 20 / 25 / 30, k = 5: 8,6 / 9,9 / 11,5 / 11,9 / 12,1. Bei n = 25 braucht die elementare Rechnung im Median das 1,5-Fache der Labels und das 23,5-Fache der Vergleiche von k = 5. | `test_claims.py::test_wall_tables…` |
| Abbrüche (30 Kunden, Zeitgrenze 30 s je Pricing-Aufruf, je Breite 6 Instanzen, elementar, Neurechnung) | Breite 40: 0 von 6, Breite 100: 4 von 6, Breite 200: 6 von 6 abgebrochen; alle 10 abgebrochenen Läufe brachen im ersten Pricing-Aufruf ab. | `test_claims.py::test_abort_table…` (Zeilen der Messreihe; Zeitgrenzen werden nicht neu gerechnet) |
| Abbrüche in den Zahlen früherer Messungen (nicht neu gerechnet) | 30 Kunden, Breite 100: 3 von 6 (frühere Messung V1), 4 von 6 (fünf Rechnungen gleichzeitig); 30 Kunden, Überdeckungs-Master, Breite 100 zufällig verteilt und gruppiert je 4 von 5, Breite 60 5 von 5; 50 und 100 Kunden (8 Zellen mit je 12 Instanzen): 94 von 96; alle abgebrochenen im ersten Pricing-Aufruf. | `test_claims.py::test_premeasured_rows…` (Zeilen der Messreihe) |

**Teilnetze des Handbeispiels (Experiment 3a), Dualpreise der ersten Runde.** m = Zahl der ersten Kunden; „Faktor“ = erzeugte Labels (elementar) geteilt durch die beim Teilnetz mit einem Kunden weniger.

Variante A: das Handbeispiel unverändert (Last 6, enge Fenster).

| m | Labels elementar | davon am Ende lebend | Labels ohne Dominanz | Labels mit k = 1 | zulässige elementare Routen | Faktor |
|---|---|---|---|---|---|---|
| 2 | 4 | 4 | 4 | 4 | 3 | – |
| 3 | 8 | 6 | 8 | 8 | 7 | 2,00 |
| 4 | 13 | 10 | 13 | 13 | 12 | 1,62 |
| 5 | 24 | 17 | 26 | 26 | 25 | 1,85 |
| 6 | 35 | 22 | 48 | 37 | 47 | 1,46 |
| 7 | 56 | 36 | 80 | 62 | 79 | 1,60 |

Variante B: ohne Lastgrenze (Kapazität 99), weite Fenster, Horizont 60.

| m | Labels elementar | davon am Ende lebend | Labels ohne Dominanz | Labels mit k = 1 | zulässige elementare Routen | Faktor |
|---|---|---|---|---|---|---|
| 2 | 5 | 5 | 5 | 29 | 4 | – |
| 3 | 14 | 10 | 16 | 73 | 15 | 2,80 |
| 4 | 41 | 25 | 65 | 345 | 64 | 2,93 |
| 5 | 127 | 63 | 326 | 545 | 325 | 3,10 |
| 6 | 333 | 137 | 1 957 | 798 | 1 956 | 2,62 |
| 7 | 962 | 342 | 13 604 | 1 061 | 13 603 | 2,89 |

Die Zahl der Labels (elementar) wächst in Variante B je zusätzlichem Kunden (m = 3 bis 7) um das 2,62- bis 3,10-Fache, die Zahl der zulässigen elementaren Routen (m = 4 bis 7) um das 4,3- bis 7,0-Fache. Im Handbeispiel mit 7 Kunden und Last 6 (Variante A) ist die Wand
noch nicht zu sehen. Bei 7 Kunden ist k = 1 in Variante B noch nicht kleiner als elementar (1 061 gegen 962 Labels).

**Die Wand in den Messreihen (Experiment 4), Fensterbreite 100.** Je Kundenzahl 6 Zufallsinstanzen (Zufalls-Seeds 0 bis 5), die ganze Spaltenerzeugung mit Überdeckungs-Master; Zeitgrenze 30 Sekunden je Pricing-Aufruf, 120 Sekunden je Spaltenerzeugung. Mediane über die fertigen Läufe (ganzzahlig gerundet),
„Gestrichen“ = mittlerer Anteil der erzeugten Labels, der durch Dominanz entfällt, „Vergleiche je Label“ = Summe der Vergleiche geteilt durch Summe der Labels über die fertigen Läufe.

| n | fertig (elementar) | Labels elementar | Labels k = 5 | Labels k = 1 | Gestrichen elementar | Gestrichen k = 5 | Vergleiche elementar | Vergleiche k = 5 | je Label elementar | je Label k = 5 |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 6 von 6 | 1 430 | 943 | 984 | 46,1 % | 53,6 % | 17 537 | 8 908 | 17,3 | 8,6 |
| 15 | 6 von 6 | 8 139 | 6 870 | 4 928 | 52,0 % | 68,4 % | 375 214 | 78 330 | 51,3 | 9,9 |
| 20 | 6 von 6 | 21 646 | 15 142 | 11 432 | 53,2 % | 75,7 % | 2 162 309 | 163 268 | 346,4 | 11,5 |
| 25 | 6 von 6 | 56 877 | 37 712 | 27 164 | 53,2 % | 79,1 % | 10 694 645 | 454 962 | 214,6 | 11,9 |
| 30 | 2 von 6 | 135 326 | 92 038 | 57 330 | 54,6 % | 84,4 % | 64 144 852 | 953 248 | 474,0 | 12,1 |

Fensterbreite 40, sonst gleich:

| n | fertig (elementar) | Labels elementar | Labels k = 5 | Labels k = 1 | Gestrichen elementar | Gestrichen k = 5 | Vergleiche elementar | Vergleiche k = 5 | je Label elementar | je Label k = 5 |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 6 von 6 | 500 | 482 | 475 | 36,3 % | 45,7 % | 4 013 | 2 697 | 9,3 | 5,4 |
| 15 | 6 von 6 | 1 566 | 1 590 | 1 258 | 38,9 % | 55,6 % | 35 668 | 10 261 | 23,8 | 7,7 |
| 20 | 6 von 6 | 5 255 | 4 372 | 4 197 | 47,2 % | 67,8 % | 129 000 | 27 609 | 76,9 | 6,8 |
| 25 | 6 von 6 | 15 104 | 9 264 | 8 630 | 44,6 % | 71,1 % | 853 214 | 83 333 | 80,9 | 8,2 |
| 30 | 6 von 6 | 40 175 | 20 904 | 16 938 | 49,5 % | 78,2 % | 5 585 908 | 158 308 | 234,1 | 7,5 |

Bei 30 Kunden und Breite 100 stammen die Mediane der elementaren Rechnung aus den 2 fertigen von 6 Läufen und sind nicht mit den Zeilen darüber vergleichbar (bei Breite 40 sind alle 6 fertig). Die Vergleiche je Label der elementaren Rechnung steigen von 17,3 (n = 10)
auf 474,0 (n = 30), aber nicht gleichmäßig: bei n = 25 ist der Wert (214,6) niedriger als bei n = 20 (346,4). Bei k = 5 liegen sie zwischen 8,6 und 12,1.

**Abbrüche (Experiment 5).** 30 Kunden, je Breite 6 Instanzen, elementar, Zeitgrenze 30 Sekunden je Pricing-Aufruf.

| Fensterbreite | Läufe | fertig | abgebrochen | davon im ersten Pricing-Aufruf | frühere Messung V1 (abgebrochen) |
|---|---|---|---|---|---|
| 40 | 6 | 6 | 0 | 0 | 0 |
| 100 | 6 | 2 | 4 | 4 | 3 |
| 200 | 6 | 0 | 6 | 6 | 6 |

**Schnellstart-Szenarien (Größenversuch, Experiment 3b).**

| Szenario | Instanz | Befund |
|---|---|---|
| Erste Runde, elementar (Voreinstellung) | 10 Kunden, Breite 100, Zufalls-Seed 0 | 634 Labels, 47 529 Vergleiche; mit k = 1 421 Labels, ohne Dominanz 772 |
| 20 Kunden, Breite 100: die Rechnung wird fertig | Zufalls-Seed 1 | 5 844 Labels, 2 000 502 Vergleiche; mit k = 1 1 761 Labels, ohne Dominanz 7 542 |
| 20 Kunden, Breite 100: Abbruch am Budget | Zufalls-Seed 0 | Abbruch nach 10 000 152 Vergleichen (Budget 10 Millionen) bei 11 754 Labels; mit k = 1 3 310 Labels |
| 10 Kunden, Breite 40: kleines Beispiel | Zufalls-Seed 0 | 188 Labels, 6 661 Vergleiche; mit k = 1 138 Labels, ohne Dominanz 193 |

**Messung dieser README, nicht im Test:** Ein einmaliger Orakel-Lauf mit 300 Zufallsinstanzen (5 bis 7 Kunden; elementar, Gedächtnis k = 1, 2, 3 und die Zählungen der zweiten Fassung) im Arbeitsordner, nicht im Repo, fand keine Abweichung im Kern; er zeigte, dass die Tiefengrenze des ersten Entwurfs der Aufzählung zu knapp war (das Orakel, nicht der Kern, wurde korrigiert). Die Sekunden der Rechnungen (`sekunden` in `data/laeufe.json`) stammen von einem durch parallele Läufe ausgelasteten Rechner; sie stehen in keinem Test und in keiner Aussage der Demo.

## Ehrliche Grenzen

- Eigene Instanzen im Stil der Solomon-Instanzen, **nicht die Originalinstanzen**, nur zufällig verteilte Kunden; die Messreihen haben je Kundenzahl und Breite 6 Instanzen, 10 bis 30 Kunden. Die Zahlen für gruppiert verteilte Kunden und für 50 und 100 Kunden stammen aus Messdateien früherer Messungen und sind in der Demo
  **nicht neu gerechnet**.
- Ein Abbruch ist ein Abbruch an einer Zeitgrenze von 30 Sekunden je Pricing-Aufruf. Er zeigt nicht, dass die elementare Rechnung bei dieser Größe grundsätzlich nicht zu lösen wäre, und die Quote hängt von Rechner und Last ab (4 von 6 in der Neurechnung gegen 3 von 6 in der früheren Messung bei 30 Kunden und Breite 100).
- Gemessen ist eine Python-Fassung des Label-Verfahrens ohne Beschleunigungen (keine Eimer, kein beidseitiges Suchen) und mit genau den Dominanzregeln dieser Demo. Die Zahl der Vergleiche je Label gilt für diese Fassung; über andere Fassungen sagt die Demo nichts.
- Die Gegenprobe „Dominanz ohne Menge“ gilt für das Handbeispiel: 1 von 3 000 Dualpreis-Sätzen ist eine Zählung an diesem Netz, keine Wahrscheinlichkeit für andere Instanzen. Ob solche Dualpreise in einer echten Spaltenerzeugung vorkommen, ist nicht gemessen.
- Das Handbeispiel (7 Kunden, Last 6) zeigt die Wand noch nicht; sie steht in den Messreihen.
- Ursachen („weil …“) sind Deutungen, wo es dasteht; gemessen sind die Zählungen.
- Literatur (Prüfstand: Titel, Zeitschrift und Jahr per Suchtreffer bzw. Zusammenfassung geprüft, Volltexte nicht gelesen, keine Zahl daraus übernommen): Feillet, Dejax, Gendreau, Gueguen (2004), Networks; Boland, Dethridge, Dumitrescu (2006), Operations Research Letters;
  Irnich, Desaulniers (2005), Kapitel 2 in *Column Generation*. Dass der elementare Fall im schlimmsten Fall schwer ist, ist aus dem Gedächtnis genannt und nicht geprüft; die Demo behauptet es nicht.

Annahmen, Grenzen und bekannte Probleme, wie sie auch in der App stehen (ein Test prüft, dass beide Fassungen gleich sind):

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

## Verifikation

- **Kern** (`tests/conftest.py`, `tests/test_algorithm.py`): je Einheit gegen Handrechnung am Handbeispiel: Fortsetzung, Dominanzregel (dominiert, blockiert nur durch die Menge, nein), Gedächtnis, Zählungen für jedes Gedächtnis, Teilnetze, Spaltenerzeugung mit genauem Master, Abbruch an Budget und Zeitgrenze; unabhängige Routenprüfer.
- **Orakel** (`tests/test_oracle_elementar_pricing.py`): Aufzählung aller Besuchsfolgen (Tiefensuche und Permutationen aller Teilmengen) gegen das elementare Verfahren an 90 Zufallsinstanzen (Wert und jede gelieferte Route); Gedächtnis k = 1, 2, 3 gegen die Aufzählung der erlaubten Folgen (108 Fälle); eine zweite, anders
  geschriebene Fassung des Label-Verfahrens liefert dieselben Zählungen (erzeugte, verworfene, verdrängte Labels, Vergleiche, Prüfungen nur an der Menge); ohne Dominanz entsteht ein Label je zulässigem Teilweg; der genaue Master gegen scipy (HiGHS); die Spaltenerzeugung gegen einen Master über alle Routen.
- **Eigenschaften** (`tests/test_eigenschaften_elementar_pricing.py`): Umnummerieren der Kunden, Skalieren aller Längen und Zeiten, mit Dominanz nie mehr Labels, gleicher bester Wert mit und ohne Dominanz, kleineres Gedächtnis nie schlechter, zusätzliche Option verschlechtert nie.
- **Randfälle** (`tests/test_edge_cases.py`): ein und zwei Kunden, zwei Kunden am selben Ort, alle Dualpreise null, Last gleich Kapazität, so enge Fenster, dass jede Route einen Kunden hat, Ankunft und Rückkehr genau an der Grenze, Gleichstand, Abbruch, Gedächtnis größer als die Kundenzahl.
- **Zahlen der README** (`tests/test_claims.py`): Handbeispiel und Gegenprobe exakt; Größenversuche neu gerechnet; die Messreihen unter `data/` stehen mit Quelle je Zeile, die Tabellen der README werden aus den Rohzeilen abgeleitet, eine Stichprobe (n = 10 und 15, Breite 40 und 100) wird mit dem Kern neu gerechnet (Schranke gleich bis 1e-6, Labels und Vergleiche in Bändern).
- **Verdikte** (`tests/test_verdicts.py`) und **je Schnellstart-Szenario die erwartete Verdikt-Zeile** (`tests/test_presets.py`, `tests/test_app.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Knopf, jeder Regler am Minimum und Maximum, jede Option, Eckfälle und Worst-Case am Regler-Maximum, Permalink mit ungültigen Werten), Layout (fester Kopf, Schnellstart in der Seitenleiste, Hervorhebung), Footer, Laufzeit-Importe.
- **Testzahl:** 170 Tests (`pytest --collect-only -q tests`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Kopf, Handbeispiel, fünf Experimente, Grenzen, Formeln, Fußzeile |
| `epr_algorithm.py` | Kern: Label-Verfahren mit Besuchsmenge und wählbarer Dominanz, Fortsetzung, Gedächtnis, Aufzählung aller Routen, Routenprüfer |
| `epr_colgen.py` | Spaltenerzeugung mit genauem Master (Brüche) für das Handbeispiel |
| `epr_constants.py` | Regler-Grenzen, Farben, Schnellstart-Szenarien, gemeinsamer Text der Annahmen |
| `epr_evaluation.py` | Handbeispiel-Auswertung, Entscheidungstabelle, Gegenprobe und Suche, Größenversuch, Laden und Auswerten der Messreihen, Verdikte (reine Funktionen) |
| `epr_layout.py` | Fester Kopf (Stylesheet) |
| `epr_presets.py` | Permalink (Begrenzen), Schnellstart in der Seitenleiste, aktives Szenario hervorgehoben, Zufalls-Seed-Knopf |
| `epr_scenario.py` | Handbeispiel und Teilnetze, Zufallsinstanzen im Solomon-Stil, Dualpreise der ersten Runde |
| `epr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `data/laeufe.json`, `data/vormessung.json` | feste Messreihen (neu gerechnete Läufe; Zahlen früherer Messungen), jede Zeile mit Quelle |
| `tools/bands_bauen.py` | rechnet die Läufe mit dem Kern der Demo (`messen`) und baut `data/*.json` aus den Rohzeilen und den Rohausgaben der früheren Messungen (`bauen`) |
| `tools/colgen_ref.py` | Spaltenerzeugung (scipy, Überdeckungs-Master) für Messreihen und Tests, nicht für die App |
| `requirements-dev.txt` | Laufzeit plus pytest, scipy und numpy (nur für `tools/colgen_ref.py` und die Tests) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | siehe Verifikation |

## Bewusst nicht umgesetzt

- Keine Aussage über Rechenzeit und keine Zeitmessung in der App; die Sekunden der Neurechnung stehen nur in `data/laeufe.json`.
- Keine Abhilfe gegen die Wand: kein kleineres Gedächtnis als Verfahren der Wahl (nur als Vergleich k = 1 und k = 5; dazu [ng-routen-demo](https://github.com/sebastian-hanisch/ng-routen-demo)), kein beidseitiges Suchen, keine Eimer, keine Dominanz mit Ersatzgrößen.
- Keine gruppiert verteilten Kunden und keine Instanzen mit mehr als 30 Kunden in der Neurechnung (nur die Zahlen früherer Messungen für Abbrüche).
- Keine Live-Spaltenerzeugung für Zufallsinstanzen in der App (Experimente 4 und 5 zeigen feste Messreihen; der Größenversuch ist ein einzelner Pricing-Aufruf); die Spaltenerzeugung am Handbeispiel läuft live.
- Kein PDF-Export.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Python 3.12 oder neuer (die CI läuft mit 3.12). Die in der Streamlit Cloud eingestellte Python-Version ist beim ersten Deploy einzutragen. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html).
