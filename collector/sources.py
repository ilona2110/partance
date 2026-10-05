"""Sources d'offres VIE. Chaque source renvoie (offres brutes, liste complète ?)."""
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit, parse_qs

from bs4 import BeautifulSoup

from extract import clean_text, is_vie, clean_title, duration_months
from geo import slug_to_text

TODAY = date.today()


def _g(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, "", []):
            return d[k]
    return None


def _date(v):
    """Chaîne de date quelconque -> AAAA-MM-JJ (ou None)."""
    if not v:
        return None
    s = str(v).strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%b %d, %Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return parsedate_to_datetime(s).date().isoformat()
    except (TypeError, ValueError):
        return None


def _detail_targets(offers, ctx):
    """Offres nouvelles dont il faut lire la page détaillée, dans la limite du budget."""
    known = ctx.get("known", set())
    todo = [o for o in offers if o["id"] not in known and not o.get("desc")]
    return todo[: ctx.get("detail_budget", 25)]


def _page_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "form"]):
        tag.decompose()
    main = soup.select_one("article") or soup.select_one("main") or soup.select_one("[role=main]") or soup.body or soup
    return clean_text(main.get_text("\n"))[:8000]


# ---------------------------------------------------------------- Business France
BF_SITE = "https://mon-vie-via.businessfrance.fr"


def _bf_config(http):
    """Le site officiel publie dans sa page d'accueil l'adresse de son service d'offres et la clé
    publique qu'il envoie avec chaque requête. On les relit à chaque passage."""
    html = http.get_text(BF_SITE + "/")

    def conf(name):
        m = re.search(name + r':"([^"]+)"', html)
        return m.group(1).encode().decode("unicode_escape") if m else None

    api = conf("OFFRE_API_ENDPOINT") or "https://civiweb-api-prd.azurewebsites.net/api/Offers"
    key = conf("API_KEY")
    headers = {"Origin": BF_SITE, "Referer": BF_SITE + "/"}
    if key:
        headers["X-API-KEY"] = key
    return api, headers


def businessfrance(src, http, ctx):
    api, headers = _bf_config(http)
    out, skip, total, info = [], 0, None, {}
    while True:
        payload = {
            "limit": 100, "skip": skip, "latest": ["true"], "activitySectorId": [], "missionsTypesIds": [],
            "missionsDurations": [], "gerographicZones": [], "countriesIds": [], "studiesLevelId": [],
            "companiesSizes": [], "specializationsIds": [], "entreprisesIds": [0], "missionStartDate": None,
            "query": None,
        }
        r = http.post_json(api + "/search", payload, headers=headers)
        items = r if isinstance(r, list) else (_g(r, "result", "results", "offers", "items", "data") or [])
        if total is None:
            total = (r.get("count") or r.get("total") or r.get("totalCount")) if isinstance(r, dict) else None
            if isinstance(r, dict):
                info["top_keys"] = sorted(r.keys())[:20]
            if items and isinstance(items[0], dict):
                info["fields"] = sorted(items[0].keys())[:80]
        if not items:
            break
        for it in items:
            oid = _g(it, "id", "offerId", "idOffre")
            titre = _g(it, "missionTitle", "title", "offerTitle", "intitule")
            if not oid or not titre:
                continue
            mtype = str(_g(it, "missionType", "missionTypeLabel", "typeMission") or "")
            if "VIA" in mtype.upper() and "VIE" not in mtype.upper():
                continue
            desc = "\n".join(str(x) for x in [_g(it, "missionDescription", "description"), _g(it, "missionProfile", "profile", "candidateProfile")] if x)
            ind = _g(it, "indemnite", "indemnity", "allowance", "monthlyAllowance", "remuneration")
            dur = _g(it, "missionDuration", "duration", "duree")
            out.append({
                "id": f"bf-{oid}",
                "_raw_id": oid,
                "titre": clean_title(titre),
                "ent": _g(it, "organizationName", "companyName", "organisationName", "entreprise") or "",
                "url": f"{BF_SITE}/offres/{oid}",
                "ville": _g(it, "cityName", "city", "cityNameEn", "ville") or "",
                "pays_hint": _g(it, "countryName", "countryNameFr", "country", "countryNameEn", "pays") or "",
                "desc": clean_text(desc),
                "ind": round(float(ind)) if isinstance(ind, (int, float)) or (isinstance(ind, str) and re.fullmatch(r"[\d.]+", ind)) else None,
                "duree": int(dur) if isinstance(dur, (int, float)) or (isinstance(dur, str) and dur.isdigit()) else None,
                "debut": _date(_g(it, "missionStartDate", "startDate")),
                "publie": _date(_g(it, "startBroadcastDate", "publicationDate", "creationDate", "createdAt")),
                "cloture": _date(_g(it, "endBroadcastDate", "applicationEndDate", "closingDate")),
            })
        skip += len(items)
        if (total and skip >= total) or skip >= 5000 or len(items) < 100:
            break
    # Description absente de la recherche : lecture de la fiche pour les nouvelles offres
    for o in _detail_targets(out, ctx):
        try:
            d = http.get_json(f"{api}/details/{o['_raw_id']}", headers=headers)
            if o is out[0] or "detail_fields" not in info:
                info["detail_fields"] = sorted(d.keys())[:80] if isinstance(d, dict) else str(type(d))
            desc = "\n".join(str(x) for x in [_g(d, "missionDescription", "description"), _g(d, "missionProfile", "profile", "candidateProfile")] if x)
            o["desc"] = clean_text(desc)
            if o["ind"] is None:
                ind = _g(d, "indemnite", "indemnity", "allowance")
                o["ind"] = round(float(ind)) if isinstance(ind, (int, float)) else None
        except Exception as e:  # la recherche suffit si la fiche ne répond pas
            info["detail_error"] = str(e)[:200]
            break
    info["total"] = total
    return out, True, info


