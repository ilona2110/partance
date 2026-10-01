"""Lecture des exigences d'une offre (langues, diplôme, compétences, expérience, domaine)."""
import re
import html as htmlmod

LANGS = [
    ("Anglais", ["anglais", "english"]),
    ("Espagnol", ["espagnol", "spanish", "español", "castillan"]),
    ("Allemand", ["allemand", "german", "deutsch"]),
    ("Italien", ["italien", "italian"]),
    ("Portugais", ["portugais", "portuguese"]),
    ("Chinois", ["chinois", "mandarin", "chinese"]),
    ("Japonais", ["japonais", "japanese"]),
    ("Coréen", ["coréen", "coreen", "korean"]),
    ("Arabe", ["arabe", "arabic"]),
    ("Néerlandais", ["néerlandais", "neerlandais", "dutch"]),
    ("Polonais", ["polonais", "polish"]),
    ("Russe", ["russe", "russian"]),
    ("Français", ["français", "francais", "french"]),
]

SKILLS = {
    "Excel": ["excel"], "SQL": ["sql"], "Python": ["python"], "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau software", "tableau desktop"], "SAP": ["sap"], "Salesforce": ["salesforce"],
    "Java": ["java"], "JavaScript": ["javascript", "typescript"], "React": ["react", "reactjs"],
    "AWS": ["aws", "amazon web services"], "Azure": ["azure"], "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"], "CATIA": ["catia"], "SolidWorks": ["solidworks"],
    "AutoCAD": ["autocad"], "MATLAB": ["matlab"], "Lean": ["lean"], "Six Sigma": ["six sigma", "6 sigma"],
    "Gestion de projet": ["gestion de projet", "project management", "chef de projet", "pilotage de projet", "project manager"],
    "Prospection": ["prospection", "business development", "développement commercial", "developpement commercial"],
    "Négociation": ["négociation", "negociation", "negotiation"],
    "CRM": ["crm", "hubspot"],
    "Marketing digital": ["marketing digital", "digital marketing", "seo", "réseaux sociaux", "social media"],
    "Supply chain": ["supply chain", "approvisionnement"],
    "Achats": ["achats", "procurement", "sourcing", "purchasing"],
    "Logistique": ["logistique", "logistics"],
    "Contrôle de gestion": ["contrôle de gestion", "controle de gestion", "controlling", "fp&a", "reporting budgétaire", "financial controller"],
    "Audit": ["audit", "auditeur", "auditrice"],
    "IFRS": ["ifrs"], "Consolidation": ["consolidation"], "KYC": ["kyc"],
    "Conformité": ["conformité", "compliance", "lcb-ft", "aml"],
}

_LVL = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}


