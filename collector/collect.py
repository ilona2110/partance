"""Passage du robot : récupère les offres, met à jour docs/data/offers.json, envoie l'email d'alerte.

Variables d'environnement (secrets GitHub) :
  SMTP_USER, SMTP_PASS   adresse Gmail et mot de passe d'application (sans eux : pas d'email)
  EMAIL_TO               destinataire (par défaut SMTP_USER)
  PROFILE_JSON           profil copié depuis le site (sans lui : toutes les nouvelles offres sont envoyées)
  FULL=1                 force un passage complet sur toutes les pages
"""
import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mailer  # noqa: E402
from config import SOURCES, NOT_YET  # noqa: E402
from extract import requirements, duration_months  # noqa: E402
from geo import find_country  # noqa: E402
from score import score  # noqa: E402
from sources import ADAPTERS  # noqa: E402
from web import Http, Blocked  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("PARTANCE_DATA") or ROOT / "docs" / "data" / "offers.json")
KNOWN = Path(os.environ.get("PARTANCE_KNOWN") or ROOT / "state" / "known_ids.json")
KEEP_INCOMPLETE_DAYS = 45


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


def parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def site_url():
    if os.environ.get("SITE_URL"):
        return os.environ["SITE_URL"]
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner.lower()}.github.io/{name}/"
    return ""


def initial_seen(o, now):
    if o.get("publie") and o["publie"] <= now.date().isoformat():
        return o["publie"] + "T00:00:00Z"
    return iso(now - timedelta(days=2))


def enrich(raw, src):
    text = raw.get("desc") or ""
    req = requirements(raw["titre"], text)
    iso_, pays = find_country(raw.get("pays_hint"), raw.get("lieu"), raw.get("ville"), raw["titre"], text[:800])
    if not iso_ and raw.get("pays_hint") and len(raw["pays_hint"]) < 40:
        pays = raw["pays_hint"].strip().title()
    ville = raw.get("ville") or ""
    lieu = (raw.get("lieu") or "").strip()
    if not ville and lieu and not lieu[:1].isdigit():
        ville = lieu.split(",")[0].strip()
    return {
        "id": raw["id"],
        "src": "bf" if src["type"] == "businessfrance" else "carriere",
        "source": src["name"],
        "skey": src["key"],
        "titre": raw["titre"],
        "ent": raw.get("ent") or src["name"],
        "url": raw["url"],
        "ville": ville.title() if ville.isupper() else ville,
        "pays": pays,
        "iso": iso_,
        "ind": raw.get("ind"),
        "duree": raw.get("duree") or duration_months(raw["titre"] + "\n" + text),
        "debut": raw.get("debut"),
        "publie": raw.get("publie"),
        "cloture": raw.get("cloture"),
        **req,
        "extrait": text[:500],
    }


