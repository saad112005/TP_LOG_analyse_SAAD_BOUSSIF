import logging
import os
from logging.handlers import RotatingFileHandler
"""
Configuration du logging pour tout le pipeline (chapitre 1 : logging)
in: niveau minimum des messages (INFO par défaut)
out: logger racine configuré -> fichier logs/app.log + console
Chaque module fait ensuite : logger = logging.getLogger(__name__)
"""

LOG_DIR = 'logs'
LOG_FILE = LOG_DIR + '/app.log'

# même format que dans le cours
logger_format = logging.Formatter(
    fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S'
)

logger = logging.getLogger(__name__)


def setup_logging(level=logging.INFO):
    root = logging.getLogger()
    # si le logging est déjà configuré, on ne rajoute pas les handlers une 2e fois
    if root.handlers:
        return root
    root.setLevel(level)

    # 1. console
    console = logging.StreamHandler()
    console.setFormatter(logger_format)
    root.addHandler(console)

    # 2. fichier logs/app.log avec rotation (1 Mo max, 5 anciens fichiers gardés)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        file_rotate = RotatingFileHandler(
            filename=LOG_FILE,
            maxBytes=1_000_000,
            backupCount=5,
            encoding='utf-8',
        )
        file_rotate.setFormatter(logger_format)
        root.addHandler(file_rotate)
    except PermissionError as e:
        # pas le droit d'écrire : on continue avec la console seulement
        logger.warning(f'Pas de permission pour écrire dans {LOG_FILE} ({e}) : logs en console uniquement')
    except OSError as e:
        # ex : "logs" existe déjà mais c'est un fichier, disque plein...
        logger.warning(f'Impossible de créer {LOG_FILE} ({e}) : logs en console uniquement')

    return root


if __name__ == "__main__":
    setup_logging(logging.DEBUG)
    logger.debug('From logger Debug message')
    logger.info('From logger Info message')
    logger.warning('From logger Warning message')
    logger.error('From logger Error message')
    logger.critical('From logger Critical message')
