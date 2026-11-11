"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import epr_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360, legend_below=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.25) if legend_below else {})
    return lock_axes(fig)


def _manhattan_path(points, route):
    """Linienzug einer Route auf dem Gitter: erst waagerecht, dann senkrecht (der Abstand der Demo ist der Manhattan-Abstand)."""
    seq = (0,) + tuple(route) + (0,)
    xs, ys = [], []
    for a, b in zip(seq, seq[1:]):
        (x1, y1), (x2, y2) = points[a], points[b]
        xs += [x1, x2, x2]
        ys += [y1, y1, y2]
    return xs, ys


def build_hand_map(inst, ref_route, found_route, found_label):
    """Die Kunden des Handbeispiels auf dem Gitter; der beste elementare Weg (Aufzählung) und der Weg des Verfahrens."""
    fig = go.Figure()
    if ref_route:
        xs, ys = _manhattan_path(inst.points, ref_route)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_OK, width=7), opacity=0.45, name="beste elementare Route (Aufzählung)", hoverinfo="skip"))
    if found_route and tuple(found_route) != tuple(ref_route):
        xs, ys = _manhattan_path(inst.points, found_route)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_BAD, width=3, dash="dash"), name=f"Weg des Verfahrens ({found_label})", hoverinfo="skip"))
    elif found_route:
        xs, ys = _manhattan_path(inst.points, found_route)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_LINE, width=2, dash="dot"), name=f"Weg des Verfahrens ({found_label}, derselbe)", hoverinfo="skip"))
    cust = list(range(1, inst.n + 1))
    hover = [f"Kunde {i}: Last {inst.demand[i]}, Fenster [{inst.ready[i]}, {inst.due[i]}]" for i in cust]
    fig.add_trace(go.Scatter(x=[inst.points[i][0] for i in cust], y=[inst.points[i][1] for i in cust], mode="markers+text", text=[str(i) for i in cust],
                             textposition="top center", marker=dict(size=16, color=C.COLOR_LINE), textfont=dict(size=13), name="Kunden", hovertext=hover,
                             hovertemplate="%{hovertext}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[inst.points[0][0]], y=[inst.points[0][1]], mode="markers+text", text=["Depot"], textposition="bottom center",
                             marker=dict(size=16, color="black", symbol="square"), name="Depot", hovertemplate="Depot<extra></extra>"))
    fig.update_xaxes(range=[-4, 4], title_text="Gitter, waagerecht", dtick=1)
    fig.update_yaxes(range=[-3, 4], title_text="Gitter, senkrecht", dtick=1)
    return _base(fig, height=380)


def build_subnet_chart(rows, variant):
    """Teilnetze des Handbeispiels: erzeugte Labels elementar, ohne Dominanz und mit k = 1 sowie die Zahl der zulässigen Routen, logarithmische Achse."""
    xs = [r["m"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["wege"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_OTHER.replace("0.55", "1"), width=2, dash="dot"), name="zulässige elementare Routen",
                             hovertemplate="m = %{x}: %{y} Routen<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["ohne_dominanz"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_LINE2, width=2), name="Labels ohne Dominanz",
                             hovertemplate="m = %{x}: %{y} Labels<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["k1"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_LINE, width=2, dash="dash"), name="Labels mit Gedächtnis k = 1",
                             hovertemplate="m = %{x}: %{y} Labels<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["elementar"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_OK, width=3), name="Labels elementar (mit Menge)",
                             hovertemplate="m = %{x}: %{y} Labels<extra></extra>"))
    fig.update_xaxes(title_text="Kunden m (die ersten m des Handbeispiels)", dtick=1, range=[1.7, 7.3])
    fig.update_yaxes(title_text="Anzahl (logarithmisch)", type="log", range=[0.5, 4.5])
    return _base(fig)


