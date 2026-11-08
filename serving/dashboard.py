import logging
from processing.statistiques import sort_desc
"""
Affichage des 3 dashboards dans la console (print)
in: dictionnaires de comptage (processing/statistiques.py)
out: rien (tableaux affichés)
"""

logger = logging.getLogger(__name__)

LARGEUR_BARRE = 40      # nombre de # pour la plus grande valeur
TOP = 10                # nombre de lignes du dashboard "invalid user"


def accord(nombre, singulier, pluriel):
    """
    in: un nombre + le mot au singulier et au pluriel
    out: texte accordé, ex : "1 connexion réussie", "4 connexions réussies"
    (en français, 0 et 1 sont au singulier)
    """
    if nombre <= 1:
        return f'{nombre} {singulier}'
    return f'{nombre} {pluriel}'


def barre(nombre, maximum):
    """
    in: une valeur + la plus grande valeur du tableau
    out: barre de # proportionnelle (LARGEUR_BARRE caractères max)
    """
    if maximum <= 0:
        return ''
    longueur = round(nombre * LARGEUR_BARRE / maximum)
    # au moins un # pour qu'une petite valeur reste visible
    if nombre > 0 and longueur == 0:
        longueur = 1
    return '#' * longueur


def print_table(titre, colonne, lignes):
    """
    in: titre du tableau, nom de la 1re colonne, list de tuples (clé, nombre) déjà triée
    out: rien (affiche le tableau ou "Aucune donnée")
    """
    print()
    print(titre)
    print('=' * len(titre))

    # on garde seulement les lignes correctes (clé, nombre entier)
    lignes_ok = []
    for ligne in lignes:
        try:
            cle, nombre = ligne
            lignes_ok.append((str(cle), int(nombre)))
        except (TypeError, ValueError):
            logger.warning(f'{titre} : ligne invalide ignorée -> {ligne}')

    if not lignes_ok:
        logger.warning(f'{titre} : aucune donnée à afficher')
        print('Aucune donnée')
        return

    # largeur de la 1re colonne = le texte le plus long
    largeur = len(colonne)
    maximum = 0
    for cle, nombre in lignes_ok:
        if len(cle) > largeur:
            largeur = len(cle)
        if nombre > maximum:
            maximum = nombre

    print(f'{colonne:<{largeur}} | {"Nombre":>7} | Proportion')
    print('-' * largeur + '-+-' + '-' * 7 + '-+-' + '-' * LARGEUR_BARRE)
    for cle, nombre in lignes_ok:
        print(f'{cle:<{largeur}} | {nombre:>7} | {barre(nombre, maximum)}')


def show_dashboard(par_pays, reussites, invalid):
    """
    in: {pays: échecs}, {utilisateur: réussites}, {nom essayé: échecs invalid user}
    out: rien (affiche les 3 dashboards)
    """
    print_table('1. Échecs par pays', 'Pays', sort_desc(par_pays))
    print('Total : ' + accord(sum(par_pays.values()), 'tentative échouée', 'tentatives échouées'))

    print_table('2. Réussites par utilisateur', 'Utilisateur', sort_desc(reussites))
    print('Total : ' + accord(sum(reussites.values()), 'connexion réussie', 'connexions réussies'))

    print_table(f'3. Invalid user : total + top {TOP}', 'Utilisateur essayé', sort_desc(invalid, TOP))
    print('Total : ' + accord(sum(invalid.values()), 'tentative "invalid user"', 'tentatives "invalid user"')
          + ' avec ' + accord(len(invalid), 'nom différent', 'noms différents'))


if __name__ == "__main__":
    from log_config import setup_logging
    setup_logging()
    # données d'exemple + cas vide
    show_dashboard({'CN': 9, 'RU': 5, 'US': 4, 'Privée': 1}, {}, {'test': 4, 'admin': 3})
