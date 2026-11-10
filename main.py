import logging
import sys
from log_config import setup_logging
from ingestion import raw
from processing import extract_transforme, geo_location, statistiques
from serving import dashboard, dashboard_graphique
"""
Pipeline Log Analyzer
in: dossier des fichiers auth.log (./data par défaut)
out: 3 dashboards dans la console + dashboard graphique (output/dashboard.png)
     + messages dans logs/app.log
utilisation : python main.py [dossier]
"""

logger = logging.getLogger(__name__)

DATA_DIR = './data'


def run(path):
    """
    in: chemin du dossier des logs
    out: code de sortie (0 = tout s'est bien passé, 1 = arrêt sur erreur)
    """
    logger.info(f'début de l\'analyse du dossier {path}')

    # 1. ingestion : lecture de tous les fichiers du dossier
    data = raw.to_rows(path)
    if not data:
        logger.critical(f'aucune ligne lue dans {path} (dossier inexistant, vide ou fichiers illisibles) : arrêt')
        return 1

    # 2. extraction : échecs et réussites sshd
    events = extract_transforme.extract_from_rows(data)
    if not events:
        logger.critical(f'aucune connexion sshd trouvée dans {path} : '
                        f'ce ne sont pas des fichiers de log auth.log, arrêt')
        return 1

    # 3. pays des ip (seulement pour les échecs : c'est le seul dashboard qui en a besoin)
    ips = set()
    for event in events:
        if event['status'] == 'failed':
            ips.add(event['ip'])
    countries = geo_location.get_countries(ips)

    # 4. calcul des 3 dashboards
    par_pays = statistiques.failed_by_country(events, countries)
    reussites = statistiques.success_by_user(events)
    invalid = statistiques.invalid_user_attempts(events)

    # 5. affichage : d'abord dans la console, puis la figure matplotlib
    dashboard.show_dashboard(par_pays, reussites, invalid)
    dashboard_graphique.show_dashboard_graphique(par_pays, reussites, invalid)
    logger.info('analyse terminée')
    return 0


if __name__ == "__main__":
    setup_logging()
    if len(sys.argv) > 2:
        logger.warning(f'arguments en trop ignorés : {sys.argv[2:]} (utilisation : python main.py [dossier])')
    path = sys.argv[1] if len(sys.argv) > 1 else DATA_DIR

    try:
        code = run(path)
    except KeyboardInterrupt:
        # Ctrl+C : arrêt propre (le cache des pays est déjà sauvegardé par geo_location)
        logger.warning('analyse interrompue par l\'utilisateur (Ctrl+C)')
        code = 130
    except Exception as e:
        # erreur imprévue : on garde le détail dans logs/app.log avant d'arrêter
        logger.critical(f'erreur inattendue : {e}', exc_info=True)
        code = 1
    sys.exit(code)