def build_size_chart(stats, n):
    """Erzeugte Labels je Kunde: am Ende lebend und gestrichen (gestapelt)."""
    labels = [f"K{i}" for i in range(1, n + 1)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=list(stats.alive_per_customer), name="lebt am Ende", marker_color=C.COLOR_OK, hovertemplate="%{x}: %{y} lebende Labels<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=list(stats.dominated_per_customer), name="gestrichen", marker_color=C.COLOR_OTHER, hovertemplate="%{x}: %{y} gestrichene Labels<extra></extra>"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Kunde, bei dem das Label endet")
    fig.update_yaxes(title_text="erzeugte Labels")
    return _base(fig)


def build_wall_chart(table, width, live_n=None, live_per_label=None):
    """Dominanzvergleiche je Label über die Kundenzahl (nur fertige Läufe): elementar gegen k = 5 und k = 1; optional der Wert der Live-Rechnung."""
    fig = go.Figure()
    for mode, name, color, dash, w in (("elementar", "elementar", C.COLOR_OK, "solid", 3), ("k5", "Gedächtnis k = 5", C.COLOR_LINE, "dash", 2), ("k1", "Gedächtnis k = 1", C.COLOR_LINE2, "dot", 2)):
        pts = [(r["n"], r[mode]["vergleiche_je_label"]) for r in table if r[mode]["vergleiche_je_label"] is not None]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines+markers", line=dict(color=color, width=w, dash=dash), name=name,
                                 hovertemplate="n = %{x}: %{y:.1f} Vergleiche je Label<extra></extra>"))
    if live_per_label is not None:
        fig.add_trace(go.Scatter(x=[live_n], y=[live_per_label], mode="markers", marker=dict(size=14, color=C.COLOR_BAD, symbol="star"), name="Ihre Instanz (Experiment 3)",
                                 hovertemplate="n = %{x}: %{y:.1f} Vergleiche je Label<extra></extra>"))
    fig.update_xaxes(title_text="Kunden n", range=[4, 31], dtick=5)
    fig.update_yaxes(title_text="Dominanzvergleiche je Label (logarithmisch)", type="log", range=[0.3, 4.0])
    return _base(fig)


def build_labels_chart(table):
    """Median der erzeugten Labels der ganzen Spaltenerzeugung über die Kundenzahl: elementar gegen k = 5 und k = 1 (nur fertige Läufe)."""
    fig = go.Figure()
    for mode, name, color, dash, w in (("elementar", "elementar", C.COLOR_OK, "solid", 3), ("k5", "Gedächtnis k = 5", C.COLOR_LINE, "dash", 2), ("k1", "Gedächtnis k = 1", C.COLOR_LINE2, "dot", 2)):
        pts = [(r["n"], r[mode]["labels_median"]) for r in table if r[mode]["labels_median"] is not None]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines+markers", line=dict(color=color, width=w, dash=dash), name=name,
                                 hovertemplate="n = %{x}: %{y:,.0f} Labels<extra></extra>"))
    fig.update_xaxes(title_text="Kunden n", range=[8, 31], dtick=5)
    fig.update_yaxes(title_text="Labels (Median, logarithmisch)", type="log", range=[2.5, 5.4])
    return _base(fig)


def build_abort_chart(rows):
    """Abgebrochene und fertige elementare Läufe je Fensterbreite bei 30 Kunden (gestapelt)."""
    names = [f"Breite {r['breite']}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=[r["fertig"] for r in rows], name="fertig", marker_color=C.COLOR_OK, hovertemplate="%{x}: %{y} fertige Läufe<extra></extra>"))
    fig.add_trace(go.Bar(x=names, y=[r["abgebrochen"] for r in rows], name="abgebrochen (Zeitgrenze)", marker_color=C.COLOR_BAD, hovertemplate="%{x}: %{y} abgebrochene Läufe<extra></extra>"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Fensterbreite")
    fig.update_yaxes(title_text="Läufe (je 6 Instanzen)", range=[0, 6.5], dtick=1)
    return _base(fig)
