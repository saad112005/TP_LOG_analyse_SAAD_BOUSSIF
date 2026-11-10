# Pipeline Log Analyzer

Projet de Python avancé (3e année) - Saad Boussif

## Le but du projet

On avait des fichiers de logs d'un serveur Linux (`auth.log`). Ils contiennent toutes les tentatives de connexion SSH au serveur, réussies ou ratées. Le but était de les analyser en Python et d'afficher 3 dashboards, d'abord dans la console, puis dans une figure avec matplotlib :

1. le nombre de tentatives échouées par pays ;
2. le nombre de connexions réussies par utilisateur ;
3. les tentatives avec un utilisateur qui n'existe pas (« invalid user ») : le total et le top 10 des noms essayés.

## Comment le projet est organisé

J'ai repris la structure du code de départ du prof : un dossier par étape du pipeline.

- `ingestion/raw.py` : lit tous les fichiers du dossier `data/`, même ceux compressés en `.gz`.
- `processing/extract_transforme.py` : avec des regex, je garde seulement les lignes SSH utiles (échecs et réussites) et je récupère la date, l'utilisateur et l'IP.
- `processing/geo_location.py` : trouve le pays de chaque IP avec la fonction `get_location` du prof (API ipinfo.io).
- `processing/statistiques.py` : fait les comptages pour les 3 dashboards.
- `serving/dashboard.py` : affiche les tableaux dans la console.
- `serving/dashboard_graphique.py` : dessine les mêmes résultats en graphiques avec matplotlib.
- `log_config.py` : configure le logging (console + fichier `logs/app.log`).
- `main.py` : lance toutes les étapes dans l'ordre.

## Installation

Il faut Python 3.13. J'utilise deux bibliothèques externes : `requests` (pour l'API ipinfo.io) et `matplotlib` (pour le dashboard graphique). Elles sont déjà dans `pyproject.toml`, donc une seule commande suffit :

```
uv sync
```

## Lancer le programme

Depuis le dossier `log_analysis` :

```
.venv\Scripts\python.exe main.py
```

Par défaut, il lit le dossier `data/`. On peut aussi lui donner un autre dossier, par exemple le fichier d'exemple :

```
.venv\Scripts\python.exe main.py tests/sample
```

Le programme affiche d'abord les tableaux dans la console, puis il ouvre une fenêtre avec les graphiques. L'image est aussi enregistrée dans `output/dashboard.png`. Attention : le programme ne se termine qu'une fois la fenêtre des graphiques fermée.

Les vrais logs (`data/`) ne sont pas sur GitHub, parce qu'ils contiennent de vraies adresses IP et que le dépôt est public. Pour tester, j'ai mis un petit fichier d'exemple de 50 lignes dans `tests/sample/sample.log`.

## Exemple de résultat

Voici ce que ça donne sur le fichier d'exemple :

```
1. Échecs par pays
==================
Pays   |  Nombre | Proportion
-------+---------+-----------------------------------------
CN     |       9 | ########################################
RU     |       5 | ######################
KR     |       4 | ##################
US     |       4 | ##################
FR     |       3 | #############
AU     |       2 | #########
BR     |       2 | #########
DE     |       2 | #########
Privée |       1 | ####
Total : 32 tentatives échouées

2. Réussites par utilisateur
============================
Utilisateur |  Nombre | Proportion
------------+---------+-----------------------------------------
adminesisa  |       3 | ########################################
saad        |       1 | #############
Total : 4 connexions réussies

3. Invalid user : total + top 10
================================
Utilisateur essayé |  Nombre | Proportion
-------------------+---------+-----------------------------------------
test               |       4 | ########################################
admin              |       3 | ##############################
esisa              |       1 | ##########
oracle             |       1 | ##########
support            |       1 | ##########
ubuntu             |       1 | ##########
Total : 11 tentatives "invalid user" avec 6 noms différents
```

## Le dashboard graphique

Le prof a aussi demandé une version graphique. J'ai fait une seule figure, « Analyse des logs SSH (auth.log) », avec 3 graphiques en barres horizontales :

1. les tentatives échouées par pays (top 15) ;
2. les connexions réussies par utilisateur ;
3. les tentatives avec « invalid user » (top 15).

Dans chaque graphique, la plus grande valeur est en haut et le nombre est écrit au bout de la barre. Je ne refais aucun calcul : j'utilise les mêmes résultats que pour les tableaux de la console (`sort_desc` de `processing/statistiques.py`).

Le dossier `output/` n'est pas sur GitHub, parce que l'image est recréée à chaque lancement.

