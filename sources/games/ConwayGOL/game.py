# Importation des librairies

import pygame
from os import path
from utils import loadAssetsFolder, PopUp, Button
from .simulation import CatalogItem, catalog_items, simulate, render, reset

# Information importante : ce jeu a été développé "à part" du système de mini-jeux et a ensuite été importé ce qui explique sa structure un peu étrange

FOLDER_PATH = path.dirname(__file__)  # Chemin absolu du dossier contenant ce script
WINDOW_WIDTH, WINDOW_HEIGHT = WINDOW_SIZE = (1600, 900)

event_list = []  # Liste des évènements

surface = pygame.Surface(WINDOW_SIZE)  # La surface utilisée dans la fonction display
info: PopUp = None
info_button: Button = None
music: pygame.Sound = None

# On définit les 5 fonctions principales

def load() -> None:
    """
    La fonction load charge les assets.
    """
    def onClickClose() -> None:
        info.displayed = False
    
    def openInfo() -> None:
        info.displayed = True
    
    global info, info_button, music
    
    assets = {}
    loadAssetsFolder(assets, path.join(FOLDER_PATH, "assets"))  # On utilise la fonction utilitaire loadAssetsFolder définie dans sources/utils.py

    music = assets["sounds"]["music.mp3"]

    info = PopUp(surface, WINDOW_WIDTH//2, WINDOW_HEIGHT//2, assets["images"]["info.png"],
                 Button(380, -280, assets["images"]["close.png"], onClickClose))
    info_button = Button(WINDOW_WIDTH-50, 50, assets["images"]["info_button.png"], openInfo, surface)

    CatalogItem.catalog = assets["json"]["catalog.json"]
    for i in range(len(CatalogItem.catalog)):
        catalog_items.append(CatalogItem(i))


def init() -> None:
    """
    Initialise/réinitialise le mini-jeu
    """
    event_list.clear()
    info.displayed = False
    music.play(-1)
    reset()


def tick(keys: dict, mouse: dict, wheel: int) -> None:
    """
    Docstring for tick
    
    :param keys: Dictionnaire des touches pressées par l'utilisateur. Les valeurs correspondent à la durée de la pression de la touche. Exemple `{pygame.K_UP: 8, pygame.K_LEFT: 0, pygame.K_RIGHT: 1}`
    :type keys: dict
    :param mouse: Dictionnaire contenant les informations liées à la souris `{'x': int, 'y'; int, 'click': list[int, int, int]}`
    :type mouse: dict
    :param wheel: Mouvement de la roulette de la souris depuis le dernier tick
    :type wheel: int
    """

    click = 0 if info.displayed else mouse["click"][0]

    if info_button.tick(mouse["x"], mouse["y"], click):
        click = 0

    simulate(keys, [click, mouse["x"], mouse["y"]], wheel)

    if info.displayed:
        info.tick(mouse["x"], mouse["y"], mouse["click"][0])

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
    info_button.display()
    if info.displayed:
        info.display()
    
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


def quit() -> None:
    music.stop()
    