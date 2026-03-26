# Importation des librairies

import pygame
from os import path
from utils import loadAssetsFolder
from .simulation import CatalogItem, catalog_items, simulate, render


WINDOW_WIDTH, WINDOW_HEIGHT = WINDOW_SIZE = (1600, 900)
FOLDER_PATH = path.dirname(__file__)  # Chemin absolu du dossier contenant ce script

event_list = []  # Liste des évènements

surface = pygame.Surface(WINDOW_SIZE)  # La surface utilisée dans la fonction display

# Préciser le type de la variable est facultatif mais permet à l'éditeur de code de proposer l'auto-complétion
# Les variables initialisées à None sont des variables globales qui seront initialisées dans la fonction load


# On initialise les variables qui vont contenir les assets
background: pygame.Surface = None

# On définit les 5 fonctions principales

def load() -> None:
    """
    La fonction load charge les assets.
    """
    
    assets = {}
    loadAssetsFolder(assets, path.join(FOLDER_PATH, "assets"))  # On utilise la fonction utilitaire loadAssetsFolder définie dans sources/utils.py

    CatalogItem.catalog = assets["json"]["catalog.json"]
    for i in range(len(CatalogItem.catalog)):
        catalog_items.append(CatalogItem(i))


def init() -> None:
    """
    Initialise/réinitialise le mini-jeu
    """
    event_list.clear()


def tick(keys: dict, mouse: dict, wheel: int) -> None:
    """
    Docstring for tick
    
    :param keys: Dictionnaire des touches pressées par l'utilisateur. Les valeurs correspondent à la durée de la pression de la touche. Exemple `{pygame.K_UP: 8, pygame.K_LEFT: 0, pygame.K_RIGHT: 1}`
    :type keys: dict
    :param mouse: Dictionnaire contenant les informations liées à la souris `{'x': int, 'y'; int, 'click': list[int, int, int]}`
    :type mouse: dict
    """

    simulate(keys, [mouse["click"][0], mouse["x"], mouse["y"]], wheel)

    # Option pour mettre en pause

    if keys[pygame.K_ESCAPE]:
        event_list.append({"type": "pause"})


def display() -> pygame.Surface:
    """
    Docstring for display
    
    :return: L'affichage du mini-jeu
    :rtype: pygame.Surface
    """
    surface.fill((255, 255, 255))

    render(surface)
    
    return surface


def events() -> list:
    """
    Docstring for events
    
    :return: Retourne la liste des évènements s'étant produit dans le mini-jeu. Exemple `['quit']`
    :rtype: list[str]
    """
    events_copy = event_list.copy()
    event_list.clear()  # On vide la liste des évènements pour ne pas les renvoyer à nouveau au prochain appel
    return events_copy
    