def clean_text(s):
    """HTML -> texte brut sur une ligne par bloc."""
    if not s:
        return ""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</(p|li|div|h\d|tr)>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = htmlmod.unescape(s)
    s = re.sub(r"[ \t\r\f\v ]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def _wre(alias):
    return re.compile(r"(?<![\w])" + re.escape(alias) + r"(?![\w])")


_SKILL_RE = {name: [_wre(a) for a in al] for name, al in SKILLS.items()}


def level_in(t):
    m = re.search(r"\b([abc][12])\b", t, re.I)
    if m:
        return m.group(1).upper()
    if re.search(r"bilingue|bilingual|natif|native|maternelle|mother tongue", t):
        return "C2"
    if re.search(r"courant|fluent|fluency|avancé|advanced|excellent|parfaite|maîtrise|maitrise|proficien|toeic 9", t):
        return "C1"
    if re.search(r"professionnel|professional|working|upper|bon niveau|good", t):
        return "B2"
    if re.search(r"intermédiaire|intermediate|conversation", t):
        return "B1"
    if re.search(r"notions|scolaire|basic|débutant|beginner", t):
        return "A2"
    return None


def languages(text, default="B2", include_french=False):
    t = text.lower()
    out = []
    for name, aliases in LANGS:
        if name == "Français" and not include_french:
            continue
        found, lvl = False, None
        for a in aliases:
            for m in _wre(a).finditer(t):
                found = True
                after = t[m.end(): m.end() + 60]
                before = t[max(0, m.start() - 40): m.start()]
                sep = r"[·|\n;•,.]|\bet\b|\band\b|\bou\b|\bor\b"
                lv = level_in(re.split(sep, after)[0]) or level_in(re.split(sep, before)[-1])
                if lv:
                    lvl = lv
                    break
            if lvl:
                break
        if found:
            out.append({"l": name, "n": lvl or default})
    return out


def skills(text):
    t = text.lower()
    out = [name for name, res in _SKILL_RE.items() if any(r.search(t) for r in res)]
    if "Salesforce" in out and "CRM" not in out:
        out.append("CRM")
    return out


def diploma(text):
    t = text.lower()
    if re.search(r"bac\s*\+\s*5|master|msc|mba|grande[s]? école|grande[s]? ecole|école d'ingénieur|ecole d'ingenieur|école de commerce|business school|engineering degree|diplôme d'ingénieur", t):
        return 5
    if re.search(r"bac\s*\+\s*4|maîtrise|\bm1\b", t):
        return 4
    if re.search(r"bac\s*\+\s*3|licence|bachelor|\bbut\b", t):
        return 3
    if re.search(r"bac\s*\+\s*2|\bbts\b|\bdut\b", t):
        return 2
    return None


def experience(text):
    t = text.lower()
    best = None
    for m in re.finditer(r"(\d{1,2})\s*(?:à|-|to)?\s*(?:\d{1,2})?\s*(?:ans|années|annees|an|years?|yrs?)\s*(?:minimum\s*)?(?:d['’]\s*)?(?:expérience|experience|of experience|d'exp)", t):
        n = int(m.group(1))
        if n < 15:
            best = n if best is None else min(best, n)
    if best is None and re.search(r"première expérience|premiere experience|first experience|1ère expérience", t):
        best = 0
    return best


def duration_months(text):
    t = text.lower()
    m = re.search(r"\b(6|9|1[0-9]|2[0-4])\s*(?:mois|months?)\b", t)
    return int(m.group(1)) if m else None


DOM_RULES = [
    ("sc", r"supply|logisti|achat|acheteu|buyer|procurement|purchas|approvision|planning|planif|demand planner|transport|douane|customs"),
    ("fin", r"financ|contr[ôo]l(e|eur|euse) de gestion|controller|controlling|fp&a|audit|comptab|accountant|accounting|tr[ée]sor|treasury|kyc|compliance|conformit|\brisk|risque|cr[ée]dit|\btax\b|fiscal|middle office|back office|investment|asset|portfolio|reporting officer|p&l|actuari|banque|banking"),
    ("rh", r"\brh\b|\bhr\b|human resources|ressources humaines|talent|recrut|recruit|people"),
    ("it", r"\bit\b|data|d[ée]veloppeu|developer|software|logiciel|devops|cyber|cloud|informatique|syst[eè]mes? d'information|digital|\bweb\b|full[- ]?stack|back[- ]?end|front[- ]?end|\bsap\b|\bai\b|\bia\b|machine learning"),
    ("mkt", r"marketing|communication|brand|marque|chef de produit|product manager|trade|e-?commerce|retail|merchandis|category|cat[ée]gorie|\bpr\b|relations presse|event"),
    ("biz", r"business dev|commercial|\bsales\b|vente|account manager|key account|charg[ée]e? d'affaires|export|\bbid\b|business developer|customer|client"),
    ("cons", r"consult|conseil|advisory"),
    ("ing", r"ing[ée]nieu|engineer|engineering|production|qualit|quality|m[ée]thodes|process|\bhse\b|maintenance|industriali|technique|technical|r&d|m[ée]canique|mechanical|[ée]lectri|chantier|construction|site manager|projet|project"),
]


def domain(title, text=""):
    for src in (title or "", (text or "")[:400]):
        t = src.lower()
        for key, pat in DOM_RULES:
            if re.search(pat, t):
                return key
    return "autre"


_VIE_STRICT = re.compile(r"(?<![A-Za-z])V\.?\s?I\.?\s?E\.?(?![A-Za-z])")
_NOT_VIE = re.compile(r"^\s*(alternance|stage|stagiaire|apprenti|apprentissage|cdi|cdd|internship|intern)\b", re.I)


def is_vie(title):
    """Titre d'offre VIE : « VIE » en capitales (pas le mot « vie ») ou « volontariat international »."""
    if not title or _NOT_VIE.search(title):
        return False
    return bool(_VIE_STRICT.search(title) or re.search(r"volontariat international", title, re.I))


def clean_title(title):
    t = re.sub(r"\s+", " ", title or "").strip()
    return t


def requirements(title, text):
    full = f"{title}\n{text}"
    return {
        "langues": languages(full),
        "comps": skills(full),
        "niv": diploma(full),
        "exp": experience(full),
        "dom": domain(title, text),
    }
