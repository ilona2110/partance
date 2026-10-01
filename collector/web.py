"""Client HTTP poli : respecte robots.txt, espace les requêtes vers un même site, réessaie une fois."""
import time
import urllib.robotparser
from urllib.parse import urlsplit

import requests

UA = "Mozilla/5.0 (compatible; PartanceBot/1.0; alertes VIE a usage personnel)"


class Blocked(Exception):
    """Le site interdit cette adresse aux robots (robots.txt)."""


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
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.s.get(host + "/robots.txt", timeout=10)
                if r.status_code >= 500:
                    rp.disallow_all = True
                elif r.status_code >= 400:
                    rp.allow_all = True
                else:
                    rp.parse(r.text.splitlines())
            except requests.RequestException:
                rp.allow_all = True
            self._robots[host] = rp
        rp = self._robots[host]
        if not rp.can_fetch(UA, url) and not rp.can_fetch("*", url):
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
