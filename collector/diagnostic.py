"""Diagnostic ponctuel : comment répondent les sources. Écrit ses résultats dans probe/."""
import json
import re
from pathlib import Path

import requests

OUT = Path("probe")
OUT.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (compatible; PartanceBot/1.0; alertes VIE a usage personnel)"
s = requests.Session()
s.headers["User-Agent"] = UA


def save(name, text):
    (OUT / name).write_text(text if isinstance(text, str) else json.dumps(text, ensure_ascii=False, indent=1))


def short(r):
    return {"status": r.status_code, "headers": {k: v for k, v in r.headers.items() if k.lower() in ("content-type", "www-authenticate", "server", "cf-ray", "x-cache", "set-cookie")}, "body": r.text[:800]}


report = {}

# 1. Business France : quel appel fait le site officiel ?
try:
    site = "https://mon-vie-via.businessfrance.fr/"
    html = s.get(site, timeout=30).text
    save("bf_index.html", html)
    scripts = re.findall(r'src="([^"]+\.js)"', html)
    report["bf_scripts"] = scripts
    found = []
    for src in scripts:
        url = src if src.startswith("http") else site + src.lstrip("/")
        js = s.get(url, timeout=60).text
        (OUT / ("js_" + src.rstrip("/").split("/")[-1])).write_text(js)
        for pat in [r"civiweb[^\"'`]{0,120}", r"api/Offers[^\"'`]{0,80}", r"[Oo]cp-[Aa]pim[^\"'`]{0,80}", r"apiUrl[^,;]{0,160}", r"environment[^;]{0,300}?api[^;]{0,200}", r"Authorization[^;]{0,160}", r"[Tt]oken[\"']?\s*[:=][^;]{0,120}", r"setHeaders[^;]{0,200}", r"headers\s*:\s*\{[^}]{0,200}"]:
            for m in re.finditer(pat, js):
                a = max(0, m.start() - 150)
                found.append(f"[{src}] …{js[a:m.end() + 150]}…")
    save("bf_js_matches.txt", "\n\n".join(dict.fromkeys(found))[:200000])
    payload = {"limit": 2, "skip": 0, "latest": ["true"], "query": None}
    api = "https://civiweb-api-prd.azurewebsites.net/api/Offers/search"
    report["bf_post_plain"] = short(s.post(api, json=payload, timeout=30))
    report["bf_post_origin"] = short(s.post(api, json=payload, headers={"Origin": site.rstrip("/"), "Referer": site}, timeout=30))
    report["bf_robots_site"] = s.get(site + "robots.txt", timeout=20).text[:1500]
except Exception as e:
    report["bf_error"] = repr(e)

# 2. Workday : combien d'offres « VIE » et quels titres
for name, host, tenant, site_ in [("airbus", "ag.wd3.myworkdayjobs.com", "ag", "Airbus"), ("thales", "thales.wd3.myworkdayjobs.com", "thales", "Careers"),
                                  ("airliquide", "airliquidehr.wd3.myworkdayjobs.com", "airliquidehr", "AirLiquideExternalCareer"), ("michelin", "michelinhr.wd3.myworkdayjobs.com", "michelinhr", "Michelin")]:
    out = {}
    for q in ["VIE", "V.I.E", "Volontariat International"]:
        try:
            r = s.post(f"https://{host}/wday/cxs/{tenant}/{site_}/jobs", json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": q}, timeout=30)
            j = r.json()
            out[q] = {"status": r.status_code, "total": j.get("total"), "titles": [p.get("title") for p in j.get("jobPostings", [])],
                      "facets": j.get("facets", [])}
        except Exception as e:
            out[q] = repr(e)
    report[f"wd_{name}"] = out

# 3. Sites qui ont répondu 403 : robots.txt et type de blocage
for name, url in [("loreal", "https://careers.loreal.com/fr_FR/jobs/SearchJobs/VIE"), ("bnp", "https://group.bnpparibas/emploi-carriere/toutes-offres-emploi/vie"),
                  ("total", "https://jobs.totalenergies.com/fr_FR/careers/SearchJobs/VIE")]:
    try:
        root = re.match(r"https://[^/]+", url).group(0)
        report[f"{name}_robots"] = s.get(root + "/robots.txt", timeout=20).text[:2000]
        report[f"{name}_get"] = short(s.get(url, timeout=30))
    except Exception as e:
        report[f"{name}_error"] = repr(e)

save("report.json", report)
print("ok")
