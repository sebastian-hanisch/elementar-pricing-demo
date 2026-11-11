"""Erzeugt die festen Messreihen (data/*.json): rechnet sie mit dem Kern der Demo neu und liest die nicht neu gerechneten Zahlen aus den Rohausgaben.

Zwei Schritte (im Ordner der Demo, Python des Test-venv):

1. Messen (neu gerechnet mit dem Kern der Demo, `tools/colgen_ref.py`, Überdeckungs-Master):
       python tools/bands_bauen.py messen --n 10 15 20 25 --breiten 40 100 --out roh_a.jsonl
       python tools/bands_bauen.py messen --n 30 --breiten 200 --out roh_c.jsonl
   Eine Zeile je Spaltenerzeugung: n, Breite, Zufalls-Seed, Gedächtnis k (k = n heißt elementar), Schranke, Runden, Spalten, erzeugte und gestrichene Labels,
   Dominanzvergleiche, Prüfungen, die nur an der Besuchsmenge scheiterten, Abbruch (Zeitgrenze je Pricing-Aufruf, Standard 30 s; 120 s je Spaltenerzeugung),
   die Runde des Abbruchs und die Sekunden (nur Information; Abbrüche hängen von der Zeitgrenze und der Last des Rechners ab).
2. Bauen (liest die Rohzeilen und die Rohausgaben der Vormessung):
       python tools/bands_bauen.py bauen roh_a.jsonl roh_b.jsonl roh_c.jsonl --vormessung <Ordner label-setting-planung/vormessung>
   schreibt data/laeufe.json (alle neu gerechneten Läufe, je Zeile mit Quelle) und data/vormessung.json (nicht neu gerechnete Zahlen und die Zahlen der
   Vormessung zum Vergleich, je Zeile mit Quelldatei).

Die Zeilen der Vormessung, die hier NICHT neu gerechnet werden: V7 (30 Kunden, drei Instanztypen, Überdeckung und Partitionierung) und V8 (50 und 100 Kunden);
beide stammen aus ihren Rohausgaben und stehen mit `nicht_neu_gerechnet: true` in `data/vormessung.json`."""

import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

DATA = ROOT / "data"


def messen(args) -> None:
    import colgen_ref as R
    from epr_scenario import make_instance

    with open(args.out, "a", encoding="utf-8") as out:
        for width in args.breiten:
            for n in args.n:
                for seed in range(args.seeds):
                    inst = make_instance(n, seed, width)
                    for k in (n if x == "e" else int(x) for x in args.ks):
                        started = time.perf_counter()
                        r = R.colgen(inst, k, time_limit_price=args.zeitgrenze, time_limit_total=4 * args.zeitgrenze)
                        row = {"n": n, "breite": width, "seed": seed, "k": k, "schranke": r["bound"], "runden": r["iterations"], "spalten": r["columns"],
                               "labels": r["generated"], "gestrichen": r["dominated"], "vergleiche": r["comps"], "scheitert_an_menge": r["blocked"],
                               "abgebrochen": r["aborted"], "abbruch_runde": r["abort_round"], "erste_runde_labels": r["first_call"]["generated"],
                               "sekunden": round(time.perf_counter() - started, 2), "zeitgrenze_je_aufruf": args.zeitgrenze}
                        out.write(json.dumps(row) + "\n")
                        out.flush()
                        print(row, flush=True)


def _zahlen(text: str) -> list[str]:
    return re.findall(r"-?\d+(?:\.\d+)?", text)


