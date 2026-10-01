"""Sources suivies. Pour ajouter une entreprise sur Workday, copie une ligne et change l'hôte, le tenant et le site."""

SOURCES = [
    {"key": "bf", "type": "businessfrance", "name": "Business France", "secteur": "Catalogue officiel"},
    {"key": "airbus", "type": "workday", "name": "Airbus", "host": "ag.wd3.myworkdayjobs.com", "tenant": "ag", "site": "Airbus", "secteur": "Aéro & défense"},
    {"key": "thales", "type": "workday", "name": "Thales", "host": "thales.wd3.myworkdayjobs.com", "tenant": "thales", "site": "Careers", "secteur": "Aéro & défense"},
    {"key": "safran", "type": "safran", "name": "Safran", "secteur": "Aéro & défense"},
    {"key": "caceis", "type": "talentsoft_rss", "name": "CACEIS", "url": "https://jobs.caceis.com/handlers/offerRss.ashx?LCID=1036", "secteur": "Banque & finance"},
    {"key": "amundi", "type": "talentsoft_rss", "name": "Amundi", "url": "https://jobs.amundi.com/handlers/offerRss.ashx?LCID=1036", "secteur": "Banque & finance"},
    {"key": "total", "type": "avature", "name": "TotalEnergies", "base": "https://jobs.totalenergies.com/fr_FR/careers", "secteur": "Industrie & énergie"},
    {"key": "airliquide", "type": "workday", "name": "Air Liquide", "host": "airliquidehr.wd3.myworkdayjobs.com", "tenant": "airliquidehr", "site": "AirLiquideExternalCareer", "secteur": "Industrie & énergie"},
    {"key": "michelin", "type": "workday", "name": "Michelin", "host": "michelinhr.wd3.myworkdayjobs.com", "tenant": "michelinhr", "site": "Michelin", "secteur": "Industrie & énergie"},
]

# Entreprises demandées mais pas branchées : leur site ne s'affiche qu'avec un navigateur, ou une
# protection anti-robots bloque l'accès (L'Oréal, BNP Paribas). Leurs VIE passent en général aussi
# par le catalogue Business France.
NOT_YET = ["L'Oréal", "BNP Paribas", "LVMH", "Hermès", "Chanel", "Société Générale", "Naval Group", "Schneider Electric"]
