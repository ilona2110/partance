"""Tests hors ligne du robot : `python collector/test_collector.py` (aucune requête réseau)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import extract  # noqa: E402
import geo  # noqa: E402
import mailer  # noqa: E402
import score as scoring  # noqa: E402
import sources  # noqa: E402
import web  # noqa: E402


class FakeResp:
    def __init__(self, body, status=200):
        self.body, self.status_code = body, status

    @property
    def text(self):
        return self.body if isinstance(self.body, str) else json.dumps(self.body)

    def json(self):
        return self.body if not isinstance(self.body, str) else json.loads(self.body)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeHttp(web.Http):
    """Répond à partir d'une table {(méthode, début d'URL): réponse ou fonction}."""

    def __init__(self, routes):
        super().__init__(delay=0)
        self.routes = routes
        self.calls = []

    def _robot(self, url):
        if "interdit" in url:
            raise web.Blocked("robots.txt interdit " + url)

    def request(self, method, url, **kw):
        self._robot(url)
        self.calls.append((method, url))
        self.count += 1
        for (m, prefix), resp in self.routes.items():
            if m == method and url.startswith(prefix):
                body = resp(url, kw) if callable(resp) else resp
                r = FakeResp(body)
                r.raise_for_status()
                return r
        raise RuntimeError(f"route inconnue {method} {url}")


BF_ITEMS = [
    {"id": 101, "missionTitle": "Analyste FP&A", "organizationName": "GROUPE TEST", "cityName": "NEW YORK", "countryName": "ETATS-UNIS",
     "missionDuration": 18, "missionStartDate": "2026-11-01T00:00:00", "creationDate": "2026-09-30T08:00:00", "indemnite": 4120.5,
     "missionDescription": "<p>Reporting mensuel, Excel et Power BI.</p>", "missionProfile": "Master en finance, anglais courant, 2 ans d'expérience."},
    {"id": 102, "missionTitle": "Ingénieur procédés", "organizationName": "AGRO SA", "cityName": "MONTERREY", "countryName": "MEXIQUE",
     "missionDuration": 12, "creationDate": "2026-09-29T08:00:00", "indemnite": 2580, "missionDescription": "Lean, Six Sigma. Espagnol B2."},
]

AVATURE_HTML = """<html><body><nav><a href="/fr_FR/careers/JobDetail/Ignore/1">x</a></nav>
<ul class="results">
<li class="job"><h3><a href="https://jobs.totalenergies.com/fr_FR/careers/JobDetail/VIE-Acheteur-Congo/83140">VIE – Acheteur de services (H/F) – Congo</a></h3>
<ul><li>05-08-2026</li><li>Republic of the Congo</li><li>VIE</li><li>TotalEnergies EP Congo</li></ul>
<a href="https://jobs.totalenergies.com/fr_FR/careers/ApplicationMethods?jobId=83140">Postuler</a></li>
<li class="job"><h3><a href="/fr_FR/careers/JobDetail/CDI-Juriste/83999">CDI - Juriste (H/F)</a></h3><ul><li>01-09-2026</li><li>France</li></ul></li>
<li class="job"><h3><a href="/fr_FR/careers/JobDetail/VIE-Business-Developer-Pays-Bas/83717">VIE – Business Developer (H/F) – Pays-Bas</a></h3>
<ul><li>01-09-2026</li><li>Netherlands</li><li>VIE</li></ul></li>
</ul></body></html>"""

SAFRAN_HTML = """<html><body><div class="list">
<div class="card"><a href="/fr/offres/royaume-uni/segensworth-north-fareham-hampshire/it-business-application-186357"><h3>VIE IT business application</h3></a><span>Royaume-Uni</span></div>
<div class="card"><a href="/fr/offres/france/rennes/apprenti-e-rh-generaliste-fh-186647">Apprenti(e) RH généraliste F/H</a></div>
<div class="card"><a href="https://www.safran-group.com/fr/offres/indonesie/jakartapekanbaru/vie-coordinateur-activites-support-soutien-indonesie-fh-170110">VIE Coordinateur des activités de support en Indonésie F-H</a></div>
</div><a href="/fr/offres?search=VIE&page=1">Suivant</a></body></html>"""

BNP_HTML = """<html><body>
<article><a href="/emploi-carriere/offre-emploi/vie-compliance-analyst-hong-kong-h-f"><h3>VIE - Compliance Analyst - Hong Kong H/F</h3></a><p>Hong Kong · Conformité</p></article>
<article><a href="/emploi-carriere/offre-emploi/alternance-charge-de-coordination-vie-international-rh-h-f-paris">Alternance - Chargé de coordination VIE International RH H/F</a></article>
<article><a href="/emploi-carriere/offre-emploi/v-i-e-communication-officer-milan-h-f">V.I.E - Communication Officer - Milan, H/F</a></article>
</body></html>"""

RSS = """<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>CACEIS</title>
<item><title>2026-116038 - VIE - Analyste KYC M/F H/F</title><link>https://jobs.caceis.com/Pages/Offre/detailoffre.aspx?idOffre=116038&amp;idOrigine=192440&amp;LCID=1036</link>
<description>&lt;p&gt;Luxembourg. Revue KYC, anglais C1.&lt;/p&gt;</description><pubDate>Tue, 29 Sep 2026 10:00:00 GMT</pubDate></item>
<item><title>2026-115106 - Middle Officer H/F</title><link>https://jobs.caceis.com/Pages/Offre/detailoffre.aspx?idOffre=115106</link></item>
</channel></rss>"""

DETAIL_HTML = "<html><body><header>Menu Excel</header><main><h1>Poste</h1><p>Profil : Bac+5, anglais courant, SAP. Mission de 24 mois.</p></main><footer>x</footer></body></html>"


def workday_route(url, kw):
    if url.endswith("/jobs"):
        body = kw["json"]
        if body["limit"] == 1:
            facets = [{"facetParameter": "jobFamilyGroup", "values": [{"descriptor": "Finance", "id": "f1"}]}]
            if "ag.wd3" in url:
                facets.append({"facetParameter": "workerSubType", "values": [{"descriptor": "CDI", "id": "x"}, {"descriptor": "VIE", "id": "vie-id"}]})
            return {"total": 500, "jobPostings": [], "facets": facets}
        if body["appliedFacets"]:
            assert body["appliedFacets"] == {"workerSubType": ["vie-id"]}
            if body["offset"] == 0:
                return {"total": 2, "jobPostings": [
                    {"title": "Ingénieur qualité (H/F)", "externalPath": "/job/Hamburg/Ingenieur-qualite_JR100", "locationsText": "Hamburg", "postedOn": "Posted Today"},
                    {"title": "Supply Chain Analyst", "externalPath": "/job/Singapore/SC_JR102", "locationsText": "2 Locations", "postedOn": "Posted 30+ Days Ago"},
                ]}
            return {"total": 0, "jobPostings": []}
        if body["offset"] == 0:
            return {"total": 3, "jobPostings": [
                {"title": "VIE - Ingénieur qualité (H/F)", "externalPath": "/job/Hamburg/VIE-Ingenieur-qualite_JR100", "locationsText": "Hamburg", "postedOn": "Posted Today"},
                {"title": "Vienna Office Manager", "externalPath": "/job/Vienna/Office_JR101", "locationsText": "Vienna", "postedOn": "Posted 3 Days Ago"},
                {"title": "V.I.E Supply Chain Analyst", "externalPath": "/job/Singapore/VIE-SC_JR102", "locationsText": "2 Locations", "postedOn": "Posted 30+ Days Ago"},
            ]}
        return {"total": 0, "jobPostings": []}
    return {"jobPostingInfo": {"jobDescription": "<p>Allemand B2, anglais courant. Lean.</p>", "location": "Hamburg", "country": {"descriptor": "Germany"}}}


BF_HOME = '<html><script>window.__NUXT__=(function(a){return {config:{OFFRE_API_ENDPOINT:"https:\\u002F\\u002Fciviweb-api-prd.azurewebsites.net\\u002Fapi\\u002FOffers",API_KEY:"cle\\u002Fpublique+1="}}}(1))</script></html>'


def bf_search(url, kw):
    assert kw["headers"].get("X-API-KEY") == "cle/publique+1=", kw["headers"]
    return {"result": BF_ITEMS, "count": len(BF_ITEMS)}


def routes():
    return {
        ("GET", "https://mon-vie-via.businessfrance.fr/"): BF_HOME,
        ("POST", "https://civiweb-api-prd.azurewebsites.net/api/Offers/search"): bf_search,
        ("POST", "https://ag.wd3.myworkdayjobs.com/wday/cxs/ag/Airbus/jobs"): workday_route,
        ("GET", "https://ag.wd3.myworkdayjobs.com/wday/cxs/ag/Airbus/job/"): workday_route,
        ("POST", "https://thales.wd3.myworkdayjobs.com/wday/cxs/thales/Careers/jobs"): workday_route,
        ("GET", "https://thales.wd3.myworkdayjobs.com/wday/cxs/thales/Careers/job/"): workday_route,
        ("GET", "https://jobs.totalenergies.com/fr_FR/careers/SearchJobs/VIE?jobRecordsPerPage=50&jobOffset=0"): AVATURE_HTML,
        ("GET", "https://jobs.totalenergies.com/fr_FR/careers/SearchJobs/VIE?"): "<html><body>Aucun résultat</body></html>",
        ("GET", "https://jobs.totalenergies.com/fr_FR/careers/JobDetail/"): DETAIL_HTML,
        ("GET", "https://www.safran-group.com/fr/offres?search=VIE&page=0"): SAFRAN_HTML,
        ("GET", "https://www.safran-group.com/fr/offres?search=VIE&page="): "<html><body></body></html>",
        ("GET", "https://www.safran-group.com/fr/offres/"): DETAIL_HTML,
        ("GET", "https://group.bnpparibas/emploi-carriere/toutes-offres-emploi/vie?page="): "<html><body></body></html>",
        ("GET", "https://group.bnpparibas/emploi-carriere/toutes-offres-emploi/vie"): BNP_HTML,
        ("GET", "https://group.bnpparibas/emploi-carriere/offre-emploi/"): DETAIL_HTML,
        ("GET", "https://jobs.caceis.com/handlers/offerRss.ashx"): RSS,
        ("GET", "https://jobs.caceis.com/Pages/Offre/"): DETAIL_HTML,
    }


class TestExtract(unittest.TestCase):
    def test_vie_filter(self):
        self.assertTrue(extract.is_vie("VIE – Business Developer (M/F)"))
        self.assertTrue(extract.is_vie("V.I.E - Communication Officer - Milan"))
        self.assertTrue(extract.is_vie("Industrial Project Engineer - VIE F-H"))
        self.assertFalse(extract.is_vie("Vienna Office Manager"))
        self.assertFalse(extract.is_vie("Qualité de vie au travail"))
        self.assertFalse(extract.is_vie("Alternance - Chargé de coordination VIE International RH"))

    def test_requirements(self):
        r = extract.requirements("Analyste FP&A", "Master en finance, anglais courant, espagnol B1, Excel, SAP. 2 ans d'expérience minimum.")
        self.assertEqual(r["niv"], 5)
        self.assertIn({"l": "Anglais", "n": "C1"}, r["langues"])
        self.assertIn({"l": "Espagnol", "n": "B1"}, r["langues"])
        self.assertEqual(set(r["comps"]) >= {"Excel", "SAP"}, True)
        self.assertEqual(r["exp"], 2)
        self.assertEqual(r["dom"], "fin")
        self.assertEqual(extract.domain("Ingénieur DevOps"), "it")
        self.assertEqual(extract.domain("Supply Chain Engineer"), "sc")

    def test_geo(self):
        self.assertEqual(geo.find_country("ETATS-UNIS")[0], "US")
        self.assertEqual(geo.find_country("Toulouse, France", "VIE Hamburg")[0], "DE")
        self.assertEqual(geo.find_country("Toulouse, France")[0], "FR")
        self.assertEqual(geo.find_country("", "VIE - Operational Risk - Tokyo, H/F")[0], "JP")

    def test_score(self):
        o = {"langues": [{"l": "Anglais", "n": "C1"}], "niv": 5, "comps": ["Excel", "SQL"], "exp": None, "dom": "fin"}
        p = {"langues": [{"l": "Anglais", "n": "C1"}], "niv": 5, "comps": ["Excel"], "exp": 2, "doms": ["fin"]}
        s, ok, ko = scoring.score(o, p)
        self.assertEqual(s, round(100 * (30 + 20 + 15 + 10) / 90))
        self.assertIn("SQL", ko)
        self.assertEqual(scoring.score({"dom": "fin"}, p)[0], None)


class TestSources(unittest.TestCase):
    def run_src(self, src, ctx=None):
        return sources.ADAPTERS[src["type"]](src, FakeHttp(routes()), ctx or {"known": set(), "full": True})

    def test_businessfrance(self):
        out, complete, info = self.run_src({"type": "businessfrance", "name": "Business France"})
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["ind"], 4120)
        self.assertEqual(out[0]["publie"], "2026-09-30")
        self.assertIn("anglais courant", out[0]["desc"])
        self.assertIn("missionTitle", info["fields"])

    def test_workday_facet(self):
        out, complete, info = self.run_src({"type": "workday", "name": "Airbus", "host": "ag.wd3.myworkdayjobs.com", "tenant": "ag", "site": "Airbus"})
        self.assertEqual([o["titre"] for o in out], ["Ingénieur qualité (H/F)", "Supply Chain Analyst"])
        self.assertIn("workerSubType", info["filtre"])
        self.assertTrue(complete)
        self.assertEqual(out[0]["pays_hint"], "Germany")
        self.assertIn("Allemand B2", out[0]["desc"])

    def test_workday_titles(self):
        out, complete, info = self.run_src({"type": "workday", "name": "Thales", "host": "thales.wd3.myworkdayjobs.com", "tenant": "thales", "site": "Careers"})
        self.assertEqual([o["titre"] for o in out], ["VIE - Ingénieur qualité (H/F)", "V.I.E Supply Chain Analyst"])
        self.assertIn("titres", info["filtre"])

    def test_robots(self):
        r = web.Robots("User-agent: *\nAllow: /*/careers\nDisallow: /*/careers/*qtvc=\nDisallow: /\n")
        self.assertTrue(r.allowed("PartanceBot", "/fr_FR/careers/SearchJobs/VIE?jobOffset=0"))
        self.assertFalse(r.allowed("PartanceBot", "/fr_FR/careers/x?qtvc=1"))
        self.assertFalse(r.allowed("PartanceBot", "/admin"))
        self.assertTrue(web.Robots("User-agent: *\nDisallow: /refresh\n").allowed("PartanceBot", "/offres/1"))

    def test_avature(self):
        out, complete, _ = self.run_src({"type": "avature", "name": "TotalEnergies", "base": "https://jobs.totalenergies.com/fr_FR/careers"})
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["id"], "av-totalenergies-83140")
        self.assertEqual(out[0]["publie"], "2026-08-05")
        self.assertIn("Congo", out[0]["lieu"])
        self.assertTrue(complete)

    def test_safran(self):
        out, complete, _ = self.run_src({"type": "safran", "name": "Safran"})
        self.assertEqual([o["id"] for o in out], ["safran-186357", "safran-170110"])
        self.assertEqual(out[0]["pays_hint"], "royaume uni")

    def test_bnp(self):
        out, _, _ = self.run_src({"type": "bnp", "name": "BNP Paribas"})
        self.assertEqual(len(out), 2)
        self.assertTrue(out[0]["titre"].startswith("VIE - Compliance"))

    def test_rss(self):
        out, complete, _ = self.run_src({"type": "talentsoft_rss", "name": "CACEIS", "url": "https://jobs.caceis.com/handlers/offerRss.ashx?LCID=1036"})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["titre"], "VIE - Analyste KYC M/F H/F")
        self.assertEqual(out[0]["id"], "ts-caceis-116038")
        self.assertFalse(complete)


class TestRun(unittest.TestCase):
    def test_two_runs_and_email(self):
        import collect
        with tempfile.TemporaryDirectory() as d:
            data, known = Path(d) / "offers.json", Path(d) / "known.json"
            cfg = [
                {"key": "bf", "type": "businessfrance", "name": "Business France", "secteur": "x"},
                {"key": "airbus", "type": "workday", "name": "Airbus", "host": "ag.wd3.myworkdayjobs.com", "tenant": "ag", "site": "Airbus", "secteur": "x"},
                {"key": "bloque", "type": "bnp", "name": "Site interdit", "secteur": "x"},
            ]
            r = routes()
            sent = []
            env = {"SMTP_USER": "moi@example.com", "SMTP_PASS": "x", "GITHUB_REPOSITORY": "Moi/partance",
                   "PROFILE_JSON": json.dumps({"langues": [{"l": "Anglais", "n": "C1"}], "niv": 5, "comps": ["Excel", "Power BI"], "exp": 2, "doms": ["fin"], "min": 60})}
            with mock.patch.object(collect, "DATA", data), mock.patch.object(collect, "KNOWN", known), \
                    mock.patch.object(collect, "SOURCES", cfg), mock.patch.object(collect, "Http", lambda: FakeHttp(r)), \
                    mock.patch.dict(os.environ, env), mock.patch.object(collect.mailer, "send", lambda items, url: sent.append((items, url)) or "sujet"), \
                    mock.patch.object(sources, "bnp", lambda *a: (_ for _ in ()).throw(web.Blocked("robots.txt interdit"))):
                collect.ADAPTERS["bnp"] = sources.bnp
                collect.run()
                doc = json.loads(data.read_text())
                self.assertEqual(len(doc["offers"]), 4)
                self.assertEqual(sent, [])  # premier passage : pas d'email
                st = {s["key"]: s for s in doc["sources"]}
                self.assertTrue(st["bf"]["ok"])
                self.assertFalse(st["bloque"]["ok"])
                self.assertIn("robots", st["bloque"]["error"])
                fp = next(o for o in doc["offers"] if o["id"] == "bf-101")
                self.assertEqual(fp["iso"], "US")
                self.assertEqual(fp["ville"], "New York")

                BF_ITEMS.append({"id": 103, "missionTitle": "Contrôleur de gestion junior", "organizationName": "AERO", "cityName": "SINGAPOUR",
                                 "countryName": "SINGAPOUR", "missionDuration": 24, "indemnite": 3420,
                                 "missionDescription": "Bac+5, anglais courant, Excel et Power BI. Contrôle de gestion."})
                collect.run()
                BF_ITEMS.pop()
                doc = json.loads(data.read_text())
                self.assertEqual(doc["new_last_run"], 1)
                self.assertEqual(len(sent), 1)
                self.assertEqual(sent[0][0][0][0]["id"], "bf-103")
                self.assertEqual(sent[0][1], "https://moi.github.io/partance/")
                self.assertEqual(doc["email"]["last_count"], 1)
            collect.ADAPTERS["bnp"] = sources.bnp

    def test_email_build(self):
        o = {"titre": "Analyste", "ent": "ACME", "ville": "Tokyo", "pays": "Japon", "ind": 3500, "duree": 12, "source": "Business France", "url": "https://x"}
        subj, text, body = mailer.build([(o, 88, ["Anglais C1"], ["SQL"])], "https://site")
        self.assertIn("Analyste", subj)
        self.assertIn("3 500 €/mois", text)
        self.assertIn("88", body)


if __name__ == "__main__":
    unittest.main(verbosity=1)
