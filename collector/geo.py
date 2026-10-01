"""Reconnaissance du pays d'une offre à partir du lieu, du titre ou de la description."""
import re
import unicodedata

# code ISO -> (nom français, alias en minuscules)
COUNTRIES = {
    "US": ("États-Unis", ["united states", "usa", "etats-unis", "états-unis", "etats unis", "u.s.a"]),
    "CA": ("Canada", ["canada"]),
    "MX": ("Mexique", ["mexique", "mexico", "méxico"]),
    "BR": ("Brésil", ["brésil", "bresil", "brazil", "brasil"]),
    "AR": ("Argentine", ["argentine", "argentina"]),
    "CL": ("Chili", ["chili", "chile"]),
    "CO": ("Colombie", ["colombie", "colombia"]),
    "PE": ("Pérou", ["pérou", "perou", "peru"]),
    "GB": ("Royaume-Uni", ["royaume-uni", "royaume uni", "united kingdom", "uk", "angleterre", "england", "scotland", "écosse"]),
    "IE": ("Irlande", ["irlande", "ireland"]),
    "DE": ("Allemagne", ["allemagne", "germany", "deutschland"]),
    "ES": ("Espagne", ["espagne", "spain", "españa", "espana"]),
    "IT": ("Italie", ["italie", "italy", "italia"]),
    "PT": ("Portugal", ["portugal"]),
    "BE": ("Belgique", ["belgique", "belgium", "belgië", "belgie"]),
    "NL": ("Pays-Bas", ["pays-bas", "pays bas", "netherlands", "nederland", "holland"]),
    "LU": ("Luxembourg", ["luxembourg"]),
    "CH": ("Suisse", ["suisse", "switzerland", "schweiz"]),
    "AT": ("Autriche", ["autriche", "austria", "österreich"]),
    "DK": ("Danemark", ["danemark", "denmark"]),
    "SE": ("Suède", ["suède", "suede", "sweden"]),
    "NO": ("Norvège", ["norvège", "norvege", "norway"]),
    "FI": ("Finlande", ["finlande", "finland"]),
    "PL": ("Pologne", ["pologne", "poland", "polska"]),
    "CZ": ("Tchéquie", ["tchéquie", "tchequie", "république tchèque", "czech republic", "czechia"]),
    "SK": ("Slovaquie", ["slovaquie", "slovakia"]),
    "HU": ("Hongrie", ["hongrie", "hungary"]),
    "RO": ("Roumanie", ["roumanie", "romania"]),
    "BG": ("Bulgarie", ["bulgarie", "bulgaria"]),
    "GR": ("Grèce", ["grèce", "grece", "greece"]),
    "HR": ("Croatie", ["croatie", "croatia"]),
    "RS": ("Serbie", ["serbie", "serbia"]),
    "TR": ("Turquie", ["turquie", "turkey", "türkiye", "turkiye"]),
    "MT": ("Malte", ["malte", "malta"]),
    "CY": ("Chypre", ["chypre", "cyprus"]),
    "EE": ("Estonie", ["estonie", "estonia"]),
    "LV": ("Lettonie", ["lettonie", "latvia"]),
    "LT": ("Lituanie", ["lituanie", "lithuania"]),
    "UA": ("Ukraine", ["ukraine"]),
    "MA": ("Maroc", ["maroc", "morocco"]),
    "TN": ("Tunisie", ["tunisie", "tunisia"]),
    "DZ": ("Algérie", ["algérie", "algerie", "algeria"]),
    "EG": ("Égypte", ["égypte", "egypte", "egypt"]),
    "SN": ("Sénégal", ["sénégal", "senegal"]),
    "CI": ("Côte d'Ivoire", ["côte d'ivoire", "cote d'ivoire", "côte d’ivoire", "ivory coast"]),
    "CM": ("Cameroun", ["cameroun", "cameroon"]),
    "GA": ("Gabon", ["gabon"]),
    "CD": ("RD Congo", ["république démocratique du congo", "democratic republic of the congo", "rdc", "rd congo"]),
    "CG": ("Congo", ["république du congo", "republic of the congo", "congo"]),
    "AO": ("Angola", ["angola"]),
    "NG": ("Nigeria", ["nigeria", "nigéria"]),
    "GH": ("Ghana", ["ghana"]),
    "KE": ("Kenya", ["kenya"]),
    "TZ": ("Tanzanie", ["tanzanie", "tanzania"]),
    "ET": ("Éthiopie", ["éthiopie", "ethiopie", "ethiopia"]),
    "MZ": ("Mozambique", ["mozambique"]),
    "MG": ("Madagascar", ["madagascar"]),
    "MU": ("Maurice", ["île maurice", "ile maurice", "mauritius", "maurice"]),
    "GN": ("Guinée", ["guinée", "guinee", "guinea"]),
    "KM": ("Comores", ["comores", "comoros"]),
    "ZA": ("Afrique du Sud", ["afrique du sud", "south africa"]),
    "AE": ("Émirats arabes unis", ["émirats arabes unis", "emirats arabes unis", "united arab emirates", "uae", "émirats", "emirates"]),
    "SA": ("Arabie saoudite", ["arabie saoudite", "saudi arabia", "ksa"]),
    "QA": ("Qatar", ["qatar"]),
    "KW": ("Koweït", ["koweït", "koweit", "kuwait"]),
    "OM": ("Oman", ["oman"]),
    "BH": ("Bahreïn", ["bahreïn", "bahrein", "bahrain"]),
    "JO": ("Jordanie", ["jordanie", "jordan"]),
    "LB": ("Liban", ["liban", "lebanon"]),
    "IL": ("Israël", ["israël", "israel"]),
    "IN": ("Inde", ["inde", "india"]),
    "CN": ("Chine", ["chine", "china"]),
    "HK": ("Hong Kong", ["hong kong", "hong-kong"]),
    "TW": ("Taïwan", ["taïwan", "taiwan"]),
    "JP": ("Japon", ["japon", "japan"]),
    "KR": ("Corée du Sud", ["corée du sud", "coree du sud", "south korea", "korea", "corée"]),
    "SG": ("Singapour", ["singapour", "singapore"]),
    "MY": ("Malaisie", ["malaisie", "malaysia"]),
    "TH": ("Thaïlande", ["thaïlande", "thailande", "thailand"]),
    "VN": ("Viêt Nam", ["viêt nam", "viet nam", "vietnam", "viêtnam"]),
    "ID": ("Indonésie", ["indonésie", "indonesie", "indonesia"]),
    "PH": ("Philippines", ["philippines"]),
    "BD": ("Bangladesh", ["bangladesh"]),
    "PK": ("Pakistan", ["pakistan"]),
    "LK": ("Sri Lanka", ["sri lanka"]),
    "UZ": ("Ouzbékistan", ["ouzbékistan", "ouzbekistan", "uzbekistan"]),
    "KZ": ("Kazakhstan", ["kazakhstan"]),
    "AU": ("Australie", ["australie", "australia"]),
    "NZ": ("Nouvelle-Zélande", ["nouvelle-zélande", "nouvelle zélande", "new zealand"]),
    "MN": ("Mongolie", ["mongolie", "mongolia"]),
    "GY": ("Guyana", ["guyana"]),
    "DO": ("République dominicaine", ["république dominicaine", "republique dominicaine", "dominican republic"]),
    "UG": ("Ouganda", ["ouganda", "uganda"]),
    "RW": ("Rwanda", ["rwanda"]),
    "BJ": ("Bénin", ["bénin", "benin"]),
    "TG": ("Togo", ["togo"]),
    "BF": ("Burkina Faso", ["burkina faso", "burkina"]),
    "ML": ("Mali", ["mali"]),
    "NE": ("Niger", ["niger"]),
    "TD": ("Tchad", ["tchad", "chad"]),
    "MR": ("Mauritanie", ["mauritanie", "mauritania"]),
    "DJ": ("Djibouti", ["djibouti"]),
    "NA": ("Namibie", ["namibie", "namibia"]),
    "BW": ("Botswana", ["botswana"]),
    "ZM": ("Zambie", ["zambie", "zambia"]),
    "ZW": ("Zimbabwe", ["zimbabwe"]),
    "LY": ("Libye", ["libye", "libya"]),
    "IQ": ("Irak", ["irak", "iraq"]),
    "AZ": ("Azerbaïdjan", ["azerbaïdjan", "azerbaidjan", "azerbaijan"]),
    "GE": ("Géorgie", ["géorgie", "georgie"]),
    "AM": ("Arménie", ["arménie", "armenie", "armenia"]),
    "MD": ("Moldavie", ["moldavie", "moldova"]),
    "SI": ("Slovénie", ["slovénie", "slovenie", "slovenia"]),
    "BA": ("Bosnie-Herzégovine", ["bosnie", "bosnia"]),
    "MK": ("Macédoine du Nord", ["macédoine", "macedoine", "macedonia"]),
    "AL": ("Albanie", ["albanie", "albania"]),
    "ME": ("Monténégro", ["monténégro", "montenegro"]),
    "IS": ("Islande", ["islande", "iceland"]),
    "NP": ("Népal", ["népal", "nepal"]),
    "KH": ("Cambodge", ["cambodge", "cambodia"]),
    "LA": ("Laos", ["laos"]),
    "MM": ("Myanmar", ["myanmar", "birmanie"]),
    "PA": ("Panama", ["panama"]),
    "CR": ("Costa Rica", ["costa rica"]),
    "EC": ("Équateur", ["équateur", "equateur", "ecuador"]),
    "UY": ("Uruguay", ["uruguay"]),
    "PY": ("Paraguay", ["paraguay"]),
    "BO": ("Bolivie", ["bolivie", "bolivia"]),
    "GT": ("Guatemala", ["guatemala"]),
    "FR": ("France", ["france"]),
}