# ---------------------------------------------------------------- Workday (Airbus, Thales, Air Liquide, Michelin)
def _posted_on(s):
    if not s:
        return None
    s = s.lower()
    if "today" in s or "aujourd" in s:
        n = 0
    elif "yesterday" in s or "hier" in s:
        n = 1
    else:
        m = re.search(r"(\d+)", s)
        n = int(m.group(1)) if m else None
    return (TODAY - timedelta(days=n)).isoformat() if n is not None else None


_VIE_FACET = re.compile(r"(?<![A-Za-z])V\.?\s?I\.?\s?E\.?(?![A-Za-z])|volontariat international|international volunteer", re.I)


def _find_vie_facet(facets):
    """Cherche dans les filtres Workday une valeur « VIE » (type de contrat, type de poste…)."""
    for f in facets or []:
        for v in f.get("values", []) or []:
            if "values" in v:
                hit = _find_vie_facet([v])
                if hit:
                    return hit
            elif _VIE_FACET.search(v.get("descriptor") or ""):
                return f.get("facetParameter"), v.get("id"), v.get("descriptor")
    return None


def workday(src, http, ctx):
    base = f"https://{src['host']}/wday/cxs/{src['tenant']}/{src['site']}"
    first = http.post_json(base + "/jobs", {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""})
    facet = _find_vie_facet(first.get("facets"))
    if facet:
        body = {"appliedFacets": {facet[0]: [facet[1]]}, "searchText": ""}
        info = {"filtre": f"{facet[0]} = {facet[2]}"}
    else:
        body = {"appliedFacets": {}, "searchText": src.get("search", "VIE")}
        info = {"filtre": "recherche « VIE » dans les titres"}
    out, off, total = [], 0, None
    complete = False
    while off < 1000:
        r = http.post_json(base + "/jobs", {**body, "limit": 20, "offset": off})
        posts = r.get("jobPostings") or []
        if total is None:
            total = r.get("total") or 0
        for j in posts:
            title, path = j.get("title", ""), j.get("externalPath", "")
            if not path or (not facet and not is_vie(title)):
                continue
            out.append({
                "id": f"wd-{src['tenant']}-{path.rstrip('/').split('/')[-1]}",
                "_path": path,
                "titre": clean_title(title),
                "ent": src["name"],
                "url": f"https://{src['host']}/{src['site']}{path}",
                "lieu": j.get("locationsText", ""),
                "publie": _posted_on(j.get("postedOn")),
            })
        off += 20
        if not posts or off >= total:
            complete = True
            break
    for o in _detail_targets(out, ctx):
        try:
            jp = http.get_json(base + o["_path"]).get("jobPostingInfo", {})
            o["desc"] = clean_text(jp.get("jobDescription", ""))
            if jp.get("location") and not re.match(r"\d+ (locations|sites)", o["lieu"], re.I):
                o["lieu"] = jp["location"]
            o["pays_hint"] = (jp.get("country") or {}).get("descriptor", "")
            o["publie"] = _date(jp.get("startDate")) or o["publie"]
        except Exception:
            pass
    info["total"] = total
    return out, complete, info


