"""Score d'une offre par rapport au profil. Même logique que le site (docs/index.html)."""

LV = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
NIV = {2: "Bac+2", 3: "Bac+3", 4: "Bac+4", 5: "Bac+5"}


def score(o, p):
    """Renvoie (score sur 100 ou None, atouts, manques)."""
    W = E = 0.0
    ok, ko = [], []
    pl = {x["l"]: x["n"] for x in p.get("langues", [])}
    if o.get("langues"):
        sub = 0.0
        for r in o["langues"]:
            hv, rv = LV.get(pl.get(r["l"]), 0), LV.get(r["n"], 4)
            if hv >= rv:
                sub += 1
                ok.append(f'{r["l"]} {pl[r["l"]]}')
            elif hv and rv - hv == 1:
                sub += 0.5
                ko.append(f'{r["l"]} {r["n"]} (tu as {pl[r["l"]]})')
            else:
                ko.append(f'{r["l"]} {r["n"]}')
        W += 30
        E += 30 * sub / len(o["langues"])
    if o.get("niv"):
        W += 20
        if (p.get("niv") or 0) >= o["niv"]:
            E += 20
            ok.append(NIV.get(p["niv"], ""))
        else:
            ko.append(NIV.get(o["niv"], "diplôme"))
    if o.get("comps"):
        W += 30
        have = set(p.get("comps", []))
        n = 0
        for c in o["comps"]:
            if c in have:
                n += 1
                ok.append(c)
            else:
                ko.append(c)
        E += 30 * n / len(o["comps"])
    if o.get("exp") is not None:
        W += 10
        y = p.get("exp") or 0
        if y >= o["exp"]:
            E += 10
        elif y > 0:
            E += 5
        else:
            ko.append(f'{o["exp"]} an(s) d\'expérience')
    if W == 0:
        return None, ok, ko
    if p.get("doms"):
        W += 10
        if o.get("dom") in p["doms"]:
            E += 10
    return round(100 * E / W), ok, ko