CITIES = {
    "US": ["californie", "california", "texas", "floride", "florida", "caroline du nord", "caroline du sud", "géorgie (usa)", "new york", "boston", "chicago", "houston", "dallas", "san francisco", "los angeles", "miami", "atlanta", "seattle", "washington", "detroit", "san diego", "philadelphie", "philadelphia", "denver", "wichita", "andover"],
    "CA": ["montréal", "montreal", "toronto", "vancouver", "québec", "quebec", "ottawa", "calgary", "mirabel", "saint-bruno"],
    "GB": ["londres", "london", "manchester", "bristol", "edinburgh", "birmingham", "filton", "broughton", "fareham"],
    "IE": ["dublin", "cork"],
    "DE": ["munich", "münchen", "hambourg", "hamburg", "berlin", "francfort", "frankfurt", "düsseldorf", "dusseldorf", "köln", "stuttgart", "brême", "bremen"],
    "ES": ["madrid", "barcelone", "barcelona", "séville", "sevilla", "seville", "getafe"],
    "IT": ["milan", "milano", "rome", "roma", "turin", "torino"],
    "PT": ["lisbonne", "lisbon", "lisboa", "porto"],
    "BE": ["bruxelles", "brussels", "anvers", "antwerp", "zeebrugge", "liège"],
    "NL": ["amsterdam", "rotterdam", "la haye", "the hague", "eindhoven"],
    "CH": ["genève", "geneve", "geneva", "zurich", "zürich", "bâle", "bale", "basel", "lausanne"],
    "AT": ["vienne", "vienna", "wien"],
    "PL": ["varsovie", "warsaw", "warszawa", "cracovie", "krakow", "kraków", "wroclaw", "wrocław"],
    "CZ": ["prague", "praha"],
    "RO": ["bucarest", "bucharest", "bucuresti", "timisoara", "cluj"],
    "HU": ["budapest"],
    "TR": ["istanbul", "ankara"],
    "MA": ["casablanca", "rabat", "tanger", "marrakech"],
    "TN": ["tunis"],
    "SN": ["dakar"],
    "CI": ["abidjan"],
    "CM": ["douala", "yaoundé"],
    "GA": ["libreville", "port-gentil"],
    "CG": ["pointe-noire", "brazzaville"],
    "AO": ["luanda"],
    "NG": ["lagos", "abuja"],
    "KE": ["nairobi"],
    "ZA": ["johannesburg", "le cap", "cape town"],
    "AE": ["dubaï", "dubai", "abu dhabi", "abou dabi"],
    "SA": ["riyad", "riyadh", "djeddah", "jeddah"],
    "QA": ["doha"],
    "IN": ["bangalore", "bengaluru", "mumbai", "bombay", "new delhi", "delhi", "chennai", "pune", "hyderabad", "gurgaon", "noida"],
    "CN": ["shanghai", "pékin", "pekin", "beijing", "shenzhen", "guangzhou", "tianjin", "suzhou"],
    "HK": ["kowloon"],
    "JP": ["tokyo", "osaka", "kyoto", "nagoya"],
    "KR": ["séoul", "seoul", "busan"],
    "TW": ["taipei"],
    "MY": ["kuala lumpur"],
    "TH": ["bangkok", "rayong"],
    "VN": ["hô chi minh", "ho chi minh", "hanoï", "hanoi"],
    "ID": ["jakarta"],
    "PH": ["manille", "manila"],
    "AU": ["sydney", "melbourne", "brisbane", "perth", "adelaide"],
    "NZ": ["auckland", "wellington"],
    "BR": ["são paulo", "sao paulo", "rio de janeiro", "curitiba", "belo horizonte"],
    "MX": ["monterrey", "querétaro", "queretaro", "guadalajara", "chihuahua", "san luis potosi"],
    "AR": ["buenos aires"],
    "CL": ["santiago"],
    "CO": ["bogota", "bogotá", "medellin", "medellín"],
    "PE": ["lima"],
}


