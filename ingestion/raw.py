import gzip
import logging
import os
"""
Read from data all files
in:data [directory]
out:list of rows
"""

logger = logging.getLogger(__name__)


def open_file(file_path, encoding):
    """
    in: chemin d'un fichier + encodage
    out: fichier ouvert en mode texte (gzip.open pour les .gz, open sinon)
    """
    if file_path.endswith('.gz'):
        return gzip.open(file_path, mode='rt', encoding=encoding)
    return open(file_path, encoding=encoding)


def read_file(file_path):
    """
    in: chemin d'un fichier (.gz ou texte)
    out: list of rows du fichier ([] si vide, None si le fichier ne peut pas être lu)
    """
    try:
        try:
            with open_file(file_path, 'utf-8') as f:
                return f.readlines()
        except UnicodeDecodeError:
            # le fichier n'est pas en UTF-8 : on le relit en latin-1 (accepte tous les octets)
            logger.warning(f'{file_path} : encodage non UTF-8, relecture en latin-1')
            with open_file(file_path, 'latin-1') as f:
                return f.readlines()
    except FileNotFoundError:
        logger.error(f'{file_path} : fichier introuvable (supprimé pendant la lecture ?)')
    except PermissionError:
        logger.error(f'{file_path} : permission refusée, fichier ignoré')
    except (gzip.BadGzipFile, EOFError):
        logger.error(f'{file_path} : fichier .gz corrompu ou incomplet, fichier ignoré')
    except OSError as e:
        logger.error(f'{file_path} : erreur de lecture ({e}), fichier ignoré')
    return None


def to_rows(path: str):
    """
    in: chemin du dossier data
    out: list of rows de tous les fichiers du dossier ([] si erreur)
    """
    try:
        files = sorted(os.listdir(path))
    except FileNotFoundError:
        logger.error(f'{path} : dossier introuvable')
        return []
    except NotADirectoryError:
        logger.error(f'{path} : ce n\'est pas un dossier')
        return []
    except PermissionError:
        logger.error(f'{path} : permission refusée sur le dossier')
        return []

    if not files:
        logger.warning(f'{path} : dossier vide, aucun fichier à lire')
        return []

    rows = []
    nb_files = 0
    for file in files:
        file_path = os.path.join(path, file)
        # un sous-dossier n'est pas un fichier de log : on le saute
        if os.path.isdir(file_path):
            logger.warning(f'{file_path} : sous-dossier ignoré')
            continue
        file_rows = read_file(file_path)
        if file_rows is None:
            continue            # erreur déjà loggée dans read_file
        if not file_rows:
            logger.warning(f'{file_path} : fichier vide')
            continue
        logger.info(f'{file_path} : {len(file_rows)} lignes lues')
        rows.extend(file_rows)
        nb_files += 1

    logger.info(f'Total : {len(rows)} lignes lues dans {nb_files} fichier(s)')
    return rows


if __name__ == "__main__":
    import sys
    from log_config import setup_logging
    setup_logging()
    # on peut donner un autre dossier en argument : python -m ingestion.raw tests/data_erreurs
    data = to_rows(sys.argv[1] if len(sys.argv) > 1 else './data')
    if data:
        print(data[:3])