def load_previous():
    if DATA.exists():
        try:
            return json.loads(DATA.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def write(doc):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    offers = doc.pop("offers")
    head = json.dumps(doc, ensure_ascii=False, indent=1)
    lines = ",\n".join(json.dumps(o, ensure_ascii=False, sort_keys=True) for o in offers)
    DATA.write_text(head[:-2] + ',\n "offers": [\n' + lines + "\n ]\n}\n", encoding="utf-8")


def alert_countries(profile):
    """Pays des alertes : alertes.json à la racine du dépôt s'il en liste, sinon ceux du profil."""
    try:
        cfg = json.loads((ROOT / "alertes.json").read_text(encoding="utf-8"))
        if cfg.get("pays"):
            return set(cfg["pays"])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return set((profile or {}).get("pays") or [])


def run():
    now = now_utc()
    prev = load_previous()
    prev_offers = {o["id"]: o for o in prev.get("offers", [])}
    prev_sources = {s["key"]: s for s in prev.get("sources", [])}
    try:
        known_ever = set(json.loads(KNOWN.read_text())) | set(prev_offers)
    except (FileNotFoundError, json.JSONDecodeError):
        known_ever = set(prev_offers)
    full_env = os.environ.get("FULL") == "1" or (now.hour == 4 and now.minute < 15)
    http = Http()
    current, new_ids, statuses = {}, [], []

    for src in SOURCES:
        key = src["key"]
        ps = prev_sources.get(key, {})
        seeded = ps.get("seeded", False)
        mine = {i: o for i, o in prev_offers.items() if o.get("skey") == key}
        ctx = {
            "known": {i for i, o in mine.items() if o.get("extrait")},
            "full": full_env or not seeded,
            "detail_budget": 60 if src["type"] == "businessfrance" else 25,
        }
        st = {"key": key, "name": src["name"], "secteur": src.get("secteur", ""), "checked_at": iso(now), "seeded": seeded}
        t0 = time.time()
        try:
            raws, complete, info = ADAPTERS[src["type"]](src, http, ctx)
            ok, err = True, None
        except Blocked as e:
            raws, complete, info, ok, err = [], False, {}, False, f"Interdit aux robots : {e}"
        except Exception as e:  # une source en panne ne bloque pas les autres
            raws, complete, info, ok, err = [], False, {}, False, f"{type(e).__name__}: {str(e)[:300]}"
            traceback.print_exc()
        st["secs"] = round(time.time() - t0, 1)

        if ok and complete and not raws and len(mine) >= 5:
            ok, err = False, "0 offre trouvée alors qu'il y en avait avant : la page a peut-être changé"

        if ok:
            seen_now = set()
            for raw in raws:
                if raw["id"] in seen_now:
                    continue
                seen_now.add(raw["id"])
                o = enrich(raw, src)
                p = mine.get(o["id"])
                if p:
                    o["first_seen"] = p.get("first_seen", iso(now))
                    if not raw.get("desc") and p.get("extrait"):
                        for k in ("langues", "comps", "niv", "exp", "extrait"):
                            o[k] = p.get(k)
                        o["duree"] = o["duree"] or p.get("duree")
                elif seeded:
                    o["first_seen"] = iso(now)
                    if o["id"] not in known_ever:
                        new_ids.append(o["id"])
                else:
                    # Premier passage de la source : les offres déjà en ligne ne sont pas « nouvelles »
                    o["first_seen"] = initial_seen(o, now)
                o["last_seen"] = iso(now)
                current[o["id"]] = o
            if not complete:
                for pid, p in mine.items():
                    if pid not in current and now - parse_iso(p["first_seen"]) < timedelta(days=KEEP_INCOMPLETE_DAYS):
                        current[pid] = p
            st.update(ok=True, error=None, seeded=True, last_ok=iso(now))
        else:
            for pid, p in mine.items():
                current[pid] = p
            st.update(ok=False, error=err, last_ok=ps.get("last_ok"))
        st["count"] = sum(1 for o in current.values() if o.get("skey") == key)
        if info.get("fields"):
            st["fields"] = info["fields"]
        if info.get("filtre"):
            st["filtre"] = info["filtre"]
        derr = info.get("detail_error") or (ctx.get("detail_errors") or [None])[0]
        if derr:
            st["note"] = "Fiches détaillées indisponibles : " + derr
        statuses.append(st)
        print(f"[{key}] ok={st['ok']} offres={st['count']} nouvelles={sum(1 for i in new_ids if current.get(i, {}).get('skey') == key)} {st['secs']}s {err or ''}", flush=True)

    # ------------------------------------------------------------ email
    email_state = dict(prev.get("email", {}))
    email_state["configured"] = mailer.configured()
    profile = None
    if os.environ.get("PROFILE_JSON"):
        try:
            profile = json.loads(os.environ["PROFILE_JSON"])
        except json.JSONDecodeError:
            email_state["last_error"] = "PROFILE_JSON illisible : recopie-le depuis la page Alertes du site"
    email_state["profile"] = bool(profile)
    email_state["pays"] = sorted(alert_countries(profile))
    fresh = [current[i] for i in new_ids if i in current]
    if fresh and mailer.configured():
        items = []
        mn = (profile or {}).get("min", 70)
        pays = alert_countries(profile)
        for o in fresh:
            if pays and o.get("iso") not in pays:
                continue
            if profile:
                s, ok_, ko_ = score(o, profile)
                if s is None:
                    if profile.get("doms") and o.get("dom") not in profile["doms"]:
                        continue
                elif s < mn:
                    continue
            else:
                s, ok_, ko_ = None, [], []
            items.append((o, s, ok_, ko_))
        items.sort(key=lambda x: -(x[1] if x[1] is not None else -1))
        if items:
            try:
                subj = mailer.send(items[:40], site_url())
                email_state.update(last_sent_at=iso(now), last_count=len(items), last_subject=subj, last_error=None)
                print(f"Email envoyé : {subj}")
            except Exception as e:
                email_state["last_error"] = f"{type(e).__name__}: {str(e)[:200]}"
                print("Échec de l'email :", e)

    if os.environ.get("TEST_EMAIL") == "1":
        if not mailer.configured():
            email_state["last_error"] = "Test impossible : les secrets SMTP_USER et SMTP_PASS sont absents"
        else:
            pool = []
            for o in current.values():
                sc = score(o, profile) if profile else (None, [], [])
                pool.append((o, *sc))
            pool.sort(key=lambda x: (-(x[1] if x[1] is not None else -1), x[0]["first_seen"]), reverse=False)
            try:
                subj = mailer.send(pool[:3], site_url(), prefix="[Test Partance] ")
                email_state.update(test_sent_at=iso(now), last_error=None)
                print("Email de test envoyé :", subj)
            except Exception as e:
                email_state["last_error"] = f"Test : {type(e).__name__}: {str(e)[:200]}"
                print("Échec de l'email de test :", e)

    offers = sorted(current.values(), key=lambda o: (o["first_seen"], o["id"]), reverse=True)
    KNOWN.parent.mkdir(parents=True, exist_ok=True)
    KNOWN.write_text(json.dumps(sorted(known_ever | set(current))))
    doc = {
        "updated_at": iso(now),
        "requests": http.count,
        "not_yet": NOT_YET,
        "email": email_state,
        "sources": statuses,
        "new_last_run": len(fresh),
        "offers": offers,
    }
    write(doc)
    print(f"Total : {len(offers)} offres, {len(fresh)} nouvelles, {http.count} requêtes")


if __name__ == "__main__":
    run()
