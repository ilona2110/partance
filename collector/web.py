"""Client HTTP poli : respecte robots.txt, espace les requêtes vers un même site, réessaie une fois."""
import re
import time
from urllib.parse import urlsplit

import requests

UA = "Mozilla/5.0 (compatible; PartanceBot/1.0; alertes VIE a usage personnel)"


class Blocked(Exception):
    """Le site interdit cette adresse aux robots (robots.txt)."""


class Robots:
    """robots.txt selon la RFC 9309 : la règle la plus longue gagne, Allow l'emporte à égalité, jokers * et $."""

    def __init__(self, text="", allow_all=False, disallow_all=False):
        self.allow_all, self.disallow_all = allow_all, disallow_all
        self.groups = {}
        agents, rules_started = [], False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, val = (x.strip() for x in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if rules_started:
                    agents, rules_started = [], False
                agents.append(val.lower())
                for a in agents:
                    self.groups.setdefault(a, [])
            elif key in ("allow", "disallow") and agents:
                rules_started = True
                for a in agents:
                    self.groups[a].append((key == "allow", val))

    @staticmethod
    def _match(pattern, path):
        rx = re.escape(pattern).replace(r"\*", ".*")
        if rx.endswith(r"\$"):
            rx = rx[:-2] + "$"
        return re.match(rx, path) is not None

    def allowed(self, agent, path):
        if self.allow_all:
            return True
        if self.disallow_all:
            return False
        agent = agent.lower()
        rules = next((r for a, r in self.groups.items() if a != "*" and a in agent), None)
        if rules is None:
            rules = self.groups.get("*", [])
        best = None
        for allow, pat in rules:
            if not pat:
                continue
            if self._match(pat, path):
                cand = (len(pat), allow)
                if best is None or cand[0] > best[0] or (cand[0] == best[0] and allow):
                    best = cand
        return best is None or best[1]


class Http:
    def __init__(self, delay=1.0, timeout=25):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"})
        self.delay = delay
        self.timeout = timeout
        self._robots = {}
        self._last = {}
        self.count = 0

    def _robot(self, url):
        parts = urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host not in self._robots:
            try:
                r = self.s.get(host + "/robots.txt", timeout=10)
                if r.status_code >= 500:
                    rp = Robots(disallow_all=True)
                elif r.status_code >= 400:
                    rp = Robots(allow_all=True)
                else:
                    rp = Robots(r.text)
            except requests.RequestException:
                rp = Robots(allow_all=True)
            self._robots[host] = rp
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        if not self._robots[host].allowed("PartanceBot", path):
            raise Blocked(f"robots.txt interdit {parts.netloc}{parts.path}")

    def _wait(self, url):
        host = urlsplit(url).netloc
        last = self._last.get(host)
        if last is not None:
            gap = time.time() - last
            if gap < self.delay:
                time.sleep(self.delay - gap)
        self._last[host] = time.time()

    def request(self, method, url, **kw):
        self._robot(url)
        kw.setdefault("timeout", self.timeout)
        for attempt in range(2):
            self._wait(url)
            self.count += 1
            try:
                r = self.s.request(method, url, **kw)
            except requests.RequestException:
                if attempt:
                    raise
                time.sleep(3)
                continue
            if r.status_code in (429, 502, 503, 504) and not attempt:
                time.sleep(5)
                continue
            r.raise_for_status()
            return r
        raise RuntimeError("échec de la requête")

    def get_text(self, url, **kw):
        return self.request("GET", url, **kw).text

    def get_json(self, url, **kw):
        return self.request("GET", url, headers={"Accept": "application/json"}, **kw).json()

    def post_json(self, url, payload, headers=None, **kw):
        h = {"Accept": "application/json", "Content-Type": "application/json"}
        h.update(headers or {})
        return self.request("POST", url, json=payload, headers=h, **kw).json()
