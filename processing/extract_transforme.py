import ipaddress
import logging
import re
"""
in: list of rows
out: dateTime,ip,success,failed,Invalid user for sshd service
"""

logger = logging.getLogger(__name__)

# mois du log -> numéro (sert aussi à vérifier que le mois est valide)
MOIS = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

# 1. en-tête commun à toutes les lignes
#    May 24 00:28:00 ns sshd[1351222]: message...
#    May 19 08:50:49 ns sudo: message...            (pas de pid -> partie [pid] optionnelle)
pattern = re.compile(r'^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<server>\S+)\s+(?P<service>[\w-]+)(\[(?P<pid>\d+)\])?:\s+(?P<message>.*)')

# 2. échec de connexion sshd (avec ou sans "message repeated N times", avec ou sans "invalid user")
#    Failed password for root from 45.148.10.147 port 8868 ssh2
#    message repeated 4 times: [ Failed password for invalid user admin from 1.2.3.4 port 22 ssh2]
pattern_failed = re.compile(r'(message repeated (?P<repeat>\d+) times: \[\s*)?Failed password for (?P<invalid>invalid user )?(?P<user>\S*) from (?P<ip>\S+) port (?P<port>\d+)')

# 3. connexion réussie sshd
#    Accepted password for adminesisa from 10.10.33.81 port 59176 ssh2
pattern_success = re.compile(r'Accepted (?P<method>\w+) for (?P<user>\S+) from (?P<ip>\S+) port (?P<port>\d+)')


def check_ip(ip, num):
    """
    in: adresse ip (texte) + numéro de ligne
    out: True si l'ip est valide, sinon False (+ WARNING)
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        logger.warning(f'ligne {num} : adresse ip invalide "{ip}", ligne ignorée')
        return False


def parse_row(row, num):
    """
    in: une ligne du log + son numéro
    out: dictionnaire de l'événement (échec ou réussite sshd),
         'ignore' si la ligne ne concerne pas une connexion,
         None si la ligne est invalide (erreur loggée)
    """
    row = row.strip()
    if not row:
        logger.debug(f'ligne {num} : ligne vide')
        return 'ignore'

    match = re.search(pattern, row)
    if not match:
        logger.warning(f'ligne {num} : ligne mal formée -> "{row[:80]}"')
        return None

    # date : mois et jour doivent être valides
    try:
        mois = MOIS[match.group('month')]
    except KeyError:
        logger.warning(f'ligne {num} : mois inconnu "{match.group("month")}"')
        return None
    jour = int(match.group('day'))
    if jour < 1 or jour > 31:
        logger.warning(f'ligne {num} : jour invalide "{jour}"')
        return None

    # seules les lignes du service sshd nous intéressent (CRON, sudo... sont ignorées)
    if match.group('service') != 'sshd':
        return 'ignore'

    message = match.group('message')
    event = {
        'date': f'{match.group("month")} {jour}',
        'time': match.group('time'),
        'mois': mois,
        'jour': jour,
        'service': match.group('service'),
        'pid': match.group('pid'),
    }

    failed = re.search(pattern_failed, message)
    if failed:
        if not check_ip(failed.group('ip'), num):
            return None
        user = failed.group('user')
        if not user:
            logger.warning(f'ligne {num} : nom d\'utilisateur vide, remplacé par "(vide)"')
            user = '(vide)'
        event['status'] = 'failed'
        event['invalid_user'] = failed.group('invalid') is not None
        event['user'] = user
        event['ip'] = failed.group('ip')
        event['port'] = int(failed.group('port'))
        # "message repeated 4 times" = 4 échecs, sinon 1 seul
        event['nb'] = int(failed.group('repeat')) if failed.group('repeat') else 1
        return event

    success = re.search(pattern_success, message)
    if success:
        if not check_ip(success.group('ip'), num):
            return None
        event['status'] = 'success'
        event['invalid_user'] = False
        event['user'] = success.group('user')
        event['ip'] = success.group('ip')
        event['port'] = int(success.group('port'))
        event['nb'] = 1
        return event

    # le message parle d'un échec/succès mais la regex ne le reconnaît pas : format inattendu
    if 'Failed password' in message or message.startswith('Accepted '):
        logger.warning(f'ligne {num} : message de connexion non reconnu -> "{message[:80]}"')
        return None

    return 'ignore'


def extract_from_rows(rows):
    """
    in: list of rows
    out: list d'événements (dictionnaires) : échecs et réussites sshd
    """
    if not rows:
        logger.warning('aucune ligne à analyser')
        return []

    events = []
    nb_ignore = 0
    nb_errors = 0
    for num, row in enumerate(rows, start=1):
        result = parse_row(row, num)
        if result is None:
            nb_errors += 1
        elif result == 'ignore':
            nb_ignore += 1
        else:
            events.append(result)

    nb_failed = sum(event['nb'] for event in events if event['status'] == 'failed')
    nb_success = sum(event['nb'] for event in events if event['status'] == 'success')
    logger.info(f'{len(rows)} lignes analysées : {nb_failed} échecs, {nb_success} réussites, '
                f'{nb_ignore} lignes ignorées (autres messages), {nb_errors} lignes invalides')
    if nb_errors:
        logger.warning(f'{nb_errors} ligne(s) invalide(s) ignorée(s), voir les messages ci-dessus')
    return events


if __name__ == "__main__":
    import sys
    from log_config import setup_logging
    from ingestion import raw
    setup_logging()
    # python -m processing.extract_transforme tests/sample
    data = raw.to_rows(sys.argv[1] if len(sys.argv) > 1 else './data')
    events = extract_from_rows(data)
    for event in events[:3]:
        print(event)
