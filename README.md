# Partance

Mon site perso pour trouver un VIE. Un robot passe toutes les 15 minutes environ : il récupère les offres VIE du catalogue Business France et des sites carrière de plusieurs entreprises, met le site à jour et m'envoie un email dès qu'une nouvelle offre me correspond.

- **Le site** : `docs/index.html`, publié par GitHub Pages. Chaque offre reçoit un score sur 100 calculé à partir de mon CV. Mon profil et mes candidatures restent dans mon navigateur.
- **Le robot** : `collector/`, lancé par GitHub Actions (`.github/workflows/collecte.yml`).
- **Les offres** : `docs/data/offers.json`, réécrit à chaque passage.

## Mise en route (une seule fois)

### 1. Publier le site

Dans le dépôt : **Settings → Pages**. Sous « Build and deployment », choisis **Deploy from a branch**, la branche **main** et le dossier **/docs**, puis **Save**.

Le site sera à l'adresse `https://<ton-nom-github>.github.io/partance/` au bout d'une minute ou deux.

### 2. Lancer le robot une première fois

Onglet **Actions** du dépôt. Si GitHub le demande, clique sur le bouton qui active les workflows. Ouvre ensuite **Collecte des offres**, clique sur **Run workflow**, puis à nouveau sur **Run workflow**.

Ce premier passage enregistre toutes les offres déjà en ligne, sans envoyer d'email. Les emails partent ensuite pour les offres publiées après lui. Il prend quelques minutes. Les passages suivants se lancent tout seuls toutes les 15 minutes.

### 3. Activer les emails (Gmail)

1. Active la **validation en deux étapes** sur ton compte Google, si ce n'est pas déjà fait.
2. Va sur <https://myaccount.google.com/apppasswords>, crée un mot de passe d'application nommé « Partance » et copie les 16 caractères.
3. Dans le dépôt : **Settings → Secrets and variables → Actions → New repository secret**. Crée ces deux secrets :
   - `SMTP_USER` : ton adresse Gmail
   - `SMTP_PASS` : le mot de passe d'application

   Tu peux aussi créer `EMAIL_TO` si tu veux recevoir les alertes sur une autre adresse.

Ces secrets restent invisibles, même si le dépôt est public.

### 4. Donner ton profil au robot

Sur le site, ouvre **Mon profil**, dépose ton CV, puis clique sur **Analyser le CV** et corrige ce qui est faux. Va ensuite dans **Alertes & sources**, règle le score minimum et clique sur **Copier le profil**. Colle-le dans un nouveau secret nommé `PROFILE_JSON`.

Sans ce secret, le robot t'envoie toutes les nouvelles offres. Avec lui, il n'envoie que celles qui dépassent ton score minimum, et seulement dans tes pays visés si tu en as choisi. Refais la copie quand tu changes ton profil.

### 5. Choisir les pays des alertes

Le fichier `alertes.json`, à la racine du dépôt, liste les pays pour lesquels tu reçois un email, en codes à deux lettres (`US`, `CA`, `ES`, `GB`, `AU`, `SG`…). Modifie-le directement sur GitHub (icône crayon). Une liste vide `[]` envoie les alertes pour tous les pays. Le site, lui, continue d'afficher les offres de tous les pays.

### 6. Passages vraiment toutes les 15 minutes (facultatif)

GitHub ne respecte pas toujours l'horaire « toutes les 15 minutes » : sur un compte gratuit, il lance souvent le robot toutes les 3 à 4 heures seulement. Pour un rythme fiable, un service gratuit comme cron-job.org peut déclencher le robot lui-même :

1. Crée un jeton sur <https://github.com/settings/personal-access-tokens/new> : nom « Partance cron », « Only select repositories » → `partance`, puis dans « Permissions », **Actions : Read and write**. Copie le jeton.
2. Crée un compte sur <https://cron-job.org>, puis **Create cronjob** :
   - URL : `https://api.github.com/repos/ilona2110/partance/actions/workflows/collecte.yml/dispatches`
   - Exécution : toutes les 15 minutes
   - Onglet « Advanced » : méthode **POST**, corps `{"ref":"main"}`, et trois en-têtes :
     `Authorization: Bearer <ton jeton>`, `Accept: application/vnd.github+json`, `Content-Type: application/json`

L'horaire GitHub reste actif en secours. Le jeton ne donne accès qu'au lancement du robot de ce dépôt.

## Sources suivies

| Source | Comment elle est lue |
|---|---|
| Business France | Le service qui alimente le catalogue officiel, avec la clé publique que le site envoie à chaque visiteur |
| Airbus, Thales, Air Liquide, Michelin | Workday, avec le filtre « type de contrat VIE » quand il existe, sinon une recherche « VIE » dans les titres |
| TotalEnergies | Pages de résultats de son site carrière (Avature) |
| CACEIS, Amundi | Flux RSS de leur site carrière |

L'état de chaque source s'affiche sur le site, dans **Alertes & sources**. Une source en panne n'empêche pas les autres de tourner. Ses offres déjà connues restent affichées pendant 3 jours, puis disparaissent.

Ne sont pas branchés : Safran, L'Oréal et BNP Paribas, dont le site bloque les robots, ainsi que LVMH, Hermès, Chanel, Société Générale, Naval Group et Schneider Electric, dont le site ne s'affiche qu'avec un navigateur. Leurs VIE passent en général aussi par Business France.

Le robot respecte le fichier robots.txt de chaque site et espace ses requêtes. Une entreprise qui interdit les robots, comme le Crédit Agricole, n'est pas lue.

## Bon à savoir

- GitHub peut lancer un passage avec 5 à 20 minutes de retard quand ses serveurs sont chargés.
- Si GitHub t'envoie un email disant que le workflow planifié a été désactivé, réactive-le en un clic depuis l'onglet Actions.
- Le score est calculé à partir des exigences repérées automatiquement dans chaque annonce. Vérifie toujours l'offre complète avant de postuler.
- Tes candidatures sont enregistrées dans le navigateur où tu les as saisies : elles ne passent pas d'un appareil à l'autre.

## Tester le robot sans réseau

```
pip install -r collector/requirements.txt
python collector/test_collector.py
```
