import logging
"""
Calcul des données des 3 dashboards
in: list d'événements (extract_transforme) + dictionnaire {ip: pays} (geo_location)
out: dictionnaires de comptage et listes triées
"""

logger = logging.getLogger(__name__)


def get_field(event, field, num):
    """
    in: un événement, le nom du champ, son numéro
    out: la valeur du champ, ou None si le champ manque (+ WARNING)
    """
    try:
        return event[field]
    except KeyError:
        logger.warning(f'événement {num} : champ "{field}" manquant, événement ignoré')
    except TypeError:
        logger.warning(f'événement {num} : ce n\'est pas un dictionnaire, événement ignoré')
    return None


def failed_by_country(events, countries):
    """
    in: list d'événements + dictionnaire {ip: pays}
    out: dictionnaire {pays: nombre de tentatives échouées}
    """
    if not events:
        logger.warning('aucun événement : pas d\'échecs par pays à calculer')
        return {}

    resultat = {}
    nb_inconnu = 0
    for num, event in enumerate(events, start=1):
        if get_field(event, 'status', num) != 'failed':
            continue
        ip = get_field(event, 'ip', num)
        nb = get_field(event, 'nb', num)
        if ip is None or nb is None:
            continue
        pays = countries.get(ip)
        if pays is None:
            logger.warning(f'événement {num} : pas de pays pour l\'ip {ip}, compté dans "Inconnu"')
            pays = 'Inconnu'
        if pays == 'Inconnu':
            nb_inconnu += nb
        resultat[pays] = resultat.get(pays, 0) + nb

    if nb_inconnu:
        logger.warning(f'{nb_inconnu} échecs avec un pays inconnu (relancer pour compléter le cache ipinfo.io)')
    logger.info(f'échecs par pays : {sum(resultat.values())} échecs dans {len(resultat)} pays')
    return resultat


def success_by_user(events):
    """
    in: list d'événements
    out: dictionnaire {utilisateur: nombre de connexions réussies}
    """
    if not events:
        logger.warning('aucun événement : pas de réussites par utilisateur à calculer')
        return {}

    resultat = {}
    for num, event in enumerate(events, start=1):
        if get_field(event, 'status', num) != 'success':
            continue
        user = get_field(event, 'user', num)
        nb = get_field(event, 'nb', num)
        if nb is None:
            continue
        if not user:
            logger.warning(f'événement {num} : utilisateur manquant, compté dans "(inconnu)"')
            user = '(inconnu)'
        resultat[user] = resultat.get(user, 0) + nb

    if not resultat:
        logger.warning('aucune connexion réussie trouvée')
    logger.info(f'réussites par utilisateur : {sum(resultat.values())} réussites pour {len(resultat)} utilisateur(s)')
    return resultat


def invalid_user_attempts(events):
    """
    in: list d'événements
    out: dictionnaire {nom d'utilisateur essayé: nombre d'échecs "invalid user"}
    """
    if not events:
        logger.warning('aucun événement : pas de tentatives "invalid user" à calculer')
        return {}

    resultat = {}
    for num, event in enumerate(events, start=1):
        if get_field(event, 'status', num) != 'failed':
            continue
        if not get_field(event, 'invalid_user', num):
            continue
        user = get_field(event, 'user', num)
        nb = get_field(event, 'nb', num)
        if nb is None:
            continue
        if not user:
            logger.warning(f'événement {num} : utilisateur manquant, compté dans "(inconnu)"')
            user = '(inconnu)'
        resultat[user] = resultat.get(user, 0) + nb

    logger.info(f'"invalid user" : {sum(resultat.values())} tentatives avec {len(resultat)} noms différents')
    return resultat


def sort_desc(compteur, top=None):
    """
    in: dictionnaire {clé: nombre} + nombre de lignes à garder (None = toutes)
    out: list de tuples (clé, nombre) du plus grand au plus petit
         (à égalité : ordre alphabétique)
    """
    # on trie des tuples (-nombre, clé) : le plus grand nombre passe en premier
    liste = []
    for cle in compteur:
        liste.append((-compteur[cle], cle))
    liste = sorted(liste)
    resultat = []
    for moins_nb, cle in liste:
        resultat.append((cle, -moins_nb))
    if top is not None:
        return resultat[:top]
    return resultat


if __name__ == "__main__":
    import sys
    from log_config import setup_logging
    from ingestion import raw
    from processing import extract_transforme, geo_location
    setup_logging()
    # python -m processing.statistiques tests/sample
    events = extract_transforme.extract_from_rows(raw.to_rows(sys.argv[1] if len(sys.argv) > 1 else './data'))
    countries = geo_location.get_countries(set(event['ip'] for event in events))
    print('1. échecs par pays            :', sort_desc(failed_by_country(events, countries)))
    print('2. réussites par utilisateur   :', sort_desc(success_by_user(events)))
    invalid = invalid_user_attempts(events)
    print('3. invalid user (total)        :', sum(invalid.values()))
    print('   invalid user (top 10)       :', sort_desc(invalid, 10))
