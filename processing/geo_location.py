import ipaddress
import json
import logging
import os
import requests
"""
Correspondance ip -> pays avec l'API ipinfo.io (fonction get_location du prof)
in: liste d'adresses ip
out: dictionnaire {ip: pays}  (code pays 'FR', 'Privée' ou 'Inconnu')
Les pays déjà trouvés sont gardés dans cache/geo_cache.json :
aux lancements suivants, l'API n'est plus appelée pour ces ip.
"""

logger = logging.getLogger(__name__)

URL_IPINFO = 'http://ipinfo.io'
TIMEOUT = 5                     # secondes d'attente max pour une réponse de l'API
CACHE_DIR = 'cache'
CACHE_FILE = CACHE_DIR + '/geo_cache.json'
MAX_ERREURS_RESEAU = 10         # erreurs d'affilée (réseau, limite 429...) avant d'arrêter d'appeler l'API


# fonction du prof (seul ajout : timeout=TIMEOUT)
def get_location(ip):
    response= requests.get(URL_IPINFO + "/" + ip+'/json', timeout=TIMEOUT)
    if response.status_code == 200:
        return response.json()


def load_cache():
    """
    in: rien (lit CACHE_FILE)
    out: dictionnaire {ip: pays} ({} si le cache est absent ou corrompu)
    """
    try:
        with open(CACHE_FILE, encoding='utf-8') as f:
            cache = json.load(f)
    except FileNotFoundError:
        logger.info(f'{CACHE_FILE} absent : le cache sera créé')
        return {}
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f'{CACHE_FILE} corrompu ({e}) : le cache sera recréé')
        return {}
    except OSError as e:
        logger.error(f'{CACHE_FILE} illisible ({e}) : le cache sera recréé')
        return {}

    if not isinstance(cache, dict):
        logger.error(f'{CACHE_FILE} corrompu (ce n\'est pas un dictionnaire) : le cache sera recréé')
        return {}
    # on ne garde que les entrées correctes "ip": "pays"
    cache_ok = {}
    for ip in cache:
        if isinstance(cache[ip], str):
            cache_ok[ip] = cache[ip]
        else:
            logger.warning(f'{CACHE_FILE} : entrée invalide pour {ip}, supprimée')
    logger.info(f'{CACHE_FILE} : {len(cache_ok)} pays déjà connus')
    return cache_ok


def save_cache(cache):
    """
    in: dictionnaire {ip: pays}
    out: rien (écrit CACHE_FILE)
    """
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, sort_keys=True, ensure_ascii=False)
        logger.info(f'{CACHE_FILE} : {len(cache)} pays enregistrés')
    except OSError as e:
        # PermissionError, "cache" est un fichier, disque plein...
        logger.error(f'impossible d\'écrire {CACHE_FILE} ({e}) : l\'API sera rappelée au prochain lancement')


def get_country(ip, cache):
    """
    in: une adresse ip + le cache {ip: pays}
    out: code pays ('FR'), 'Privée', 'Inconnu',
         ou None si erreur réseau (non mise en cache pour réessayer la prochaine fois)
    """
    if ip in cache:
        return cache[ip]

    try:
        adresse = ipaddress.ip_address(ip)
    except ValueError:
        logger.warning(f'{ip} : adresse ip invalide, pays "Inconnu"')
        return 'Inconnu'
    # ip privée (10.x, 192.168.x, 127.0.0.1...) : pas de pays, inutile d'appeler l'API
    if adresse.is_private:
        cache[ip] = 'Privée'
        return 'Privée'

    try:
        location = get_location(ip)
    except requests.Timeout:
        logger.error(f'{ip} : ipinfo.io ne répond pas (timeout de {TIMEOUT} s)')
        return None
    except requests.ConnectionError:
        logger.error(f'{ip} : connexion à ipinfo.io impossible (pas d\'internet ?)')
        return None
    except ValueError:
        # avant RequestException : l'erreur JSON de requests hérite des deux
        logger.error(f'{ip} : réponse de ipinfo.io illisible (JSON invalide)')
        return None
    except requests.RequestException as e:
        logger.error(f'{ip} : erreur de requête vers ipinfo.io ({e})')
        return None

    if not isinstance(location, dict):
        # get_location renvoie None si le code HTTP n'est pas 200 (ex : 429 = trop de requêtes)
        logger.warning(f'{ip} : ipinfo.io n\'a pas renvoyé de réponse valide (code HTTP différent de 200, ex : 429 = limite de requêtes atteinte)')
        return None
    pays = location.get('country')
    if not pays:
        logger.warning(f'{ip} : pas de pays dans la réponse de ipinfo.io, pays "Inconnu"')
        pays = 'Inconnu'
    cache[ip] = pays
    return pays


def get_countries(ips):
    """
    in: liste d'adresses ip
    out: dictionnaire {ip: pays}
    """
    cache = load_cache()
    countries = {}
    nb_api = 0
    erreurs_suivies = 0
    api_disponible = True
    try:
        for ip in sorted(ips):
            if ip in cache:
                countries[ip] = cache[ip]
                continue
            if not api_disponible:
                countries[ip] = 'Inconnu'
                continue

            pays = get_country(ip, cache)
            if pays is None:
                erreurs_suivies += 1
                pays = 'Inconnu'
                if erreurs_suivies >= MAX_ERREURS_RESEAU:
                    logger.critical(f'{MAX_ERREURS_RESEAU} erreurs d\'affilée avec ipinfo.io (réseau ou limite de requêtes) : arrêt des appels, '
                                    f'les ip restantes seront "Inconnu"')
                    api_disponible = False
            else:
                erreurs_suivies = 0
                if pays != 'Privée' and pays != 'Inconnu':
                    nb_api += 1
                    if nb_api % 100 == 0:
                        logger.info(f'{nb_api} nouvelles ip localisées par ipinfo.io...')
            countries[ip] = pays
    finally:
        # on sauvegarde même si le programme est interrompu (Ctrl+C) : rien n'est perdu
        save_cache(cache)

    nb_inconnu = 0
    for ip in countries:
        if countries[ip] == 'Inconnu':
            nb_inconnu += 1
    logger.info(f'{len(countries)} ip : {nb_api} nouvelles localisées par ipinfo.io, {nb_inconnu} pays inconnus')
    if nb_inconnu:
        logger.warning(f'{nb_inconnu} ip sans pays (classées "Inconnu")')
    return countries


if __name__ == "__main__":
    from log_config import setup_logging
    setup_logging()
    print(get_location('176.32.193.16'))
    print(get_countries(['8.8.8.8', '10.10.33.81', '192.0.2.10', 'abc']))