def vormessung_zeilen(folder: Path) -> list[dict]:
    """Zahlen der Vormessung, die in der Demo gezeigt werden: aus den Rohausgaben gelesen (nicht neu gerechnet) und zum Vergleich mit dem Neurechnen."""
    rows: list[dict] = []
    # V1, 30 Kunden: elementare Läufe je Breite (Zahl abgebrochen von Läufen)
    v1 = (folder / "out_v1_n30.txt").read_text(encoding="utf-8").splitlines()[1:]
    for width in (40, 100, 200):
        runs = [line.split() for line in v1 if len(line.split()) >= 11 and int(line.split()[1]) == width and int(line.split()[3]) == 30]
        rows.append({"gruppe": "V1", "bezeichnung": f"30 Kunden, Fensterbreite {width}, elementar (Zeitgrenze 30 s je Pricing-Aufruf)", "n": 30, "breite": width,
                     "laeufe": len(runs), "abgebrochen": sum(1 for r in runs if r[10] == "1"), "im_ersten_aufruf": sum(1 for r in runs if r[10] == "1" and r[5] == "1"),
                     "nicht_neu_gerechnet": False, "quelle": "out_v1_n30.txt (Vormessung, ls_kern.py); in der Demo neu gerechnet, siehe data/laeufe.json"})
    # V7: Instanztypen, Überdeckung (nur die Überdeckungs-Zeilen werden gezeigt)
    for typ, breite, name in (("zufall", 100, "zufällig verteilt"), ("cluster", 100, "gruppiert"), ("lang", 60, "zufällig verteilt, schmale Fenster")):
        lines = [line.split() for line in (folder / f"out_v7_{typ}.txt").read_text(encoding="utf-8").splitlines()[1:]]
        runs = [p for p in lines if len(p) >= 13 and p[4] == "cover" and int(p[5]) == 30]
        rows.append({"gruppe": "V7", "bezeichnung": f"30 Kunden, {name}, Fensterbreite {breite}, Überdeckungs-Master, elementar", "n": 30, "breite": breite,
                     "laeufe": len(runs), "abgebrochen": sum(1 for p in runs if p[12] == "1"),
                     "im_ersten_aufruf": sum(1 for p in runs if p[12] == "1" and p[7] == "1"), "nicht_neu_gerechnet": True,
                     "quelle": f"out_v7_{typ}.txt (Vormessung, Zeitgrenze laut GLIEDERUNG.md 15 s je Pricing-Aufruf)"})
    # V8: 50 und 100 Kunden, elementar
    runs8 = []
    for f in sorted(folder.glob("out_v8_*_elem.txt")):
        runs8 += [line.split() for line in f.read_text(encoding="utf-8").splitlines()[1:] if len(line.split()) >= 11]
    rows.append({"gruppe": "V8", "bezeichnung": "50 und 100 Kunden, 8 Zellen (zufällig und gruppiert, Breiten 20, 40, 100) mit je 12 Instanzen, elementar", "n": None, "breite": None,
                 "laeufe": len(runs8), "abgebrochen": sum(1 for p in runs8 if p[-1] == "1"), "im_ersten_aufruf": sum(1 for p in runs8 if p[-1] == "1" and p[6] == "1"),
                 "nicht_neu_gerechnet": True, "quelle": "out_v8_*_elem.txt (Vormessung, Zeitgrenze 30 s je Pricing-Aufruf)"})
    # n = 30 unter anderer Last (fünf Läufe gleichzeitig)
    lines = [line.split() for line in (folder / "run_p07_vergleiche_n30.log").read_text(encoding="utf-8").splitlines() if re.match(r"^30 100 \d+ 30 ", line)]
    rows.append({"gruppe": "P07b", "bezeichnung": "30 Kunden, Fensterbreite 100, elementar, fünf Läufe gleichzeitig (mehr Last)", "n": 30, "breite": 100,
                 "laeufe": len(lines), "abgebrochen": sum(1 for p in lines if p[9] == "1"), "im_ersten_aufruf": sum(1 for p in lines if p[9] == "1" and p[5] == "1"),
                 "nicht_neu_gerechnet": True, "quelle": "run_p07_vergleiche_n30.log (Vormessung, ls_mehrres.py)"})
    return rows


def vormessung_wand(folder: Path) -> list[dict]:
    """Medianwerte der Wand-Tabelle aus run_p07.log zum Abgleich mit den neu gerechneten (Zeilen: Breite, n, k, Medianlabels, Anteil dominiert)."""
    rows = []
    n = None
    for line in (folder / "run_p07.log").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^n = (\d+);", line)
        if m:
            n = int(m.group(1))
            continue
        parts = line.split()
        if n and len(parts) == 10 and parts[0].isdigit() and parts[1].isdigit():
            rows.append({"n": n, "breite": int(parts[0]), "k": int(parts[1]), "laeufe": int(parts[2]), "abgebrochen": int(parts[3]),
                         "labels_median": None if parts[5] == "nan" else int(parts[5]), "anteil_gestrichen_prozent": None if parts[6] == "nan" else float(parts[6]),
                         "quelle": f"run_p07.log (Vormessung, ls_kern.py), Abschnitt n = {n}"})
    return rows


def bauen(args) -> None:
    rows = []
    for path in args.roh:
        rows += [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda r: (r["breite"], r["n"], r["seed"], r["k"]))
    seen = set()
    for r in rows:
        key = (r["breite"], r["n"], r["seed"], r["k"])
        if key in seen:
            sys.exit(f"doppelte Zeile {key}")
        seen.add(key)
        r["quelle"] = f"tools/bands_bauen.py messen (Kern der Demo, tools/colgen_ref.py), Überdeckungs-Master, Lauf vom {date.today().isoformat()}"
    folder = Path(args.vormessung)
    DATA.mkdir(exist_ok=True)
    (DATA / "laeufe.json").write_text(json.dumps({"hinweis": "Je Zeile eine Spaltenerzeugung (Überdeckungs-Master), neu gerechnet mit dem Kern der Demo; k = n heißt elementar. "
                                                  "Sekunden und Abbrüche hängen von Rechner und Last ab.", "zeilen": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "vormessung.json").write_text(json.dumps({"hinweis": "Zahlen der Vormessung: V1 zum Vergleich mit dem Neurechnen, V7 und V8 und der Lauf unter Last NICHT neu gerechnet; "
                                                      "jede Zeile nennt ihre Quelldatei.", "abbrueche": vormessung_zeilen(folder), "wand_median": vormessung_wand(folder)},
                                                     ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rows)} Läufe -> data/laeufe.json; data/vormessung.json geschrieben")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("messen")
    m.add_argument("--n", type=int, nargs="+", required=True)
    m.add_argument("--breiten", type=int, nargs="+", required=True)
    m.add_argument("--ks", nargs="+", default=["1", "5", "e"])
    m.add_argument("--seeds", type=int, default=6)
    m.add_argument("--zeitgrenze", type=float, default=30.0)
    m.add_argument("--out", required=True)
    b = sub.add_parser("bauen")
    b.add_argument("roh", nargs="+")
    b.add_argument("--vormessung", required=True)
    args = parser.parse_args()
    (messen if args.cmd == "messen" else bauen)(args)


if __name__ == "__main__":
    main()