def _norm(s):
    return (s or "").lower().replace("’", "'")


# Alias triés du plus long au plus court, pour que « république démocratique du congo » passe avant « congo »
_ALIASES = sorted(
    [(a, iso) for iso, (_, al) in COUNTRIES.items() for a in al]
    + [(c, iso) for iso, cs in CITIES.items() for c in cs],
    key=lambda x: -len(x[0]),
)
_RE = {a: re.compile(r"(?<![\w])" + re.escape(a) + r"(?![\w])") for a, _ in _ALIASES}


def find_country(*texts):
    """Renvoie (iso, nom) du premier pays étranger trouvé, sinon la France, sinon (None, None)."""
    fallback_fr = False
    for t in texts:
        t = _norm(t)
        if not t:
            continue
        hits = []
        taken = []
        for alias, iso in _ALIASES:
            for m in _RE[alias].finditer(t):
                span = (m.start(), m.end())
                if any(s < span[1] and span[0] < e for s, e in taken):
                    continue
                taken.append(span)
                hits.append((m.start(), iso))
        hits.sort()
        for _, iso in hits:
            if iso == "FR":
                fallback_fr = True
                continue
            return iso, COUNTRIES[iso][0]
    if fallback_fr:
        return "FR", "France"
    return None, None


def name_of(iso):
    return COUNTRIES.get(iso, (None,))[0]


def slug_to_text(slug):
    return (slug or "").replace("-", " ")


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
