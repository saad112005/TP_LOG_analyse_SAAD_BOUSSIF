import logging
import os
from processing.statistiques import sort_desc
"""
Dashboard graphique avec matplotlib : une figure avec 3 graphiques en barres horizontales
in: dictionnaires de comptage (processing/statistiques.py)
out: image output/dashboard.png + fenêtre matplotlib
matplotlib est importé dans la fonction : s'il n'est pas installé,
le reste du programme (dont le dashboard print) continue de marcher.
"""

logger = logging.getLogger(__name__)

OUTPUT_DIR = 'output'
OUTPUT_FILE = OUTPUT_DIR + '/dashboard.png'
TOP = 15                # nombre de barres max pour les pays et les "invalid user"


def draw_bars(ax, titre, label_x, label_y, lignes):
    """
    in: un graphique (ax), son titre, les noms des axes, list de tuples (clé, nombre) déjà triée
    out: rien (dessine les barres, ou "Aucune donnée" si la liste est vide)
    """
    from matplotlib.ticker import MaxNLocator

    ax.set_title(titre)
    ax.set_xlabel(label_x)
    ax.set_ylabel(label_y)

    if not lignes:
        logger.warning(f'{titre} : aucune donnée à afficher')
        ax.text(0.5, 0.5, 'Aucune donnée', ha='center', va='center', transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return

    noms = []
    valeurs = []
    for cle, nombre in lignes:
        noms.append(str(cle))
        valeurs.append(nombre)

    ax.barh(noms, valeurs)
    ax.invert_yaxis()                                   # la plus grande valeur en haut
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # graduations entières
    ax.set_xlim(0, max(valeurs) * 1.15)                 # place pour écrire le nombre au bout
    for i in range(len(valeurs)):
        ax.text(valeurs[i], i, f' {valeurs[i]}', va='center')


def save_figure(fig):
    """
    in: la figure matplotlib
    out: True si output/dashboard.png est enregistré, sinon False (+ ERROR)
    """
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        fig.savefig(OUTPUT_FILE, dpi=100)
        logger.info(f'dashboard graphique enregistré dans {OUTPUT_FILE}')
        return True
    except PermissionError as e:
        logger.error(f'pas de permission pour enregistrer {OUTPUT_FILE} ({e})')
    except OSError as e:
        # ex : "output" existe déjà mais c'est un fichier, disque plein...
        logger.error(f'impossible d\'enregistrer {OUTPUT_FILE} ({e})')
    return False


def show_dashboard_graphique(par_pays, reussites, invalid, afficher=True):
    """
    in: {pays: échecs}, {utilisateur: réussites}, {nom essayé: échecs invalid user},
        afficher=True pour ouvrir la fenêtre (plt.show)
    out: True si la figure a été créée, False si matplotlib est absent
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error('matplotlib n\'est pas installé (uv add matplotlib) : dashboard graphique ignoré')
        return False

    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    fig.suptitle('Analyse des logs SSH (auth.log)', fontsize=16)

    draw_bars(axes[0], f'Tentatives échouées par pays (top {TOP})',
              'Nombre de tentatives échouées', 'Pays', sort_desc(par_pays, TOP))
    draw_bars(axes[1], 'Connexions réussies par utilisateur',
              'Nombre de connexions réussies', 'Utilisateur', sort_desc(reussites))
    draw_bars(axes[2], f'Tentatives échouées avec "invalid user" (top {TOP})',
              'Nombre de tentatives', 'Nom d\'utilisateur essayé', sort_desc(invalid, TOP))

    fig.tight_layout()
    save_figure(fig)
    if afficher:
        plt.show()
    plt.close(fig)
    return True


if __name__ == "__main__":
    from log_config import setup_logging
    setup_logging()
    # données d'exemple + un graphique vide
    show_dashboard_graphique({'CN': 9, 'RU': 5, 'US': 4, 'Privée': 1}, {}, {'test': 4, 'admin': 3})