# ---------------------------------------------------------------- Avature (L'Oréal, TotalEnergies)
_AVATURE_RE = re.compile(r"/JobDetail/([^/?#]+)/(\d+)")
_BUTTON_WORDS = re.compile(r"^(apply|apply now|postuler|candidater|voir l'offre|en savoir plus|read more|view job)$", re.I)
_DATE_RE = re.compile(r"\b(\d{1,2}[-/.](?:\d{1,2}|[A-Za-zéû]{3,4})[-/.]\d{4})\b")


def _single_job_block(a, pattern, jid):
    """Remonte depuis le lien jusqu'au plus grand bloc qui ne contient que cette offre."""
    node = a
    while node.parent is not None and node.parent.name not in ("body", "html", "[document]"):
        ids = {m.group(m.lastindex) for x in node.parent.find_all("a", href=True) for m in [pattern.search(x["href"])] if m}
        if ids - {jid}:
            break
        node = node.parent
    return node


def parse_link_list(html, base_url, pattern, id_group):
    """Liste d'offres à partir des liens : renvoie [{id, titre, url, bloc}] dans l'ordre de la page."""
    soup = BeautifulSoup(html, "html.parser")
    found = {}
    for a in soup.find_all("a", href=True):
        m = pattern.search(a["href"])
        if not m:
            continue
        jid = m.group(id_group)
        text = re.sub(r"\s+", " ", a.get_text(" ")).strip()
        cur = found.get(jid)
        if cur is None:
            found[jid] = cur = {"id": jid, "titre": "", "url": urljoin(base_url, a["href"]), "a": a, "m": m}
        if text and not _BUTTON_WORDS.match(text) and len(text) > len(cur["titre"]):
            cur["titre"] = text
    out = []
    for jid, it in found.items():
        block = _single_job_block(it["a"], pattern, jid)
        if not it["titre"]:
            h = block.find(["h2", "h3", "h4"])
            it["titre"] = re.sub(r"\s+", " ", h.get_text(" ")).strip() if h else ""
        lines = [l.strip() for l in block.get_text("\n").split("\n") if l.strip()]
        it["bloc"] = [l for l in lines if l != it["titre"] and not _BUTTON_WORDS.match(l)][:6]
        it["match"] = it.pop("m")
        it.pop("a")
        out.append(it)
    return out


def avature(src, http, ctx):
    out, seen, off = [], set(), 0
    complete = False
    for _ in range(25):
        url = f"{src['base']}/SearchJobs/{src.get('search', 'VIE')}?jobRecordsPerPage=50&jobOffset={off}"
        items = parse_link_list(http.get_text(url), url, _AVATURE_RE, 2)
        new = [i for i in items if i["id"] not in seen]
        if not new:
            complete = True
            break
        for it in new:
            seen.add(it["id"])
            if not is_vie(it["titre"]):
                continue
            date_ = next((d for l in it["bloc"] for d in [_DATE_RE.search(l)] if d), None)
            lieu = next((l for l in it["bloc"] if not _DATE_RE.search(l) and len(l) < 60 and l.upper() not in ("VIE", "V.I.E")), "")
            out.append({
                "id": f"av-{urlsplit(src['base']).netloc.split('.')[1]}-{it['id']}",
                "titre": clean_title(it["titre"]), "ent": src["name"], "url": it["url"],
                "lieu": lieu, "pays_hint": " ".join(it["bloc"]),
                "publie": _date(date_.group(1)) if date_ else None,
            })
        off += len(items)
    for o in _detail_targets(out, ctx):
        try:
            o["desc"] = _page_text(http.get_text(o["url"]))
        except Exception as e:
            ctx.setdefault("detail_errors", []).append(f"{type(e).__name__}: {str(e)[:150]}")
    return out, complete, {}