## Comment je trouve le pays d'une IP

J'utilise la fonction `get_location` donnée par le prof, qui appelle le site ipinfo.io. Le problème, c'est que sans compte, ipinfo.io limite le nombre de requêtes (erreur 429). Avec les vrais logs, il y a plus de 1800 IP différentes, donc j'ai ajouté :

- un **cache** (`cache/geo_cache.json`) : chaque IP n'est demandée qu'une seule fois, même si on relance le programme ;
- les IP privées (`10.x`, `192.168.x`...) sont classées « Privée » directement, sans appel à l'API ;
- si l'API ne répond pas, l'IP est classée « Inconnu », et elle sera redemandée au prochain lancement ;
- après 10 erreurs de suite, le programme arrête d'appeler l'API mais continue l'analyse.

Si on a un token ipinfo.io, on peut le donner avec une variable d'environnement (il n'est jamais écrit dans le code) :

```powershell
$env:IPINFO_TOKEN = "votre_token"; .venv\Scripts\python.exe main.py
```

## Gestion des erreurs et logging

J'ai utilisé le module `logging` comme dans le cours : chaque module a son logger (`logging.getLogger(__name__)`), et les messages sont écrits dans la console et dans `logs/app.log`.

L'idée principale : **une ligne ou un fichier invalide ne doit pas faire planter le programme**. Il écrit un message et passe à la suite. Par exemple :

- fichier `.gz` corrompu, fichier vide, permission refusée → le fichier est ignoré (ERROR ou WARNING) ;
- ligne mal formée, mois inconnu, IP invalide → la ligne est ignorée (WARNING), avec son numéro ;
- pas de connexion internet ou limite ipinfo.io → les pays restent « Inconnu » (ERROR puis CRITICAL) ;
- dossier inexistant ou sans logs SSH → le programme s'arrête proprement (CRITICAL) ;
- graphique sans données → il affiche « Aucune donnée » au lieu de planter (WARNING) ;
- image impossible à enregistrer dans `output/` → message d'erreur, mais la fenêtre s'affiche quand même (ERROR) ;
- matplotlib pas installé → pas de graphiques, mais les tableaux de la console marchent toujours (ERROR).

## Tests

Chaque module peut se lancer tout seul pour le tester, par exemple :

```
.venv\Scripts\python.exe -m ingestion.raw tests/data_erreurs
.venv\Scripts\python.exe -m processing.extract_transforme tests/parser
.venv\Scripts\python.exe -m serving.dashboard_graphique
```

La dernière commande dessine une figure avec des données d'exemple, dont un graphique vide, pour vérifier que « Aucune donnée » s'affiche bien.

- `tests/data_erreurs/` : des fichiers cassés exprès (gz corrompu, fichier vide, mauvais encodage...) pour tester la lecture.
- `tests/parser/` : des lignes de log fausses (mauvais mois, IP invalide, ligne coupée...) pour tester les regex.
- `tests/sample/` : le fichier d'exemple pour les 3 dashboards.

## Ce que j'ai corrigé ou choisi

- La regex du code de départ ne marchait pas : il manquait une parenthèse fermante. Une fois corrigée, elle ne reconnaissait pas encore les lignes sans pid (comme `sudo:`) ni les services avec un tiret (`systemd-logind`), et elle ne gardait que le premier mot du message. J'ai corrigé ces trois points.
- Une ligne `message repeated 4 times: [ Failed password ...]` compte pour 4 échecs.
- Je compte seulement les lignes `Failed password` comme échecs, pour ne pas compter deux fois la même tentative (les lignes `pam_unix` décrivent la même chose).
- Les pays sont affichés avec leur code (`CN`, `US`, `FR`...), parce que c'est ce que renvoie ipinfo.io.
- Je n'ai utilisé que ce qu'on a vu en cours, la bibliothèque standard, `requests` et `matplotlib`. J'ai gardé deux affichages séparés : les tableaux avec `print`, et les graphiques avec matplotlib. Comme ça, si matplotlib pose problème, les résultats restent visibles dans la console.
- J'importe matplotlib à l'intérieur de la fonction du dashboard graphique, et pas en haut du fichier. Si matplotlib n'est pas installé, seul le graphique est ignoré, le reste du programme continue.

## Limites

- Les logs ne contiennent pas l'année, seulement le mois et le jour.
- Sans token ipinfo.io, il faut parfois relancer le programme plusieurs fois pour trouver le pays de toutes les IP.
- Le dossier `stoage/` du code de départ (stockage en base de données) n'est pas utilisé.