# ---------------------------------------------------------------- Safran
_SAFRAN_RE = re.compile(r"/(?:fr/)?(?:offres|jobs)/([a-z0-9-]+)/([a-z0-9-]+)/([a-z0-9-]+?)-(\d+)(?:[/?#]|$)")


def safran(src, http, ctx):
    out, seen = [], set()
    pages = 80 if ctx.get("full") else 4
    complete = False
    for n in range(pages):
        url = f"https://www.safran-group.com/fr/offres?search=VIE&page={n}"
        items = parse_link_list(http.get_text(url), url, _SAFRAN_RE, 4)
        new = [i for i in items if i["id"] not in seen]
        if not new:
            complete = True
            break
        for it in new:
            seen.add(it["id"])
            if not is_vie(it["titre"]):
                continue
            m = it["match"]
            out.append({
                "id": f"safran-{it['id']}", "titre": clean_title(it["titre"]), "ent": "Safran", "url": it["url"],
                "lieu": slug_to_text(m.group(2)).title(), "pays_hint": slug_to_text(m.group(1)),
            })
    for o in _detail_targets(out, ctx):
        try:
            o["desc"] = _page_text(http.get_text(o["url"]))
        except Exception as e:
            ctx.setdefault("detail_errors", []).append(f"{type(e).__name__}: {str(e)[:150]}")
    return out, complete and ctx.get("full", False), {}


# ---------------------------------------------------------------- BNP Paribas
_BNP_RE = re.compile(r"/emploi-carriere/offre-emploi/([a-z0-9-]+)")


def bnp(src, http, ctx):
    base = "https://group.bnpparibas/emploi-carriere/toutes-offres-emploi/vie"
    out, seen = [], set()
    complete = False
    for n in range(1, 20):
        url = base if n == 1 else f"{base}?page={n}"
        items = parse_link_list(http.get_text(url), url, _BNP_RE, 1)
        new = [i for i in items if i["id"] not in seen]
        if not new:
            complete = True
            break
        for it in new:
            seen.add(it["id"])
            if not is_vie(it["titre"]):
                continue
            out.append({
                "id": f"bnp-{it['id']}", "titre": clean_title(it["titre"]), "ent": "BNP Paribas", "url": it["url"],
                "lieu": "", "pays_hint": " ".join(it["bloc"]),
            })
    for o in _detail_targets(out, ctx):
        try:
            o["desc"] = _page_text(http.get_text(o["url"]))
        except Exception as e:
            ctx.setdefault("detail_errors", []).append(f"{type(e).__name__}: {str(e)[:150]}")
    return out, complete, {}


# ---------------------------------------------------------------- Flux RSS Talentsoft (CACEIS, Amundi)
def talentsoft_rss(src, http, ctx):
    root = ET.fromstring(http.get_text(src["url"]).encode("utf-8"))
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        title = re.sub(r"^\s*\d{4}-\d+\s*-\s*", "", title)
        if not link or not is_vie(title):
            continue
        q = parse_qs(urlsplit(link).query)
        oid = (q.get("idOffre") or [link])[0]
        out.append({
            "id": f"ts-{src['name'].lower()}-{oid}", "titre": clean_title(title), "ent": src["name"], "url": link,
            "lieu": "", "desc": clean_text(item.findtext("description") or ""),
            "publie": _date(item.findtext("pubDate")),
        })
    for o in [x for x in out if x["id"] not in ctx.get("known", set())][: ctx.get("detail_budget", 25)]:
        try:
            o["desc"] = _page_text(http.get_text(o["url"]))
        except Exception as e:
            ctx.setdefault("detail_errors", []).append(f"{type(e).__name__}: {str(e)[:150]}")
    return out, False, {}


ADAPTERS = {
    "businessfrance": businessfrance,
    "workday": workday,
    "avature": avature,
    "safran": safran,
    "bnp": bnp,
    "talentsoft_rss": talentsoft_rss,
}
